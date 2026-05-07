from django import forms
from .models import ServiceCategory, Service, SparePart


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ('name', 'description', 'icon', 'sort_order', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'icon': forms.TextInput(attrs={'placeholder': 'fas fa-wrench'}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('category', 'name', 'description', 'base_price', 'estimated_duration', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'base_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'estimated_duration': forms.NumberInput(attrs={'min': '1', 'placeholder': 'мин.'}),
        }


class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = (
            'name', 'part_number', 'manufacturer', 'price',
            'quantity_in_stock', 'min_stock_level', 'unit', 'is_active',
        )
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
