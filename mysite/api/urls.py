from django.urls import path
from .views import *

urlpatterns = [
    path("inboxes", InboxListView.as_view()),
    path("inboxes/<str:pk>", InboxView.as_view()),
    path("replies", ReplyListView.as_view()),
    path("inboxes/<str:id>/replies", InboxReplyListView.as_view()),
]
