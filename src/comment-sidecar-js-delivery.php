<?php
include_once "common.php";

function deliverJsWithTranslationsAndPath(){
    header('Content-Type: application/json');
    $jsTemplate = 'comment-sidecar.js';
    if (!file_exists($jsTemplate)) {
        http_response_code(500);
        echo "Can't find javascript template file $jsTemplate";
        return;
    }
    $page = file_get_contents($jsTemplate, FILE_USE_INCLUDE_PATH);

    // poor man's templating (but at least I prevent nice tooling in the js and html file)
    $page = str_replace("{{formHtml}}", readFormTemplate(), $page);
    foreach (readTranslations() as $key => $translation) {
        $page = str_replace("{{".$key."}}",$translation,$page);
    }
    $page = str_replace("{{SITE}}",SITE,$page);
    $currentDir = BASE_URL;
    $page = str_replace("{{BASE_PATH}}","${currentDir}comment-sidecar.php", $page);
    echo $page;
}

function readFormTemplate(): string  {
    $formTemplateFile = 'form-templates/'. FORM_TEMPLATE .'.html';
    if (!file_exists($formTemplateFile)) {
        http_response_code(500);
        echo "Can't find form template file $formTemplateFile";
        return "";
    }

    $file = fopen($formTemplateFile, "r");
    $content = fread($file, filesize($formTemplateFile));
    fclose($file);
    return $content;
}

deliverJsWithTranslationsAndPath();