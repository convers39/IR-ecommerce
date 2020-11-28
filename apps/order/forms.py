
from django import forms

from account.models import Address


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ('recipient', 'phone_no', 'addr', 'city',
                  'country', 'zip_code', 'is_default')

        widgets = {
            'recipient': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={}),
            'addr': forms.TextInput(attrs={}),
            'city': forms.TextInput(attrs=...),
            'country': forms.TextInput(attrs=...),
            'zip_code': forms.TextInput(attrs=...),
            'is_default': forms.CheckboxInput(attrs=...)

        }
