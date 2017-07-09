# Under Development!


# comment-sidecar

comment-sidecar is a lightweight, tracking-free, self-hosted comment service. It aims at restricted web spaces where only PHP and MySQL is available. And it is easy to embed into statically generated sites that are created with Hugo or Jekyll.
  
# Planned Features

- Tracking-free and fast. The comment-sidecar only needs one additional request. Contrary, Disqus leads to **110 additional requests**! Read [here](http://donw.io/post/github-comments/) for more details about Disqus' tracking greed and performance impact.
- Privacy. Your data belongs to you.
- Easy to integrate. Just a simple Javascript call. This makes is easy to use the comment-sidecar in conjunction with static site generators like **Hugo** or Jekyll. You don't have to integrate PHP code in the generated HTML files.
- Lightweight: Zero Dependencies.
- No performance impact on TTFB (Time To First Byte), because the comments are loaded asynchronously.
- Spam Protection.
- E-Mail Notification. E-Mail includes a deletion link to easily remove undesired comments. 
- Gravatar Support.
- Markdown Support.
- Use one comment-sidecar installation for multiple sites.
- Replying to a comment is supported.

# Disclaimer

I'm not a PHP expert. ;-)

# Development

## PHP Backend Service

```bash
# start apache with php and mysql database in docker containers
docker-compose up -d

# create the table 'comments'. either execute test/create-comments-table.sql manually or execute the tests (see below)

# now you can execute HTTP requests like
http localhost/comment-sidecar.php
http POST localhost/comment-sidecar.php < adhoc/comment-payload.json

# develop in src/comment-sidecar.php. The changes take affect immediately. 
```

## Run Python Test for the Backend

```bash
# start mysql database in docker container
docker-compose up -d

# set up python environment
python3 --version # you need at least python 3.5 to run the tests
sudo apt install python3-pip
sudo apt install libmysqlclient-dev python-dev && pip3 install mysqlclient
pip3 install requests
pip3 install path.py

cd test
./test_comment_sidecar.py
```