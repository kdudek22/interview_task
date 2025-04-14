from django.test import TestCase
from rest_framework.test import APITestCase
from .models import Inbox, Reply
from datetime import datetime, UTC
from .auth import get_tripcode, get_signature_from_headers, separator, salt
from unittest.mock import patch, MagicMock
from .test_utils import create_inboxes, create_replies, get_basic_auth_headers, format_datetime
from .serializers import ReplySerializer, InboxSerializer


class TestAuthentication(TestCase):

    def test_tripcode_starts_with_the_username_and_separator(self):
        tripcode = get_tripcode("username", "someSecret")

        self.assertTrue(tripcode.startswith("username" + separator))

    @patch("api.auth.hashlib.md5")
    def test_tripcode_hashes_correct_values(self, mock_md5):
        get_tripcode("username", "someSecret")
        mock_md5.assert_called_once_with(("username" + "someSecret" + salt).encode())

    @patch("api.auth.hashlib.md5")
    def test_tripcode_has_correct_format(self, mock_md5):
        mock = MagicMock()
        mock.hexdigest.return_value = "some_hash"
        mock_md5.return_value = mock

        tripcode = get_tripcode("username", "secret")
        self.assertEqual(tripcode, "username" + separator + "some_hash")

    def test_get_signature_from_headers(self):
        """
        1. If the request has no auth headers, they are None - the signature should be None
        2. If the request has the HTTP_AUTHORIZATION headers, the signature should be obtained
        """
        signature_1 = get_signature_from_headers(None)
        self.assertEqual(signature_1, None)

        signature_2 = get_signature_from_headers(get_basic_auth_headers("admin", "secret")["HTTP_AUTHORIZATION"])
        self.assertEqual(signature_2, get_tripcode("admin", "secret"))

    @patch("api.auth.get_tripcode")
    def test_get_signature_from_headers_calls_tripcode(self, mock_tripcode):
        get_signature_from_headers(get_basic_auth_headers("admin", "secret")["HTTP_AUTHORIZATION"])
        mock_tripcode.assert_called_once_with("admin", "secret")


