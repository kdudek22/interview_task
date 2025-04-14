from rest_framework import serializers
from .models import Inbox, Reply
from .auth import get_signature_from_headers


class ReplySerializer(serializers.ModelSerializer):
    body = serializers.CharField()
    signature = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    inbox = serializers.PrimaryKeyRelatedField(queryset=Inbox.objects.all())

    def create(self, validated_data):
        inbox = validated_data["inbox"]

        if inbox.is_expired():
            raise serializers.ValidationError("Cannot add replies to this inbox, as it has expired")

        signature = get_signature_from_headers(self.context["request"].META.get("HTTP_AUTHORIZATION"))

        if signature is None and not inbox.allows_anonymous_submission:
            raise serializers.ValidationError("This topic does not allow for anonymous submission")

        return super().create(validated_data | {"signature": signature})

    class Meta:
        model = Reply
        fields = ["body", "signature", "timestamp", "inbox"]


class InboxSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    topic = serializers.CharField()
    signature = serializers.CharField(read_only=True)
    expiration_date = serializers.DateTimeField()
    allows_anonymous_submission = serializers.BooleanField()

    not_editable_fields = ["id", "signature", "expiration_date", "allows_anonymous_submission"]

    def get_fields(self):
        fields = super().get_fields()
        if self.instance:
            for field in self.not_editable_fields:
                fields[field].read_only = True

        return fields

    def create(self, validated_data):
        signature = get_signature_from_headers(self.context["request"].META.get("HTTP_AUTHORIZATION"))

        if not signature:
            raise serializers.ValidationError(
                {"signature": "You have to pass the credentials in the auth header to create an inbox"})

        return super().create(validated_data | {"signature": signature})

    def update(self, instance, validated_data):
        signature = get_signature_from_headers(self.context["request"].META.get("HTTP_AUTHORIZATION"))

        if signature != instance.signature:
            raise serializers.ValidationError({"signature": "Provided signature does not match the one of the inbox"})

        if Reply.objects.filter(inbox=instance).exists():
            raise serializers.ValidationError(
                {"topic": "Cannot change the topic as there already exists a reply to it"})

        return super().update(instance, validated_data)

    class Meta:
        model = Inbox
        fields = ["id", "topic", "signature", "expiration_date", "allows_anonymous_submission"]
