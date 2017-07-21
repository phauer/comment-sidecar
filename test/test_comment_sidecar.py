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
MAILHOG_BASE_URL = 'http://localhost:8025/api/'
MAILHOG_MESSAGES_URL = MAILHOG_BASE_URL + 'v2/messages'

class CommentSidecarTest(unittest.TestCase):
    def setUp(self):
        # first, run `docker-compose up`
        db = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='comment-sidecar')
        cur = db.cursor()
        with Path("../sql/create-comments-table.sql").open('r') as sql:
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
        response = self.post_comment(post_payload)
        timestamp_after = int(time.time())
        self.assertEqual(response.json()['id'], 1)

        get_response = get_comments()
        self.assertEqual(get_response.status_code, 200)
        comments_json = get_response.json()
        self.assertEqual(len(comments_json), 1)

        returned_comment = comments_json[0]
        self.assertEqual(returned_comment["id"], "1")
        self.assertEqual(returned_comment["author"], post_payload["author"])
        self.assertEqual(returned_comment["content"], post_payload["content"])
        gravatar_url = create_gravatar_url(post_payload["email"])
        self.assertEqual(returned_comment["gravatarUrl"], gravatar_url)
        self.assertTimestampBetween(returned_comment["creationTimestamp"], start=timestamp_before, end=timestamp_after)
        self.assertEqual(len(returned_comment["replies"]), 0)
        self.assertTrue('email' not in returned_comment, "Don't send the email back to browser")
        self.assertTrue('path' not in returned_comment, "Don't send the path to browser")
        self.assertTrue('site' not in returned_comment, "Don't send the site to browser")
        self.assertTrue('replyTo' not in returned_comment, "Don't send the replyTo to browser")

    def test_POST_and_GET_comment_with_german_umlauts(self):
        post_payload = create_post_payload()
        post_payload['content'] = "äöüß - Deutsche Umlaute? Kein Problem für utf-8! ÖÄÜ"
        post_payload['author'] = "öäüßÖÄÜ"
        response = self.post_comment(post_payload)
        self.assertEqual(response.json()['id'], 1)

        get_response = get_comments()
        self.assertEqual(get_response.status_code, 200)
        returned_comment = get_response.json()[0]
        self.assertEqual(returned_comment["author"], post_payload["author"])
        self.assertEqual(returned_comment["content"], post_payload["content"])

    def test_GET_different_paths(self):
        path_with_two_comments = "/post1/"
        path_with_one_comment = "/post2/"

        post_payload = create_post_payload()
        post_payload['path'] = path_with_two_comments
        self.post_comment(post_payload)
        self.post_comment(post_payload)
        post_payload['path'] = path_with_one_comment
        self.post_comment(post_payload)

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
        self.post_comment(post_payload)
        self.post_comment(post_payload)
        post_payload['site'] = site_with_one_comment
        self.post_comment(post_payload)

        response = get_comments(site=site_with_two_comments)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        response = get_comments(site=site_with_one_comment)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_POST_without_optional_email(self):
        post_payload = create_post_payload()
        post_payload.pop('email')
        response = self.post_comment(post_payload)
        self.assertEqual(response.json()['id'], 1)

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

    def test_POST_to_long_fields(self):
        self.post_comment_to_long_field_and_assert_error('author', 40)
        self.post_comment_to_long_field_and_assert_error('email', 40)
        self.post_comment_to_long_field_and_assert_error('site', 40)
        self.post_comment_to_long_field_and_assert_error('path', 170)

    def test_POST_spam_protection_set_url_is_spam(self):
        post_payload = create_post_payload()
        post_payload['url'] = 'http://only.spambots.will/populate/this/field/'
        response = self.post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400, "POST payload with an URL field should be rejected. The URL an hidden form field and used for spam protection.")
        self.assertEqual(response.json()['message'], "")

    def test_email_notification_after_successful_POST(self):
        self.clear_mails()

        post_payload = create_post_payload()
        self.post_comment(post_payload)

        json = requests.get(MAILHOG_MESSAGES_URL).json()
        self.assertEqual(json['total'], 1)
        mail_content = json['items'][0]['Content']
        mail_body = mail_content['Body']
        self.assertIn(post_payload['site'], mail_body)
        self.assertIn(post_payload['path'], mail_body)
        self.assertIn(post_payload['content'], mail_body)
        headers = mail_content['Headers']
        self.assertEqual(headers['Content-Transfer-Encoding'][0], '8bit')
        self.assertEqual(headers['Content-Type'][0], 'text/plain; charset=UTF-8')
        self.assertEqual(headers['Mime-Version'][0], '1.0')
        self.assertEqual(headers['From'][0], '{}<{}>'.format(post_payload['author'], post_payload['email']))
        self.assertEqual(headers['Subject'][0], 'Comment by {} on {}'.format(post_payload['author'], post_payload['path']))
        self.assertEqual(headers['To'][0], 'test@localhost.de')

    def test_no_email_notification_after_invalid_POST(self):
        self.clear_mails()

        post_payload = create_post_payload()
        post_payload.pop('author')
        self.post_comment(post_payload, assert_success=False)

        json = requests.get(MAILHOG_MESSAGES_URL).json()
        self.assertEqual(json['total'], 0)

    def test_POST_spam_protection_empty_url_is_fine(self):
        post_payload = create_post_payload()
        post_payload['url'] = ""
        response = self.post_comment(post_payload)
        self.assertEqual(response.json()['id'], 1)

    def test_escaped_HTML_XSS_protection(self):
        post_payload = create_post_payload()
        post_payload['author'] = "<strong>Peter</strong>"
        post_payload['content'] = '<script type="text/javascript">document.querySelector("aside#comment-sidecar h1").innerText = "XSS";</script>'
        response = self.post_comment(post_payload)
        self.assertEqual(response.json()['id'], 1)

        returned_json = get_comments().json()[0]
        self.assertEqual(returned_json['author'], '&lt;strong&gt;Peter&lt;/strong&gt;')
        self.assertEqual(returned_json['content'], '&lt;script type=&quot;text/javascript&quot;&gt;document.querySelector(&quot;aside#comment-sidecar h1&quot;).innerText = &quot;XSS&quot;;&lt;/script&gt;')

    def clear_mails(self):
        response = requests.delete(MAILHOG_BASE_URL + 'v1/messages')
        self.assertEqual(response.status_code, 200, "Test setup failed: Couldn't delete mails in mailhog.")

    def post_comment_with_missing_field_and_assert_error(self, missing_field: str):
        post_payload = create_post_payload()
        post_payload.pop(missing_field)
        response = self.post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], missing_field + " is missing, empty or blank")

    def post_comment_with_empty_field_and_assert_error(self, empty_field: str):
        post_payload = create_post_payload()
        post_payload[empty_field] = ""
        response = self.post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], empty_field + " is missing, empty or blank")

    def post_comment_with_blank_field_and_assert_error(self, blank_field: str):
        post_payload = create_post_payload()
        post_payload[blank_field] = " "
        response = self.post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], blank_field + " is missing, empty or blank")

    def post_comment_to_long_field_and_assert_error(self, field: str, max_length: int):
        post_payload = create_post_payload()
        post_payload[field] = "x" * (max_length + 1)
        response = self.post_comment(post_payload, assert_success=False)
        self.assertEqual(response.json()['message'], field + " value exceeds maximal length of " + str(max_length))
        self.assertEqual(response.status_code, 400)

        # valid length (check it to avoid off-by-one-errors)
        post_payload[field] = "x" * max_length
        self.post_comment(post_payload)

    def assertTimestampBetween(self, creation_timestamp: str, start: int, end: int):
        timestamp = int(creation_timestamp)
        self.assertGreaterEqual(timestamp, start)
        self.assertLessEqual(timestamp, end)

    def post_comment(self, post_payload, assert_success=True):
        response = requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)
        if assert_success:
            self.assertEqual(response.status_code, 201, "Comment creation failed. Message: " + response.text)
        return response

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

