<?php
ob_start("ob_gzhandler");
include_once "config.php";

function connect() {
    $handler = new PDO("mysql:host=".DB_HOST.":".DB_PORT.";dbname=".DB_NAME.";charset=utf8", DB_USER, DB_PW);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
    // PHP >= 8.1 returns native ints; keep the strings of PHP 7.x so the JSON API stays unchanged
    $handler->setAttribute( PDO::ATTR_STRINGIFY_FETCHES, true );
    return $handler;
}

function getSiteConfig($site): array {
    if (!is_string($site) or !isset(SITES[$site])) {
        throw new InvalidRequestException("Unknown site. Please use one of the configured site keys.");
    }
    return SITES[$site];
}

function getSiteConfigOrDefault($site): array {
    return (is_string($site) and isset(SITES[$site])) ? SITES[$site] : SITES[DEFAULT_SITE];
}

function readTranslations(string $language): array  {
    $translationFile = 'translations/'. $language .'.php';
    if (!file_exists($translationFile)) {
        http_response_code(500);
        echo "Can't find translation file $translationFile";
        return [];
    }
    include $translationFile;
    return $translations;
}

class InvalidRequestException extends Exception {}
class ForbiddenRequestException extends Exception {}

/**
 * Writes the error response. Never leaks internals (like database messages) for unexpected errors.
 */
function respondWithError(Throwable $ex) {
    if ($ex instanceof InvalidRequestException) {
        http_response_code(400);
        $message = $ex->getMessage();
    } else if ($ex instanceof ForbiddenRequestException) {
        http_response_code(403);
        $message = $ex->getMessage();
    } else { //like PDOException
        error_log($ex);
        http_response_code(500);
        $message = "Internal server error";
    }
    echo json_encode(["message" => $message], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
}