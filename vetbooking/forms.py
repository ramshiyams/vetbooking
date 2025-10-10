from django import forms
from .models import Pet, Appointment, Order, Product
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Vet
class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'pet_type', 'age']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pet name'}),
            'pet_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pet type'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter pet age'}),
        }
class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class VetForm(forms.ModelForm):
    class Meta:
        model = Vet
        fields = ['name', 'specialization', ]
        widgets = {
            'available_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'image']