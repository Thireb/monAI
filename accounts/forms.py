"""Forms for user registration, admin edits, and profile updates."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users via the admin or signup flows."""

    class Meta:
        model = User
        fields = ("email", "username")


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in the admin interface."""

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name")


class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile and Resend email settings."""

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "resend_api_key",
            "resend_from_email",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "First Name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Last Name"}
            ),
            "resend_api_key": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Leave blank to keep current key",
                    "autocomplete": "off",
                },
                render_value=False,
            ),
            "resend_from_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "you@yourdomain.com",
                }
            ),
        }
        help_texts = {
            "resend_api_key": (
                "Your Resend API key (re_…). Required to email budget PDFs from the app."
            ),
            "resend_from_email": (
                "Sender address verified in your Resend account (e.g. onboarding@yourdomain.com)."
            ),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Apply Bootstrap classes to labels/help text."""
        super().__init__(*args, **kwargs)
        self.fields["resend_api_key"].required = False
        # Validation copies the blank field onto the instance, so keep the old key now.
        self.saved_resend_api_key = self.instance.resend_api_key if self.instance.pk else ""

    def clean_email(self) -> str:
        """Ensure the email is unique among all users except the current one."""
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit: bool = True) -> User:
        """Persist profile fields; keep existing API key when the password field is left blank."""
        user = super().save(commit=False)
        new_key = self.cleaned_data.get("resend_api_key", "")
        if not new_key and self.saved_resend_api_key:
            user.resend_api_key = self.saved_resend_api_key
        if commit:
            user.save()
        return user
