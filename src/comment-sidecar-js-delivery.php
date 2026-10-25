<?php
include_once "common.php";

/**
 * HTTP endpoint
 * GET comment-sidecar-js-delivery.php?site=<site>
 *      delivers the javascript with the translations and settings of the given site.
 *      Without the site parameter, the DEFAULT_SITE is used.
 */
function deliverJsWithTranslationsAndPath(){
    header('Content-Type: application/json');
    try {
        $site = $_GET['site'] ?? DEFAULT_SITE;
        $siteConfig = getSiteConfig($site);
    } catch (Throwable $ex) {
        respondWithError($ex);
        return;
    }
    $jsTemplate = 'comment-sidecar.js';
    if (!file_exists($jsTemplate)) {
        http_response_code(500);
        echo "Can't find javascript template file $jsTemplate";
        return;
    }
    $page = file_get_contents($jsTemplate, FILE_USE_INCLUDE_PATH);

    // poor man's templating (but at least I prevent nice tooling in the js and html file)
    $page = str_replace("{{FORM_HTML}}", readFormTemplate($siteConfig['formTemplate']), $page);
    $page = str_replace("{{BUTTON_CSS_CLASSES_ADD_COMMENT}}", $siteConfig['buttonCssAddComment'], $page);
    $page = str_replace("{{BUTTON_CSS_CLASSES_REPLY}}", $siteConfig['buttonCssReply'], $page);
    foreach (readTranslations($siteConfig['language']) as $key => $translation) {
        $page = str_replace("{{".$key."}}",$translation,$page);
    }
    $page = str_replace("{{SITE}}", $site, $page);
    $page = str_replace("{{BASE_PATH}}", BASE_URL . "comment-sidecar.php", $page);
    echo $page;
}

function readFormTemplate(string $formTemplate): string  {
    $formTemplateFile = 'form-templates/'. $formTemplate .'.html';
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
