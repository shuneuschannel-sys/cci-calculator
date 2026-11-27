"""Merge data/part*.json into the template and write the three page variants.

usage: python3 build.py
  -> index.html            standalone page (full HTML document)
  -> wordpress-embed.html  paste into a WordPress "Custom HTML" block (light theme fixed)
  -> preview.html          bare fragment used for the Claude artifact preview
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
items = []
for p in sorted((HERE / "data").glob("part*.json")):
    items += json.loads(p.read_text(encoding="utf-8"))
items.sort(key=lambda x: x["q"])

qs = [x["q"] for x in items]
missing = sorted(set(range(1, 97)) - set(qs))
dups = sorted({q for q in qs if qs.count(q) > 1})
if missing or dups:
    print("missing:", missing, "duplicates:", dups)

bad = re.compile(r"[—–―;；]")
for it in items:
    for k, v in it.items():
        for s in (v if isinstance(v, list) else [v]):
            text = json.dumps(s, ensure_ascii=False) if not isinstance(s, str) else s
            if bad.search(text):
                print(f"Q{it['q']} {k}: forbidden dash/semicolon -> {bad.findall(text)}")

(HERE / "data" / "iap2025.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

tpl = (HERE / "template.html").read_text(encoding="utf-8")
data_js = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
frag = tpl.replace("__DATA__", data_js)

(HERE / "preview.html").write_text(frag.replace("__ROOTCLASS__", ""), encoding="utf-8")

head, body = frag.split("<style>", 1)
standalone = ("<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"UTF-8\">\n"
              "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
              + head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
              + "<style>\nhtml,body{margin:0;background:#fff}@media(prefers-color-scheme:dark){html,body{background:#0a1222}}\n"
              + body.replace("</style>", "</style>\n</head>\n<body>", 1).replace("__ROOTCLASS__", "")
              + "\n</body>\n</html>\n")
(HERE / "index.html").write_text(standalone, encoding="utf-8")

embed = frag.split("\n", 2)[2]  # drop <title> and claude meta
(HERE / "wordpress-embed.html").write_text(
    "<!-- IAP 2025 急性膵炎ガイドライン 解説ブラウザ（EUS channel）: WordPress のカスタムHTMLブロックに丸ごと貼り付け -->\n"
    + embed.replace("__ROOTCLASS__", "lightonly"), encoding="utf-8")
print(f"built {len(items)} items, {len(data_js)//1024} KB data")
