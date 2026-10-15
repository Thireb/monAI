"""Tests for accounts.fields.EncryptedCharField (the encrypted Resend API key)."""

from __future__ import annotations

import importlib

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings

from accounts.fields import PREFIX, decrypt, encrypt
from accounts.forms import ProfileUpdateForm

User = get_user_model()
KEY = "re_test_1234567890abcdef"
migration = importlib.import_module("accounts.migrations.0006_encrypt_resend_api_key")


def raw_key(user_id: int) -> str:
    """The value as it is in the database, past the field."""
    table = User._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT resend_api_key FROM {table} WHERE id = %s", [user_id])
        return cursor.fetchone()[0]


def set_raw_key(user_id: int, value: str) -> None:
    """Write a value to the database, past the field (an old plain-text key)."""
    table = User._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET resend_api_key = %s WHERE id = %s", [value, user_id])


class EncryptedFieldTests(TestCase):
    """The key is plain in Python and encrypted in the database."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="enc", email="enc@example.com", password="testpassword"
        )

    def test_round_trip(self) -> None:
        self.user.resend_api_key = KEY
        self.user.save()
        stored = raw_key(self.user.pk)
        self.assertTrue(stored.startswith(PREFIX))
        self.assertNotIn(KEY, stored)
        self.assertLessEqual(len(stored), 255)
        self.assertEqual(User.objects.get(pk=self.user.pk).resend_api_key, KEY)

    def test_old_plain_text_still_reads(self) -> None:
        set_raw_key(self.user.pk, KEY)
        self.assertEqual(User.objects.get(pk=self.user.pk).resend_api_key, KEY)

    def test_changed_secret_key_reads_as_empty(self) -> None:
        stored = encrypt(KEY)
        with override_settings(SECRET_KEY="another-secret-key-" + "x" * 40):
            self.assertEqual(decrypt(stored), "")
        self.assertEqual(decrypt(stored), KEY)
        self.assertEqual(encrypt(""), "")

    def test_profile_form_keeps_and_limits_the_key(self) -> None:
        self.user.resend_api_key = KEY
        self.user.save()
        data = {"username": "enc", "email": "enc@example.com", "resend_api_key": ""}
        form = ProfileUpdateForm(data, instance=User.objects.get(pk=self.user.pk))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(User.objects.get(pk=self.user.pk).resend_api_key, KEY)
        form = ProfileUpdateForm(
            {**data, "resend_api_key": "x" * 121}, instance=User.objects.get(pk=self.user.pk)
        )
        self.assertFalse(form.is_valid())

    def test_migration_encrypts_and_decrypts(self) -> None:
        set_raw_key(self.user.pk, KEY)
        migration.encrypt_keys(apps, connection.schema_editor())
        self.assertTrue(raw_key(self.user.pk).startswith(PREFIX))
        migration.encrypt_keys(apps, connection.schema_editor())  # Runs twice safely.
        self.assertEqual(User.objects.get(pk=self.user.pk).resend_api_key, KEY)
        migration.decrypt_keys(apps, connection.schema_editor())
        self.assertEqual(raw_key(self.user.pk), KEY)
