from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from accounts.forms import RegistrationForm, UserUpdateForm


def registration(request):
    """
        Отображение страницы регистрации нового пользователя.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аккаунт создан успешно!')
            return redirect('log_in')
        else:
            messages.warning(request, 'Неверно введены данные!')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def log_in(request):
    """
        Отображение страницы входа пользователя в систему.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('expense_list')
        else:
            messages.warning(request, 'Неверный логин или пароль!')
    return render(request, 'accounts/log_in.html')


def logout_page(request):
    """
        Выход пользователя из системы.
    """
    logout(request)
    return redirect('log_in')


@login_required
def edit_profile(request):
    """
        Изменение профиля пользователя.
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Ваш профиль успешно изменен!')
            return redirect('edit_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html',
                  {'user_form': user_form})


def change_password(request):
    """
        Изменение пароля пользователя.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Ваш пароль успешно изменен!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
