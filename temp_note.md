# nginx 403 Fix for Blog Post URLs

## Problem
Browser Claude (and likely any non-browser client) gets a 403 on individual blog post URLs like `/blog/aim-for-mediocre/`. The root domain and index pages work fine. This is an nginx routing issue — when a request hits a directory path, nginx can't find the `index.html` inside it and falls back to directory listing, which is forbidden.

## What to do

1. Open the nginx.conf for the Hugo site (should be in `/home/u49382/seattlewren-prod/` or mounted into the `seattlewren-hugo-dev` container)

2. Find the `location /` block and check the `try_files` directive

3. It should look like this:
```nginx
location / {
    try_files $uri $uri/index.html $uri/ =404;
}
```

The critical part is `$uri/index.html` — that tells nginx to look for `index.html` inside the matching directory when the URL is something like `/blog/aim-for-mediocre/`.

4. After editing, rebuild the container:
```bash
cd /home/u49382/seattlewren-prod && docker compose up -d --build
```

5. Test with curl:
```bash
curl -o /dev/null -s -w "%{http_code}" https://jonnywren.com/blog/aim-for-mediocre/
```
Should return 200 instead of 403.

6. Delete this file when done — it's just a temp note.
