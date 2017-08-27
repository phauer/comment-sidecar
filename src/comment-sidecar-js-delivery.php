<?php
include_once "config.php";

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
    $currentDir = BASE_URL;
    $page = str_replace("{{BASE_PATH}}","${currentDir}comment-sidecar.php", $page);

    echo $page;
}

deliverJsWithTranslationsAndPath();