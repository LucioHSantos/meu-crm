from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CustomUserCreationForm, CustomUserChangeForm, LoginForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('dashboard:index')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def register_view(request):
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to create users.')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('accounts:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_list_view(request):
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:index')

    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_edit_view(request, pk):
    if not (request.user.is_admin_user() or request.user.pk == pk):
        messages.error(request, 'You do not have permission to edit this user.')
        return redirect('accounts:user_list')

    edited_user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=edited_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{edited_user.username}" updated successfully.')
            if request.user.is_admin_user():
                return redirect('accounts:user_list')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=edited_user)

    return render(request, 'accounts/user_edit.html', {'form': form, 'edited_user': edited_user})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
