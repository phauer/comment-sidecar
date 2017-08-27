<?php
include_once "common.php";

function deliverJsWithTranslationsAndPath(){
    $jsTemplate = 'comment-sidecar.js';
    if (!file_exists($jsTemplate)) {
        http_response_code(500);
        echo "Can't find javascript template file $jsTemplate";
        return;
    }

    // poor man's templating (but at least I prevent nice tooling in the js file)

    //set translations
    header('Content-Type: application/json');
    $page = file_get_contents($jsTemplate, FILE_USE_INCLUDE_PATH);
    foreach (readTranslations() as $key => $translation) {
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