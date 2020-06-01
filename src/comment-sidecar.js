(function() {
    const BASE_PATH = "{{BASE_PATH}}";
    const SITE = "{{SITE}}";

    function handleResponse(response, formDiv) {
        if (response.status === 201) {
            formDiv.querySelectorAll("input").forEach(input => input.value = "");
            formDiv.querySelectorAll("textarea").forEach(input => input.value = "");

            const element = formDiv.querySelector(".cs-form-message");
            element.innerText = "{{successMessage}}";
            element.classList.remove("fail");
            element.classList.add("success");

            refresh();
        } else {
            const element = formDiv.querySelector(".cs-form-message");
            response.json().then(json => {
                element.innerText = `{{failMessage}} ${json['message']}`;
            });
            element.classList.remove("success");
            element.classList.add("fail");
        }
    }
    function markInvalidFieldsAndIsValid(formDiv) {
        let isValid = true;
        const inputs = formDiv.querySelectorAll(".form-control:required");
        inputs.forEach(input => {
            if (input.value.trim().length === 0) {
                input.parentNode.classList.add("has-error");
                isValid = false;
            } else {
                input.parentNode.classList.remove("has-error");
            }
        });
        return isValid;
    }
    function submitComment(formDiv, parentId) {
        if (!markInvalidFieldsAndIsValid(formDiv)) {
            return false;
        }
        const payload = {
            author: formDiv.querySelector(".cs-author").value,
            email: formDiv.querySelector(".cs-email").value,
            content: formDiv.querySelector(".cs-content").value,
            site: SITE,
            path: location.pathname,
            url: formDiv.querySelector(".cs-url").value
        };
        if (parentId !== undefined) {
            payload.replyTo = parentId;
        }
        fetch(BASE_PATH,
            {
                headers: {
                    'Content-Type': 'application/json'
                },
                method: "POST",
                body: JSON.stringify(payload)
            })
            .then(response => handleResponse(response, formDiv));
        return false;
    }
    function createNodesForComments(comments) {
        if (comments.length === 0){
            const heading = document.createElement("p");
            heading.innerText = '{{noCommentsYet}}';
            return [heading];
        } else {
            return comments.map(createNodeForComment);
        }
    }
    function formatDate(creationTimestamp) {
        let creationDate = new Date(creationTimestamp * 1000);
        const agoAndUnit = getTimeSinceInBiggestUnit(creationDate);
        return "{{dateString}}".replace("{}", agoAndUnit);

    }
    function getTimeSinceInBiggestUnit(creationDate) {
        const seconds = Math.floor((new Date() - creationDate) / 1000);

        let interval = Math.floor(seconds / 31536000);
        if (interval > 1) return interval + " {{years}}";

        interval = Math.floor(seconds / 2592000);
        if (interval > 1) return interval + " {{months}}";

        interval = Math.floor(seconds / 86400);
        if (interval >= 1) return interval + " {{days}}";

        interval = Math.floor(seconds / 3600);
        if (interval >= 1) return interval + " {{hours}}";

        interval = Math.floor(seconds / 60);
        if (interval > 1) return interval + " {{minutes}}";

        return Math.floor(seconds) + " {{seconds}}";
    }

    function createNodeForComment(comment) {
        const postDiv = document.createElement('div');
        postDiv.setAttribute("class", "cs-post");
        postDiv.setAttribute("id", `cs-post-${comment.id}`);
        const contentWithBrTags = comment.content.replace(/\n/g, "<br />");
        postDiv.innerHTML = `
            <div class="cs-avatar">${createAvatarSvg()}</div>
            <div class="cs-body">
                <header class="cs-header">
                    <span class="cs-author">${comment.author}</span> 
                    <span class="cs-date">${formatDate(comment.creationTimestamp)}</span>
                </header>
                <div class="cs-content">${contentWithBrTags}</div>
                <button class="cs-expand-button {{BUTTON_CSS_CLASSES_REPLY}} btn-sm">{{reply}}</button>
                <div class="cs-form"></div>
                <div class="cs-replies"></div>
            </div>
        `;
        postDiv.querySelector("button").onclick = (event) => expandForm(event.target, postDiv, comment.id);
        if (comment.replies !== undefined){
            const repliesDiv = postDiv.querySelector(".cs-replies");
            comment.replies.map(createNodeForComment).forEach(node => repliesDiv.appendChild(node));
        }

        return postDiv;
    }
    function expandForm(expandButton, formDiv, commentId) {
        if (expandButton.classList.contains("cs-collapsed")) {
            clearReplyForm(formDiv);
            expandButton.classList.remove("cs-collapsed")
        } else {
            expandReplyForm(formDiv, commentId);
            expandButton.classList.add("cs-collapsed")
        }
    }
    function clearReplyForm(postDiv) {
        const replyForm = postDiv.querySelector(".cs-form");
        replyForm.innerHTML = ""
    }
    function expandReplyForm(postDiv, parentCommentId) {
        const replyForm = postDiv.querySelector(".cs-form");
        replyForm.innerHTML = createFormHtml();
        replyForm.querySelector("button").onclick = () => submitComment(replyForm, parentCommentId);
    }

    function createFormHtml() {
        return `{{FORM_HTML}}`;
    }

    function createFormNode() {
        const mainFormDiv = document.createElement('div');
        mainFormDiv.setAttribute("class", "cs-form-root");
        mainFormDiv.innerHTML = `
            <button class="cs-expand-button {{BUTTON_CSS_CLASSES_ADD_COMMENT}}">{{writeComment}}</button>
            <div class="cs-form"></div>
        `;
        mainFormDiv.querySelector("button").onclick = (event) => expandForm(event.target, mainFormDiv);
        return mainFormDiv;
    }
    function loadComments(){
        const path = encodeURIComponent(location.pathname);
        return fetch(`${BASE_PATH}?site=${SITE}&path=${path}`)
            .then(response => response.json())
            .then(createNodesForComments);
    }

    function createAvatarSvg() {
        return `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 482.9 482.9" fill="currentColor"><path d="M239.7 260.2h3.2c29.3-.5 53-10.8 70.5-30.5 38.5-43.4 32.1-117.8 31.4-124.9-2.5-53.3-27.7-78.8-48.5-90.7C280.8 5.2 262.7.4 242.5 0h-1.7c-11.1 0-32.9 1.8-53.8 13.7-21 11.9-46.6 37.4-49.1 91.1-.7 7.1-7.1 81.5 31.4 124.9 17.4 19.7 41.1 30 70.4 30.5zm-75.1-152.9c0-.3.1-.6.1-.8 3.3-71.7 54.2-79.4 76-79.4h1.2c27 .6 72.9 11.6 76 79.4 0 .3 0 .6.1.8.1.7 7.1 68.7-24.7 104.5-12.6 14.2-29.4 21.2-51.5 21.4h-1c-22-.2-38.9-7.2-51.4-21.4-31.7-35.6-24.9-103.9-24.8-104.5zm282.2 276.3v-.3l-.1-2.5c-.6-19.8-1.9-66.1-45.3-80.9-.3-.1-.7-.2-1-.3-45.1-11.5-82.6-37.5-83-37.8-6.1-4.3-14.5-2.8-18.8 3.3s-2.8 14.5 3.3 18.8c1.7 1.2 41.5 28.9 91.3 41.7 23.3 8.3 25.9 33.2 26.6 56 0 .9 0 1.7.1 2.5.1 9-.5 22.9-2.1 30.9-16.2 9.2-79.7 41-176.3 41-96.2 0-160.1-31.9-176.4-41.1-1.6-8-2.3-21.9-2.1-30.9 0-.8.1-1.6.1-2.5.7-22.8 3.3-47.7 26.6-56 49.8-12.8 89.6-40.6 91.3-41.7 6.1-4.3 7.6-12.7 3.3-18.8s-12.7-7.6-18.8-3.3c-.4.3-37.7 26.3-83 37.8-.4.1-.7.2-1 .3-43.4 14.9-44.7 61.2-45.3 80.9 0 .9 0 1.7-.1 2.5v.3c-.1 5.2-.2 31.9 5.1 45.3a12.83 12.83 0 0 0 5.2 6.3c3 2 74.9 47.8 195.2 47.8s192.2-45.9 195.2-47.8c2.3-1.5 4.2-3.7 5.2-6.3 5-13.3 4.9-40 4.8-45.2z"/></svg>
        `
    }

    const commentAreaNode = document.querySelector("#comment-sidecar");

    commentAreaNode.appendChild(createFormNode());

    const commentListNode = document.createElement("div");
    commentListNode.className = 'cs-comment-list';
    commentAreaNode.appendChild(commentListNode);

    const refresh = () => {
        commentListNode.innerHTML = '';
        loadComments().then(commentDomNodes => {
            commentDomNodes.forEach(node => commentListNode.appendChild(node));
        });
    };
    refresh();
})();