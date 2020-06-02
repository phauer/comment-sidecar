# prio 1

- disqus export: write tests for the import script. maybe with my own disqus xml.
- update privacy policy
- proper multi-site support. e.g. SITE variable set to a fixed value on the server-side.
- pagination

# prio 2

- not embedd avatar svg multiple times. instead use `defs` and `use` to reuse a single declaration.
- network_mode = hosts (required for xdebug) makes sql queries extremely slow!
- sql injection test
- improve replyTo check: referring id has to be in the same site and path (separate post required for this)
- watch comments -> get notified if someone replies to my comment
    - related issues: management of subscriptions? dedicated subscription table? check/uncheck notification when posting? unsubscribe link in mail? different table? -> postpone this feature!
- db:
    - index correctly used? use `explain`.
    - insert with different timezone? -> insert as unix timestamp not as string
    - use epoch timestamp or datetime with timezone for read and write
- deletion link (comes with security efforts): 
    - README text: "E-Mail includes a deletion link to easily remove undesired comments." 
    - on post creation, generate a token. this is required to delete a post (passed via url). this way, nobody can easily clear the whole db just by increasing the id.
        - alternative: use uuid instead of id&token. works, if this uuid is not delivered to client at all. so this uuid is hidden.
    - additional pw protection ("admin pw" or so). put in local webstorage for convenience?
        - enforce https?
    - OR: no uuid, no admin pw; just http basic auth protection
    - moreover, only trash comments (set state to trashed/deleted). don't really delete it from db. reduces effects of an attack.
- refactoring
    - use proper templating in comment-sidecar-js-delivery.php. maybe with php means, but prevent js tooling in IDE.
- ui:
    - drop-down indicator for "Write a Comment" and "Reply"
    - save name and email in local webstorage -> no need to type it in again.
    - after comment -> scroll to submitted comment and highlight it!
- make file to automate test execution and zipping of the relevant files 
- markdown support
- OpCache to store compiled php files. 

# ideas: security means and spam protection

- spam bot protection using a honeypot field in the HTML form
- usage of PDO's prepared statements (sql injection)
- rate limit: put ip with timestamp into php cache (spam; DoS)
- frontend: no form action in HTML. no form-encoded http request. custom ajax request and js payload (spam bots)
- CORS and referer check (other web sites can't use your comment-sidecar installation)