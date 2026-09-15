# Prototype Pollution CTF — Notes

## Challenge clue → concept
"Pollute the origin and the lies will be inherited" = **JS Prototype Pollution**.
If you can write to `Object.prototype`, every object in the app "inherits" your
fake property — including internal checks like `isAdmin`.

## Step-by-step method

1. **Recon the app**
   - `curl -v <url>` → check headers (`x-powered-by: Express` = Node.js backend)
   - Look at cookies — session cookies mean requests may be pinned to a backend node
   - `gobuster dir -u <url> -w wordlist -x html,json` → find hidden pages

2. **Find real endpoints from the frontend JS**
   - Don't guess blindly — pull JS out of HTML:
     `grep -oE '/api/[a-zA-Z0-9/_-]+' page.html`
     `grep -n "fetch(" page.html`
   - This revealed the real endpoints: `/api/login`, `/api/update`, `/api/flag`

3. **Authenticate**
   - Tried obvious guest creds (`guest`/`guest`) — worked
   - Kept a cookie jar so session persists across requests:
     `curl -c cookies.txt -b cookies.txt ...`

4. **Identify the pollution point**
   - `/api/update` took `{"path": "...", "value": ...}` — a **path-based setter**
     (like `lodash.set`), which is a classic prototype pollution vector.
   - Baseline test worked normally (`"path": "runtime.theme"`).

5. **Try the pollution payload**
   - `{"path": "__proto__.isAdmin", "value": true}` → blocked by a WAF
     (`"WAF ALERT: Malicious prototype manipulation blocked"`)

6. **Bypass the WAF — try encoding variants**
   Since the WAF was matching the literal string `__proto__`, tried alternate
   forms that still resolve to the same property at runtime:
   - Case variation: `__PROTO__` 
   - Array-form path instead of dot-string: `["__proto__", "isAdmin"]`
   - (Also tried `constructor.prototype`, bracket notation, unicode escapes,
     leading dot — these got blocked, only the two above passed)

7. **Confirm and exploit**
   - After a payload got past the WAF, check whether it actually polluted
     the object (not just evaded the filter) by hitting the protected route:
     `curl -b cookies.txt <url>/api/flag`
   - If the guessed property name (`isAdmin`) doesn't work, brute a small
     list of likely field names (`admin`, `authorized`, `elevated`, etc.)
     using the working bypass payload shape.

## Key lessons / reusable checklist
- [ ] Check response headers & cookies for backend architecture clues
- [ ] Always extract real endpoints from frontend JS instead of guessing paths
- [ ] Path-based `set()`/`merge()`/`extend()` utilities = prototype pollution risk
- [ ] Test `__proto__`, `constructor.prototype` variants
- [ ] If blocked by a WAF, try: case changes, array-form paths, encoding tricks,
      whitespace, bracket notation
- [ ] Pollution ≠ success until you *verify* it via a protected endpoint
- [ ] Keep a cookie jar (`-c`/`-b`) to stay authenticated & pinned to session/node
