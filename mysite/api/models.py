import uuid
from django.db import models
from datetime import datetime, UTC


class Inbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    topic = models.CharField(max_length=255)
    signature = models.CharField(max_length=255)
    expiration_date = models.DateTimeField()
    allows_anonymous_submission = models.BooleanField()

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expiration_date


class Reply(models.Model):
    body = models.CharField(max_length=255)
    signature = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    inbox = models.ForeignKey(Inbox, on_delete=models.CASCADE)
