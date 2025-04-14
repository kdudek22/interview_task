from datetime import datetime, UTC
import uuid


class Reply:
    def __init__(self, body: str, signature: str | None = None):
        self.body = body
        self.signature = signature
        self.timestamp = datetime.now(UTC)

    def get_info(self):
        return {"body": self.body, "signature": self.signature, "timestamp": self.timestamp}


class Inbox:
    def __init__(self, topic: str, signature: str, expiration_date: datetime, allow_anonymous_submission: bool):
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.signature = signature
        self.expiration_date = expiration_date
        self.allow_anonymous_submission = allow_anonymous_submission
        self.replies: list[Reply] = []

    def is_expired(self):
        return datetime.now(UTC) > self.expiration_date

    def add_reply(self, reply: Reply):
        if self.is_expired():
            raise ValueError("Cannot reply to this inbox, as it is expired")

        if not self.allow_anonymous_submission and not reply.signature:
            raise ValueError("Adding reply with no signature is not allowed for this topic")

        self.replies.append(reply)

    def change_topic(self, new_topic: str, signature: str):
        if self.signature != signature:
            raise PermissionError("Signature does not match the signature of the Inbox")

        if self.replies:
            raise ValueError("Cannot change the inbox topic, because it already has replies")

        self.topic = new_topic

    def get_replies(self, signature: str):
        if self.signature != signature:
            raise PermissionError("Signature does not match the signature of the Inbox")

        return self.replies

    def get_info(self):
        return {"id": self.id, "topic": self.topic, "signature": self.signature,
                "expiration_date": str(self.expiration_date),
                "allow_anonymous_submission": self.allow_anonymous_submission}
