from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm as AuthPasswordChangeForm


class RegistrationForm(UserCreationForm):
    """
    Форма для регистрации новых пользователей.
    """
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    """
    Форма для редактирования профиляю
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PasswordChangeForm(AuthPasswordChangeForm):
    error_css_class = 'error'
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Старый пароль'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Новый пароль'})
        self.fields['new_password2'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Повторите новый пароль'})
