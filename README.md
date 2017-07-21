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

# Try it out up front!

Do you want to try the comment-sidecar before you install it on your site? No problem! You only need Docker and Docker-Compose and your are ready to go.
 
```bash
docker-compose up
```

This starts a MySQL database (which already contains the required table and index), [MailHog](https://github.com/mailhog/MailHog) (a test mail server) and an Apache with PHP.

Now open [`http://localhost/playground.html`](http://localhost/playground.html) in your browser and play with the comment-sidecar in action. On [`http://localhost:8025/`](http://localhost:8025/) you can see the send notification mails.

# Installation

Create a MySQL database and note the credentials. 

Create the required table and the index. Therefore, execute the SQL statements in  [`sql/create-comments-table.sql`](https://github.com/phauer/comment-sidecar/blob/master/sql/create-comments-table.sql) 

Copy whole content of the `src` directory (except `playground.html`) to your webspace. You can put it wherever you like. Just remember the path. The following example assumes that all files are put in the root directory `/`.

Open `comment-sidecar-config.php` and configure it:

```php
<?php
const LANGUAGE = "en"; # see translations folder for supported languages
const SITE = "domain.com"; # key for this site to identity comment of this site
const E_MAIL_FOR_NOTIFICATIONS = "your.email@domain.com";
const DB_HOST = 'localhost'; # to access from host system, use 127.0.0.1
const DB_NAME = 'wb3d23s';
const DB_USER = 'wb3d23s';
const DB_PW = '1234';
const DB_PORT = 3306;
```

Open the HTML file where you like to embed the comments. Insert the following snippet and set the correct path of `comment-sidecar.js`.

```html
<aside id="comment-sidecar"></aside>
<script type="text/javascript">
    (function() {
        const scriptNode = document.createElement('script');
        scriptNode.type = 'text/javascript';
        scriptNode.async = true;
        scriptNode.src = '/comment-sidecar-js-delivery.php'; //adjust to the correct path
        (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(scriptNode);
    })();
</script>
```

Optionally, you can include `comment-sidecar-basic.css` in the HTML header to get some basic styling. Or you can simply copy its content to your own CSS file in order to avoid a additional HTTP request.

A complete example for the frontend can be found in [`src/playground.html`](https://github.com/phauer/comment-sidecar/blob/master/src/playground.html).  

# Development

## PHP Backend Service

```bash
# start apache with php, mysql database (with the required table) and mailhog in docker containers
docker-compose up -d

# now you can execute HTTP requests like
http http://localhost/comment-sidecar.php
http POST http://localhost/comment-sidecar.php < adhoc/comment-payload.json

# develop in src/comment-sidecar.php. The changes take affect immediately. 
```

## Run the Python Tests for the Backend

```bash
# start mysql database and mailhog in docker containers
docker-compose up -d

# set up python environment
python3 --version # you need at least python 3.5 to run the tests
sudo apt install python3-pip libmysqlclient-dev python-dev
pip3 install mysqlclient requests path.py

cd test
python3 -m unittest discover . 
# or only one test file: ./test_comment_sidecar.py
```

## See the Send Mails

MailHog provides a neat Web UI. Just open [`http://localhost:8025/`](http://localhost:8025/) after calling `docker-compose up`.

## Connect to the MySQL Container using a MySQL Client

Use host `127.0.0.1` instead of `localhost`! Port `3306`. Database `comment-sidecar`. User `root` and password `root`.

## Debugging with IntelliJ IDEA/PhpStorm

The PHP container contains already xdebug. You only have to set up IntelliJ IDEA Ultimate or PhpStorm.

- Create a Run Configuration "PHP Remote Debug". You may need to click on "n items more (irrelevant)" to find this Run Configuration.
- Create a new Server
    - Name: docker (or so)
    - Host: `localhost`
    - Port: `80`
    - Debugger: `Xdebug`
    - Use path mappings: `src` -> `/var/www/html`
- ide key(session id): `IDEA_DEBUG` (or everything you like; but remember this key)

Start the Run Configuration and set a breakpoint. To trigger it, you have to append the query parameter `XDEBUG_SESSION_START=IDEA_DEBUG` to the URL when calling the service. Other means (like browser extensions) can be found here: [Remote debugging with xdebug](https://xdebug.org/docs/remote). 

### Tips and Links for the Debug Setup

- Does xdebug work at all in the container? Call [`http://localhost/phpinfo.php`](http://localhost/phpinfo.php) and check if xdebug is loaded and how it is configured. Other means can be found [here](https://stackoverflow.com/questions/14046501/check-if-xdebug-is-working) 
- ['How to setup xdebug and phpstorm'](https://forums.docker.com/t/solved-how-to-setup-xdebug-and-phpstorm/13641/12) was very helpful to set up xdebug in this dockerized environment properly.
- [Install xdebug](https://xdebug.org/docs/install) - just if you are curious.
- Maybe ['Configuring xdebug in IDEA'](https://www.jetbrains.com/help/idea/configuring-xdebug.html) can also be helpful.
