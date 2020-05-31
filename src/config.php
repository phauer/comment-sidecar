<?php
const LANGUAGE = "en"; # see translations folder for supported languages
const FORM_TEMPLATE = "bootstrap-default"; # see for-templates folder to available form templates or define your own.
const SITE = "http://localhost"; # key for this site to identity comment of this site. it will also be used to build urls.
const E_MAIL_FOR_NOTIFICATIONS = "test@localhost.de";
const BASE_URL = "http://localhost/"; # base url of the comment-sidecar backend. can differ from the embedding site.
const ALLOWED_ACCESSING_SITES = [ "http://localhost:1313", "http://localhost:3000", "http://testdomain.com" ]; # sites that are allowed to access the backend (required for multisite setups, where the backend is deployed on a different domain than the embedding site.)
const DB_HOST = 'mysql'; # to access from host system, use 127.0.0.1
const DB_NAME = 'comment-sidecar';
const DB_USER = 'root';
const DB_PW = 'root';
const DB_PORT = 3306;
