# Under Development!


# comment-sidecar

comment-sidecar is a lightweight, tracking-free, self-hosted comment service. It aims at restricted web spaces where only PHP and MySQL is available. And it is easy to embed into statically generated sites that are created with Hugo or Jekyll.
  
# Planned Features

- Tracking-free and fast. The comment-sidecar only needs one additional request. Contrary, with Disqus my site needs 124 requests to be fully loaded. Without: only 14! Read [here](http://donw.io/post/github-comments/) for more details about Disqus' tracking greed and performance hit.
- Privacy. Your data belongs to you.
- Easy to integrate. Just a simple Javascript call. This makes is easy to use the comment-sidecar in conjunction with static site generators like Hugo or Jekyll. You don't have to integrate PHP code in the generated HTML files.
- Lightweight: Zero Dependencies.
- No performance impact on TTFB (Time To First Byte), because the comments are loaded asynchronously.
- Spam Protection.
- E-Mail Notification. E-Mail includes a deletion link to easily remove undesired comments. 
- Gravatar Support.
- Markdown Support.
- Use one comment-sidecar installation for multiple sites.
- Replying to a comment is supported.

# Disclaimer

I'm not a PHP expert. ;-)