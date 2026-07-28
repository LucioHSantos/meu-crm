from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from .models import User


INPUT_CLASSES = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500'


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Email'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'First name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Last name'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Phone'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': INPUT_CLASSES}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']


class CustomUserChangeForm(UserChangeForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Email'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'First name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Last name'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Phone'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': INPUT_CLASSES}))
    avatar = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'w-full text-white'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Password'}))
