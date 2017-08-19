#!/usr/bin/env python3

import requests
import MySQLdb
import dateutil.parser
from typing import List, Dict, Any

api_key = "" # get api key via: https://disqus.com/api/applications/register/
forum = "blog-philipphauer" # your website's name in disqus
blog_url_prefix = "https://blog.philipphauer.de" # used to find the correct thread/post URLs (filtering out synthetic threads). you must set the SITE variable in the php configuration to this value.
db_host = '127.0.0.1'
db_port = 3306
db_user = 'root'
db_passwd = 'root'
db_name = 'comment-sidecar'

def import_comments():
    print("Retrieving thread ids and urls from Disqus...")
    thread_id_to_url_map = get_thread_id_to_url_map()
    print("Got {} threads from Disqus.".format(len(thread_id_to_url_map)))

    print("Retrieving comments from Disqus...")
    comments = get_comments(thread_id_to_url_map)
    print("Got {} comments from Disqus.".format(len(comments)))

    print("Inserting Disqus comments into comment-sidecar db...")
    insert_into_db(comments)
    print("Done.")

class Comment:
    def __init__(self, id: str, author, email, content, reply_to: str, site, path, creation_date_timestamp):
        self.id = id
        self.author = author
        self.email = email
        self.content = content
        self.reply_to = reply_to
        self.site = site
        self.path = path
        self.creation_date_timestamp = creation_date_timestamp

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        return "{} {} {} {} {} {} {} {}".format(self.id, self.author, self.email, self.content[:30]+"...", self.reply_to, self.site, self.path, self.creation_date_timestamp)

def insert_into_db(all_comments: List[Comment]):
    # mind to map disqus's ids to our new ones
    connection = MySQLdb.connect(host=db_host, port=db_port, user=db_user, passwd=db_passwd, db=db_name, charset='utf8', use_unicode=True)
    cur = connection.cursor()

    # first, insert all root comments and remember their new ids
    root_comments = [comment for comment in all_comments if comment.reply_to is None]
    disqus_id_to_sidecar_id = insert_comments_and_get_created_ids(cur, root_comments)

    # second insert comments, that have a reply_to that already exists in disqus_id_to_sidecar_id (= 2th level)... and again...
    while True:
        next_level_reply_comments = [comment for comment in all_comments if comment.reply_to in disqus_id_to_sidecar_id]
        if not next_level_reply_comments: # is empty
            break
        disqus_id_to_sidecar_id = insert_comments_and_get_created_ids(cur, next_level_reply_comments, parents_disqus_id_to_sidecar_id=disqus_id_to_sidecar_id)

    connection.commit()

def insert_comments_and_get_created_ids(cur, comments: List[Comment], parents_disqus_id_to_sidecar_id=None):
    print("Inserting {} comments...".format(len(comments)))
    current_disqus_id_to_sidecar_id = dict()
    for disqus_comment in comments:
        sidecar_id = None if disqus_comment.reply_to is None else parents_disqus_id_to_sidecar_id[disqus_comment.reply_to]
        cur.execute(
            "INSERT INTO comments (author, content, reply_to, site, path, creation_date) VALUES (%s,%s,%s,%s,%s,from_unixtime(%s));",
            (disqus_comment.author, disqus_comment.content, sidecar_id, disqus_comment.site, disqus_comment.path,
             disqus_comment.creation_date_timestamp))
        created_id = cur.lastrowid
        current_disqus_id_to_sidecar_id[disqus_comment.id] = created_id
    return current_disqus_id_to_sidecar_id

def get_all_results(url) -> List[Dict[str, Any]]:
    """pages through the responses to fetch all responses"""
    if not api_key:
        raise Exception("api key is not set!")
    has_next = True
    next_cursor = None
    result = []
    while has_next:
        cursor_param = "" if next_cursor is None else "&cursor=" + next_cursor
        json = requests.get(url="{}&api_key={}{}".format(url, api_key, cursor_param)).json()
        has_next = json["cursor"]["hasNext"]
        next_cursor = json["cursor"]["next"]
        result.extend(json["response"])
    return result

def get_thread_id_to_url_map() -> Dict[str, str]:
    threads = get_all_results(url="https://disqus.com/api/3.0/forums/listThreads.json?forum={}&limit=100".format(forum))
    thread_id_to_url_map = {}
    for thread in threads:
        url = thread["link"]
        if url.startswith(blog_url_prefix):
            thread_id_to_url_map[thread["id"]] = url
    return thread_id_to_url_map

def get_comments(thread_id_to_url_map: Dict[str, str]) -> List[Comment]:
    disqus_comments = get_all_results(url="https://disqus.com/api/3.0/posts/list.json?forum={}&limit=100".format(forum))
    return [map_to_comment(x, thread_id_to_url_map) for x in disqus_comments]

def map_to_comment(disqus_comment, thread_id_to_url_map: Dict[str, str]) -> Comment:
    url = thread_id_to_url_map[disqus_comment["thread"]]
    path = url.replace(blog_url_prefix, "")
    utc_created_at = get_second_timestamp(disqus_comment["createdAt"])
    parent = disqus_comment["parent"]
    return Comment(
        id=disqus_comment["id"],
        author=disqus_comment["author"]["name"],
        email=None,
        content=disqus_comment["raw_message"],
        reply_to=None if parent is None else str(parent),
        site=blog_url_prefix,
        path=path,
        creation_date_timestamp=utc_created_at
    )

def get_second_timestamp(created_at: str) -> str:
    # timestamps in the api are UTC.
    utc_created_at = dateutil.parser.parse(created_at+"Z")
    timestamp = utc_created_at.timestamp() # 1499256719.0
    return str(timestamp).replace(".0", "")

import_comments()

# ideas
# no email in disqus api => no avatar. insert author.avatar.small.permalink instead? new column "avatar_url" required...

