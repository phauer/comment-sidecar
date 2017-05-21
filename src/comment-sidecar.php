<?php
function process(){
    $method = $_SERVER['REQUEST_METHOD'];
    $request = explode('/', trim($_SERVER['PATH_INFO'],'/'));
    $input = json_decode(file_get_contents('php://input'),true);

    //docker-compose creates links and adds entries to /etc/hosts -> use "commentsidecar_mysql_1" instead of "localhost"
    $dbhost = 'commentsidecar_mysql_1';
    $dbname = 'comment-sidecar';
    $dbuser = 'root';
    $dbpw = 'root';
    $dbport = 3306;
    try {
        $handler = new PDO("mysql:host=$dbhost:$dbport;dbname=$dbname", $dbuser, $dbpw);
        $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_WARNING );
        $stmt = $handler->prepare("SELECT id, author, email, content, reply_to as replyTo, site, path, unix_timestamp(creation_date) as creationTimestamp FROM comments order by creation_date desc;");
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        header('Content-Type: application/json');
        $json=json_encode($results);
        echo $json;
    } catch(PDOException $exception) {
        echo $exception->getMessage();
    }
    $handler = null; //close connection

    //switch ($method) {
    //    case 'GET': break;
    //}
    //
    //if (!$result) {
    //    http_response_code(404);
    //    die(mysqli_error($link));
    //}
}

process();