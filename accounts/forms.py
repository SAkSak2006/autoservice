from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(
        max_length=12,
        required=True,
        label='Телефон',
        widget=forms.TextInput(attrs={'placeholder': '+7XXXXXXXXXX'}),
    )
    first_name = forms.CharField(max_length=150, required=True, label='Имя')
    last_name = forms.CharField(max_length=150, required=True, label='Фамилия')
    patronymic = forms.CharField(max_length=150, required=False, label='Отчество')
    consent_personal_data = forms.BooleanField(
        required=True,
        label='Я согласен на обработку персональных данных',
    )

    class Meta:
        model = User
        fields = (
            'email', 'phone', 'last_name', 'first_name', 'patronymic',
            'password1', 'password2', 'consent_personal_data',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role = User.Role.CLIENT
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'patronymic', 'email', 'phone',
            'avatar', 'notification_preferences',
        )
        widgets = {
            'notification_preferences': forms.HiddenInput(),
        }

    notify_email = forms.BooleanField(required=False, label='Email-уведомления')
    notify_telegram = forms.BooleanField(required=False, label='Telegram-уведомления')
    notify_sms = forms.BooleanField(required=False, label='SMS-уведомления')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            prefs = self.instance.notification_preferences or {}
            self.fields['notify_email'].initial = prefs.get('email', False)
            self.fields['notify_telegram'].initial = prefs.get('telegram', False)
            self.fields['notify_sms'].initial = prefs.get('sms', False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.notification_preferences = {
            'email': self.cleaned_data.get('notify_email', False),
            'telegram': self.cleaned_data.get('notify_telegram', False),
            'sms': self.cleaned_data.get('notify_sms', False),
        }
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    login_field = forms.CharField(
        label='Email или телефон',
        widget=forms.TextInput(attrs={'placeholder': 'Email или +7XXXXXXXXXX'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super().clean()
        login_field = cleaned_data.get('login_field', '').strip()
        password = cleaned_data.get('password')

        if not login_field or not password:
            return cleaned_data

        # Determine if email or phone
        if '@' in login_field:
            try:
                user_obj = User.objects.get(email=login_field)
                username = user_obj.username
            except User.DoesNotExist:
                raise forms.ValidationError('Неверный email или пароль.')
        elif login_field.startswith('+7'):
            try:
                user_obj = User.objects.get(phone=login_field)
                username = user_obj.username
            except User.DoesNotExist:
                raise forms.ValidationError('Неверный телефон или пароль.')
        else:
            username = login_field

        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError('Неверные учётные данные.')
        if not user.is_active:
            raise forms.ValidationError('Аккаунт деактивирован.')

        cleaned_data['user'] = user
        return cleaned_data
