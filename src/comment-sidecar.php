<?php

$method = $_SERVER['REQUEST_METHOD'];
$request = explode('/', trim($_SERVER['PATH_INFO'],'/'));
$input = json_decode(file_get_contents('php://input'),true);

//TODO PDO supports object mapping!

//docker-compose creates links and adds entries to /etc/hosts -> use "commentsidecar_mysql_1" instead of "localhost"
$dbhost = 'commentsidecar_mysql_1';
$dbname = 'comment-sidecar';
$dbuser = 'root';
$dbpw = 'root';
$dbport = 3306;
try {
    $handler = new PDO("mysql:host=$dbhost:$dbport;dbname=$dbname", $dbuser, $dbpw);
    $handler->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_WARNING );
//    $stmt = $handler->prepare("SELECT version();");
    $stmt = $handler->prepare("SELECT * from comments;");
//    $stmt = $handler->prepare("Normales MySQL, z.B. SELECT * FROM table WHERE name = :name");
//    $stmt->bindParam(':name', $name);
    $stmt->execute();
    $allResults = $stmt->fetchAll();
    echo $allResults[0]["version()"];
} catch(PDOException $e) {
    echo $e->getMessage();
}
$handler = null; //close connection

//$link = mysqli_connect('commentsidecar_mysql_1', 'root','root',  'comment-sidecar', 3306);
//mysqli_set_charset($link,'utf8');
//mysqli_real_escape_string

//switch ($method) {
//    case 'GET': $sql = "select version();"; break;
////    case 'GET': $sql = "select * from `$table`".($key?" WHERE id=$key":''); break;
//}
//
//$result = mysqli_query($link,$sql);
//
//if (!$result) {
//    http_response_code(404);
//    die(mysqli_error($link));
//}
//
//if ($method == 'GET') {
//    header('Content-Type: application/json');
//    echo '[';
//    for ($i=0;$i<mysqli_num_rows($result);$i++) {
//        echo ($i>0?',':'').json_encode(mysqli_fetch_object($result));
//    }
//    echo ']';
//}
//
//mysqli_close($link);