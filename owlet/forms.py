from django import forms

from .models import OwletAccount


class OwletAccountCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, help_text="Used once to retrieve a refresh token; not stored.")

    class Meta:
        model = OwletAccount
        fields = ["email", "region", "password"]


class OwletDeviceMapForm(forms.Form):
    child_id = forms.IntegerField(required=False)

