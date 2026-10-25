<?php
# Production config skeleton. Copy to deploy/config.php (gitignored) and fill in your values.
# deploy.sh uploads it as `config.php` on the server. It mirrors src/config.php (the dev config).
const SITES = [
    "example.com" => [
        "url" => "https://example.com",
        "language" => "en",
        "notificationEmail" => "you@example.com",
        "allowedOrigins" => [ "https://example.com" ],
        "formTemplate" => "bootstrap-default",
        "buttonCssAddComment" => "btn btn-link",
        "buttonCssReply" => "btn btn-link",
    ],
    "example.de" => [
        "url" => "https://example.de",
        "language" => "de",
        "notificationEmail" => "you@example.com",
        "allowedOrigins" => [ "https://example.de" ],
        "formTemplate" => "bulma-default",
        "buttonCssAddComment" => "button is-link",
        "buttonCssReply" => "button is-link is-small",
    ],
];
const DEFAULT_SITE = "example.com"; # used if the embedding site passes no ?site=

const BASE_URL = "https://comments.example.com/";

const DB_HOST = 'localhost';
const DB_NAME = 'your_db_name';
const DB_USER = 'your_db_user';
const DB_PW = 'change-me';
const DB_PORT = 3306;

const RATE_LIMIT_THRESHOLD_SECONDS = "60";
const UNSUBSCRIBE_DELAY_SECONDS = "2";
