from django import forms
from clients.models import Vehicle
from clients.forms import CAR_MAKES


class PortalVehicleForm(forms.ModelForm):
    make = forms.CharField(
        max_length=50, label='Марка',
        widget=forms.TextInput(attrs={'list': 'car-makes-list', 'placeholder': 'Марка'}),
    )

    class Meta:
        model = Vehicle
        fields = ('make', 'model', 'year', 'license_plate', 'vin')
        widgets = {
            'model': forms.TextInput(attrs={'placeholder': 'Модель'}),
            'year': forms.NumberInput(attrs={'placeholder': 'Год', 'min': 1900, 'max': 2027}),
            'license_plate': forms.TextInput(attrs={'placeholder': 'А123БВ777'}),
            'vin': forms.TextInput(attrs={'placeholder': 'VIN (необязательно)', 'maxlength': 17}),
        }


class PortalSettingsForm(forms.Form):
    first_name = forms.CharField(max_length=100, label='Имя')
    last_name = forms.CharField(max_length=100, label='Фамилия')
    patronymic = forms.CharField(max_length=100, required=False, label='Отчество')
    email = forms.EmailField(required=False, label='Email')
    phone = forms.CharField(max_length=20, label='Телефон')
    notify_email = forms.BooleanField(required=False, label='Email-уведомления')
    notify_telegram = forms.BooleanField(required=False, label='Telegram-уведомления')
    notify_sms = forms.BooleanField(required=False, label='SMS-уведомления')


class BookingStep1Form(forms.Form):
    vehicle = forms.IntegerField(widget=forms.HiddenInput())


class BookingStep2Form(forms.Form):
    services = forms.CharField(widget=forms.HiddenInput(), required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишите проблему...'}),
        required=False, label='Описание проблемы',
    )


class BookingStep3Form(forms.Form):
    booking_date = forms.DateField(widget=forms.HiddenInput())
    booking_time = forms.TimeField(widget=forms.HiddenInput())
