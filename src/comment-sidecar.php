<?php
/**
 * REST API:
 * GET comment-sidecar.php
 * POST comment-sidecar.php with comment JSON
 */

function main(){
    $method = $_SERVER['REQUEST_METHOD'];
    $request = explode('/', trim($_SERVER['PATH_INFO'],'/'));
    header('Content-Type: application/json');
    try {
        switch ($method) {
            case 'GET':  {
                //TODO where `site`, `path`
                echo getCommentsJson();
                break;
            }
            case 'POST': {
                createComment();
                http_response_code(201);
                break;
            }
        }
    } catch (PDOException $exception) {
        http_response_code(500);
        echo '{ "message" : "'.$exception->getMessage().'" }';
    }
}

function connect(){
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

function getCommentsJson() {
        $handler = connect();
        $stmt = $handler->prepare("SELECT id, author, email, content, reply_to as replyTo, site, path, unix_timestamp(creation_date) as creationTimestamp FROM comments order by creation_date desc;");
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $json = json_encode($results);
        $handler = null; //close connection
        return $json;
}

function createComment() {
    $input = json_decode(file_get_contents('php://input'),true);
    $handler = connect();
    $stmt = $handler->prepare("INSERT INTO comments (author, email, content, reply_to, site, path, creation_date) VALUES (:author, :email, :content, :reply_to, :site, :path, from_unixtime(:creation_date_timestamp));");
    $stmt->bindParam(':author', $input["author"]);
    $stmt->bindParam(':email', $input["email"]);
    $stmt->bindParam(':content', $input["content"]);
    $stmt->bindParam(':reply_to', $input["replyTo"]);
    $stmt->bindParam(':site', $input["site"]);
    $stmt->bindParam(':path', $input["path"]);
    $stmt->bindParam(':creation_date_timestamp', $input["creationTimestamp"]);
    $stmt->execute();
    $handler = null; //close connection
}

main();