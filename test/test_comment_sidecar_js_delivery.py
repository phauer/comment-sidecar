#!/usr/bin/env python3

import requests
import unittest

from assertpy import assert_that

COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar-js-delivery.php'

def test_GET_js_with_translations_path_and_site():
    response = requests.get(COMMENT_SIDECAR_URL)
    assert_that(response.status_code).is_equal_to(200)
    js = response.text

    assert_that(js).does_not_contain("{{comments}}")
    assert_that(js).contains("Comments")
    assert_that(js).does_not_contain("{{name}}")
    assert_that(js).contains("Name")
    assert_that(js).does_not_contain("{{emailHint}}")
    assert_that(js).contains("The E-Mail is optional.")
    assert_that(js).does_not_contain("{{submit}}")
    assert_that(js).contains("Submit")
    assert_that(js).does_not_contain("{{noCommentsYet}}")
    assert_that(js).contains("No comments yet. Be the first!")
    assert_that(js).does_not_contain("{{successMessage}}")
    assert_that(js).contains("Successfully submitted comment.")
    assert_that(js).does_not_contain("{{failMessage}}")
    assert_that(js).contains("Couldn't submit your comment. Reason: ")

    assert_that(js).does_not_contain("{{SITE}}")
    assert_that(js).contains("localhost")

    assert_that(js).does_not_contain("{{BASE_PATH}}")
    assert_that(js).contains("/comment-sidecar.php")

if __name__ == '__main__':
    unittest.main()