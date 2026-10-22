"""Isolated runtime verification for each frozen executable.

PyInstaller runs this hook before the entry script. --build-smoke exits without
opening sockets, databases, scheduled tasks, or writing application data.
"""
import importlib
import sys

if "--build-smoke" in sys.argv:
    modules = (
        "flask", "flask_cors", "pyodbc", "pandas", "numpy",
        "openpyxl", "openpyxl.reader.excel", "openpyxl.writer.excel",
        "requests", "dateutil.parser", "dotenv", "waitress",
        "lxml.etree", "chardet", "charset_normalizer",
        "Crypto.Cipher.AES", "cryptography.hazmat.primitives.ciphers.aead",
        "jwt", "ldap3",
    )
    try:
        for module in modules:
            importlib.import_module(module)
    except Exception as exc:
        print(f"BUILD-SMOKE-FAIL: {module}: {exc}", file=sys.stderr)
        sys.exit(1)
    print("BUILD-SMOKE-OK " + ", ".join(modules), flush=True)
    sys.exit(0)
