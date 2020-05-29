#!/usr/bin/env python3

import pytest
import requests
from mysql.connector import connect
from requests.models import Response
import unittest
import hashlib
import time
from path import Path
from assertpy import assert_that, fail

UNSUBSCRIBE_SUCCESS_MSG = "You have been unsubscribed successfully."
UNSUBSCRIBE_ERROR_MSG = "Nothing has been updated. Either the comment doesn't exist or the unsubscribe token is invalid."
ADMIN_EMAIL = 'test@localhost.de'
DEFAULT_PATH = "/blogpost1/"
DEFAULT_SITE = "https://petersworld.com"
ERROR_MESSAGE_MISSING_SITE_PATH = "Please submit both query parameters 'site' and 'path'"
INVALID_QUERY_PARAMS_UNSUBSCRIBE = "Please submit both query parameters 'commentId' and 'unsubscribeToken'"
COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar.php'
UNSUBSCRIBE_URL = 'http://localhost/unsubscribe.php'
MAILHOG_BASE_URL = 'http://localhost:8025/api/'
MAILHOG_MESSAGES_URL = MAILHOG_BASE_URL + 'v2/messages'
MYSQLDB_CONNECTION = {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'passwd': 'root', 'db': 'comment-sidecar'}

@pytest.fixture
def db():
    # first, run `docker-compose up`
    db = connect(**MYSQLDB_CONNECTION)
    cur = db.cursor()
    with get_sql_file_path().open('r') as sql:
        query = "".join(sql.readlines())
        cur.execute(query)
    return db

@pytest.mark.parametrize("queryParams", {'', 'site=&path=', 'site=domain.com', 'path=blogpost1'})
def test_GET_invalid_query_params(db, queryParams):
    response = requests.get(f'{COMMENT_SIDECAR_URL}?{queryParams}')
    assert_that(response.status_code).is_equal_to(400)
    assert_that(response.json()["message"]).is_equal_to(ERROR_MESSAGE_MISSING_SITE_PATH)

def test_GET_empty_array_if_no_comments(db):
    response = get_comments()
    assert_that(response.text).is_equal_to('[]')

def test_POST_and_GET_comment(db):
    post_payload = create_post_payload()
    timestamp_before = int(time.time())
    response = post_comment(post_payload)
    timestamp_after = int(time.time())
    assert_that(response.json()['id']).is_equal_to(1)

    get_response = get_comments()
    comments_json = get_response.json()
    assert_that(comments_json).is_length(1)

    returned_comment = comments_json[0]
    assert_that(returned_comment)\
        .contains_entry({'id': '1'})\
        .contains_entry({'author': post_payload["author"]})\
        .contains_entry({'content': post_payload["content"]})\
        .contains_entry({'gravatarUrl': create_gravatar_url(post_payload["email"])}) \
        .does_not_contain_key('replies')
    assert_timestamp_between(returned_comment["creationTimestamp"], start=timestamp_before, end=timestamp_after)
    assert_absent_fields(returned_comment)

def test_POST_comments_and_replies_and_GET_reply_chain(db):
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
    assert_that(returned_comments).is_length(1) # replies are nested so only one root comment
    replies = returned_comments[0]['replies']

    # check reply level 1
    assert_that(replies).is_not_none().is_length(2)
    assert_replies_contains(replies, {
        'content': 'reply 1 to root', 'id': '2', 'author': 'Peter',
    })
    assert_replies_contains(replies, {
        'content': 'reply 2 to root', 'id': '3', 'author': 'Peter',
    })
    for reply in replies:
        assert_absent_fields(reply)

    # check reply level 2
    comment = get_comment_by_content(replies, 'reply 2 to root')
    replies_to_reply = comment['replies']
    assert_that(replies_to_reply).is_length(1)
    assert_replies_contains(replies_to_reply, {
        'content': 'reply 3 to reply 2', 'id': '4', 'author': 'Peter',
    })

def test_POST_invalid_replyTo_ID(db):
    post_payload = create_post_payload()
    post_payload['replyTo'] = '989089'
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.status_code).described_as("Invalid replyTo ID should be rejected.").is_equal_to(400)
    assert_that(response.json()['message']).is_equal_to("The replyTo value '989089' refers to a not existing id.")

def test_POST_and_GET_comment_with_german_umlauts(db):
    post_payload = create_post_payload()
    post_payload['content'] = "äöüß - Deutsche Umlaute? Kein Problem für utf-8! ÖÄÜ"
    post_payload['author'] = "öäüßÖÄÜ"
    response = post_comment(post_payload)
    assert_that(response.json()['id']).is_equal_to(1)

    get_response = get_comments()
    returned_comment = get_response.json()[0]
    assert_that(returned_comment)\
        .contains_entry({'author': post_payload["author"]})\
        .contains_entry({'content': post_payload["content"]})

