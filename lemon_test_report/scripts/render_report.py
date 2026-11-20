#!/usr/bin/env python3
"""安全地把审核后的 Markdown 转成无外部依赖的静态 HTML。"""
from __future__ import annotations
import argparse, html, json, re
from pathlib import Path

def inline(value):
    value = html.escape(value, quote=True)
    value = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", value)
    return value

def table(lines, pos):
    rows=[]; i=pos
    while i < len(lines) and "|" in lines[i] and lines[i].strip():
        cells=[c.strip() for c in lines[i].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-+:?", c) for c in cells): rows.append(cells)
        i += 1
    if not rows: return "", pos
    head="".join(f"<th>{inline(c)}</th>" for c in rows[0])
    body="".join("<tr>"+"".join(f"<td>{inline(c)}</td>" for c in row)+"</tr>" for row in rows[1:])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", i

def markdown(source):
    lines=source.splitlines(); out=[]; i=0
    while i < len(lines):
        s=lines[i].strip()
        if not s: i+=1; continue
        m=re.match(r"^(#{1,3})\s+(.+)$", s)
        if m: out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>"); i+=1; continue
        if "|" in s:
            block, nxt=table(lines,i)
            if block: out.append(block); i=nxt; continue
        if re.match(r"^[-*+]\s+", s):
            items=[]
            while i<len(lines) and (m:=re.match(r"^[-*+]\s+(.+)$", lines[i].strip())):
                items.append(f"<li>{inline(m.group(1))}</li>"); i+=1
            out.append("<ul>"+"".join(items)+"</ul>"); continue
        if s.startswith("> "): out.append(f"<blockquote>{inline(s[2:])}</blockquote>"); i+=1; continue
        para=[s]; i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r"^(#{1,3})\s|^[-*+]\s|^> |.*\|",lines[i].strip()): para.append(lines[i].strip()); i+=1
        out.append("<p>"+inline(" ".join(para))+"</p>")
    return "\n".join(out)

def render(source, audit, title):
    status=audit.get("conclusion","Pending"); cls={"Go":"go","No-Go":"nogo","Pending":"pending"}.get(status,"pending")
    warning="".join(f"<li>{inline(x)}</li>" for x in audit.get("warnings",[])+audit.get("errors",[]))
    banner=f'<aside class="status {cls}">门禁结论：{html.escape(status)}</aside>'
    alerts=f'<section><h2>审计提示</h2><ul>{warning}</ul></section>' if warning else ''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>body{{font:16px system-ui,sans-serif;background:#f5f7fb;color:#172033;max-width:1100px;margin:0 auto;padding:24px}}main,section{{background:white;border:1px solid #dbe2ee;border-radius:12px;padding:22px;margin:16px 0}}h1{{color:#173b70}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #dbe2ee;padding:8px;text-align:left}}th{{background:#edf4ff}}.status{{padding:14px;border-radius:8px;font-weight:700}}.go{{background:#dcfce7;color:#166534}}.nogo{{background:#fee2e2;color:#991b1b}}.pending{{background:#fef3c7;color:#92400e}}code{{background:#eef2f7;padding:2px 4px}}</style></head><body><main><h1>{html.escape(title)}</h1>{banner}</main>{alerts}<section>{markdown(source)}</section><footer>由 lemon-test-report 生成；不包含外部资源。</footer></body></html>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report",type=Path); ap.add_argument("--audit",type=Path); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    source=args.report.read_text(encoding="utf-8"); audit=json.loads(args.audit.read_text(encoding="utf-8")) if args.audit else {}
    args.output.write_text(render(source,audit,args.report.stem),encoding="utf-8"); print(f"已生成安全静态报告：{args.output}")
if __name__ == "__main__": main()
