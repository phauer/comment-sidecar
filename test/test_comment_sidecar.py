#!/usr/bin/env python3

import MySQLdb # requires: sudo apt install libmysqlclient-dev python-dev
import requests
from requests.models import Response
import unittest
import hashlib
import time
from path import Path
from assertpy import assert_that, fail

ADMIN_EMAIL = 'test@localhost.de'
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
        with get_sql_file_path().open('r') as sql:
            query = "\n".join(sql.readlines())
            cur.execute(query)

    def test_GET_missing_query_params(self):
        response = requests.get(COMMENT_SIDECAR_URL)
        assert_that(response.status_code).is_equal_to(400)
        assert_that(response.json()["message"]).is_equal_to(INVALID_QUERY_PARAMS)

    def test_GET_empty_query_params(self):
        response = get_comments(site='', path='', assert_success=False)
        assert_that(response.status_code).is_equal_to(400)
        assert_that(response.json()["message"]).is_equal_to(INVALID_QUERY_PARAMS)

    def test_GET_missing_path(self):
        response = get_comments(site='domain.com', path='', assert_success=False)
        assert_that(response.status_code).is_equal_to(400)
        assert_that(response.json()["message"]).is_equal_to(INVALID_QUERY_PARAMS)

    def test_GET_missing_site(self):
        response = get_comments(site='', path='blogpost1', assert_success=False)
        assert_that(response.status_code).is_equal_to(400)
        assert_that(response.json()["message"]).is_equal_to(INVALID_QUERY_PARAMS)

    def test_GET_empty_array_if_no_comments(self):
        response = get_comments()
        self.assertEqual(response.text, '[]')

    def test_POST_and_GET_comment(self):
        post_payload = create_post_payload()
        timestamp_before = int(time.time())
        response = post_comment(post_payload)
        timestamp_after = int(time.time())
        assert_that(response.json()['id']).is_equal_to(1)

        get_response = get_comments()
        comments_json = get_response.json()
        self.assertEqual(len(comments_json), 1)

        returned_comment = comments_json[0]
        self.assertEqual(returned_comment["id"], "1")
        self.assertEqual(returned_comment["author"], post_payload["author"])
        self.assertEqual(returned_comment["content"], post_payload["content"])
        gravatar_url = create_gravatar_url(post_payload["email"])
        self.assertEqual(returned_comment["gravatarUrl"], gravatar_url)
        assert_timestamp_between(returned_comment["creationTimestamp"], start=timestamp_before, end=timestamp_after)
        self.assertTrue("replies" not in returned_comment, "field 'replies' should not be in the payload. element: ".format(str(returned_comment)))
        self.assertAbsentFields(returned_comment)

    def assertAbsentFields(self, returned_comment):
        self.assertTrue('email' not in returned_comment, "Don't send the email back to browser")
        self.assertTrue('path' not in returned_comment, "Don't send the path to browser")
        self.assertTrue('site' not in returned_comment, "Don't send the site to browser")
        self.assertTrue('replyTo' not in returned_comment, "Don't send the replyTo to browser")

    def test_POST_comments_and_replies_and_GET_reply_chain(self):
        # for adhoc debugging: `http "localhost/comment-sidecar.php?site=peterworld%2Ecom&path=%2Fblogpost1%2F&XDEBUG_SESSION_START=IDEA_DEBUG"`
        # root1
        # - reply 1 to root
        # - reply 2 to root
        #   - reply  to reply 2
        post_payload = create_post_payload()
        post_payload['content'] = 'root'
        response = post_comment(post_payload)
        root_id = response.json()['id']

        post_payload = create_post_payload()
        post_payload['replyTo'] = root_id
        post_payload['content'] = 'reply 1 to root'
        post_comment(post_payload)

        post_payload = create_post_payload()
        post_payload['replyTo'] = root_id
        post_payload['content'] = 'reply 2 to root'
        response = post_comment(post_payload)
        reply2_id = response.json()['id']

        post_payload = create_post_payload()
        post_payload['replyTo'] = reply2_id
        post_payload['content'] = 'reply 3 to reply 2'
        post_comment(post_payload)

        get_response = get_comments()

        # check root comments
        returned_comments = get_response.json()
        self.assertEqual(len(returned_comments), 1) # replies are nested so only one root comment
        replies = returned_comments[0]['replies']

        # check reply level 1
        self.assertIsNotNone(replies)
        self.assertEqual(len(replies), 2)
        self.assertRepliesContains(replies, {
            'content': 'reply 1 to root', 'id': '2', 'author': 'Peter',
        })
        self.assertRepliesContains(replies, {
            'content': 'reply 2 to root', 'id': '3', 'author': 'Peter',
        })
        for reply in replies:
            self.assertAbsentFields(reply)

        # check reply level 2
        comment = get_comment_by_content(replies, 'reply 2 to root')
        replies_to_reply = comment['replies']
        self.assertEqual(len(replies_to_reply), 1)
        self.assertRepliesContains(replies_to_reply, {
            'content': 'reply 3 to reply 2', 'id': '4', 'author': 'Peter',
        })

    def assertRepliesContains(self, replies, assumed_element):
        replies_matching_assumed_element = [reply for reply in replies
                                            if reply['content'] == assumed_element['content']
                                            and reply['id'] == assumed_element['id']
                                            and reply['author'] == assumed_element['author']
         ]
        self.assertEqual(len(replies_matching_assumed_element), 1, "Element is not in the list (or more than once).\nassumed_element: {}\nall elements: {}\n".format(assumed_element, replies))

    def test_POST_invalid_replyTo_ID(self):
        post_payload = create_post_payload()
        post_payload['replyTo'] = '989089'
        response = post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400, "Invalid replyTo ID should be rejected.")
        self.assertEqual(response.json()['message'], "The replyTo value '989089' refers to a not existing id.")

    def test_POST_and_GET_comment_with_german_umlauts(self):
        post_payload = create_post_payload()
        post_payload['content'] = "äöüß - Deutsche Umlaute? Kein Problem für utf-8! ÖÄÜ"
        post_payload['author'] = "öäüßÖÄÜ"
        response = post_comment(post_payload)
        assert_that(response.json()['id']).is_equal_to(1)

        get_response = get_comments()
        returned_comment = get_response.json()[0]
        self.assertEqual(returned_comment["author"], post_payload["author"])
        self.assertEqual(returned_comment["content"], post_payload["content"])

    def test_OPTIONS_CORS_headers_valid_origin(self):
        # before sending a POST, the browser will send an OPTION request as a preflight to see the CORS headers.
        # the backend will only return the required CORS headers, if the Origin is set to a allowed domain.
        post_payload = create_post_payload()
        valid_origin = 'http://testdomain.com'
        preflight_response = requests.options(url=COMMENT_SIDECAR_URL, json=post_payload, headers={'Origin': valid_origin})
        self.assertCORSHeadersExists(preflight_response, valid_origin)
        self.assertEqual(preflight_response.text, "")
        self.assertEqual(len(get_comments().json()), 0, "No comment should have been created after an OPTIONS request")

    def test_OPTIONS_CORS_headers_invalid_origin(self):
        post_payload = create_post_payload()
        valid_origin = 'http://invalid.com'
        preflight_response = requests.options(url=COMMENT_SIDECAR_URL, json=post_payload, headers={'Origin': valid_origin})
        self.assertCORSHeadersDoesntExists(preflight_response)
        self.assertEqual(preflight_response.text, "")
        self.assertEqual(len(get_comments().json()), 0, "No comment should have been created after an OPTIONS request")

    def test_GET_CORS_headers_valid_origin(self):
        # for GETs, the browser will request immediately (without preflight), but will reject the response, if the CORS are not set.
        # the backend will only return the required CORS headers, if the Origin is set to a allowed domain.
        valid_origin = 'http://testdomain.com'
        response = requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, DEFAULT_SITE, DEFAULT_PATH), headers={'Origin': valid_origin})
        self.assertCORSHeadersExists(response, valid_origin)

    def test_GET_CORS_headers_invalid_origin(self):
        valid_origin = 'http://invalid.com'
        response = requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, DEFAULT_SITE, DEFAULT_PATH), headers={'Origin': valid_origin})
        self.assertCORSHeadersDoesntExists(response)

    def assertCORSHeadersExists(self, preflight_response, exptected_allowed_origin):
        self.assertTrue('Access-Control-Allow-Origin' in preflight_response.headers, "Access-Control-Allow-Origin not set!")
        self.assertEqual(preflight_response.headers['Access-Control-Allow-Origin'], exptected_allowed_origin)
        self.assertTrue('Access-Control-Allow-Methods' in preflight_response.headers, "Access-Control-Allow-Methods not set!")
        self.assertEqual(preflight_response.headers['Access-Control-Allow-Methods'], 'GET, POST')
        self.assertTrue('Access-Control-Allow-Headers' in preflight_response.headers, "Access-Control-Allow-Headers not set!")
        self.assertEqual(preflight_response.headers['Access-Control-Allow-Headers'], 'Content-Type')

    def assertCORSHeadersDoesntExists(self, preflight_response):
        self.assertTrue('Access-Control-Allow-Origin' not in preflight_response.headers, "Access-Control-Allow-Origin is set!")
        self.assertTrue('Access-Control-Allow-Methods' not in preflight_response.headers, "Access-Control-Allow-Methods is set!")
        self.assertTrue('Access-Control-Allow-Headers' not in preflight_response.headers, "Access-Control-Allow-Headers is set!")

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
        assert_that(response.json()).is_length(2)

        response = get_comments(path=path_with_one_comment)
        assert_that(response.json()).is_length(1)

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
        assert_that(response.json()).is_length(2)

        response = get_comments(site=site_with_one_comment)
        assert_that(response.json()).is_length(1)

    def test_POST_without_optional_email(self):
        post_payload = create_post_payload()
        post_payload.pop('email')
        response = post_comment(post_payload)
        assert_that(response.json()['id']).is_equal_to(1)

    def test_POST_missing_fields(self):
        post_comment_with_missing_field_and_assert_error('author')
        post_comment_with_missing_field_and_assert_error('content')
        post_comment_with_missing_field_and_assert_error('site')
        post_comment_with_missing_field_and_assert_error('path')

    def test_POST_empty_fields(self):
        post_comment_with_empty_field_and_assert_error('author')
        post_comment_with_empty_field_and_assert_error('content')
        post_comment_with_empty_field_and_assert_error('site')
        post_comment_with_empty_field_and_assert_error('path')

    def test_POST_blank_fields(self):
        post_comment_with_blank_field_and_assert_error('author')
        post_comment_with_blank_field_and_assert_error('content')
        post_comment_with_blank_field_and_assert_error('site')
        post_comment_with_blank_field_and_assert_error('path')

    def test_POST_to_long_fields(self):
        post_comment_to_long_field_and_assert_error('author', 40)
        post_comment_to_long_field_and_assert_error('email', 40)
        post_comment_to_long_field_and_assert_error('site', 40)
        post_comment_to_long_field_and_assert_error('path', 170)

    def test_POST_spam_protection_set_url_is_spam(self):
        post_payload = create_post_payload()
        post_payload['url'] = 'http://only.spambots.will/populate/this/field/'
        response = post_comment(post_payload, assert_success=False)
        self.assertEqual(response.status_code, 400, "POST payload with an URL field should be rejected. The URL an hidden form field and used for spam protection.")
        self.assertEqual(response.json()['message'], "")

    def test_email_notification_after_successful_POST(self):
        clear_mails()

        post_payload = create_post_payload()
        post_comment(post_payload)

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
        self.assertEqual(headers['To'][0], ADMIN_EMAIL)

    def test_no_email_notification_after_invalid_POST(self):
        clear_mails()

        post_payload = create_post_payload()
        post_payload.pop('author')
        post_comment(post_payload, assert_success=False)

        json = requests.get(MAILHOG_MESSAGES_URL).json()
        self.assertEqual(json['total'], 0)

    def test_POST_spam_protection_empty_url_is_fine(self):
        post_payload = create_post_payload()
        post_payload['url'] = ""
        response = post_comment(post_payload)
        assert_that(response.json()['id']).is_equal_to(1)

    def test_escaped_HTML_XSS_protection(self):
        post_payload = create_post_payload()
        post_payload['author'] = "<strong>Peter</strong>"
        post_payload['content'] = '<script type="text/javascript">document.querySelector("aside#comment-sidecar h1").innerText = "XSS";</script>'
        response = post_comment(post_payload)
        assert_that(response.json()['id']).is_equal_to(1)

        returned_json = get_comments().json()[0]
        self.assertEqual(returned_json['author'], '&lt;strong&gt;Peter&lt;/strong&gt;')
        self.assertEqual(returned_json['content'], '&lt;script type=&quot;text/javascript&quot;&gt;document.querySelector(&quot;aside#comment-sidecar h1&quot;).innerText = &quot;XSS&quot;;&lt;/script&gt;')

    def test_subscription_mail_on_reply(self):
        clear_mails()
        root_payload = create_post_payload()
        root_payload["email"] = "root@root.com"
        response = post_comment(root_payload)
        root_id = response.json()['id']

        reply_payload = create_post_payload()
        reply_payload["replyTo"] = root_id
        reply_payload["content"] = "Root, I disagree!"
        reply_payload["email"] = "reply@reply.com!"
        reply_payload["author"] = "Replyer"
        post_comment(reply_payload)

        json = requests.get(MAILHOG_MESSAGES_URL).json()
        assert_that(json['total']).is_greater_than(1)

        assert_mail_exists(items=json['items'],
                           expected_body=reply_payload["content"],
                           expected_from=reply_payload["author"], # don't reveal replyer's email to notified parent author
                           expected_subject="Reply to your comment by {} on /blogpost1/".format(reply_payload["author"]),
                           expected_to=root_payload["email"])

    def test_subscription_no_mail_on_reply_if_no_parent_mail_defined(self):
        clear_mails()
        root_payload = create_post_payload()
        root_payload.pop('email')
        response = post_comment(root_payload)
        root_id = response.json()['id']

        reply_payload = create_post_payload()
        reply_payload["replyTo"] = root_id
        reply_payload["content"] = "Root, I disagree!"
        reply_payload["email"] = "reply@reply.com!"
        reply_payload["author"] = "Replyer"
        post_comment(reply_payload)

        json = requests.get(MAILHOG_MESSAGES_URL).json()
        assert_no_mail_except_admin_mail(items=json['items'])

