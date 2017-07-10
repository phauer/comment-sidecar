(function() {
    // TODO avatar
    // TODO form
    const commentArea = document.querySelector("#comment-sidecar");
    const handleComments = comments => {
        const heading = document.createElement("h1");
        heading.innerText = 'Comments';
        commentArea.appendChild(heading);
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
        postDiv.setAttribute("class", "post");
        postDiv.innerHTML = `
            <header class="post-header">
                <span class="author">${comment.author}</span> 
                <span class="date">${formatDate(comment.creationTimestamp)}</span>
            </header>
            <div class="post-content">${comment.content}</div>
        `;
        commentArea.appendChild(postDiv);
    };

    const path = encodeURIComponent(location.pathname);
    fetch(`/comment-sidecar.php?site=localhost&path=${path}`)
        .then(response => response.json())
        .then(handleComments);
})();