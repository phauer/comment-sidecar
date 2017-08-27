<?php
include_once "comment-sidecar-config.php";

/**
 * HTTP endpoint
 * GET unsubscribe.php?comment_id=<comment_id>&unsubscribe_token=<token>
 *       to disable a subscription.
 * Definitely not restful, but this way, the user only has to click on a link in the email. at least, it's idempotent. ;-)
 */
function main() {
    $method = $_SERVER['REQUEST_METHOD'];
    try {
        switch ($method) {
            case 'GET': {
                unsubscribe();
                break;
            }
        }
    } catch (Exception $ex) {
        if ($ex instanceof InvalidRequestException) {
            http_response_code(400);
            echo '{ "message" : "' . $ex->getMessage() . '" }';
        } else { //like PDOException
            http_response_code(500);
            echo '{ "message" : "' . $ex->getMessage() . '" }';
        }
    }
}

function unsubscribe() {
    if (!isset($_GET['commentId']) or empty($_GET['commentId'])
        or !isset($_GET['unsubscribeToken']) or empty($_GET['unsubscribeToken'])) {
        throw new InvalidRequestException("Please submit both query parameters 'commentId' and 'unsubscribeToken'");
    }
    $handler = connect();
    $stmt = $handler->prepare("UPDATE comments SET subscribed = false WHERE id = :commentId and unsubscribe_token = :unsubscribeToken;");
    $stmt->bindParam(":commentId", $_GET['commentId']);
    $stmt->bindParam(":unsubscribeToken", $_GET['unsubscribeToken']);
    $stmt->execute();
    if ($stmt->rowCount() === 0){
        echo "Nothing has been updated. Either the comment doesn't exist or the unsubscribe token is invalid.";
    }
    if ($stmt->rowCount() === 1){
        echo "You have been unsubscribed successfully.";
    }
    $handler = null; //close connection
}

function connect() {
    $handler = new PDO("mysql:host=".DB_HOST.":".DB_PORT.";dbname=".DB_NAME.";charset=utf8", DB_USER, DB_PW);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
    return $handler;
}

class InvalidRequestException extends Exception {}

main();