def clear_mails():
    response = requests.delete(MAILHOG_BASE_URL + 'v1/messages')
    assert_that(response.status_code).described_as("Test setup failed: Couldn't delete mails in mailhog.")\
        .is_equal_to(200)

def post_comment_with_missing_field_and_assert_error(missing_field: str):
    post_payload = create_post_payload()
    post_payload.pop(missing_field)
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.status_code).is_equal_to(400)
    assert_that(response.json()['message']).is_equal_to(missing_field + " is missing, empty or blank")

def post_comment_with_empty_field_and_assert_error(empty_field: str):
    post_payload = create_post_payload()
    post_payload[empty_field] = ""
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.status_code).is_equal_to(400)
    assert_that(response.json()['message']).is_equal_to(empty_field + " is missing, empty or blank")

def post_comment_with_blank_field_and_assert_error(blank_field: str):
    post_payload = create_post_payload()
    post_payload[blank_field] = " "
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.status_code).is_equal_to(400)
    assert_that(response.json()['message']).is_equal_to(blank_field + " is missing, empty or blank")

def post_comment_to_long_field_and_assert_error(field: str, max_length: int):
    post_payload = create_post_payload()
    post_payload[field] = "x" * (max_length + 1)
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.json()['message']).is_equal_to(field + " value exceeds maximal length of " + str(max_length))
    assert_that(response.status_code).is_equal_to(400)

    # valid length (check it to avoid off-by-one-errors)
    post_payload[field] = "x" * max_length
    post_comment(post_payload)

