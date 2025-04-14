from .models import Reply, Inbox
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, CreateAPIView, ListAPIView
from .serializers import InboxSerializer, ReplySerializer
from .auth import get_signature_from_headers
from rest_framework.response import Response


class InboxListView(ListCreateAPIView):
    queryset = Inbox.objects.all()
    serializer_class = InboxSerializer


class InboxView(RetrieveUpdateAPIView):
    queryset = Inbox.objects.all()
    serializer_class = InboxSerializer

    http_method_names = ["get", "patch"]  # to remove the put


class ReplyListView(CreateAPIView):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer


class InboxReplyListView(ListAPIView):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer

    def get_queryset(self):
        return Reply.objects.filter(inbox__id=self.kwargs["id"])

    def get(self, request, *args, **kwargs):
        signature = get_signature_from_headers(request.META.get("HTTP_AUTHORIZATION"))

        inbox = Inbox.objects.get(id=self.kwargs["id"])

        if inbox.signature != signature:
            return Response({"error": f"Provided signature does not match the inbox"}, 403)

        return super().get(request, *args, **kwargs)
