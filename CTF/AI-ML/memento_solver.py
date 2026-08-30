import base64

campaign = b"m3m0ry-p0is0n-p3rs1sts-acr0ss-s3ss10ns!!"
chunks = [
    "JWcvSwES",  # s=1 (index.html)
    "HBxcGixD",  # s=2 (about.html)
    "GhwcXy0D",  # s=3 (catalogue.html)
    "Q0AHAHIV",  # s=4 (provenance.html)
    "C0FvHkdf",  # s=5 (ledger.html)
    "GE4="        # s=6 (petitions.html)
]

decoded = []
for chunk in chunks:
    missing_padding = len(chunk) % 4
    if missing_padding:
        chunk += "=" * (4 - missing_padding)
    dec = base64.urlsafe_b64decode(chunk)
    decoded.append(dec)

xor_bytes = b"".join(decoded)
flag = "".join(chr(xor_bytes[i] ^ campaign[i % len(campaign)]) for i in range(len(xor_bytes)))
print("Flag:", flag)
