"""TeamLitz GroupMe card renderer (phone-sized PNG, 1170px wide).

Usage:
  python3 teamlitz_render.py schedule data.json out.png
  python3 teamlitz_render.py scout      data.json out.png  coach_avatar.jpg   (one tall card)
  python3 teamlitz_render.py scout_main data.json out.png  coach_avatar.jpg   (scouting report, no keys)
  python3 teamlitz_render.py scout_keys data.json out.png  coach_avatar.jpg   (keys to the game only)
GroupMe drops tall images, so post scout_main then scout_keys instead of one tall scout card.

schedule data.json:
  {"date_label": "Thursday, Oct 15", "updated": "Tue 10/13, 3:05 PM",
   "status": "NEW" | "UPDATED", "changes": ["Time: 7:40 -> 8:35 PM"],
   "games": [{"time": "7:40 PM", "opponent": "...", "opp_record": "2-1",
              "opp_division": "Div 4", "location": "PSBL Sodo", "court": "Court 1"}]}

scout data.json:
  {"game_label": "Thu Oct 15 · 7:40 PM", "opponent": "...",
   "opp_meta": "Division 4 · 2-1 (tied 1st) · Won 2 straight",
   "stats": [{"v": "74", "l": "PPG"}, {"v": "68", "l": "ALLOWED"}, {"v": ".390", "l": "OPP WIN %"}],
   "last_games": [{"date": "9/24", "res": "W", "score": "94-92", "opp": "...", "opp_info": "Div 4 · 2-1"}],
   "common": ["Team: they lost by 10, we lost by 25."],
   "keys": [{"head": "Make it a grind.", "body": "..."}],
   "updated": "Tue 10/13, 3:05 PM"}
"""
import base64, html, json, sys
from playwright.sync_api import sync_playwright

