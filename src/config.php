<?php
# All sites served by this comment-sidecar installation. One installation and one database can serve many sites.
# The key is the site key. The embedding site passes it as `comment-sidecar-js-delivery.php?site=<key>` and it's stored with every comment.
const SITES = [
    "localhost" => [
        "url" => "http://localhost:1313", # base url of the site. used to build the links to the comments in e-mails.
        "language" => "en", # see the `translations` folder for supported languages
        "notificationEmail" => "test@localhost.de", # admin mail that will receive a notification e-mail after every new comment
        "allowedOrigins" => [ "http://localhost:1313", "http://localhost:3000", "http://testdomain.com" ], # origins that are allowed to access the backend for this site (required when the backend is deployed on a different domain than the embedding site.)
        "formTemplate" => "bootstrap-default", # see the `form-templates` folder for the available form templates or define your own. examples: "bootstrap-default" or "bulma-default".
        "buttonCssAddComment" => "btn btn-link", # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"
        "buttonCssReply" => "btn btn-link", # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link is-small"
    ],
    "localhost-de" => [
        "url" => "http://localhost:3001",
        "language" => "de",
        "notificationEmail" => "test-de@localhost.de",
        "allowedOrigins" => [ "http://localhost:3001" ],
        "formTemplate" => "bulma-default",
        "buttonCssAddComment" => "button is-link",
        "buttonCssReply" => "button is-link is-small",
    ],
];
const DEFAULT_SITE = "localhost"; # used if the embedding site doesn't pass a `site` parameter to the js delivery script.

const BASE_URL = "http://localhost/"; # base url of the comment-sidecar backend. can differ from the embedding sites.

const DB_HOST = 'mysql'; # to access from host system, use 127.0.0.1
const DB_NAME = 'comment-sidecar';
const DB_USER = 'root';
const DB_PW = 'root';
const DB_PORT = 3306;

# mind, that the following line is temporarily changed by the integration test
const RATE_LIMIT_THRESHOLD_SECONDS = "0"; # how long a user (defined by their IP) have to wait until they can comment again
const UNSUBSCRIBE_DELAY_SECONDS = "0"; # artificially delay responses of the unsubscribe link to delay brute force attacks.
