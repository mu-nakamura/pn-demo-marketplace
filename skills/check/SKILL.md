---
name: check
description: records/ が OKF v0.2 の最小の適合条件（frontmatter と type、index.md・log.md の構造、時刻形式）を満たすか確認する。リハーサルでの点検用。「記録をチェックして」「OKF の適合を確認して」と言われたときに使う。pn-demo のデモ用。
---

# check：記録の点検（OKF v0.2 の最小の適合）

`records/` の記録が、OKF v0.2 の最小の適合条件を満たすかを、スクリプトで確認する。**読むだけで、記録を変更しない。**

## 手順

1. 下の Python スクリプトを、作業用の場所（`/tmp/okf_check.py`）に保存する（作業フォルダには置かない）。
2. `python3 /tmp/okf_check.py records` を実行する。`yaml` が無ければ `pip install pyyaml` を実行してから再実行する。
3. 出力をそのまま示し、問題があれば、ファイルごとに原因と直し方の案を述べる（**直すかどうかは人に尋ね、勝手に書き換えない**）。
4. 述べる範囲：このスクリプトが確認するのは次の範囲だけ。OKF の完全な検証ではない（公式の検証器はまだ無い）。
   - 予約名以外の `.md` が、解析できる YAML frontmatter と、空でない `type` を持つこと
   - `index.md`（根以外は frontmatter なし。根は `okf_version` のみ可）、`log.md`（日付見出しが `YYYY-MM-DD`）の構造
   - `generated.at`／`verified[].at`／`stale_after` が UTC オフセット付きの ISO 8601 であること

## スクリプト

```python
#!/usr/bin/env python3
"""OKF v0.2 の最小適合チェック（仕様 §11 の3条件 + 時刻形式）。
使い方: python3 okf_check.py <バンドルのルート>
確認すること:
  1. 予約名以外の .md は、パースできる YAML frontmatter を持つ
  2. frontmatter に空でない type がある
  3. index.md / log.md は §8 / §9 の構造（index.md は frontmatter なし。ルートのみ okf_version 可。log.md の日付見出しは YYYY-MM-DD）
  + 時刻キー（generated.at / verified[].at / stale_after）が UTC オフセット付き ISO 8601
スキーマの完全検証ではない（OKF にはまだ公式の検証器がない）。
"""
import re, sys, pathlib, datetime
import yaml

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
errors, warns, n = [], [], 0

def ts(v):
    if isinstance(v, datetime.datetime):
        return v.tzinfo is not None
    return isinstance(v, str) and bool(ISO.match(v))

def split_fm(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    return text[4:end], text[end + 4:]

root = pathlib.Path(sys.argv[1])
for p in sorted(root.rglob("*.md")):
    rel = p.relative_to(root).as_posix()
    text = p.read_text(encoding="utf-8")
    fm_raw, body = split_fm(text)
    if p.name == "index.md":
        if fm_raw is not None:
            if rel != "index.md":
                errors.append(f"{rel}: index.md に frontmatter（ルート以外は不可）")
            else:
                d = yaml.safe_load(fm_raw) or {}
                if set(d) - {"okf_version"}:
                    errors.append(f"{rel}: ルート index.md の frontmatter は okf_version のみ")
        continue
    if p.name == "log.md":
        for h in re.findall(r"^## (.+)$", text, re.M):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", h.strip()):
                errors.append(f"{rel}: log.md の日付見出しが YYYY-MM-DD でない: {h}")
        continue
    n += 1
    if fm_raw is None:
        errors.append(f"{rel}: frontmatter がない"); continue
    try:
        d = yaml.safe_load(fm_raw) or {}
    except Exception as e:
        errors.append(f"{rel}: YAML を解析できない: {e}"); continue
    if not isinstance(d.get("type"), str) or not d["type"].strip():
        errors.append(f"{rel}: type が空または無い")
    g = d.get("generated")
    if g is not None:
        if not isinstance(g, dict) or "by" not in g:
            errors.append(f"{rel}: generated.by が無い")
        elif "at" in g and not ts(g["at"]):
            errors.append(f"{rel}: generated.at が UTC オフセット付き ISO 8601 でない: {g['at']}")
    v = d.get("verified")
    if v is not None:
        for e in (v if isinstance(v, list) else [v]):
            if not isinstance(e, dict) or "by" not in e or "at" not in e:
                errors.append(f"{rel}: verified の要素に by/at が無い")
            elif not ts(e["at"]):
                errors.append(f"{rel}: verified.at が UTC オフセット付き ISO 8601 でない: {e['at']}")
    if "stale_after" in d and not ts(d["stale_after"]):
        errors.append(f"{rel}: stale_after が UTC オフセット付き ISO 8601 でない")
    if "status" in d and d["status"] not in ("draft", "stable", "deprecated"):
        warns.append(f"{rel}: status が draft/stable/deprecated 以外: {d['status']}")
    for s in d.get("sources", []) or []:
        if not isinstance(s, dict) or "resource" not in s:
            errors.append(f"{rel}: sources の要素に resource が無い")
print(f"concept 文書: {n} 件")
for w in warns: print("WARN ", w)
for e in errors: print("ERROR", e)
print("結果:", "適合（上記の範囲）" if not errors else f"{len(errors)} 件の問題")
sys.exit(1 if errors else 0)
```