def assert_timestamp_between(creation_timestamp: str, start: int, end: int):
    timestamp = int(creation_timestamp)
    assert_that(timestamp).is_greater_than_or_equal_to(start)
    assert_that(timestamp).is_less_than_or_equal_to(end)

def post_comment(post_payload, assert_success: bool=True) -> Response:
    response = requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)
    if assert_success:
        assert_that(response.status_code) \
            .described_as("Comment creation failed. Message: " + response.text) \
            .is_equal_to(201)
    return response

def get_comments(site: str = DEFAULT_SITE, path: str = DEFAULT_PATH, assert_success: bool=True) -> Response:
    response = requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, site, path))
    if assert_success:
        assert_that(response.status_code)\
            .described_as("Getting comments failed. Message: " + response.text)\
            .is_equal_to(200)
    return response

def get_comment_by_content(replies, content):
    comments = [comment for comment in replies if comment['content'] == content]
    assert_that(comments)\
        .described_as("There should be at least on comment with the content '{}'. Elements: {}".format(content, str(replies)))\
        .is_length(1)
    return comments[0]


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

def assert_mail_exists(items, expected_body, expected_from, expected_subject, expected_to):
    for item in items:
        content = item['Content']
        headers = content['Headers']
        if content['Body'] == expected_body \
                and headers['From'][0] == expected_from \
                and headers['Subject'][0] == expected_subject \
                and headers['To'][0] == expected_to:
            return
    expected_mail = "({}; {}; {}; {})".format(expected_body, expected_from, expected_subject, expected_to)
    actual_mails = ["({}; {}; {}; {})".format(item['Content']['Body'], item['Content']['Headers']['From'][0], item['Content']['Headers']['Subject'][0], item['Content']['Headers']['To'][0]) for item in items]
    fail("No mail was sent to the author of a comment that was replied to.\nExpected mail:\n{}\nbut found only:\n{}".format(expected_mail, "\n".join(actual_mails)))

def assert_no_mail_except_admin_mail(items):
    for item in items:
        to = item['Content']['Headers']['To'][0]
        if to != ADMIN_EMAIL:
            actual_mail = "({}; {}; {}; {})".format(item['Content']['Body'], item['Content']['Headers']['From'][0], item['Content']['Headers']['Subject'][0], item['Content']['Headers']['To'][0])
            fail("A mail was sent (despite the admin notification) but that shouldn't happen! " + actual_mail)

def get_sql_file_path():
    path = Path("sql/create-comments-table.sql") # if invoked via make in project root
    if path.exists():
        return path
    return Path("../sql/create-comments-table.sql") # if invoked directly in the IDE

if __name__ == '__main__':
    unittest.main()

