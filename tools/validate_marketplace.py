#!/usr/bin/env python3
"""GitHub に push する前の構造チェック。
  - .claude-plugin/marketplace.json が JSON として正しい
  - マーケットプレイス名・プラグイン名・スキル名が 小文字・数字・ハイフンのみ（Studio の登録条件）
  - 各スキルのパスに SKILL.md があり、frontmatter の name がフォルダ名と一致し、description がある
  - 各ファイルが 1MB 以下（Studio の共有の上限。プラグイン経由でも超えないように）
使い方: リポジトリのルートで  python3 tools/validate_marketplace.py
"""
import json, os, re, sys
errs = []
m = json.load(open(".claude-plugin/marketplace.json", encoding="utf-8"))
ok = lambda s: re.fullmatch(r"[a-z0-9-]+", s or "") is not None
if not ok(m.get("name")): errs.append(f"marketplace name が不正: {m.get('name')}")
for p in m.get("plugins", []):
    if not ok(p.get("name")): errs.append(f"plugin name が不正: {p.get('name')}")
    for s in p.get("skills", []):
        f = os.path.join(s, "SKILL.md")
        if not os.path.isfile(f): errs.append(f"{f} が無い"); continue
        t = open(f, encoding="utf-8").read()
        fm = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        if not fm: errs.append(f"{f}: frontmatter が無い"); continue
        n = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
        d = re.search(r"^description:\s*(.+)$", fm.group(1), re.M)
        if not n or n.group(1).strip() != os.path.basename(s): errs.append(f"{f}: name がフォルダ名と一致しない")
        if not ok(os.path.basename(s)): errs.append(f"{s}: スキル名が不正")
        if not d or len(d.group(1).strip()) < 20: errs.append(f"{f}: description が短い/無い")
for root, _, files in os.walk("."):
    if ".git" in root: continue
    for fn in files:
        pth = os.path.join(root, fn)
        if os.path.getsize(pth) > 1024 * 1024: errs.append(f"{pth}: 1MB 超")
print("プラグイン:", [p["name"] for p in m.get("plugins", [])])
for e in errs: print("ERROR", e)
print("結果:", "OK" if not errs else f"{len(errs)} 件の問題")
sys.exit(1 if errs else 0)
