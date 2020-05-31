# prio 1

- rewrite disqus export: use exportable XML as an input (instead of the API)
    - test import script with IT blog
- migration: add column for (disqus) avatars urls
- pagination
- rate limit
    - use dedicated table for this; POSTs are rare and can be a little slower; slow down attacker anyway. clean up job via web cron.
    - or use at least cookies 
- update privacy policy

# prio 2

- network_mode = hosts (required for xdebug) makes sql queries extremely slow!
- sql injection test
- improve replyTo check: referring id has to be in the same site and path (separate post required for this)
- watch comments -> get notified if someone replies to my comment
    - related issues: management of subscriptions? dedicated subscription table? check/uncheck notification when posting? unsubscribe link in mail? different table? -> postpone this feature!
    - add hint about this in the email field. "not published, but used for notification on replies and to display a gravatar avatar"
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
- unrelated:
    - md5 is very unsafe. use a spam email for gravatar! 
- make file to automate test execution and zipping of the relevant files 
- only request for a gravatar image if there is an email.
- markdown support
- OpCache to store compiled php files. 

# ideas: security means and spam protection

- spam bot protection using a honeypot field in the HTML form
- usage of PDO's prepared statements (sql injection)
- rate limit: put ip with timestamp into php cache (spam; DoS)
- frontend: no form action in HTML. no form-encoded http request. custom ajax request and js payload (spam bots)
- CORS and referer check (other web sites can't use your comment-sidecar installation)