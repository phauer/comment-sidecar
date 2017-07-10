#!/usr/bin/env python3

import requests

DEFAULT_PATH = "/playground.html"
DEFAULT_SITE = "localhost"
COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar.php'

def create_payload():
    return {
        "author": "Localhorst",
        "content": "Horst's comment",
        "creationTimestamp": "1499604757",
        "email": "host@localhost.com",
        "path": DEFAULT_PATH,
        "replyTo": None,
        "site": DEFAULT_SITE
    }

for _ in range(5):
    post_payload = create_payload()
    post_response = requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)
    print("Posted payload")
