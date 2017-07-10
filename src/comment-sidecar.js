(function() {
    //TODO use iframe (sandbox) - https://blog.dareboost.com/en/2015/07/securing-iframe-sandbox-attribute/
    const commentArea = document.querySelector("#comment-sidecar");
    const createDOMForComment = comment => {
        //TODO gravatar email. don't send email back to browser in GET!
        const postDiv = document.createElement('div');
        postDiv.setAttribute("class", "post");
        postDiv.innerHTML = `
            <header class="post-header">
                <span class="author">${comment.author}</span> 
                <span class="date">${comment.creationTimestamp}</span>
            </header>
            <div class="post-content">${comment.content}</div>
        `;
        commentArea.appendChild(postDiv);
    };

    const path = encodeURIComponent(location.pathname);
    fetch(`/comment-sidecar.php?site=localhost&path=${path}`)
        .then(response => response.json())
        .then(comments => comments.forEach(createDOMForComment));
})();