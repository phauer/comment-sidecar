(function() {
    function handleResponse(response) {
        if (response.status === 201) {
            const inputs = document.querySelectorAll("div.cs-form .form-control");
            inputs.forEach(input => input.value = "");

            const element = document.querySelector(".cs-form-message");
            element.innerText = "Successfully submitted comment.";
            element.classList.remove("fail");
            element.classList.add("success");

            reloadComments();
        } else {
            const element = document.querySelector(".cs-form-message");
            response.json().then(json => {
                element.innerText = `Couldn't submit your comment. Reason: ${json['message']}`;
            });
            element.classList.remove("success");
            element.classList.add("fail");
        }
    }
    function markInvalidFieldsAndIsValid() {
        let isValid = true;
        const inputs = document.querySelectorAll("div.cs-form .form-control");
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
    function submitComment() {
        if (!markInvalidFieldsAndIsValid()) {
            return false;
        }
        const author = document.querySelector("#cs-author").value;
        const email = document.querySelector("#cs-email").value;
        const content = document.querySelector("#cs-content").value;
        const url = document.querySelector("#cs-url").value;
        const payload = {
            author: author,
            email: email,
            content: content,
            site: commentSidecarSite,
            path: location.pathname,
            url: url
        };
        fetch("/comment-sidecar.php",
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
    function createDOMForComments(comments) {
        if (comments.length === 0){
            const heading = document.createElement("p");
            heading.innerText = 'No comments yet. Be the first!';
            return [heading];
        } else {
            return comments.map(createDOMForComment);
        }
    }
    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toString(); //convert to local timezone.
    }
    function createDOMForComment(comment) {
        const postDiv = document.createElement('div');
        postDiv.setAttribute("class", "cs-post");
        postDiv.innerHTML = `
            <div class="cs-avatar"><img src="${comment.gravatarUrl}?s=50&d=mm"/></div>
            <div class="cs-body">
                <header class="cs-header">
                    <span class="cs-author">${comment.author}</span> 
                    <span class="cs-date">${formatDate(comment.creationTimestamp)}</span>
                </header>
                <div class="cs-content">${comment.content}</div>
            </div>
        `;
        return postDiv;
    }
    function createFormDOM() {
        const div = document.createElement('div');
        div.setAttribute("class", "cs-form");
        div.innerHTML = `
            <form>
              <div class="form-group">
                <label for="cs-author" class="control-label">Name:</label>
                <input type="text" class="form-control" id="cs-author" placeholder="Name">
              </div>
              <div class="form-group">
                <label for="cs-email" class="control-label">E-Mail:</label>
                <input type="email" class="form-control" id="cs-email" placeholder="E-Mail (won't be not published; Gravatar supported)">
              </div>
              <div class="form-group cs-url-group">
                <label for="cs-url" class="control-label">URL:</label>
                <input type="url" id="cs-url" name="url" placeholder="URL">
              </div>
              <div class="form-group">
                <label for="cs-content" class="control-label">Comment:</label>
                <textarea class="form-control" id="cs-content" placeholder="Your Comment..." rows="7"></textarea>
              </div>
              <button type="submit" class="btn btn-primary">Submit</button>
              <p class="cs-form-message">Message!</p>
            </form>
        `;
        div.querySelector("button").onclick = submitComment;
        return div;
    }
    function loadComments(){
        const path = encodeURIComponent(location.pathname);
        return fetch(`/comment-sidecar.php?site=${commentSidecarSite}&path=${path}`)
            .then(response => response.json())
            .then(createDOMForComments);
    }

    const commentArea = document.querySelector("#comment-sidecar");

    const heading = document.createElement("h1");
    heading.innerText = 'Comments';
    commentArea.appendChild(heading);

    commentArea.appendChild(createFormDOM());

    loadComments().then(commentDomNodes => {
        commentDomNodes.forEach(node => commentArea.appendChild(node));
    });
})();