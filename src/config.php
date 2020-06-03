<?php
const LANGUAGE = "en"; # see the `translations` folder for supported languages
const SITE = "mydomain.com"; # key for this site to identity comments of this site. it will also be used to build urls.
const E_MAIL_FOR_NOTIFICATIONS = "test@localhost.de"; # admin mail that will receive a notification e-mail after every new comment
const BASE_URL = "http://mydomain.com/"; # base url of the comment-sidecar backend. can differ from the embedding site.
const ALLOWED_ACCESSING_SITES = [ "http://localhost:1313", "http://localhost:3000", "http://testdomain.com" ]; # sites that are allowed to access the backend (required when the backend is deployed on a different domain than the embedding site.)

const DB_HOST = 'mysql'; # to access from host system, use 127.0.0.1
const DB_NAME = 'comment-sidecar';
const DB_USER = 'root';
const DB_PW = 'root';
const DB_PORT = 3306;

const FORM_TEMPLATE = "bootstrap-default"; # see `form-templates` folder for the available form templates or define your own. examples: "bootstrap-default" or "bulma-default".
//const FORM_TEMPLATE = "bulma-default";
const BUTTON_CSS_CLASSES_ADD_COMMENT = "btn btn-link"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"
//const BUTTON_CSS_CLASSES_ADD_COMMENT = "button is-link";
const BUTTON_CSS_CLASSES_REPLY = "btn btn-link"; # css classes for the button. bootstrap: "btn btn-link". bulma: "button is-link"
//const BUTTON_CSS_CLASSES_REPLY = "button is-link is-small";

# mind, that the following line is temporarily changed by the integration test
const RATE_LIMIT_THRESHOLD_SECONDS = "0"; # how long a user (defined by their IP) have to wait until they can comment again