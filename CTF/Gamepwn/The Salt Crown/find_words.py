import re

with open("strings_dec.txt", "r") as f:
    words = [line.strip() for line in f]

# Filter out standard words, library names, etc.
filtered = []
for w in words:
    # Check if alphabetical, lowercase/mixed, length 4 to 20
    if re.match("^[a-zA-Z_][a-zA-Z0-9_]{3,20}$", w):
        # Exclude common system/Godot terms
        lower = w.lower()
        if any(x in lower for x in ("godot", "variant", "extension", "library", "interface", "mem_", "print", "error", "warn", "get_", "set_", "bad_", "alloc", "except", "class", "method", "object", "string", "utility", "array", "vector", "rect", "transform", "projection", "color", "rid", "callable", "signal", "dictionary")):
            continue
        filtered.append(w)

print(f"Found {len(filtered)} custom word candidates:")
# Print the first 100 candidates
for fw in filtered[:100]:
    print(f"  {fw}")
