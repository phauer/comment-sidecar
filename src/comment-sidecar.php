<?php
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
                createComment();
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
    //docker-compose creates links and adds entries to /etc/hosts -> use "commentsidecar_mysql_1" instead of "localhost"
    $dbhost = 'commentsidecar_mysql_1';
    $dbname = 'comment-sidecar';
    $dbuser = 'root';
    $dbpw = 'root';
    $dbport = 3306;
    $handler = new PDO("mysql:host=$dbhost:$dbport;dbname=$dbname", $dbuser, $dbpw);
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
        $json[] = array('author' => $result['author'],
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

function createComment() {
    $comment = json_decode(file_get_contents('php://input'),true);
    validatePostedComment($comment);
    $handler = connect();
    $stmt = $handler->prepare("INSERT INTO comments (author, email, content, site, path, creation_date) VALUES (:author, :email, :content, :site, :path, now());");
    $stmt->bindParam(':author', $comment["author"]);
    $stmt->bindParam(':email', $comment["email"]); // optional. can be null
    $stmt->bindParam(':content', $comment["content"]);
    $stmt->bindParam(':site', $comment["site"]);
    $stmt->bindParam(':path', $comment["path"]);
    $stmt->execute();
    $handler = null; //close connection
}

function validatePostedComment($comment){
    checkExistence($comment, 'author');
    checkExistence($comment, 'content');
    checkExistence($comment, 'site');
    checkExistence($comment, 'path');
}

function checkExistence($comment, $field) {
    if (!isset($comment[$field]) or empty(trim($comment[$field]))) {
        throw new InvalidRequestException("$field is missing, empty or blank");
    }
}

class InvalidRequestException extends Exception {}

main();
