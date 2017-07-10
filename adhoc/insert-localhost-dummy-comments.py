#!/usr/bin/env python3

import requests
import random

DEFAULT_PATH = "/playground.html"
DEFAULT_SITE = "localhost"
COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar.php'

NAMES = ['Peter', 'Albert', 'James', 'Max', 'Florian', 'Thomas']

def generate_payload():
    return {
        "author": random.choice(NAMES),
        "content": "Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
        "creationTimestamp": random.randint(1449604757, 1499604757),
        "email": "host@localhost.com",
        "path": DEFAULT_PATH,
        "replyTo": None,
        "site": DEFAULT_SITE
    }

for _ in range(5):
    post_payload = generate_payload()
    post_response = requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)
    print("Posted payload")