class InboxAPITests(APITestCase):

    def setUp(self):
        create_inboxes()

    def test_create_no_auth_header_present(self):
        data = {"topic": "test_topic",
                "expiration_date": format_datetime(datetime.now(UTC)),
                "allows_anonymous_submission": False}

        response = self.client.post("/api/inboxes", data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(),
                         '{"signature":"You have to pass the credentials in the auth header to create an inbox"}')

    def test_create_missing_title(self):
        data = {"expiration_date": format_datetime(datetime.now(UTC)),
                "allows_anonymous_submission": False}

        response = self.client.post("/api/inboxes", data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), '{"topic":["This field is required."]}')

    def test_create_topic_is_blank(self):
        data = {"topic": "",
                "expiration_date": format_datetime(datetime.now(UTC)),
                "allows_anonymous_submission": False}

        response = self.client.post("/api/inboxes", data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), '{"topic":["This field may not be blank."]}')

    # and a suite of similar tests - but the question is should i test the framework?

    def test_update_topic(self):
        inbox_id = Inbox.objects.get(topic="Expired inbox").id

        self.assertFalse(Inbox.objects.filter(topic="Some new topic").exists())

        data = {"topic": "Some new topic"}

        response = self.client.patch(f"/api/inboxes/{inbox_id}", data, **get_basic_auth_headers("admin", "admin_secret"))

        self.assertEqual(response.status_code, 200)

        self.assertTrue(Inbox.objects.filter(topic="Some new topic").exists())

    def test_changing_the_topic_of_an_inbox_wrong_signature_provided(self):
        """We try to change the topic of an inbox, but we provide a wrong signature"""
        inbox = Inbox.objects.get(topic="Anonymous inbox")

        data = {"topic": "Brand new topic name"}

        response = self.client.patch(f"/api/inboxes/{inbox.id}", data,
                                     **get_basic_auth_headers("wrong user", "wrong admin secret"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(),
                         '{"signature":"Provided signature does not match the one of the inbox"}')

    def test_changing_the_topic_of_an_inbox_with_replies_returns_an_error(self):
        """We try to update the topic of an inbox, but it already has replies"""
        inbox = Inbox.objects.get(topic="Anonymous inbox")

        Reply(body="Very nice topic", signature=None, inbox=inbox).save()

        data = {"topic": "Brand new topic name"}

        response = self.client.patch(f"/api/inboxes/{inbox.id}", data,
                                     **get_basic_auth_headers("admin", "admin_secret"))

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.content.decode(),
                         '{"topic":"Cannot change the topic as there already exists a reply to it"}')

        self.assertFalse(Inbox.objects.filter(topic="Brand new topic name").exists())

    def tes_get_inboxes(self):
        response = self.client.get("/api/inboxes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(Inbox.objects.all()))

        expected_data = InboxSerializer(Inbox.objects.all(), many=True).data

        self.assertEqual(response.json(), expected_data)

    def test_get_inbox_by_id(self):
        inbox = Inbox.objects.get(topic="Anonymous inbox")

        response = self.client.get(f"/api/inboxes/{inbox.id}")

        self.assertEqual(response.status_code, 200)

        expected_data = InboxSerializer(inbox).data

        self.assertEqual(response.json(), expected_data)


class ReplyAPITests(APITestCase):

    def setUp(self):
        create_inboxes()
        create_replies()

    def test_reply_to_an_inbox_not_anonymously_and_check_the_signature(self):
        inbox_id = Inbox.objects.get(topic="Not anonymous inbox").id

        data = {"body": "Hi I am a user", "inbox": inbox_id}

        response = self.client.post("/api/replies", data, **get_basic_auth_headers('someUsername', "someSecret"))

        self.assertEqual(response.status_code, 201)

        reply = Reply.objects.get(body="Hi I am a user", inbox__id=inbox_id)

        self.assertTrue(reply.signature.startswith("someUsername" + separator))

    def test_reply_anonymously_to_an_inbox_that_allows_anonymous_replies(self):
        inbox_id = Inbox.objects.get(topic="Anonymous inbox").id

        data = {"body": "Anonymous reply", "inbox": inbox_id}

        response = self.client.post("/api/replies", data)

        self.assertEqual(response.status_code, 201)

        self.assertTrue(Reply.objects.filter(body="Anonymous reply", inbox__id=inbox_id).exists())

    def test_reply_to_expired_inbox(self):
        inbox_id = Inbox.objects.get(topic="Expired inbox").id

        data = {"body": "Very nice expired inbox", "inbox": inbox_id}

        response = self.client.post("/api/replies", data)

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.content.decode(), '["Cannot add replies to this inbox, as it has expired"]')

    def test_reply_anonymously_to_an_inbox_that_does_not_allow_anonymous_replies(self):
        inbox_id = Inbox.objects.get(topic="Not anonymous inbox").id

        data = {"body": "I am trying to send an anonymous reply", "inbox": inbox_id}

        response = self.client.post("/api/replies", data)

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.content.decode(), '["This topic does not allow for anonymous submission"]')

    def test_read_replies_from_inbox_wrong_signature(self):
        """A user tries to access replies of an inbox, but the provided credentials don't match the ones of the inbox"""
        inbox_id = Inbox.objects.get(topic="Anonymous inbox").id

        response = self.client.get(f"/api/inboxes/{inbox_id}/replies", **get_basic_auth_headers("wrongUsername", "secret"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(),
                         '{"error":"Provided signature does not match the inbox"}')

    def test_read_replies_from_inbox(self):
        inbox_id = Inbox.objects.get(topic="Anonymous inbox").id

        response = self.client.get(f"/api/inboxes/{inbox_id}/replies", **get_basic_auth_headers("admin", "admin_secret"))

        self.assertEqual(response.status_code, 200)

        expected_data = ReplySerializer(Reply.objects.filter(inbox__id=inbox_id), many=True).data

        for api_item, expected_item in zip(response.json(), expected_data):
            self.assertEqual(api_item["body"], expected_item["body"])
            self.assertEqual(api_item["signature"], expected_item["signature"])
            self.assertEqual(api_item["timestamp"], expected_item["timestamp"])
            self.assertEqual(api_item["inbox"], str(expected_item["inbox"]))
