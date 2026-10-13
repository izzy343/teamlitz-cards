"""Render a 'Coach Fentress' update' card. Usage: python3 coach_update.py data.json out.png coach_avatar.jpg"""
import base64, html, json, sys
from playwright.sync_api import sync_playwright

e = html.escape
d = json.load(open(sys.argv[1]))
coach = base64.b64encode(open(sys.argv[3], "rb").read()).decode()

page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:390px;background:#0f1115;font-family:'DejaVu Sans',sans-serif;color:#f4f4f5}}
.card{{padding:22px 18px 18px}}
.hdr{{display:flex;align-items:center;gap:12px}}
.hdr .t{{flex:1}}
.kicker{{font-size:11px;letter-spacing:.14em;color:#f59e0b;font-weight:bold}}
.title{{font-size:22px;font-weight:bold;line-height:1.15;margin-top:4px}}
.coach{{width:84px;height:84px;border-radius:50%;border:3px solid #f59e0b;background:#c3d4e6;overflow:hidden;flex-shrink:0}}
.coach img{{width:100%;height:100%;display:block}}
.msg{{margin-top:18px;background:#1b1e25;border-radius:14px;padding:18px 16px;border-left:4px solid #f59e0b}}
.msg .big{{font-size:19px;font-weight:bold;line-height:1.3}}
.msg .big em{{font-style:normal;color:#fbbf24}}
.rows{{margin-top:12px;display:flex;flex-direction:column;gap:8px}}
.row{{display:flex;gap:10px;align-items:flex-start;font-size:13px;color:#d4d4d8;line-height:1.35}}
.dot{{width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-top:5px;flex-shrink:0}}
.foot{{font-size:10px;color:#6b7280;margin-top:12px}}
</style></head><body><div class="card">
<div class="hdr"><div class="t"><div class="kicker">TEAMLITZ · {e(d["kicker"]).upper()}</div>
<div class="title">{e(d["title"])}</div></div>
<div class="coach"><img src="data:image/jpeg;base64,{coach}"></div></div>
<div class="msg"><div class="big">{d["headline_html"]}</div>
<div class="rows">{''.join(f'<div class="row"><span class="dot"></span><span>{e(r)}</span></div>' for r in d["rows"])}</div></div>
<div class="foot">{e(d["foot"])}</div>
</div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 600}, device_scale_factor=3)
    pg.set_content(page)
    pg.locator(".card").screenshot(path=sys.argv[2])
    b.close()
print("wrote", sys.argv[2])
