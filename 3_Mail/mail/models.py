from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Email(models.Model):
    sender = models.ForeignKey("User", on_delete=models.PROTECT, related_name="emails_sent")
    recipients = models.ManyToManyField("User", through="EmailRecipient", related_name="emails_received")
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def serialize(self, status=None):
        return {
            "id": self.id,
            "sender": self.sender.email,
            "recipients": [u.email for u in self.recipients.all()],
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "read": status.read if status else False,
            "archived": status.archived if status else False,
        }

    def __str__(self):
        return f"{self.sender.email} -> {self.subject}"


class EmailRecipient(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name="recipient_statuses")
    recipient = models.ForeignKey("User", on_delete=models.CASCADE, related_name="email_statuses")
    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("email", "recipient")