def test_OPTIONS_CORS_headers_valid_origin(db):
    # before sending a POST, the browser will send an OPTION request as a preflight to see the CORS headers.
    # the backend will only return the required CORS headers, if the Origin is set to a allowed domain.
    post_payload = create_post_payload()
    valid_origin = 'http://testdomain.com'
    preflight_response = requests.options(url=COMMENT_SIDECAR_URL, json=post_payload, headers={'Origin': valid_origin})
    assert_cors_headers_exists(preflight_response, valid_origin)
    assert_that(preflight_response.text).is_empty()
    assert_that(get_comments().json())\
        .described_as("No comment should have been created after an OPTIONS request")\
        .is_empty()

def test_OPTIONS_CORS_headers_invalid_origin(db):
    post_payload = create_post_payload()
    valid_origin = 'http://invalid.com'
    preflight_response = requests.options(url=COMMENT_SIDECAR_URL, json=post_payload, headers={'Origin': valid_origin})
    assert_cors_headers_doesnt_exists(preflight_response)
    assert_that(preflight_response.text).is_empty()
    assert_that(get_comments().json()) \
        .described_as("No comment should have been created after an OPTIONS request") \
        .is_empty()

def test_GET_CORS_headers_valid_origin(db):
    # for GETs, the browser will request immediately (without preflight), but will reject the response, if the CORS are not set.
    # the backend will only return the required CORS headers, if the Origin is set to a allowed domain.
    valid_origin = 'http://testdomain.com'
    response = requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, DEFAULT_SITE, DEFAULT_PATH), headers={'Origin': valid_origin})
    assert_cors_headers_exists(response, valid_origin)

def test_GET_CORS_headers_invalid_origin(db):
    valid_origin = 'http://invalid.com'
    response = requests.get("{}?site={}&path={}".format(COMMENT_SIDECAR_URL, DEFAULT_SITE, DEFAULT_PATH), headers={'Origin': valid_origin})
    assert_cors_headers_doesnt_exists(response)

def test_GET_different_paths(db):
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

def test_GET_different_sites(db):
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

def test_POST_without_optional_email(db):
    post_payload = create_post_payload()
    post_payload.pop('email')
    response = post_comment(post_payload)
    assert_that(response.json()['id']).is_equal_to(1)

@pytest.mark.parametrize("field", {'author', 'content', 'site', 'path'})
def test_POST_missing_fields(db, field):
    post_comment_with_missing_field_and_assert_error(field)

@pytest.mark.parametrize("field", {'author', 'content', 'site', 'path'})
def test_POST_empty_fields(db, field):
    post_comment_with_empty_field_and_assert_error(field)

@pytest.mark.parametrize("field", {'author', 'content', 'site', 'path'})
def test_POST_blank_fields(db, field):
    post_comment_with_blank_field_and_assert_error(field)

def test_POST_to_long_fields(db):
    post_comment_to_long_field_and_assert_error('author', 40)
    post_comment_to_long_field_and_assert_error('email', 40)
    post_comment_to_long_field_and_assert_error('site', 40)
    post_comment_to_long_field_and_assert_error('path', 170)

def test_POST_spam_protection_set_url_is_spam(db):
    post_payload = create_post_payload()
    post_payload['url'] = 'http://only.spambots.will/populate/this/field/'
    response = post_comment(post_payload, assert_success=False)
    assert_that(response.status_code)\
        .described_as("POST payload with an URL field should be rejected. The URL an hidden form field and used for spam protection.")\
        .is_equal_to(400)
    assert_that(response.json()['message']).is_empty()

def test_email_notification_after_successful_POST(db):
    clear_mails()

    post_payload = create_post_payload()
    post_comment(post_payload)

    json = requests.get(MAILHOG_MESSAGES_URL).json()
    assert_that(json['total']).is_equal_to(1)
    mail_content = json['items'][0]['Content']
    mail_body = mail_content['Body']
    assert_that(mail_body).contains(post_payload['site'])\
        .contains(post_payload['path'])\
        .contains(post_payload['content'])
    headers = mail_content['Headers']
    assert_that(headers['Content-Transfer-Encoding'][0]).is_equal_to('8bit')
    assert_that(headers['Content-Type'][0]).is_equal_to('text/plain; charset=UTF-8')
    assert_that(headers['Mime-Version'][0]).is_equal_to('1.0')
    assert_that(headers['From'][0]).is_equal_to('{}<{}>'.format(post_payload['author'], post_payload['email']))
    assert_that(headers['Subject'][0]).is_equal_to('Comment by {} on {}'.format(post_payload['author'], post_payload['path']))
    assert_that(headers['To'][0]).is_equal_to(ADMIN_EMAIL)

