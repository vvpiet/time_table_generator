#!/usr/bin/env python
"""Quick import test"""
try:
    import export_handler
    print("OK: export_handler imported")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
