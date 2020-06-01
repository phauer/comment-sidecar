#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict

import click
import dateutil.parser
from mysql.connector import connect

disqus_namespace = {"":"http://disqus.com"}
dsq_ns_url = '{http://disqus.com/disqus-internals}'

@click.command()
@click.option("--disqus_xml_file", help="The comments in Disqus' XML format")
@click.option("--site_url", help="The base site URL where Disqus is currently embedded. e.g. 'https://phauer.com'. This is used to a) extract the path from the full URL and b) find the correct threads and to filter out the synthetic threads that also appear in the XML.")
@click.option("--cs_site_key", help="The imported comments will be assigned to this site key by comment-sidecar")
@click.option("--db_host", help="Database host")
@click.option("--db_port", help="Database port")
@click.option("--db_user", help="Database user")
@click.option("--db_password", help="Database password")
@click.option("--db_name", help="Database name")
def import_comments(disqus_xml_file: str, site_url: str, cs_site_key: str, db_host: str, db_port: str, db_user: str, db_password: str, db_name: str):
    xml_root = ET.parse(disqus_xml_file).getroot()

    print("Retrieving thread ids and urls from Disqus...")
    thread_id_to_url_map = get_thread_id_to_url_map(xml_root, site_url)
    print(f'Got {len(thread_id_to_url_map)} threads from Disqus.')

    print("Retrieving comments from Disqus...")
    comments = get_comments(xml_root)
    print(f"Got {len(comments)} comments from Disqus.")

    print("Inserting Disqus comments into comment-sidecar db...")
    connection = connect(host=db_host, port=db_port, user=db_user, passwd=db_password, db=db_name, charset='utf8', use_unicode=True)
    insert_into_db(connection, thread_id_to_url_map, comments, site_url, cs_site_key)
    print("Done.")

@dataclass
class DisqusComment:
    id: str
    thread_id: str
    author: str
    reply_to: str
    creation_date: str
    creation_date_timestamp: str
    content: str

def insert_into_db(connection, thread_id_to_url_map: Dict[str, str], comments: List[DisqusComment], site_url: str, cs_site_key: str):
    cur = connection.cursor()
    disqus_id_to_sidecar_id: Dict[str, str] = {}
    # sort the comments by the created_date. so we don't run into violation of the reply_to ref integrity.
    sorted_comments = sorted(comments, key=lambda comment: comment.creation_date_timestamp)
    for disqus_comment in sorted_comments:
        print(f'Inserting {disqus_comment}')
        try:
            reply_to_sidecar_id = None if disqus_comment.reply_to is None else disqus_id_to_sidecar_id[disqus_comment.reply_to]
            url = thread_id_to_url_map[disqus_comment.thread_id]
            path = url.replace(site_url, "")
            cur.execute(
                "INSERT INTO comments (author, content, reply_to, site, path, creation_date) VALUES (%s,%s,%s,%s,%s,from_unixtime(%s));",
                (disqus_comment.author, disqus_comment.content, reply_to_sidecar_id, cs_site_key, path,
                 disqus_comment.creation_date_timestamp)
            )
            created_id = cur.lastrowid
            disqus_id_to_sidecar_id[disqus_comment.id] = created_id
        except KeyError:
            # a key error can occur in disqus_id_to_sidecar_id[disqus_comment.reply_to] because:
            # - we try to map a reply to a deleted comment (but deleted comment already got filtered out)
            # - or it can happen when a filtered thread has somehow comments
            print('\tSkipped!')
            pass

    connection.commit()

def get_thread_id_to_url_map(xml_root: ET.Element, site_url: str) -> Dict[str, str]:
    thread_id_to_url_map = {}
    threads = xml_root.findall('thread', disqus_namespace)
    for thread in threads:
        url = thread.findtext(path="link", namespaces=disqus_namespace)
        if url.startswith(site_url) and '?' not in url: # remove strange redundant threads
            thread_id = thread.get(f'{dsq_ns_url}id')
            thread_id_to_url_map[thread_id] = url
    return thread_id_to_url_map

def get_comments(xml_root: ET.Element) -> List[DisqusComment]:
    return [DisqusComment(
        id=post_xml.get(f'{dsq_ns_url}id'),
        thread_id=post_xml.find('thread', disqus_namespace).get(f'{dsq_ns_url}id'),
        author=post_xml.findtext(path="author/name", namespaces=disqus_namespace),
        content=post_xml.findtext(path="message", namespaces=disqus_namespace).strip(),
        reply_to=None if post_xml.find('parent', disqus_namespace) is None else post_xml.find('parent', disqus_namespace).get(f'{dsq_ns_url}id'),
        creation_date=post_xml.findtext(path="createdAt", namespaces=disqus_namespace),
        creation_date_timestamp=get_second_timestamp(post_xml.findtext(path="createdAt", namespaces=disqus_namespace))
    ) for post_xml in xml_root.findall('post', disqus_namespace)
        if post_xml.findtext(path="isDeleted", namespaces=disqus_namespace) == "false"
        and post_xml.findtext(path="isSpam", namespaces=disqus_namespace) == "false"
    ]

def get_second_timestamp(created_at: str) -> str:
    # timestamps in the xml are in UTC.
    utc_created_at = dateutil.parser.parse(created_at+"Z")
    timestamp = utc_created_at.timestamp() # 1499256719.0
    return str(timestamp).replace(".0", "")


if __name__ == '__main__':
    import_comments()
