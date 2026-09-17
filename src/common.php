<?php
ob_start("ob_gzhandler");
include_once __DIR__ . "/config.php";

function connect() {
    $handler = new PDO("mysql:host=".DB_HOST.";port=".DB_PORT.";dbname=".DB_NAME.";charset=utf8mb4", DB_USER, DB_PW);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
    $handler->setAttribute( PDO::ATTR_STRINGIFY_FETCHES, true );
    return $handler;
}

function readTranslations(): array  {
    $translationFile = __DIR__ . '/translations/'. LANGUAGE .'.php';
    if (!file_exists($translationFile)) {
        http_response_code(500);
        echo "Can't find translation file $translationFile";
        return [];
    }
    include $translationFile;
    return $translations;
}

class InvalidRequestException extends Exception {}