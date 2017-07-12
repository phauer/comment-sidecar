# Under Development!


# comment-sidecar

comment-sidecar is a **lightweight, tracking-free, self-hosted comment service**. It aims at restricted web spaces where only **PHP and MySQL** are available. And it is easy to embed into statically generated sites that are created with Hugo or Jekyll.
  
# Planned Features

- Tracking-free and fast. The comment-sidecar only needs one additional request. Contrary, Disqus leads to **110 additional requests**! Read [here](http://donw.io/post/github-comments/) for more details about Disqus' tracking greed and performance impact.
- Privacy. Your data belongs to you.
- Easy to integrate. Just a simple Javascript call. This makes is easy to use the comment-sidecar in conjunction with static site generators like **Hugo** or Jekyll. You don't have to integrate PHP code in the generated HTML files.
- Lightweight: No additional PHP or JavaScript dependencies. Just drop the files on your web server and you are good to go.
- No account required. The visitors of your side don't need to have an account to drop a comment.
- No performance impact on TTFB (Time To First Byte), because the comments are loaded asynchronously.
- Spam Protection.
- E-Mail Notification. E-Mail includes a deletion link to easily remove undesired comments. 
- Gravatar Support.
- Markdown Support.
- Use one comment-sidecar installation for multiple sites.
- Replying to a comment is supported.

# Requirements

- PHP
- A MySQL database
- Some native [ECMAScript 6](http://es6-features.org/) support in the user's browser. For now, the comment-sidecar requires support for basic ECMAScript 6 features like [arrow functions](http://www.caniuse.com/#search=arrow), [`const`](http://www.caniuse.com/#search=const), [template literals](http://www.caniuse.com/#search=template) and other modern methods like [`querySelector()`](http://www.caniuse.com/#search=queryselector) and [`fetch()`](http://www.caniuse.com/#search=fetch). Currently, the supporting browser versions have a global usage of 73% - 98%. This was good enough for me. So I decided against a compilation with babel in order to avoid a dedicated build process. However, pull requests are always welcome. Alternatively, you can compile the `comment-sidecar.js` manually once only.

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

## Run Python Tests for the Backend

```bash
# start mysql database in docker container
docker-compose up -d

# set up python environment
python3 --version # you need at least python 3.5 to run the tests
sudo apt install python3-pip
sudo apt install libmysqlclient-dev python-dev 
pip3 install mysqlclient requests path.py

cd test
./test_comment_sidecar.py
```