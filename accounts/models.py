"""User account models with email as the primary login identifier."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager["CustomUser"]):
    """Custom user manager where email is the unique identifier."""

    def create_user(
        self,
        email: str,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> CustomUser:
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> CustomUser:
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model with email as the primary identifier."""

    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    resend_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Resend API key for budget PDF emails.",
    )
    resend_from_email = models.EmailField(
        blank=True,
        help_text="Verified sender address in your Resend account.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email

    def has_resend_email_config(self) -> bool:
        """Return True when Resend API key and from email are both set."""
        return bool(
            (self.resend_api_key or "").strip() and (self.resend_from_email or "").strip()
        )
