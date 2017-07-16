#!/usr/bin/env python3

import requests
import unittest

COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar-js-delivery.php'

class CommentSidecarJsDeliveryTest(unittest.TestCase):
    def test_GET_js_with_translations_path_and_site(self):
        response = requests.get(COMMENT_SIDECAR_URL)
        self.assertEqual(response.status_code, 200)
        js = response.text

        self.assertNotIn("{{comments}}", js)
        self.assertIn("Comments", js)
        self.assertNotIn("{{name}}", js)
        self.assertIn("Name", js)
        self.assertNotIn("{{comment}}", js)
        self.assertIn("Comment", js)
        self.assertNotIn("{{emailHint}}", js)
        self.assertIn("E-Mail will not be published. Gravatar is supported.", js)
        self.assertNotIn("{{submit}}", js)
        self.assertIn("Submit", js)
        self.assertNotIn("{{noCommentsYet}}", js)
        self.assertIn("No comments yet. Be the first!", js)
        self.assertNotIn("{{successMessage}}", js)
        self.assertIn("Successfully submitted comment.", js)
        self.assertNotIn("{{failMessage}}", js)
        self.assertIn("Couldn't submit your comment. Reason: ", js)

        self.assertIn("localhost", js)
        self.assertNotIn("{{SITE}}", js)

        self.assertIn("/comment-sidecar.php", js)
        self.assertNotIn("{{BASE_PATH}}", js)

if __name__ == '__main__':
    unittest.main()