"""Tiny webhook server that auto-deploys on push to main."""

import hashlib
import hmac
import os
import subprocess

from flask import Flask, abort, request

app = Flask(__name__)

SECRET = os.environ["WEBHOOK_SECRET"]


def verify_signature(payload, signature):
    expected = (
        "sha256=" + hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(expected, signature)


@app.route("/deploy", methods=["POST"])
def deploy():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        abort(403)

    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        return "ignored", 200

    data = request.json
    if data.get("ref") != "refs/heads/main":
        return "not main", 200

    subprocess.Popen(
        [
            "bash",
            "-c",
            "cd /opt/bones && git pull && uv sync && "
            "python -m bones.download && systemctl restart bones",
        ],
    )
    return "deploying", 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9001)
