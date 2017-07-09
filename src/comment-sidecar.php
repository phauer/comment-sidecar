<?php
/**
 * REST API:
 * GET comment-sidecar.php
 */

function process(){
    $method = $_SERVER['REQUEST_METHOD'];
    $request = explode('/', trim($_SERVER['PATH_INFO'],'/'));
    $input = json_decode(file_get_contents('php://input'),true);
    header('Content-Type: application/json');
    try {
        switch ($method) {
            case 'GET':  {
                echo getCommentsJson();
                break;
            }
        }
    } catch (PDOException $exception) {
        http_response_code(500);
        echo '{ "message" : "'.$exception->getMessage().'" }';
    }

    //
    //if (!$result) {
    //    http_response_code(404);
    //    die(mysqli_error($link));
    //}
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
        $stmt = $handler->prepare("SELECT i2d, author, email, content, reply_to as replyTo, site, path, unix_timestamp(creation_date) as creationTimestamp FROM comments order by creation_date desc;");
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $json = json_encode($results);
        $handler = null; //close connection
        return $json;
}

process();