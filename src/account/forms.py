from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "mb-3 ps-3 text-input", "placeholder": "Введите текст..."}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "ps-3 text-input", "placeholder": "Password"}
        )
    )


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "mb-3 ps-3 text-input", "placeholder": "Input password..."},
        ),
    )
    password2 = forms.CharField(
        label="Repeat password",
        widget=forms.PasswordInput(
            attrs={
                "class": "mb-3 ps-3 text-input",
                "placeholder": "Repeat password...",
            },
        ),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "email"]

    def clean_password2(self):
        cd = self.cleaned_data
        if cd["password"] != cd["password2"]:
            raise forms.ValidationError("Passwords don't match.")
        return cd["password2"]