def test_no_email_notification_after_invalid_POST(db):
    clear_mails()

    post_payload = create_post_payload()
    post_payload.pop('author')
    post_comment(post_payload, assert_success=False)

    json = requests.get(MAILHOG_MESSAGES_URL).json()
    assert_that(json['total']).is_equal_to(0)

def test_POST_spam_protection_empty_url_is_fine(db):
    post_payload = create_post_payload()
    post_payload['url'] = ""
    response = post_comment(post_payload)
    assert_that(response.json()['id']).is_equal_to(1)

def test_escaped_HTML_XSS_protection(db):
    post_payload = create_post_payload()
    post_payload['author'] = "<strong>Peter</strong>"
    post_payload['content'] = '<script type="text/javascript">document.querySelector("aside#comment-sidecar h1").innerText = "XSS";</script>'
    response = post_comment(post_payload)
    assert_that(response.json()['id']).is_equal_to(1)

    returned_json = get_comments().json()[0]
    assert_that(returned_json)\
        .contains_entry({'author': '&lt;strong&gt;Peter&lt;/strong&gt;'})\
        .contains_entry({'content': '&lt;script type=&quot;text/javascript&quot;&gt;document.querySelector(&quot;aside#comment-sidecar h1&quot;).innerText = &quot;XSS&quot;;&lt;/script&gt;'})

def test_subscription_mail_on_reply(db):
    clear_mails()
    path = "/commented-post/"
    site = "https://mysupersite.de"
    parent = create_post_payload()
    parent["email"] = "root@root.com"
    parent["path"] = path
    parent["site"] = site
    response = post_comment(parent)
    parent_id = response.json()['id']

    reply = create_post_payload()
    reply["replyTo"] = parent_id
    reply["path"] = path
    reply["site"] = site
    reply["content"] = "Root, I disagree!"
    reply["email"] = "reply@reply.com!"
    reply["author"] = "Replyer"
    post_comment(reply)

    json = requests.get(MAILHOG_MESSAGES_URL).json()
    assert_that(json['total']).is_greater_than(1)

    mail = find_mail_by_sender(items=json['items'], email_from=reply["author"])
    if not mail:
        fail("No notification mail was found! recipient/parent: {}. sender/reply author: {}".format(parent["email"], reply["author"]))

    assert_that(mail["from"]).contains(reply["author"])\
        .does_not_contain(reply["email"])
    assert_that(mail).has_subject("Reply to your comment by {}".format(reply["author"]))\
        .has_to(parent["email"])

    unsubscribe_token = retrieve_unsubscribe_token_from_db(parent_id)
    unsubscribe_link = "{}?commentId={}&unsubscribeToken={}".format(UNSUBSCRIBE_URL, parent_id, unsubscribe_token)
    link_to_site = "{}{}#comment-sidecar".format(site, path)
    assert_that(mail["body"]).contains(reply["content"])\
        .contains(unsubscribe_link)\
        .contains(link_to_site)\
        .contains(reply["author"])\
        .does_not_contain(reply["email"])

def test_subscription_no_mail_on_reply_if_no_parent_mail_defined(db):
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

def test_subscription_no_mail_on_reply_if_unsubscribed(db):
    clear_mails()
    root_payload = create_post_payload()
    root_payload["email"] = "root@root.com"
    response = post_comment(root_payload)
    root_id = response.json()['id']

    unsubscribe_token = retrieve_unsubscribe_token_from_db(root_id)
    unsubscribe(root_id, unsubscribe_token)

    reply_payload = create_post_payload()
    reply_payload["replyTo"] = root_id
    reply_payload["content"] = "Root, I disagree!"
    reply_payload["email"] = "reply@reply.com!"
    reply_payload["author"] = "Replyer"
    post_comment(reply_payload)

    json = requests.get(MAILHOG_MESSAGES_URL).json()
    assert_no_mail_except_admin_mail(items=json['items'])

def test_unsubscribe_missing_parameter(db):
    unsubscribe_with_url_assert_error('{}'.format(UNSUBSCRIBE_URL))
    unsubscribe_with_url_assert_error('{}?commentId={}'.format(UNSUBSCRIBE_URL, 1))
    unsubscribe_with_url_assert_error('{}?unsubscribeToken={}'.format(UNSUBSCRIBE_URL, '12391023'))

def test_unsubscribe(db):
    payload = create_post_payload()
    response = post_comment(payload)
    id = response.json()["id"]
    assume_subscription_state_in_db(id, True)
    unsubscribe_token = retrieve_unsubscribe_token_from_db(id)
    response = unsubscribe(id, unsubscribe_token)
    assert_that(response.text).is_equal_to(UNSUBSCRIBE_SUCCESS_MSG)
    assume_subscription_state_in_db(id, False)

