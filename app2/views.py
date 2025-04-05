from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import App2User
from .forms import App2UserCreationForm, App2AuthenticationForm
from .auth_backend import App2AuthBackend

def home(request):
    if request.user.is_authenticated and not isinstance(request.user, App2User):
        logout(request)
    return render(request, 'app2/home.html')

def login_view(request):
    if request.user.is_authenticated and isinstance(request.user, App2User):
        return redirect('app2:home')
        
    if request.method == 'POST':
        form = App2AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and isinstance(user, App2User):
                login(request, user, backend='app2.auth_backend.App2AuthBackend')
                messages.success(request, f'Welcome back, {username}!')
                return redirect('app2:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = App2AuthenticationForm()
    return render(request, 'app2/login.html', {'form': form})

def register(request):
    if request.user.is_authenticated and isinstance(request.user, App2User):
        return redirect('app2:home')
        
    if request.method == 'POST':
        form = App2UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='app2.auth_backend.App2AuthBackend')
            messages.success(request, 'Registration successful!')
            return redirect('app2:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = App2UserCreationForm()
    return render(request, 'app2/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app2:home') 