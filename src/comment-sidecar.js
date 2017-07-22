(function() {
    const BASE_PATH = "{{BASE_PATH}}";
    const SITE = "{{SITE}}";

    function handleResponse(response) {
        if (response.status === 201) {
            const inputs = document.querySelectorAll("div.cs-form .form-control");
            inputs.forEach(input => input.value = "");

            const element = document.querySelector(".cs-form-message");
            element.innerText = "{{successMessage}}";
            element.classList.remove("fail");
            element.classList.add("success");

            refresh();
        } else {
            const element = document.querySelector(".cs-form-message");
            response.json().then(json => {
                element.innerText = `{{failMessage}} ${json['message']}`;
            });
            element.classList.remove("success");
            element.classList.add("fail");
        }
    }
    function markInvalidFieldsAndIsValid(formDiv) {
        let isValid = true;
        const inputs = formDiv.querySelectorAll("div.cs-form .form-control");
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
        const author = formDiv.querySelector(".cs-author").value;
        const email = formDiv.querySelector(".cs-email").value;
        const content = formDiv.querySelector(".cs-content").value;
        const url = formDiv.querySelector(".cs-url").value;
        const payload = {
            author: author,
            email: email,
            content: content,
            site: SITE,
            path: location.pathname,
            url: url
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
            .then(handleResponse);
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
        postDiv.innerHTML = `
            <div class="cs-avatar"><img src="${comment.gravatarUrl}?s=65&d=mm"/></div>
            <div class="cs-body">
                <header class="cs-header">
                    <span class="cs-author">${comment.author}</span> 
                    <span class="cs-date">${formatDate(comment.creationTimestamp)}</span>
                </header>
                <div class="cs-content">${comment.content}</div>
                <button class="cs-reply-button btn btn-link btn-sm">{{reply}}</button>
                <div class="cs-reply-form"></div>
                <div class="cs-replies"></div>
            </div>
        `;
        postDiv.querySelector("button").onclick = (event) => {
            const expandReplyButton = event.target;
            if (expandReplyButton.classList.contains("cs-collapsed")) {
                clearReplyForm(postDiv);
                expandReplyButton.classList.remove("cs-collapsed")
            } else {
                expandReplyForm(postDiv, comment.id);
                expandReplyButton.classList.add("cs-collapsed")
            }
        };

        if (comment.replies !== undefined){
            const repliesDiv = postDiv.querySelector(".cs-replies");
            comment.replies.map(createNodeForComment).forEach(node => repliesDiv.appendChild(node));
        }

        return postDiv;
    }
    function clearReplyForm(postDiv) {
        const replyForm = postDiv.querySelector(".cs-reply-form");
        replyForm.innerHTML = ""
    }
    function expandReplyForm(postDiv, parentCommentId) {
        const replyForm = postDiv.querySelector(".cs-reply-form");
        replyForm.innerHTML = createFormHtml('{{reply}}');
        replyForm.querySelector("button").onclick = () => submitComment(replyForm, parentCommentId);
    }

    function createFormHtml(buttonLabel) {
        return `
            <form>
              <div class="form-group">
                <label for="cs-author" class="control-label">{{name}}:</label>
                <input type="text" class="form-control cs-author">
              </div>
              <div class="form-group">
                <label for="cs-email" class="control-label">{{email}}:</label>
                <input type="email" class="form-control cs-email" placeholder="{{emailHint}}">
              </div>
              <div class="form-group cs-url-group">
                <label for="cs-url" class="control-label">URL:</label>
                <input type="url" class="cs-url" name="url" placeholder="URL">
              </div>
              <div class="form-group">
                <label for="cs-content" class="control-label">{{comment}}:</label>
                <textarea class="form-control cs-content" rows="7"></textarea>
              </div>
              <button type="submit" class="btn btn-primary">${buttonLabel}</button>
              <p class="cs-form-message"></p>
            </form>
        `;
    }

    function createFormNode() {
        const mainFormDiv = document.createElement('div');
        mainFormDiv.setAttribute("class", "cs-form");
        mainFormDiv.innerHTML = createFormHtml('{{submit}}');
        mainFormDiv.querySelector("button").onclick = () => submitComment(mainFormDiv);
        return mainFormDiv;
    }
    function loadComments(){
        const path = encodeURIComponent(location.pathname);
        return fetch(`${BASE_PATH}?site=${SITE}&path=${path}`)
            .then(response => response.json())
            .then(createNodesForComments);
    }

    const commentAreaNode = document.querySelector("#comment-sidecar");
    commentAreaNode.innerHTML = `<h1>{{comments}}</h1>`;

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

//TODO reply: proper position of message
//TODO css-based animation for expending reply form