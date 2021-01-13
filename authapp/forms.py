from django import forms
from .models import *

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control ',
                'autofocus': True
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'autofocus': True
            }
        )
    )
