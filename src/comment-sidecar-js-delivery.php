<?php
include_once "comment-sidecar-config.php";

function deliverJsWithTranslationsAndPath(){
    $translationFile = 'translations/'. LANGUAGE .'.php';
    if (!file_exists($translationFile)) {
        http_response_code(500);
        echo "Can't find translation file $translationFile";
        return;
    }

    $jsTemplate = 'comment-sidecar.js';
    if (!file_exists($jsTemplate)) {
        http_response_code(500);
        echo "Can't find javascript template file $jsTemplate";
        return;
    }

    // poor man's templating (but at least I prevent nice tooling in the js file)

    //set translations
    include $translationFile;
    header('Content-Type: application/json');
    $page = file_get_contents($jsTemplate, FILE_USE_INCLUDE_PATH);
    foreach ($translations as $key => $translation) {
        $page = str_replace("{{".$key."}}",$translation,$page);
    }

    //set site key
    $page = str_replace("{{SITE}}",SITE,$page);

    //set sidecar path
    //assuming that "comment-sidecar-js-delivery.php" is placed in the same directory as "comment-sidecar.php"
    $currentDir = dirname($_SERVER['REQUEST_URI']);
    $currentDir = $currentDir === "/" ? $currentDir : $currentDir . "/";
    $commentSidecarPath = "${currentDir}comment-sidecar.php";
    $page = str_replace("{{BASE_PATH}}",$commentSidecarPath,$page);

    echo $page;
}

deliverJsWithTranslationsAndPath();