from django import forms

class PINForm(forms.Form):
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit PIN',
            'class': 'pin-input',
            'autocomplete': 'off',
            'pattern': '\d{6}',
            'title': '6-digit PIN'
        })
    )
    target_email = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the exact email alias (e.g. rahul@...)',
            'class': 'pin-input',
            'autocomplete': 'off',
            'style': 'margin-top: 12px; font-size: 15px; letter-spacing: normal; text-align: left;'
        })
    )

class AppPasswordForm(forms.Form):
    email_address = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter Client Gmail address',
            'class': 'pin-input'
        })
    )
    app_password = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 16-character App Password',
            'class': 'pin-input',
            'autocomplete': 'off'
        })
    )