def test_unsubscribe_twice(db):
    payload = create_post_payload()
    response = post_comment(payload)
    id = response.json()["id"]
    assume_subscription_state_in_db(id, True)
    unsubscribe_token = retrieve_unsubscribe_token_from_db(id)
    unsubscribe(id, unsubscribe_token)
    response = unsubscribe(id, unsubscribe_token)
    assert_that(response.text).is_equal_to(UNSUBSCRIBE_ERROR_MSG)
    assume_subscription_state_in_db(id, False)

def test_unsubscribe_wrong_token(db):
    payload = create_post_payload()
    response = post_comment(payload)
    id = response.json()["id"]
    assume_subscription_state_in_db(id, True)
    invalid_unsubscribe_token = "1111jd"
    response = unsubscribe(id, invalid_unsubscribe_token)
    assert_that(response.text).is_equal_to(UNSUBSCRIBE_ERROR_MSG)
    assume_subscription_state_in_db(id, True)

def test_unsubscribe_wrong_id(db):
    payload = create_post_payload()
    response = post_comment(payload)
    id = response.json()["id"]
    unsubscribe_token = retrieve_unsubscribe_token_from_db(id)
    response = unsubscribe(123, unsubscribe_token)
    assert_that(response.text).is_equal_to(UNSUBSCRIBE_ERROR_MSG)

# PRIVATE functions

def assume_subscription_state_in_db(comment_id, expected_subscription_state):
    db = connect(**MYSQLDB_CONNECTION)
    cur = db.cursor()
    cur.execute("SELECT subscribed FROM comments WHERE id = {}".format(comment_id))
    subscribed = cur.fetchone()[0]
    if expected_subscription_state:
        assert_that(subscribed).described_as('subscribed state').is_equal_to(1)
    else:
        assert_that(subscribed).described_as('subscribed state').is_equal_to(0)

def retrieve_unsubscribe_token_from_db(comment_id):
    db = connect(**MYSQLDB_CONNECTION)
    cur = db.cursor()
    cur.execute("SELECT unsubscribe_token FROM comments WHERE id = {}".format(comment_id))
    return cur.fetchone()[0]

def unsubscribe(comment_id, unsubscribe_token):
    response = requests.get(url='{}?commentId={}&unsubscribeToken={}&XDEBUG_SESSION_START=IDEA_DEBUG'.format(UNSUBSCRIBE_URL, comment_id, unsubscribe_token))
    assert_that(response).has_status_code(200)
    return response

def unsubscribe_with_url_assert_error(url):
    response = requests.get(url)
    assert_that(response).has_status_code(400)
    assert_that(response.json()['message']).is_equal_to(INVALID_QUERY_PARAMS_UNSUBSCRIBE)


def assert_cors_headers_exists(preflight_response, exptected_allowed_origin):
    assert_that(preflight_response.headers)\
        .contains_entry({'Access-Control-Allow-Origin': exptected_allowed_origin})\
        .contains_entry({'Access-Control-Allow-Methods': 'GET, POST'})\
        .contains_entry({'Access-Control-Allow-Headers': 'Content-Type'})

def assert_cors_headers_doesnt_exists(preflight_response):
    assert_that(preflight_response.headers)\
        .does_not_contain_key('Access-Control-Allow-Origin')\
        .does_not_contain_key('Access-Control-Allow-Methods')\
        .does_not_contain_key('Access-Control-Allow-Headers')

def assert_replies_contains(replies, assumed_element):
    replies_matching_assumed_element = [reply for reply in replies
                                        if reply['content'] == assumed_element['content']
                                        and reply['id'] == assumed_element['id']
                                        and reply['author'] == assumed_element['author']
                                        ]
    assert_that(replies_matching_assumed_element) \
        .described_as("Element is not in the list (or more than once).\nassumed_element: {}\nall elements: {}\n".format(assumed_element, replies)) \
        .is_length(1)

def assert_absent_fields(returned_comment):
    assert_that(returned_comment).does_not_contain_key('email')\
        .does_not_contain_key('path')\
        .does_not_contain_key('site')\
        .does_not_contain_key('replyTo')

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
    assert_that(timestamp).is_greater_than_or_equal_to(start)\
        .is_less_than_or_equal_to(end)

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

def find_mail_by_sender(items, email_from: str):
    for item in items:
        content = item['Content']
        headers = content['Headers']
        if email_from in headers['From'][0]:
            return {
                "from": headers['From'][0]
                , "subject": headers['Subject'][0]
                , "to": headers['To'][0]
                , "body": content['Body']
            }
    return None

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

