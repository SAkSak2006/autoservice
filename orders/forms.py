from django import forms
from accounts.models import User
from clients.models import Client, Vehicle
from services.models import Service, SparePart
from .models import WorkOrder, WorkOrderItem, WorkOrderPart


class WorkOrderCreateForm(forms.ModelForm):
    """Step-by-step creation form (all steps in one form, JS handles wizard)."""

    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(is_active=True),
        label='Клиент',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        label='Автомобиль',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    assigned_mechanic = forms.ModelChoiceField(
        queryset=User.objects.filter(role='mechanic', is_active=True),
        required=False,
        label='Мастер',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = WorkOrder
        fields = ('client', 'vehicle', 'assigned_mechanic', 'description', 'estimated_completion')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишите проблему...'}),
            'estimated_completion': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If client is set (POST), filter vehicles for that client
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['vehicle'].queryset = Vehicle.objects.filter(client_id=client_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.client_id:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(client=self.instance.client)


class WorkOrderUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = (
            'assigned_mechanic', 'description', 'diagnosis',
            'recommendations', 'discount_percent', 'estimated_completion',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'recommendations': forms.Textarea(attrs={'rows': 3}),
            'estimated_completion': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
            ),
        }


class WorkOrderItemForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True).select_related('category'),
        label='Услуга',
    )

    class Meta:
        model = WorkOrderItem
        fields = ('service', 'quantity', 'price', 'notes')
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1', 'value': '1', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Примечание'}),
        }


class WorkOrderPartForm(forms.ModelForm):
    spare_part = forms.ModelChoiceField(
        queryset=SparePart.objects.filter(is_active=True),
        label='Запчасть',
    )

    class Meta:
        model = WorkOrderPart
        fields = ('spare_part', 'quantity', 'price_per_unit', 'notes')
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1', 'value': '1', 'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Примечание'}),
        }


class OrderFilterForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={
        'placeholder': 'Номер заказа, ФИО клиента, госномер...',
        'class': 'form-control',
    }))
    status = forms.MultipleChoiceField(
        required=False,
        choices=WorkOrder.Status.choices,
        widget=forms.CheckboxSelectMultiple,
    )
    mechanic = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(role='mechanic', is_active=True),
        empty_label='Все мастера',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
    )
