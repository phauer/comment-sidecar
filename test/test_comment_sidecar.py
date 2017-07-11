#!/usr/bin/env python3

import MySQLdb # sudo apt install libmysqlclient-dev python-dev && pip3 install mysqlclient
import requests # pip3 install requests
import unittest
import hashlib
import time
from path import Path # pip3 install path.py

DEFAULT_PATH = "/blogpost1/"
DEFAULT_SITE = "petersworld.com"
INVALID_QUERY_PARAMS = "Please submit both query parameters 'site' and 'path'"
COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar.php'

class PlaylistTest(unittest.TestCase):
    def setUp(self):
        # first, run `docker-compose up`
        db = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='comment-sidecar')
        cur = db.cursor()
        with Path("create-comments-table.sql").open('r') as sql:
            query = "\n".join(sql.readlines())
            cur.execute(query)

    def test_GET_missing_query_params(self):
        response = requests.get(COMMENT_SIDECAR_URL)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], INVALID_QUERY_PARAMS)

    def test_GET_empty_query_params(self):
        response = get_comments(site='', path='')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], INVALID_QUERY_PARAMS)

    def test_GET_missing_path(self):
        response = get_comments(site='domain.com', path='')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], INVALID_QUERY_PARAMS)

    def test_GET_missing_site(self):
        response = get_comments(site='', path='blogpost1')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], INVALID_QUERY_PARAMS)

    def test_GET_empty_array_if_no_comments(self):
        response = get_comments()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '[]')

    def test_POST_and_GET_comment(self):
        post_payload = create_post_payload()
        timestamp_before = int(time.time())
        response = post_comment(post_payload)
        timestamp_after = int(time.time())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.text, "")

        get_response = get_comments()
        self.assertEqual(get_response.status_code, 200)
        comments_json = get_response.json()
        self.assertEqual(len(comments_json), 1)

        returned_comment = comments_json[0]
        self.assertEqual(returned_comment["author"], post_payload["author"])
        self.assertEqual(returned_comment["content"], post_payload["content"])
        gravatar_url = create_gravatar_url(post_payload["email"])
        self.assertEqual(returned_comment["gravatarUrl"], gravatar_url)
        self.assertTimestampBetween(returned_comment["creationTimestamp"], start=timestamp_before, end=timestamp_after)
        self.assertTrue('email' not in returned_comment, "Don't send the email back to browser")
        self.assertTrue('id' not in returned_comment, "Don't send the id to browser")
        self.assertTrue('path' not in returned_comment, "Don't send the path to browser")
        self.assertTrue('site' not in returned_comment, "Don't send the site to browser")
        self.assertTrue('replyTo' not in returned_comment, "Don't send the replyTo to browser")

    def test_GET_different_paths(self):
        path_with_two_comments = "/post1/"
        path_with_one_comment = "/post2/"

        post_payload = create_post_payload()
        post_payload['path'] = path_with_two_comments
        post_comment(post_payload)
        post_comment(post_payload)
        post_payload['path'] = path_with_one_comment
        post_comment(post_payload)

        response = get_comments(path=path_with_two_comments)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        response = get_comments(path=path_with_one_comment)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_GET_different_sites(self):
        site_with_two_comments = "mydomain2.com"
        site_with_one_comment = "mydomain1.com"

        post_payload = create_post_payload()
        post_payload['site'] = site_with_two_comments
        post_comment(post_payload)
        post_comment(post_payload)
        post_payload['site'] = site_with_one_comment
        post_comment(post_payload)

        response = get_comments(site=site_with_two_comments)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        response = get_comments(site=site_with_one_comment)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_POST_without_optional_email(self):
        post_payload = create_post_payload()
        post_payload.pop('email')
        response = post_comment(post_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.text, "")

    def test_POST_missing_fields(self):
        self.post_comment_with_missing_field_and_assert_error('author')
        self.post_comment_with_missing_field_and_assert_error('content')
        self.post_comment_with_missing_field_and_assert_error('site')
        self.post_comment_with_missing_field_and_assert_error('path')

    def test_POST_empty_fields(self):
        self.post_comment_with_empty_field_and_assert_error('author')
        self.post_comment_with_empty_field_and_assert_error('content')
        self.post_comment_with_empty_field_and_assert_error('site')
        self.post_comment_with_empty_field_and_assert_error('path')

    def test_POST_blank_fields(self):
        self.post_comment_with_blank_field_and_assert_error('author')
        self.post_comment_with_blank_field_and_assert_error('content')
        self.post_comment_with_blank_field_and_assert_error('site')
        self.post_comment_with_blank_field_and_assert_error('path')

    def post_comment_with_missing_field_and_assert_error(self, missing_field: str):
        post_payload = create_post_payload()
        post_payload.pop(missing_field)
        response = post_comment(post_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], missing_field + " is missing, empty or blank")

    def post_comment_with_empty_field_and_assert_error(self, empty_field: str):
        post_payload = create_post_payload()
        post_payload[empty_field] = ""
        response = post_comment(post_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], empty_field + " is missing, empty or blank")

    def post_comment_with_blank_field_and_assert_error(self, blank_field: str):
        post_payload = create_post_payload()
        post_payload[blank_field] = " "
        response = post_comment(post_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], blank_field + " is missing, empty or blank")

    def assertTimestampBetween(self, creation_timestamp: str, start: int, end: int):
        timestamp = int(creation_timestamp)
        self.assertGreaterEqual(timestamp, start)
        self.assertLessEqual(timestamp, end)

def post_comment(post_payload):
    return requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)

def get_comments(site: str = DEFAULT_SITE, path: str = DEFAULT_PATH):
    return requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, site, path))

def create_post_payload():
    return {
        "author": "Peter",
        "content": "Peter's comment",
        "email": "peter@petersworld.com",
        "path": DEFAULT_PATH,
        "site": DEFAULT_SITE
    }

def create_gravatar_url(email: str) -> str:
    md5 = hashlib.md5()
    md5.update(email.strip().lower().encode())
    return "https://www.gravatar.com/avatar/" + md5.hexdigest()

if __name__ == '__main__':
    unittest.main()

