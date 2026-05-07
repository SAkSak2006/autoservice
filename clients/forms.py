from django import forms
from django.forms import inlineformset_factory
from .models import Client, Vehicle


CAR_MAKES = [
    '', 'Audi', 'BMW', 'Chevrolet', 'Citroën', 'Ford', 'Honda', 'Hyundai',
    'Kia', 'Lada (ВАЗ)', 'Lexus', 'Mazda', 'Mercedes-Benz', 'Mitsubishi',
    'Nissan', 'Opel', 'Peugeot', 'Renault', 'Skoda', 'Subaru', 'Suzuki',
    'Toyota', 'Volkswagen', 'Volvo', 'ГАЗ', 'УАЗ',
]


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            'last_name', 'first_name', 'patronymic',
            'phone', 'email', 'consent_personal_data', 'notes',
        )
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+7XXXXXXXXXX'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class VehicleForm(forms.ModelForm):
    make = forms.CharField(
        max_length=50,
        label='Марка',
        widget=forms.TextInput(attrs={
            'list': 'car-makes-list',
            'placeholder': 'Начните вводить марку...',
        }),
    )

    class Meta:
        model = Vehicle
        fields = ('make', 'model', 'year', 'license_plate', 'vin', 'color', 'mileage', 'notes')
        widgets = {
            'vin': forms.TextInput(attrs={'placeholder': 'XXXXXXXXXXXXXXXXX', 'maxlength': 17}),
            'license_plate': forms.TextInput(attrs={'placeholder': 'А123БВ777'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


VehicleInlineFormSet = inlineformset_factory(
    Client,
    Vehicle,
    form=VehicleForm,
    extra=1,
    can_delete=False,
)


class ClientSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'ФИО, телефон, email или госномер...',
            'class': 'form-control',
        }),
    )
