<?php
include_once "comment-sidecar-config.php";

/**
 * HTTP endpoints
 * GET comment-sidecar.php?site=<site>&path=<path>
 * POST comment-sidecar.php with comment JSON
 */
function main() {
    $method = $_SERVER['REQUEST_METHOD'];
    header('Content-Type: application/json');
    try {
        switch ($method) {
            case 'GET': {
                echo getCommentsAsJson();
                break;
            }
            case 'POST': {
                $comment = json_decode(file_get_contents('php://input'),true);
                createComment($comment);
                sendNotificationViaMail($comment);
                http_response_code(201);
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

function connect() {
    $handler = new PDO("mysql:host=".DB_HOST.":".DB_PORT.";dbname=".DB_NAME.";charset=utf8", DB_USER, DB_PW);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
    return $handler;
}

function getCommentsAsJson() {
    if (!isset($_GET['site']) or empty($_GET['site'])
        or !isset($_GET['path']) or empty($_GET['path'])) {
        throw new InvalidRequestException("Please submit both query parameters 'site' and 'path'");
    }
    $handler = connect();
    $stmt = $handler->prepare("SELECT id, author, content, email, reply_to, site, path, unix_timestamp(creation_date) as creationTimestamp FROM comments WHERE site = :site and path = :path ORDER BY creation_date desc;");
    $stmt->bindParam(":site", $_GET['site']);
    $stmt->bindParam(":path", $_GET['path']);
    $stmt->execute();
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    $json = mapToJson($results);
    $handler = null; //close connection
    return $json;
}

function mapToJson($results) {
    $json = array();
    foreach ($results as $result) {
        $json[] = array(
            'id' => $result['id'],
            'author' => $result['author'],
            'content' => $result['content'],
            'creationTimestamp' => $result['creationTimestamp'],
            'gravatarUrl' => createGravatarUrl($result['email'])
        );
    }
    return json_encode($json);
}

function createGravatarUrl($email) {
    $gravatarHash = md5(strtolower(trim($email)));
    return "https://www.gravatar.com/avatar/$gravatarHash";
}

function createComment($comment) {
    checkForSpam($comment);
    validatePostedComment($comment);
    $handler = connect();
    $stmt = $handler->prepare("INSERT INTO comments (author, email, content, site, path, creation_date) VALUES (:author, :email, :content, :site, :path, now());");
    $author = htmlspecialchars($comment["author"]);
    $content = htmlspecialchars($comment["content"]);
    $stmt->bindParam(':author', $author);
    $stmt->bindParam(':email', $comment["email"]); // optional. can be null
    $stmt->bindParam(':content', $content);
    $stmt->bindParam(':site', $comment["site"]);
    $stmt->bindParam(':path', $comment["path"]);
    $stmt->execute();
    $handler = null; //close connection
}

function checkForSpam($comment) {
    if (isset($comment['url']) and !empty(trim($comment['url']))) {
       throw new InvalidRequestException("");
    }
}

function validatePostedComment($comment){
    checkExistence($comment, 'author');
    checkExistence($comment, 'content');
    checkExistence($comment, 'site');
    checkExistence($comment, 'path');
    checkMaxLength($comment, 'author', 40);
    checkMaxLength($comment, 'email', 40);
    checkMaxLength($comment, 'site', 40);
    checkMaxLength($comment, 'path', 170);
}

function checkMaxLength($comment, $fieldName, $maxLength) {
    if (strlen($comment[$fieldName]) > $maxLength) {
        throw new InvalidRequestException("$fieldName value exceeds maximal length of " . $maxLength);
    }
}

function checkExistence($comment, $field) {
    if (!isset($comment[$field]) or empty(trim($comment[$field]))) {
        throw new InvalidRequestException("$field is missing, empty or blank");
    }
}

function sendNotificationViaMail($comment) {
    $author = $comment['author'];
    $headers = "From: $author<${comment['email']}>\n";
    $headers .= "Mime-Version: 1.0\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\n";
    $headers .= "Content-Transfer-Encoding: 8bit\n";
    $headers .= "X-Mailer: PHP ".phpversion();

    $path = $comment["path"];
    $site = $comment["site"];
    $message = "
    Site: $site
    Path: $path
    Message: ${comment["content"]}
    ";

    $subject = "Comment by $author on $path";
    mail(E_MAIL_FOR_NOTIFICATIONS, $subject, $message, $headers);
}

class InvalidRequestException extends Exception {}

main();
