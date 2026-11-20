#!/usr/bin/env python3
"""Inspect Lemon JSON templates without assuming a working directory."""
import argparse, json, sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/"assets"/"templates"
def files(): return sorted(BASE.glob("*.json"))
def load(name):
    p=Path(name)
    if not p.exists():
        candidate = name if name.endswith(".json") else name+".json"
        p = BASE/candidate
        if not p.exists() and name == "api": p = BASE/"api-schema.json"
    if not p.exists(): raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding="utf-8"))
def main(argv=None):
    ap=argparse.ArgumentParser(); s=ap.add_subparsers(dest="cmd", required=True); s.add_parser("list"); i=s.add_parser("inspect"); i.add_argument("--name",required=True); args=ap.parse_args(argv)
    if args.cmd=="list":
        for p in files():
            d=load(str(p)); print(f"{d.get('name',p.stem)}: {len(d.get('columns',[]))} columns ({p.name})")
    else: print(json.dumps(load(args.name), ensure_ascii=False, indent=2))
if __name__=="__main__": sys.exit(main())
