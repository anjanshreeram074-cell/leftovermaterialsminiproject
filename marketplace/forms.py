from django import forms
from .models import User, Material, MaterialImage, Location

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password']

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'quantity', 'unit', 'original_price', 'selling_price', 'condition']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'category': forms.Select(attrs={'class': 'select'}),
            'quantity': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'unit': forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g. bags, sqft, meters'}),
            'original_price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'condition': forms.Select(attrs={'class': 'select'}),
        }

class LocationForm(forms.Form):
    lat = forms.DecimalField(max_digits=9, decimal_places=6, widget=forms.HiddenInput())
    lng = forms.DecimalField(max_digits=9, decimal_places=6, widget=forms.HiddenInput())
    address = forms.CharField(widget=forms.HiddenInput())

class ImageUploadForm(forms.Form):
    images = forms.FileField(widget=forms.FileInput(attrs={'accept': 'image/*'}), required=False)