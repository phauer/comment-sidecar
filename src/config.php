<?php
const LANGUAGE = "en"; # see translations folder for supported languages
const SITE = "http://localhost"; # key for this site to identity comment of this site. it will also be used to build urls.
const E_MAIL_FOR_NOTIFICATIONS = "test@localhost.de";
const BASE_URL = "http://localhost/"; # base url of the comment-sidecar backend. can differ from the embedding site.
const ALLOWED_ACCESSING_SITES = [ "http://localhost:1313", "http://localhost:3000", "http://testdomain.com" ]; # sites that are allowed to access the backend (required for multisite setups, where the backend is deployed on a different domain than the embedding site.)

const DB_HOST = 'mysql'; # to access from host system, use 127.0.0.1
const DB_NAME = 'comment-sidecar';
const DB_USER = 'root';
const DB_PW = 'root';
const DB_PORT = 3306;

const FORM_TEMPLATE = "bulma-default"; # see `form-templates folder to available form templates or define your own. examples: "bootstrap-default" or "bulma-default".
const BUTTON_CSS_CLASSES_ADD_COMMENT = "button is-link"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"
const BUTTON_CSS_CLASSES_REPLY = "button is-link is-small"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"

const RATE_LIMIT_THRESHOLD_SECONDS = "0"; # how long a user (defined by their IP) have to wait until they can comment again