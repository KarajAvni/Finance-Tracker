from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Use the correct class name
        if form.is_valid():
            user = form.save()
            # Optional: login the user directly
            # from django.contrib.auth import login
            # login(request, user)
            return redirect('login')  # Redirect to login page after registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

def custom_logout(request):
    logout(request)
    storage = messages.get_messages(request)
    storage.used = True
    return redirect('home')