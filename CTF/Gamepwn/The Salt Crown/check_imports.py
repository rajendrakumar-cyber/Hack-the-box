import pefile

pe = pefile.PE("challenge_core.windows.template_release.x86_64.dll")
pe.parse_data_directories()

for entry in pe.DIRECTORY_ENTRY_IMPORT:
    print(f"DLL: {entry.dll.decode()}")
    for imp in entry.imports:
        print(f"  Name: {imp.name.decode() if imp.name else 'None'}, Address/IAT RVA: {hex(imp.address)}")
