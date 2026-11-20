#!/usr/bin/env python3
"""Report optional dependency availability without importing the whole skill."""
import argparse,importlib.util,json,sys
from pathlib import Path
PACKAGES={"yaml":"PyYAML","docx":"python-docx","pdfplumber":"pdfplumber","openpyxl":"openpyxl","xmind":"xmind"}
def probe(): return {module:{"available":importlib.util.find_spec(module) is not None,"package":package} for module,package in PACKAGES.items()}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--output"); args=ap.parse_args(argv); result=probe(); text=json.dumps(result,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 0
if __name__=="__main__": sys.exit(main())
