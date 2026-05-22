from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model  = Order
        fields = ['client_name', 'phone', 'address']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Votre prénom'), 'autocomplete': 'given-name'}),
            'phone':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+32 4XX XX XX XX', 'autocomplete': 'tel', 'inputmode': 'tel'}),
            'address':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Rue, numéro, commune'), 'autocomplete': 'street-address'}),
        }
        labels = {
            'client_name': _('Prénom'),
            'phone':       _('Téléphone'),
            'address':     _('Adresse de livraison'),
        }
