# comment-sidecar

comment-sidecar is a **lightweight, tracking-free, self-hosted comment service**. It aims at restricted self-hosted web spaces where only **PHP and MySQL** are available. And it is easy to embed into statically generated sites that are created with Hugo or Jekyll. It's a Disqus alternative.

[![comment-sidecar frontend](docs/screenshot-frontend-400.png)](https://raw.githubusercontent.com/phauer/comment-sidecar/master/docs/screenshot-frontend.png)
 
# Features

- Tracking-free and fast. The comment-sidecar only needs two additional requests. Contrary, Disqus leads to **110 additional requests**. Read [here](http://donw.io/post/github-comments/) for more details about Disqus' tracking greed and performance impact.
- Privacy. No Tracking. comment-sidecar only saves the data that are required. The E-Mail is optional and only used for notifications. The IP is only saved for a short amount of time and can't be traced back to the E-Mail. It's used to support basic rate limiting. 
- Easy to integrate. Just a simple Javascript call. This makes it easy to use the comment-sidecar in conjunction with static site generators like **Hugo** or Jekyll. You don't have to integrate PHP code in the generated HTML files.
- Lightweight: No additional PHP or JavaScript dependencies. Just drop the files on your web server and you are good to go.
- No performance impact on TTFB (Time To First Byte), because the comments are loaded asynchronously.
- Spam Protection.
- E-Mail Notification.
    - Admin receives mail for every comment.
    - Users receive Mail if there is an direct reply to their comment.
- Use one comment-sidecar installation for multiple sites.
- Replying to a comment is supported.
- Multi-language support (pull requests adding more languages are highly welcome).
- Customizable form HTML
- Import existing Disqus comments.
- Simple rate limiting based on the IP address (`$_SERVER['REMOTE_ADDR']`)

# What's Different to Disqus

- Everyone can comment. There is no registration required to write a comment.
- Currently, you can't edit or delete a post after the submission.
- There is no individual avatar. I remove the Gravatar support due to privacy concerns: I don't want to share my visitor's data with Gravatar. Moreover, it's too easy to get their E-Mail out of the MD5 hash in the image URL.

# Before and After

I migrated my [blog](https://phauer.com) from Disqus to Comment-Sidecar. Here you can see the metrics of the Chrome Dev Tools and Lighthouse. Mind, that you can achieve the same performance also with many other Disqus alternatives.

![Before and After the Disqus Migration on phauer.com](docs/before-after-phauer-com.png)

# Requirements

- PHP. Tested with 7.1.
- A MySQL database. Tested with 5.7.28.
- Some native [ECMAScript 6](http://es6-features.org/) support in the user's browser. For now, the comment-sidecar requires support for basic ECMAScript 6 features like [arrow functions](http://www.caniuse.com/#search=arrow), [`const`](http://www.caniuse.com/#search=const), [template literals](http://www.caniuse.com/#search=template) and other modern methods like [`querySelector()`](http://www.caniuse.com/#search=queryselector) and [`fetch()`](http://www.caniuse.com/#search=fetch). Currently, the supporting browser versions have a global usage of 95% - 98%. This was good enough for me. So I decided against a compilation with Babel in order to avoid a dedicated build process. However, pull requests are always welcome. Alternatively, you can compile the `comment-sidecar.js` manually once only.

# Try it out up front!

Do you want to try the comment-sidecar before you install it on your site? No problem! You only need Docker and Docker-Compose and you are ready to go.
 
```bash
docker-compose up
```

This starts a MySQL database (which already contains the required table and index), [MailHog](https://github.com/mailhog/MailHog) (a test mail server) and an Apache with PHP.

Now open [`http://localhost/playground.html`](http://localhost/playground.html) in your browser and play with the comment-sidecar in action. On [`http://localhost:8025/`](http://localhost:8025/) you can see the sent notification mails.

# Installation

Create a MySQL database and note the credentials. 

Create the required tables and the index. Therefore, execute the SQL statements in  [`sql/init.sql`](https://github.com/phauer/comment-sidecar/blob/master/sql/init.sql) 

Copy the whole content of the `src` directory (except `playground.html`) to your web space. You can put it wherever you like. Just remember the path. The following example assumes that all files are put in the root directory `/`.

Open `config.php` and configure it:

```php
<?php
const LANGUAGE = "en"; # see the `translations` folder for supported languages
const SITE = "mydomain.com"; # key for this site to identity comments of this site
const E_MAIL_FOR_NOTIFICATIONS = "your.email@domain.com"; # admin mail that will receive a notification e-mail after every new comment
const BASE_URL = "http://mydomain.com/"; # base url of the comment-sidecar backend. can differ from the embedding site.
const ALLOWED_ACCESSING_SITES = [ "http://domainA.com", "http://domainB.com" ]; # sites that are allowed to access the backend (required when the backend is deployed on a different domain than the embedding site.)

const DB_HOST = 'localhost'; # to access from host system, use 127.0.0.1
const DB_NAME = 'wb3d23s';
const DB_USER = 'wb3d23s';
const DB_PW = '1234';
const DB_PORT = 3306;

const FORM_TEMPLATE = "bootstrap-default"; # see the `form-templates` folder for the available form templates or define your own. examples: "bootstrap-default" or "bulma-default".
const BUTTON_CSS_CLASSES_ADD_COMMENT = "btn btn-link"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"
const BUTTON_CSS_CLASSES_REPLY = "btn btn-link"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link is-small"

const RATE_LIMIT_THRESHOLD_SECONDS = "60"; # how long a user (defined by their IP) have to wait until they can comment again
```

Open the HTML file where you like to embed the comments. Insert the following snippet and set the correct path of the `comment-sidecar-js-delivery.php` file.

```html
<aside id="comment-sidecar"></aside>
<script type="text/javascript">
    (function() {
        const scriptNode = document.createElement('script');
        scriptNode.type = 'text/javascript';
        scriptNode.async = true;
        scriptNode.src = 'http://domainC.com/comment-sidecar-js-delivery.php'; // adjust to the correct path
        (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(scriptNode);
    })();
</script>
```

Optionally, you can include `comment-sidecar-basic.css` in the HTML header to get some basic styling. Or you can simply copy its content to your own CSS file in order to avoid a additional HTTP request.

A complete example for the frontend can be found in [`src/playground.html`](https://github.com/phauer/comment-sidecar/blob/master/src/playground.html).

# Import Existing Disqus Comments into Comment-Sidecar

The import script needs Python 3 and the dependency management tool [Poetry](https://python-poetry.org/).

First, Export your Disqus Comments as an XML file. Details can be found [here](https://help.disqus.com/en/articles/1717164-comments-export).

Second, call

```bash
poetry shell

# print the help for the CLI
python import/import_disqus_comments.py --help 

# execute the command
python import/import_disqus_comments.py --disqus_xml_file phauer.xml --site_url https://phauer.com --cs_site_key phauer.com --db_host db_host --db_port 3306 --db_user db_user --db_password db_password --db_name db_name
``` 

# Privacy Policy

When using comment-sidecar, you might add the following to your declaration:

> Comments
>
> When entering a comment, we ask you to enter a name (doesn't have to be your real name) and your e-mail address. The e-mail is not required. We store both values along with your comment in our database and don't pass them to third-parties. Your e-mail address will never be published. If you submit an e-mail is will be used to send notifications to you when an answer to your comment is published. You can unsubscribe from these notifications and delete your e-mail address by clicking on the unsubscribe link in the e-mail.
>
> We don't use your data for ads or tracking. It's only about displaying the comment on this site and to send your notifications. That's all.
>
> You can contact us, if you want us to remove your e-mail or the whole comment from our database.
>
> Additionally, we store your IP address for a short amount of time (usually a couple of days). Your IP is not stored together with your name, e-mail or comment and can never be traced back to your personal data. We only use the IP to implement rate limiting and spam protection. After these short time, we will remove your IP from our database.

# Development

## PHP Backend Service

```bash
# start apache with php, mysql database (with the required table) and mailhog in docker containers
docker-compose up -d

# now you can execute HTTP requests like
http http://localhost/comment-sidecar.php
http POST http://localhost/comment-sidecar.php < adhoc/comment-payload.json

# develop in src/comment-sidecar.php. The changes take effect immediately. 
```

## Run the Python Tests for the Backend

Python 3.5+ and [Poetry](https://python-poetry.org/) is required. Check `python3 --version`. On Arch Linux, you can install Poetry with `yay install python-poetry`,

```bash
# start mysql database and mailhog in docker containers
docker-compose up -d

# install dependencies in a venv
poetry install 
poetry env info 
# configure your IDE with the displayed path
# now, you can execute the tests directly from the IDE

# execute all tests
poetry shell
pytest

# or only a single test:
poetry shell
pytest test/test_comment_sidecar.py
```

## Frontend

I'm using [Browsersync](https://www.browsersync.io/) to automatically reload my browser during development.

```bash
# install browsersync
npm install
# watch for changes and reload browser automatically
npm run watch
```

See [Browsersync command line usage](https://www.browsersync.io/docs/command-line) for more details.

## Test Multi-site Scenarios and Different Origins

You can use one deployed comment-sidecar backend for multiple sites. So we different domains and have to take [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS) headers into account. To simulate this locally, use the proxy server of browsersync.

```bash
# the backend runs in the php container on port 80
# let's start browsersync's proxy on port 3000
npm run watch-with-proxy
# open localhost:3000/playground.html in your browser
# it will now try to communicate with the backend on port 80
```

Alternatively, you can use IntelliJ's built-in server. Just right-click on `playground.html` and select `Open in Browser`.

## See the Sent Mails

MailHog provides a neat Web UI. Just open [`http://localhost:8025/`](http://localhost:8025/) after calling `docker-compose up`.

## Connect to the MySQL Container using a MySQL Client

Use host `127.0.0.1` instead of `localhost`! Port `3306`. Database `comment-sidecar`. User `root` and password `root`.

## Debugging with IntelliJ IDEA/PhpStorm

A tutorial for set up remote debugging of PHP code executed in a Docker container can be found [here](https://blog.philipphauer.de/debug-php-docker-container-idea-phpstorm/). 
