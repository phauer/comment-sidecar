#!/usr/bin/env python3

import MySQLdb # sudo apt install libmysqlclient-dev python-dev && pip3 install mysqlclient
import requests # pip3 install requests
import unittest
from path import Path # pip3 install path.py

COMMENT_SIDECAR_URL = 'http://localhost/comment-sidecar.php'

class PlaylistTest(unittest.TestCase):
    def setUp(self):
        # first, run `docker-compose up`
        db = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='comment-sidecar')
        cur = db.cursor()
        with Path("create-comments-table.sql").open('r') as sql:
            query = "\n".join(sql.readlines())
            cur.execute(query)

    def test_create_and_get_comment(self):
        post_payload = {
            "author": "Peter",
            "content": "Super comment",
            "creationTimestamp": "1499604757",
            "email": "bla@bla.de",
            "id": "1",
            "path": "/post-abc/",
            "replyTo": None,
            "site": "mydomain.com"
        }
        post_response = requests.post(url=COMMENT_SIDECAR_URL, json=post_payload)
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(post_response.text, "")

        get_response = requests.get(COMMENT_SIDECAR_URL)
        self.assertEqual(get_response.status_code, 200)
        comments_json = get_response.json()
        self.assertEqual(len(comments_json), 1)

        created_comment = comments_json[0]
        self.assertEqual(created_comment["author"], "Peter")
        self.assertEqual(created_comment["content"], "Super comment")
        self.assertEqual(created_comment["creationTimestamp"], "1499604757")
        self.assertEqual(created_comment["email"], "bla@bla.de")
        self.assertEqual(created_comment["id"], "1")
        self.assertEqual(created_comment["path"], "/post-abc/")
        self.assertEqual(created_comment["replyTo"], None)
        self.assertEqual(created_comment["site"], "mydomain.com")


if __name__ == '__main__':
    unittest.main()

