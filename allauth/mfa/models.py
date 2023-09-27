from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from allauth import app_settings as allauth_settings


if not allauth_settings.MFA_ENABLED:
    raise ImproperlyConfigured(
        "allauth.mfa not installed, yet its models are imported."
    )


class AuthenticatorManager(models.Manager):
    def delete_dangling_recovery_codes(self, user):
        deleted_authenticator = None
        qs = Authenticator.objects.filter(user=user)
        if not qs.exclude(type=Authenticator.Type.RECOVERY_CODES).exists():
            deleted_authenticator = qs.first()
            qs.delete()
        return deleted_authenticator

    def delete_and_cleanup(self, authenticator):
        authenticator.delete()
        self.delete_dangling_recovery_codes(authenticator.user)


class Authenticator(models.Model):
    class Type(models.TextChoices):
        RECOVERY_CODES = "recovery_codes", _("Recovery codes")
        TOTP = "totp", _("TOTP Authenticator")
        WEBAUTHN = "webauthn", _("WebAuthn")

    objects = AuthenticatorManager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices)
    data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    last_used_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "type"],
                name="unique_authenticator_type",
                condition=Q(
                    type__in=(
                        "totp",
                        "recovery_codes",
                    )
                ),
            )
        ]

    def __str__(self):
        if self.type == self.Type.WEBAUTHN:
            return self.wrap().name
        return self.get_type_display()

    def __str__(self):
        return self.get_type_display()

    def wrap(self):
        from allauth.mfa.recovery_codes import RecoveryCodes
        from allauth.mfa.totp import TOTP
        from allauth.mfa.webauthn import WebAuthn

        return {
            self.Type.TOTP: TOTP,
            self.Type.RECOVERY_CODES: RecoveryCodes,
            self.Type.WEBAUTHN: WebAuthn,
        }[self.type](self)

    def record_usage(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
