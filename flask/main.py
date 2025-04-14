from models import Reply, Inbox
from datetime import datetime, UTC, timedelta
import hashlib
from flask import Flask, request, jsonify
from auth import get_tripcode, get_basic_auth_credentials

app = Flask(__name__)


inboxes: dict[str, Inbox] = {}


@app.route("/inboxes", methods=["GET"])
def get_inboxes():
    return jsonify([i.get_info() for i in inboxes.values()])


@app.route("/inboxes", methods=["POST"])
def post_inboxes():
    auth = get_basic_auth_credentials(request.headers.get("Authorization"))
    signature = get_tripcode(*auth)

    data = request.json

    inbox = Inbox(data["topic"], signature, datetime.now(UTC) + timedelta(days=1), True)
    inboxes[inbox.id] = inbox

    return jsonify(inbox.get_info())


@app.route("/inboxes/<inbox_id>", methods=["GET"])
def get_inbox(inbox_id):
    if inbox_id not in inboxes:
        return jsonify({"error": f"There is not inbox with id: {inbox_id}"}, 400)

    inbox = inboxes.get(inbox_id)

    return jsonify(inbox.get_info())


@app.route("/inboxes/<inbox_id>", methods=["PATCH"])
def update_inbox(inbox_id):
    if inbox_id not in inboxes:
        return jsonify({"error": f"There is not inbox with id: {inbox_id}"}, 400)

    signature = get_tripcode(*get_basic_auth_credentials(request.headers.get("Authorization")))

    inbox = inboxes.get(inbox_id)

    data = request.json

    try:
        inbox.change_topic(data["topic"], signature)

    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}, 400)

    return jsonify(inbox.get_info())


@app.route("/inboxes/<inbox_id>/replies", methods=["GET"])
def get_replies(inbox_id):
    if inbox_id not in inboxes:
        return jsonify({"error": f"There is not inbox with id: {inbox_id}"}, 400)

    inbox = inboxes.get(inbox_id)

    auth = get_basic_auth_credentials(request.headers.get("Authorization"))
    signature = get_tripcode(*auth)

    if inbox.signature != signature:
        return jsonify({"error": "Provided signature does not match the one of the inbox"}, 403)

    return jsonify([r.get_info() for r in inbox.replies])


@app.route("/inboxes/<inbox_id>/replies", methods=["POST"])
def post_replies(inbox_id):
    if inbox_id not in inboxes:
        return jsonify({"error": f"There is not inbox with id: {inbox_id}"}, 400)

    signature = get_tripcode(*get_basic_auth_credentials(request.headers.get("Authorization"))) if \
        request.headers.get("Authorization").startswith("Basic") else None

    inbox = inboxes.get(inbox_id)
    data = request.json

    reply = Reply(data["body"], signature=signature)

    try:
        inbox.add_reply(reply)
    except ValueError as e:
        return jsonify({"error": str(e)}, 400)

    return jsonify({"success": "Added reply"})


if __name__ == "__main__":

    print(get_tripcode("test", "test"))

    default_inbox = Inbox("Test topic", "AdamDobrzeWkladam69-735f7880b2fd54dd964236b812a52732",
                          datetime.now(UTC) + timedelta(days=1), True)
    default_inbox.add_reply(Reply("Test reply 1"))
    default_inbox.add_reply(Reply("Test reply 2", signature="AdamDobrzeWkladam69-735f7880b2fd54dd964236b812a52732"))

    inboxes[default_inbox.id] = default_inbox

    app.run()