e = html.escape

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:390px;background:#0f1115;font-family:'DejaVu Sans',sans-serif;color:#f4f4f5}
.card{padding:20px 18px 16px}
.foot{font-size:10px;color:#6b7280;margin-top:8px}
"""

SCHED_CSS = """
.top{display:flex;justify-content:space-between;align-items:baseline}
.team{font-size:13px;letter-spacing:.14em;color:#f59e0b;font-weight:bold}
.night{font-size:12px;color:#9ca3af}
.date{font-size:30px;font-weight:bold;margin:6px 0 16px;line-height:1.1}
.banner{background:#7c2d12;border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:13px}
.banner ul{margin:6px 0 0 18px}
.game{display:flex;gap:14px;background:#1b1e25;border-radius:14px;padding:14px;margin-bottom:10px;border-left:4px solid #f59e0b}
.when{width:104px;flex-shrink:0}
.lbl{font-size:10px;letter-spacing:.12em;color:#9ca3af}
.time{font-size:22px;font-weight:bold;margin-top:2px;white-space:nowrap}
.vs{font-size:11px;color:#9ca3af}
.opp{font-size:18px;font-weight:bold;line-height:1.2}
.meta{font-size:12px;color:#fbbf24;margin-top:3px}
.loc{font-size:13px;color:#d4d4d8;margin-top:6px}
.court{display:inline-block;background:#f59e0b;color:#111;font-weight:bold;font-size:11px;border-radius:6px;padding:2px 6px;margin-left:2px}
"""

SCOUT_CSS = """
.hdr{display:flex;align-items:center;gap:12px}
.hdr .t{flex:1}
.kicker{font-size:11px;letter-spacing:.14em;color:#f59e0b;font-weight:bold}
.title{font-size:21px;font-weight:bold;line-height:1.15;margin-top:3px}
.coach{width:76px;height:76px;border-radius:50%;border:3px solid #f59e0b;background:#c3d4e6;overflow:hidden;flex-shrink:0}
.coach img{width:100%;height:100%;display:block}
.olbl{margin-top:14px;font-size:12px;color:#9ca3af}
.oppname{font-size:20px;font-weight:bold;color:#fff;margin-top:2px}
.oppmeta{font-size:13px;color:#fbbf24;margin-top:3px}
.stats{display:flex;gap:8px;margin-top:12px}
.stat{flex:1;background:#1b1e25;border-radius:10px;padding:8px 6px;text-align:center}
.stat .v{font-size:18px;font-weight:bold}
.stat .l{font-size:10px;color:#9ca3af;margin-top:2px}
h3{font-size:11px;letter-spacing:.14em;color:#9ca3af;margin:16px 0 6px}
table{width:100%;border-collapse:collapse;font-size:13px}
td{padding:6px 4px;border-top:1px solid #262a33;vertical-align:top}
td.dt{color:#9ca3af;width:40px}
.res{display:inline-block;width:20px;text-align:center;border-radius:4px;font-weight:bold;font-size:11px;padding:1px 0}
.res.W{background:#166534} .res.L{background:#7f1d1d}
.sub{font-size:11px;color:#9ca3af}
.common{background:#1b1e25;border-left:4px solid #3b82f6;border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:6px}
ol{margin-left:18px;font-size:13px;line-height:1.4}
ol li{margin-bottom:6px}
ol b{color:#f59e0b}
"""


def schedule_html(d):
    rows = []
    multi = len(d["games"]) > 1
    for i, g in enumerate(d["games"], 1):
        meta = " · ".join(x for x in [g.get("opp_division"), g.get("opp_record")] if x)
        court = f'<span class="court">{e(g["court"])}</span>' if g.get("court") else ""
        rows.append(
            f'<div class="game"><div class="when"><div class="lbl">{"GAME " + str(i) if multi else "TIP-OFF"}</div>'
            f'<div class="time">{e(g["time"])}</div></div><div class="what"><div class="vs">vs</div>'
            f'<div class="opp">{e(g["opponent"])}</div>'
            + (f'<div class="meta">{e(meta)}</div>' if meta else "")
            + f'<div class="loc">{e(g["location"])} {court}</div></div></div>')
    banner = ""
    if d.get("status") == "UPDATED":
        items = "".join(f"<li>{e(c)}</li>" for c in d.get("changes", []))
        banner = f'<div class="banner"><b>SCHEDULE UPDATED</b><ul>{items}</ul></div>'
    return (f'<style>{BASE_CSS}{SCHED_CSS}</style><div class="card">'
            f'<div class="top"><div class="team">TEAMLITZ (THU)</div><div class="night">Thursday League · Div 3</div></div>'
            f'<div class="date">{e(d["date_label"])}</div>{banner}{"".join(rows)}'
            f'<div class="foot">PSBL schedule · checked {e(d["updated"])}</div></div>')


def scout_html(d, avatar_path, part="full"):
    """part: "full" (one card), "main" (no keys), or "keys" (keys-only card)."""
    mime = "image/png" if avatar_path.lower().endswith(".png") else "image/jpeg"
    coach = base64.b64encode(open(avatar_path, "rb").read()).decode()
    stats = "".join(f'<div class="stat"><div class="v">{e(s["v"])}</div><div class="l">{e(s["l"])}</div></div>' for s in d["stats"])
    games = "".join(
        f'<tr><td class="dt">{e(g["date"])}</td><td><span class="res {e(g["res"])}">{e(g["res"])}</span> {e(g["score"])}</td>'
        f'<td>{e(g["opp"])}<div class="sub">{e(g["opp_info"])}</div></td></tr>' for g in d["last_games"])
    common = "".join(f'<div class="common">{e(c)}</div>' for c in d.get("common", []))
    keys = "".join(f'<li><b>{e(k["head"])}</b> {e(k["body"])}</li>' for k in d["keys"])
    return (f'<style>{BASE_CSS}{SCOUT_CSS}</style><div class="card">'
            f'<div class="hdr"><div class="t"><div class="kicker">TEAMLITZ · {e(d["game_label"]).upper()}</div>'
            f'<div class="title">Coach Fentress\'<br>Scouting Report</div></div>'
            f'<div class="coach"><img src="data:{mime};base64,{coach}"></div></div>'
            f'<div class="olbl">OPPONENT</div><div class="oppname">{e(d["opponent"])}</div>'
            f'<div class="oppmeta">{e(d["opp_meta"])}</div><div class="stats">{stats}</div>'
            f'<h3>LAST {len(d["last_games"])} GAMES</h3><table>{games}</table>'
            + (f'<h3>COMMON OPPONENT{"S" if len(d.get("common", [])) > 1 else ""}</h3>{common}' if common else "")
            + (f'<h3>KEYS TO THE GAME</h3><ol>{keys}</ol>' if part == "full" else "")
            + f'<div class="foot">PSBL standings &amp; results · checked {e(d["updated"])}</div></div>')


def keys_html(d, avatar_path):
    mime = "image/png" if avatar_path.lower().endswith(".png") else "image/jpeg"
    coach = base64.b64encode(open(avatar_path, "rb").read()).decode()
    keys = "".join(f'<li><b>{e(k["head"])}</b> {e(k["body"])}</li>' for k in d["keys"])
    return (f'<style>{BASE_CSS}{SCOUT_CSS}</style><div class="card">'
            f'<div class="hdr"><div class="t"><div class="kicker">TEAMLITZ · {e(d["game_label"]).upper()}</div>'
            f'<div class="title">Keys to<br>the Game</div></div>'
            f'<div class="coach"><img src="data:{mime};base64,{coach}"></div></div>'
            f'<div class="olbl">VS</div><div class="oppname">{e(d["opponent"])}</div>'
            f'<ol style="margin-top:18px">{keys}</ol>'
            f'<div class="foot">Coach Fentress · checked {e(d["updated"])}</div></div>')


def main():
    kind, data_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    d = json.load(open(data_path))
    if kind == "schedule":
        body = schedule_html(d)
    elif kind == "scout_main":
        body = scout_html(d, sys.argv[4], part="main")
    elif kind == "scout_keys":
        body = keys_html(d, sys.argv[4])
    else:
        body = scout_html(d, sys.argv[4])
    page = f'<!doctype html><html><head><meta charset="utf-8"></head><body>{body}</body></html>'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 600}, device_scale_factor=3)
        pg.set_content(page)
        pg.locator(".card").screenshot(path=out)
        b.close()
    print("wrote", out)


if __name__ == "__main__":
    main()
