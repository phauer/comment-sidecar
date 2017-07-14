<?php
include_once "comment-sidecar-config.php";

$translationFile = 'translations/'. LANGUAGE .'.php';
if (!file_exists($translationFile)) {
    http_response_code(500);
    echo "Can't find translation file $translationFile";
    exit;
}

$jsTemplate = 'comment-sidecar.js';
if (!file_exists($jsTemplate)) {
    http_response_code(500);
    echo "Can't find javascript template file $jsTemplate";
    exit;
}

include $translationFile;
header('Content-Type: application/json');
$page = file_get_contents($jsTemplate, FILE_USE_INCLUDE_PATH);
// poor man's templating
foreach ($translations as $key => $translation) {
    $page = str_replace("{{".$key."}}",$translation,$page);
}
echo $page;
