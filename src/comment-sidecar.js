function submitComment(){
    const author = document.querySelector("#cs-author").value;
    const email = document.querySelector("#cs-email").value;
    const content = document.querySelector("#cs-content").value;
    const payload = {
        author: author,
        email: email,
        content: content,
        site: commentSidecarSite,
        path: location.pathname
    };
    fetch("/comment-sidecar.php",
        {
            headers: {
                'Content-Type': 'application/json'
            },
            method: "POST",
            body: JSON.stringify(payload)
        })
        .then(function(res){ console.log(res) })
        .catch(function(res){ console.log(res) });
    //TODO client-side validation
    //TODO after submission: clear and give feedback.
    return false;
}

(function() {
    const commentArea = document.querySelector("#comment-sidecar");
    const handleComments = comments => {
        if (comments.length === 0){
            const heading = document.createElement("p");
            heading.innerText = 'No comments yet. Be the first!';
            commentArea.appendChild(heading);
        } else {
            comments.forEach(drawDOMForComment);
        }
    };
    const formatDate = timestamp => {
        const date = new Date(timestamp * 1000);
        return date.toString(); //convert to local timezone.
    };
    const drawDOMForComment = comment => {
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
        commentArea.appendChild(postDiv);
    };

    const heading = document.createElement("h1");
    heading.innerText = 'Comments';
    commentArea.appendChild(heading);

    const formDOM = (function() {
        //TODO client-side validation
        const div = document.createElement('div');
        div.setAttribute("class", "cs-form");
        div.innerHTML = `
            <form>
              <div class="form-group">
                <label for="author">Name:</label>
                <input type="text" class="form-control" id="cs-author" placeholder="Name">
              </div>
              <div class="form-group">
                <label for="email">E-Mail:</label>
                <input type="email" class="form-control" id="cs-email" placeholder="E-Mail (won't be not published; Gravatar supported)">
              </div>
              <div class="form-group">
                <label for="content">Comment:</label>
                <textarea class="form-control" id="cs-content" placeholder="Your Comment..." rows="7"></textarea>
              </div>
              <button type="submit" class="btn btn-default" onclick="return submitComment()">Submit</button>
            </form>
        `;
        return div;
    })();
    commentArea.appendChild(formDOM);

    const path = encodeURIComponent(location.pathname);
    fetch(`/comment-sidecar.php?site=${commentSidecarSite}&path=${path}`)
        .then(response => response.json())
        .then(handleComments);
})();