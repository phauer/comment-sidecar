# prio 1 

- frontend
- email notification. 
    - set up dockerized env: https://github.com/docker-library/php/issues/135
- document and simplify configuration and setup (table creation script; where to put db credentials)

# prio 2

- rate limit
- multi-site support
    - CORS
    - security: check referer (browser ensures this even for AJAX requests)
- pagination
- check xss 
- db:
    - index correctly used? use `explain`.
    - insert with different timezone? -> insert as unix timestamp not as string
    - use epoch timestamp or datetime with timezone for read and write
- deletion link (comes with security efforts): 
    - on post creation, generate a token. this is required to delete a post (passed via url). this way, nobody can easily clear the whole db just by increasing the id.
        - alternative: use uuid instead of id&token. works, if this uuid is not delivered to client at all. so this uuid is hidden.
    - additional pw protection ("admin pw" or so). put in local webstorage for convenience?
        - enforce https?
    - moreover, only trash comments (set state to trashed/deleted). don't really delete it from db. reduces effects of an attack.

# ideas: security means and spam protection

- usage of PDO's prepared statements (sql injection)
- rate limit: put ip with timestamp into php cache (spam; DoS)
- frontend: no form action in HTML. no form-encoded http request. custom ajax request and js payload (spam bots)
- CORS and referer check (other web sites can't use your comment-sidecar installation)
- sandbox iframe: no access to page's DOM or locally stored data. can't draw to arbitrary positions on site.