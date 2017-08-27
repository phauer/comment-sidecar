<?php
include_once "config.php";

function connect() {
    $handler = new PDO("mysql:host=".DB_HOST.":".DB_PORT.";dbname=".DB_NAME.";charset=utf8", DB_USER, DB_PW);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
    return $handler;
}

function readTranslations(): array  {
    $translationFile = 'translations/'. LANGUAGE .'.php';
    if (!file_exists($translationFile)) {
        http_response_code(500);
        echo "Can't find translation file $translationFile";
        return;
    }
    include $translationFile;
    return $translations;
}

class InvalidRequestException extends Exception {}