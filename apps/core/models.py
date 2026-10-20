from django.db import models
import datetime

class SharedInbox(models.Model):
    email_address = models.EmailField()
    app_password = models.CharField(max_length=255, blank=True, null=True, help_text='Google App Password (16 characters)')
    pin = models.CharField(max_length=6, unique=True, blank=True)
    allowed_domain = models.CharField(max_length=255, blank=True, null=True, help_text='Strict domain lock (e.g. stripe.com)')
    expiry = models.DateField(blank=True, null=True, help_text='Expiry date (no time required)')
    is_active = models.BooleanField(default=True, help_text='Whether this PIN is currently active')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def status(self):
        if not self.is_active:
            return 'Deactivated'
        if self.expiry and datetime.date.today() > self.expiry:
            return 'Expired'
        return 'Active'

    @property
    def masked_email(self):
        if not self.email_address:
            return ""
        if "@" in self.email_address:
            name, domain = self.email_address.split("@", 1)
            if len(name) <= 2:
                masked_name = name[0] + "*"
            else:
                masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
            return f"{masked_name}@{domain}"
        return "••••••••"

    def __str__(self):
        return f"{self.email_address} ({self.pin})"

