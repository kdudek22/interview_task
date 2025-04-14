from .models import Inbox, Reply
from datetime import datetime, UTC, timedelta
from .auth import get_tripcode
import base64


def create_inboxes():
    Inbox(topic="Expired inbox", signature=get_tripcode("admin", "admin_secret"),
          expiration_date=datetime.now(UTC) - timedelta(days=1), allows_anonymous_submission=True).save()

    Inbox(topic="Anonymous inbox", signature=get_tripcode("admin", "admin_secret"),
          expiration_date=datetime.now(UTC) + timedelta(days=1), allows_anonymous_submission=True).save()

    Inbox(topic="Not anonymous inbox", signature=get_tripcode("admin", "admin_secret"),
          expiration_date=datetime.now(UTC) + timedelta(days=1), allows_anonymous_submission=False).save()


def create_replies():
    Reply(body="Hi very nice anonymous topic", signature=None, inbox=Inbox.objects.get(topic="Anonymous inbox")).save()

    Reply(body="Indeed a nice topic", signature=get_tripcode("some_user", "secret"),
          inbox=Inbox.objects.get(topic="Anonymous inbox")).save()

    Reply(body="Nice topic for users", signature=get_tripcode("user123", "secret1"),
          inbox=Inbox.objects.get(topic="Not anonymous inbox")).save()

    Reply(body="I am a user, and i comment on this", signature=get_tripcode("user222", "secret2"),
          inbox=Inbox.objects.get(topic="Not anonymous inbox")).save()

    Reply(body="Yeah I am a user", signature=get_tripcode("user555", "secret3"),
          inbox=Inbox.objects.get(topic="Not anonymous inbox")).save()




def format_datetime(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_basic_auth_headers(username, secret):
    value = f"{username}:{secret}"
    return {"HTTP_AUTHORIZATION": f"Basic {base64.b64encode(value.encode("utf-8")).decode("utf-8")}"}

