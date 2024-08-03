from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q #provides functionality to search the query using | and &
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required #to restrict the users from accessing certain function who are not loggedin 


# Create your views here.

def loginPage(request):
    page = "login"
    if request.method == "POST":
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email = email)
        except:
            messages.error(request, "User does not exist!")

        user = authenticate(request, email = email, password = password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username or password is incorrect!")

    context = {'page' : page}
    return render(request, 'base/login_register.html', context)

def logoutPage(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Error occurred during registration")
    context = {'form' : form}
    return render(request, 'base/login_register.html', context)


def user_profile(request, pk):
    user = User.objects.get(id = pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {"user" : user,"rooms":rooms, 'room_messages' : room_messages, 'topics' : topics}
    return render(request, 'base/profile.html', context)



def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q))
    room_count = rooms.count()

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    topics = Topic.objects.all()[0:5]
    context = {'rooms':rooms, 'topics' : topics, 'room_count' : room_count, 'room_messages' : room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id = pk)   
    room_messages = room.message_set.all()


    participant = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk = room.id)

    context = {'room' : room, "room_messages" : room_messages, 'participants': participant}
    return render(request, 'base/room.html', context)

@login_required(login_url='login')
def createRoom(request):
    topics = Topic.objects.all()
    form = RoomForm()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)#if the topic is already there, then it is gonig to get that topic else going to create it and give it to created

        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        return redirect('home')

    context = {'form' : form, 'topics' : topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    topics = Topic.objects.all()
    room = Room.objects.get(id = pk)
    form = RoomForm(instance=room)
    
    #authenticating access
    if request.user != room.host:
        return HttpResponse("You do not have access to perform these actions!")
    
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
        
    context = {'form' : form, 'topics' : topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id = pk)

    
    if request.user != room.host:
        return HttpResponse("You do not have access to perform these actions!")
    
    if request.method == "POST":
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj':room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id = pk)

   
    if request.user != message.user:
        return HttpResponse("You do not have access to perform these actions!")
    
    if request.method == "POST":
        message.delete()
        return redirect('room', pk = message.room.id)

    return render(request, 'base/delete.html', {'obj':message})

@login_required(login_url = 'login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk = user.id)

    return render(request, 'base/update-user.html', {'form' : form})

#For Mobile view
def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains = q)
    
    context = {'topics' : topics}
    return render(request, "base/topics.html", context)

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages' : room_messages})