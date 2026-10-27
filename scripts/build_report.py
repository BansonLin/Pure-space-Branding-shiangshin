#!/usr/bin/env python3
"""Build the A4 building-analysis + sales-planning proposal (HTML → PDF).

Data come from the DWG permit drawing extraction (see data/extracted_facts.json
and reports/dwg-extraction-shuangfu768.md). Every figure carries a tag:
    實際 = read directly from the permit drawing
    示意 = model / scenario with stated assumptions
    評估 = planner's judgement

Usage:
    python3 scripts/build_report.py            # writes build/report.html
    node scripts/print_pdf.mjs                 # prints reports/*.pdf
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "drawings"
BUILD = ROOT / "build"
FACTS = json.loads((ROOT / "data" / "extracted_facts.json").read_text(encoding="utf-8"))

M2_PER_PING = 3.305785
VERSION = "v1.0"
REPORT_DATE = "2026-10-27"


def ping(m2: float) -> float:
    return m2 / M2_PER_PING


def img(name: str) -> str:
    return (ASSETS / name).as_uri()


def tag(kind: str) -> str:
    cls = {"實際": "t-fact", "示意": "t-model", "評估": "t-judge"}[kind]
    return f'<span class="tag {cls}">{kind}</span>'


# ---------------------------------------------------------------- derived figures
F = FACTS
units = F["unit_types"]
for u in units:
    u["interior_ping"] = ping(u["interior_m2"])
    u["balcony_avg"] = sum(u["balcony_by_floor"]) / len(u["balcony_by_floor"])

residential_floors = 11
common_per_floor = sum(F["typical_floor"]["common_parts_m2"].values())
B1_PARKING_EST = 30 * 40.0  # 40 m² per space, the figure the permit review itself uses
b1_nonparking = F["areas"]["B1_m2"] - B1_PARKING_EST
common_total = (common_per_floor * residential_floors
                + (F["areas"]["1F_m2"] - F["areas"]["1F_parking_m2"])
                + F["areas"]["rooftop_total_m2"]
                + b1_nonparking)
grand_total = F["areas"]["total_floor_m2"] + F["areas"]["balcony_total_m2"]
parking_total = F["areas"]["1F_parking_m2"] + B1_PARKING_EST
residential_private = grand_total - parking_total - common_total
common_ratio = common_total / (residential_private + common_total)
for u in units:
    u["title_m2"] = (u["interior_m2"] + u["balcony_avg"]) / (1 - common_ratio)
    u["title_ping"] = ping(u["title_m2"])
sellable_ping = ping(residential_private + common_total)
parking_ping_each = ping(parking_total / F["parking"]["total"])


# ---------------------------------------------------------------- SVG helpers
def bullet(label: str, value: float, vmax: float, limit: float | None, limit_label: str,
           unit: str = "%", base: float | None = None, base_label: str = "", note: str = "") -> str:
    W, H, x0, x1 = 640, 64, 150, 610
    sx = lambda v: x0 + (x1 - x0) * v / vmax
    parts = [f'<svg viewBox="0 0 {W} {H}" class="bullet" role="img" aria-label="{label} {value}{unit}">',
             f'<text x="0" y="27" class="b-label">{label}</text>',
             f'<text x="0" y="45" class="b-note">{note}</text>',
             f'<rect x="{x0}" y="16" width="{x1 - x0}" height="22" rx="4" class="b-track"/>']
    if base is not None:
        parts.append(f'<rect x="{x0}" y="16" width="{sx(base) - x0:.1f}" height="22" rx="4" class="b-base"/>')
    parts.append(f'<rect x="{x0}" y="21" width="{sx(value) - x0:.1f}" height="12" rx="4" class="b-val"/>')
    if base is not None:
        parts.append(f'<text x="{sx(base) - 4:.1f}" y="56" text-anchor="end" class="b-tick">{base_label}</text>')
    if limit is not None:
        parts.append(f'<line x1="{sx(limit):.1f}" x2="{sx(limit):.1f}" y1="10" y2="44" class="b-limit"/>')
        parts.append(f'<text x="{sx(limit):.1f}" y="58" text-anchor="middle" class="b-tick">{limit_label}</text>')
    parts.append(f'<text x="{min(sx(value) + 6, x1 - 2):.1f}" y="12" text-anchor="{"start" if sx(value) < x1 - 80 else "end"}" class="b-value">{value:.2f}{unit}</text>')
    parts.append("</svg>")
    return "".join(parts)


def stack_svg() -> str:
    rows = [
        ("屋突三層", "設備間（水箱）", 99.76, "roof"),
        ("屋突二層", "設備空間", 99.76, "roof"),
        ("屋突一層", "樓梯間／屋頂平台", 99.76, "roof"),
    ]
    for fl in range(12, 1, -1):
        rows.append((f"{fl}F", "A1・A2・B1・B2　4 戶", 378.48, "res"))
    rows += [("1F", "汽車 23 位＋大廳", 813.95, "park"),
             ("B1", "汽車 30 位＋機電", 1360.52, "park")]
    # viewBox sized for a ~110 mm column so 11px text prints at ~8 pt
    W, rowh, gap, top = 420, 16, 3, 6
    cx, maxw = 112, 156
    H = top + len(rows) * (rowh + gap) + 6
    out = [f'<svg viewBox="0 0 {W} {H}" class="stack" role="img" aria-label="樓層量體示意">']
    for i, (fl, use, area, kind) in enumerate(rows):
        y = top + i * (rowh + gap)
        w = max(12, maxw * area / 1360.52)
        x = cx - w / 2
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{rowh}" rx="3" class="s-{kind}"/>')
        out.append(f'<text x="0" y="{y + 12}" class="s-fl">{fl}</text>')
        if kind != "res":
            out.append(f'<text x="200" y="{y + 12}" class="s-use">{use}</text>')
            out.append(f'<text x="{W}" y="{y + 12}" text-anchor="end" class="s-area">{area:,.2f} ㎡</text>')
        if fl == "7F":
            out.append(f'<text x="200" y="{y + 12}" class="s-use s-strong">標準層 ×11　44 戶</text>')
            out.append(f'<text x="{W}" y="{y + 12}" text-anchor="end" class="s-area">每層 378.48 ㎡</text>')
    gl_y = top + 15 * (rowh + gap) - gap / 2
    out.append(f'<line x1="0" x2="{W}" y1="{gl_y}" y2="{gl_y}" class="s-gl"/>')
    out.append("</svg>")
    return "".join(out)


def unit_bars() -> str:
    W, H, x0 = 330, 146, 86
    vmax = 46.0
    sx = lambda v: (W - x0 - 64) * v / vmax
    out = [f'<svg viewBox="0 0 {W} {H}" class="ubars" role="img" aria-label="各戶室內與預估權狀坪數">']
    for i, u in enumerate(sorted(units, key=lambda u: u["interior_m2"])):
        y = 6 + i * 35
        out.append(f'<text x="0" y="{y + 15}" class="u-name">{u["code"]}｜{u["layout"]}</text>')
        out.append(f'<rect x="{x0}" y="{y}" width="{sx(u["title_ping"]):.1f}" height="20" rx="4" class="u-title"/>')
        out.append(f'<rect x="{x0}" y="{y + 4}" width="{sx(u["interior_ping"]):.1f}" height="12" rx="4" class="u-int"/>')
        out.append(f'<text x="{x0 + sx(u["interior_ping"]) - 6:.1f}" y="{y + 14}" text-anchor="end" class="u-in">{u["interior_ping"]:.1f}</text>')
        out.append(f'<text x="{x0 + sx(u["title_ping"]) + 6:.1f}" y="{y + 15}" class="u-out">≈{u["title_ping"]:.1f} 坪</text>')
    out.append("</svg>")
    return "".join(out)


def composition_bar() -> str:
    segs = [("住宅專有（主建物＋陽台）", residential_private, "c1"),
            ("共用部分（不含車位）", common_total, "c2"),
            ("停車相關（1F＋B1）", parking_total, "c3")]
    W, x0, x1 = 640, 0, 640
    tot = sum(s[1] for s in segs)
    out = [f'<svg viewBox="0 0 {W} 74" class="comp" role="img" aria-label="總面積組成">']
    x = x0
    for i, (name, v, c) in enumerate(segs):
        w = (x1 - x0) * v / tot
        out.append(f'<rect x="{x + 1:.1f}" y="4" width="{w - 2:.1f}" height="24" rx="4" class="{c}"/>')
        lx = i * 218  # legend in fixed columns so a narrow segment never collides
        out.append(f'<rect x="{lx}" y="40" width="10" height="10" rx="2" class="{c}"/>')
        out.append(f'<text x="{lx + 15}" y="49" class="cp-name">{name}</text>')
        out.append(f'<text x="{lx + 15}" y="67" class="cp-val">{v:,.0f} ㎡（{v / tot * 100:.0f}%）</text>')
        x += w
    out.append("</svg>")
    return "".join(out)


def gantt() -> str:
    # month columns Nov-2026 … Jun-2027, then a compressed long-tail column
    months = ["2026/11", "12", "2027/01", "02", "03", "04", "05", "06", "07 →"]
    W, x0, colw = 680, 196, 54
    start_day = 0  # 2026-11-01
    days_in = [30, 31, 31, 28, 31, 30, 31, 30, 40]
    cum = [0]
    for d in days_in:
        cum.append(cum[-1] + d)

    def dx(m_idx: int, day: int) -> float:
        return x0 + colw * (m_idx + day / days_in[m_idx])

    def date_x(s: str) -> float:  # "2026-11-02"
        y, m, d = (int(t) for t in s.split("-"))
        idx = (y - 2026) * 12 + m - 11
        idx = min(idx, 8)
        return dx(idx, d - 1)

    bars = [
        ("0", "合作確認・資料蒐集・踏勘", "2026-11-02", "2026-11-15", "p0"),
        ("1", "市調・定位・價格策略", "2026-11-09", "2026-12-13", "p1"),
        ("2", "案名・品牌・主視覺・文案合規", "2026-11-30", "2027-01-10", "p2"),
        ("3", "銷售工具：3D／說明書／網站", "2026-12-14", "2027-03-07", "p3"),
        ("3b", "接待中心・樣品屋（設計→施工）", "2026-12-21", "2027-03-14", "p3"),
        ("4", "潛銷（A 軌：搶春節返鄉檔）", "2027-01-25", "2027-03-07", "p4"),
        ("5", "公開強銷", "2027-03-08", "2027-06-30", "p5"),
        ("6", "續銷：開工→結構體→封頂", "2027-07-01", "2027-08-09", "p6"),
    ]
    rowh, top = 30, 46
    H = top + len(bars) * rowh + 52
    out = [f'<svg viewBox="0 0 {W} {H}" class="gantt" role="img" aria-label="銷售企劃時程">']
    for i, m in enumerate(months):
        x = x0 + i * colw
        out.append(f'<rect x="{x}" y="{top - 6}" width="{colw}" height="{len(bars) * rowh + 6}" class="{"g-col" if i % 2 == 0 else "g-col2"}"/>')
        out.append(f'<text x="{x + colw / 2}" y="{top - 14}" text-anchor="middle" class="g-month">{m}</text>')
    # Chinese New Year 2027 window
    cny = date_x("2027-02-06")
    out.append(f'<rect x="{cny - 6:.1f}" y="{top - 6}" width="16" height="{len(bars) * rowh + 6}" class="g-cny"/>')
    out.append(f'<text x="{cny + 2:.1f}" y="{top - 26}" text-anchor="middle" class="g-flag">春節 2/6</text>')
    for i, (no, name, s, e, cls) in enumerate(bars):
        y = top + i * rowh
        out.append(f'<text x="0" y="{y + 18}" class="g-no">{no}</text>')
        out.append(f'<text x="22" y="{y + 18}" class="g-name">{name}</text>')
        xs, xe = date_x(s), date_x(e)
        out.append(f'<rect x="{xs:.1f}" y="{y + 7}" width="{max(6, xe - xs):.1f}" height="16" rx="4" class="g-bar {cls}"/>')
    # gates
    gates = [("CP0", "2026-11-15"), ("CP1", "2026-12-13"), ("G1", "2027-01-22"), ("CP3", "2027-02-22"), ("CP4", "2027-05-03")]
    gy = top + len(bars) * rowh + 8
    for gname, d in gates:
        x = date_x(d)
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 6}" y2="{gy + 4}" class="g-gate"/>')
        out.append(f'<path d="M{x:.1f},{gy + 2} l6,8 l-6,8 l-6,-8 z" class="g-diamond{" g-legal" if gname == "G1" else ""}"/>')
        out.append(f'<text x="{x:.1f}" y="{gy + 32}" text-anchor="middle" class="g-gname">{gname}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- page content
CSS = (ROOT / "scripts" / "report.css").read_text(encoding="utf-8")

def page(title: str, kicker: str, body: str, no: str) -> str:
    return f"""
<section class="page">
  <header class="ph"><span class="ph-k">{kicker}</span><span class="ph-p">宜蘭市雙福段 768 地號 住宅新建工程｜建案合作前評估 {VERSION}</span></header>
  <h1 class="pt"><span class="pt-no">{no}</span>{title}</h1>
  {body}
  <footer class="pf"><span>璞域國際企劃｜建案合作前評估</span><span>{{PG}}</span></footer>
</section>"""


def build_cover() -> str:
    return f"""
<section class="page cover">
  <div class="cv-top">
    <div class="cv-brand">璞域國際企劃<br><span>建案企劃・品牌策略</span></div>
    <div class="cv-date">{REPORT_DATE}　{VERSION}</div>
  </div>
  <div class="cv-title">
    <p class="cv-k">建照圖說解析 × 銷售企劃合作建議</p>
    <h1>宜蘭市雙福段 768 地號<br>住宅新建工程</h1>
    <p class="cv-sub">地下 1 層・地上 12 層 RC 集合住宅｜44 戶｜53 汽車位</p>
  </div>
  <figure class="cv-fig"><img src="{img('elevation_pair.png')}" alt="建築立面（陰影檢討立面圖）"><figcaption>立面示意（取自請照圖「建築陰影面積檢討立面圖」，非完工實景）</figcaption></figure>
  <div class="cv-foot">
    <div><b>起造人</b>向信建設有限公司・瓏翔建設有限公司</div>
    <div><b>設計</b>林建隆建築師事務所</div>
    <div><b>本文件</b>建築基本資料分析、合作時程建議、資料需求清單</div>
  </div>
</section>"""


def build_body() -> str:
    pages = []
    u = {x["code"]: x for x in units}

    # ---- P2 Key takeaways
    kpis = [
        ("44", "戶", "2F–12F 每層 4 戶"),
        ("53", "汽車位", "B1 30＋1F 23，車位比 1.20"),
        ("507", "坪", "基地 1,676.29 ㎡"),
        ("2,141", "坪", "總樓地板＋陽台 7,076 ㎡"),
        ("43.05", "m", "簷高；層高 3.6 m"),
        ("215.9", "%", "容積率（含容移 603 ㎡）"),
    ]
    tiles = "".join(f'<div class="kpi"><div class="kpi-v">{v}<small>{unit}</small></div><div class="kpi-l">{l}</div></div>' for v, unit, l in kpis)
    body = f"""
<div class="kpis">{tiles}</div>
<p class="lead">一句話：<b>宜蘭市都計住宅區、12 層 44 戶的小規模電梯大樓，賣點是「全平面車位 1.2 倍、3.6 m 層高、清水模＋木格柵立面」；最大風險是公設賣點目前建立在二工（二次施工）圖上，廣告須先做合規切割。</b></p>
<ol class="takeaways">
  <li><b>量體已用滿：</b>容積率 215.93%（上限 216%，含容積移轉 603.46 ㎡），建蔽率 48.69%（上限 60%）。產品再放大的空間幾乎為零，企劃重點在「怎麼賣」而非「改量體」。{tag('實際')}</li>
  <li><b>產品組合兩房、三房各半：</b>A1／A2 兩房（室內約 20–21 坪）各 11 戶；B1 三房（約 24 坪）、B2 三房（約 32 坪）各 11 戶。預估權狀約 29–44 坪。{tag('實際')}{tag('示意')}</li>
  <li><b>車位是最強差異點：</b>53 位全為平面車位（無機械），比戶數多 9 位，可設計「雙車位戶」或單售車位策略。{tag('實際')}{tag('評估')}</li>
  <li><b>1F 幾乎全為停車層：</b>1F 813.95 ㎡ 中 699.92 ㎡ 為停車空間，大廳僅 72.36 ㎡（管委會空間）。門面感須靠入口、景觀與退縮 12.4 m 的前庭補強。{tag('實際')}{tag('評估')}</li>
  <li><b>二工家配圖與請照用途不一致：</b>屋突交誼廳、健身房、視聽間、B1 洗衣間等僅出現在「二工」圖層；對外廣告若直接使用，有公平交易法第 21 條不實廣告風險。{tag('實際')}{tag('評估')}</li>
  <li><b>時程取決於建照：</b>圖檔仍為「請照圖」（最後修改 2026/09/29）。建照核發＋預售契約備查完成前，不得刊登廣告或收訂。若能在 2027/01 下旬過關，建議搶 2027 春節返鄉檔潛銷。{tag('實際')}{tag('評估')}</li>
</ol>
<div class="card mt"><h3>建議下一步</h3>
<table class="data compact">
  <thead><tr><th>#</th><th>事項</th><th>期限</th><th>承接人</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>確認合作範疇、分工與報價</td><td>2026/11/06</td><td>建商負責人＋璞域負責人</td></tr>
    <tr><td>2</td><td>提供 P1 資料 8 項（見第 12 頁）</td><td>2026/11/13</td><td>建商專案窗口</td></tr>
    <tr><td>3</td><td>基地踏勘：交通、學區門牌、周邊景觀與嫌惡設施</td><td>2026/11/13</td><td>璞域專案經理</td></tr>
    <tr><td>4</td><td>二工清單確認會（建商、建築師、璞域三方）</td><td>2026/11/20</td><td>建商負責人＋建築師＋璞域企劃總監</td></tr>
    <tr><td>5</td><td>宜蘭市電梯大樓 24 個月實價登錄與競品盤點</td><td>2026/11/27</td><td>璞域企劃總監</td></tr>
  </tbody>
</table></div>
<div class="legend-tags">標註說明：{tag('實際')} 取自請照圖說數據　{tag('示意')} 依假設推算，數字會隨建商正式資料修正　{tag('評估')} 企劃判斷</div>
"""
    pages.append(page("Key Takeaways", "01 摘要", body, "01"))

    # ---- P3 Basic data
    rows = F["basic_info"]
    trs = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    body = f"""
<div class="grid-2">
  <div>
    <table class="kv">{trs}</table>
    <p class="src">資料來源：請照圖圖框、法規檢討、面積計算表。{tag('實際')}</p>
  </div>
  <div>
    <figure class="fig"><img src="{img('cadastral_layout.png')}" alt="地籍配置圖"><figcaption>地籍配置圖（北向朝上）：基地西北側臨宜興路三段（12M，已開闢），另見「30M」道路標註，需確認是否為計畫道路。</figcaption></figure>
    <div class="callout"><b>待確認</b>　①建照字號與核發日　②「30M」標註道路之計畫寬度與開闢時程　③雨水滯洪檢討使用基地面積 1,679.12 ㎡，與土地使用強度 1,676.29 ㎡ 不一致　④學區（周邊資料指向新生國小／宜蘭國中，需以門牌向教育處確認）</div>
  </div>
</div>"""
    pages.append(page("案件基本資料", "02 基本資料", body, "02"))

    # ---- P4 Land-use intensity
    a = F["areas"]
    bl = "".join([
        bullet("建蔽率", 48.69, 100, 60, "法定 60%", note="816.24／1,676.29 ㎡"),
        bullet("容積率", 215.93, 250, 216, "上限 216%", base=180, base_label="基準 180%", note="3,619.55 ㎡（含容移）"),
        bullet("地下室開挖率", 81.16, 100, None, "", note="1,360.52 ㎡"),
        bullet("法定空地綠覆率", 53.39, 100, 50, "下限 50%", note="喬木 21 株（光臘樹）"),
    ])
    body = f"""
<div class="card">{bl}</div>
<div class="grid-2 mt">
  <div>
    <table class="data">
      <thead><tr><th>項目</th><th class="r">㎡</th><th class="r">坪</th></tr></thead>
      <tbody>
        <tr><td>基地面積</td><td class="r">{a['site_m2']:,.2f}</td><td class="r">{ping(a['site_m2']):,.2f}</td></tr>
        <tr><td>建築面積</td><td class="r">{a['building_m2']:,.2f}</td><td class="r">{ping(a['building_m2']):,.2f}</td></tr>
        <tr><td>法定空地（實設）</td><td class="r">860.05</td><td class="r">{ping(860.05):,.2f}</td></tr>
        <tr><td>容積樓地板</td><td class="r">3,619.55</td><td class="r">{ping(3619.55):,.2f}</td></tr>
        <tr><td>　其中容積移轉移入</td><td class="r">603.46</td><td class="r">{ping(603.46):,.2f}</td></tr>
        <tr><td>總樓地板面積</td><td class="r">{a['total_floor_m2']:,.2f}</td><td class="r">{ping(a['total_floor_m2']):,.2f}</td></tr>
        <tr><td>陽台面積合計</td><td class="r">{a['balcony_total_m2']:,.2f}</td><td class="r">{ping(a['balcony_total_m2']):,.2f}</td></tr>
        <tr class="sum"><td>合計（總樓地板＋陽台）</td><td class="r">{grand_total:,.2f}</td><td class="r">{ping(grand_total):,.2f}</td></tr>
      </tbody>
    </table>
    <p class="src">容積移轉許可：115/02/11 府建管字第 1150026888 號。雨水滯洪 126.17 m³（法定 75.56 m³）。{tag('實際')}</p>
  </div>
  <div>
    <figure class="fig"><img src="{img('site_landscape.png')}" alt="一層綠化平面圖"><figcaption>一層綠化平面圖：斜邊為宜興路三段側，喬木沿斜邊與東側帶狀配置；塔樓距建築線 12.405 m。</figcaption></figure>
    <div class="callout ok"><b>企劃解讀</b>　容積已用到 99.97%，基地多出的面積轉為 1F 停車與前庭綠帶。「退縮 12 公尺、綠覆 53%」可包裝為入口前庭，是 1F 無店面、無挑高大廳的補償型賣點。{tag('評估')}</div>
  </div>
</div>"""
    pages.append(page("土地使用強度", "03 量體與法規", body, "03"))

    # ---- P5 Massing & floors
    body = f"""
<div class="grid-2 g-6040">
  <div class="card">{stack_svg()}<p class="src">寬度依各層樓地板面積等比例繪製；虛線為地面線（GL ±0）。{tag('實際')}</p></div>
  <figure class="fig tall"><img src="{img('elevation_south.png')}" alt="南向立面圖"><figcaption>南向立面圖（請照圖 A3-01）。外牆：深灰耐候塗料、清水模、木色耐候塗料、木色烤漆鋁格柵；欄杆 H=120 cm 清／黑玻璃。</figcaption></figure>
</div>
<table class="data mt">
  <thead><tr><th>項目</th><th>內容</th><th>企劃意義</th></tr></thead>
  <tbody>
    <tr><td>層高</td><td>各層 3.6 m（立面標註 360 cm）；屋突各 3.0 m；排煙室天花 305 cm {tag('實際')}</td><td>宜蘭市大樓常見 3.2–3.4 m，3.6 m 層高可作為空間感賣點，需確認室內淨高與梁深 {tag('評估')}</td></tr>
    <tr><td>垂直動線</td><td>電梯 2 部（緊急昇降機、無障礙），各 12 人份 90 m/min；戶外安全梯 2 座 {tag('實際')}</td><td>每部電梯服務 22 戶，候梯時間友善；戶外梯自然通風 {tag('評估')}</td></tr>
    <tr><td>結構與基礎</td><td>RC 造；筏式基礎（深 1.7 m，兼雨水滯洪）；含地質改良、開挖支撐與觀測系統圖 {tag('實際')}</td><td>宜蘭市地質需改良，可轉為「看得見的結構安全」說明素材 {tag('評估')}</td></tr>
    <tr><td>隔音</td><td>分戶樓板採鎖扣式隔音地板（衝擊音合規）；電梯井與居室分隔牆 RC 20 cm {tag('實際')}</td><td>大樓客最常問的生活品質題，可在說明書單獨成頁 {tag('評估')}</td></tr>
  </tbody>
</table>"""
    pages.append(page("量體與樓層配置", "03 量體與法規", body, "04"))

    # ---- P6 Typical floor
    body = f"""
<figure class="fig plan"><img src="{img('plan_typical_furnished.png')}" alt="四、八、十二層平面圖（家具配置）"><figcaption>四、八、十二層平面（1/100 二工家配圖）。平面上方約為西向（指北針旋轉 285.6°，即北方朝圖面右側略偏上）。家具配置僅示意，對外使用前須依請照圖核對。</figcaption></figure>
<table class="data mt">
  <thead><tr><th>戶別</th><th>格局</th><th class="r">室內 ㎡</th><th class="r">室內坪</th><th class="r">陽台 ㎡<br><small>(11 層平均)</small></th><th class="r">預估權狀坪<br><small>{tag('示意')}</small></th><th>主要採光面 {tag('評估')}</th><th class="r">戶數</th></tr></thead>
  <tbody>
    {''.join(f"<tr><td><b>{x['code']}</b></td><td>{x['layout']}</td><td class='r'>{x['interior_m2']:.2f}</td><td class='r'>{x['interior_ping']:.2f}</td><td class='r'>{x['balcony_avg']:.2f}</td><td class='r'>≈{x['title_ping']:.1f}</td><td>{x['facing']}</td><td class='r'>11</td></tr>" for x in units)}
  </tbody>
</table>
<p class="src">室內面積取自面積計算表（A1 含 0.96 ㎡ 計入部分）{tag('實際')}；預估權狀 =（室內＋陽台）÷（1−公設比 {common_ratio * 100:.1f}%），公設比依下頁假設推算，正式數字以建商面積分配表為準。{tag('示意')}</p>"""
    pages.append(page("標準層與戶型", "04 產品", body, "05"))

    # ---- P7 Product reading
    body = f"""
<div class="grid-2">
  <div class="card"><h3>各戶坪數：室內 vs 預估權狀</h3>{unit_bars()}
    <div class="mini-legend"><span class="sw sw-int"></span>室內（主建物）坪 {tag('實際')}　<span class="sw sw-title"></span>預估權狀坪 {tag('示意')}</div></div>
  <div class="card"><h3>產品組合</h3>
    <table class="data compact">
      <tr><td>兩房（A1、A2）</td><td class="r">22 戶</td><td class="r">50%</td></tr>
      <tr><td>三房（B1、B2）</td><td class="r">22 戶</td><td class="r">50%</td></tr>
      <tr><td>最小／最大室內</td><td class="r" colspan="2">20.2 坪／32.1 坪</td></tr>
      <tr><td>衛浴</td><td class="r" colspan="2">四種戶型皆 2 衛</td></tr>
    </table>
    <p class="note">A2 為單面採光、A1／A2 主面朝西，西曬需靠遮陽板（3、5、7、9、11 層設透空遮陽板）、格柵與玻璃規格回應。B2 為三面採光邊間，是全案標竿戶。{tag('評估')}</p>
  </div>
</div>
<div class="card mt"><h3>總面積組成（7,076.27 ㎡）</h3>{composition_bar()}
  <p class="src">總量 {tag('實際')}；拆分 {tag('示意')}：B1 停車以法規檢討採用之每車 40 ㎡ × 30 位 = 1,200 ㎡ 估算，其餘 B1 面積視為共用。據此推得：可售住宅約 <b>{sellable_ping:,.0f} 坪</b>、公設比約 <b>{common_ratio * 100:.1f}%</b>（車位另計）、車位平均權狀約 <b>{parking_ping_each:.1f} 坪</b>。若車道與 B1 機房改按戶分攤，公設比將上升，需以建商面積分配表確認。</p>
</div>
<div class="grid-2 mt">
  <div class="callout ok"><b>可主打</b>　① 全平面車位 53 位、車位比 1.2　② 3.6 m 層高　③ 四戶一層、兩部電梯　④ 清水模＋木格柵立面　⑤ 退縮 12.4 m 綠帶前庭 {tag('評估')}</div>
  <div class="callout warn"><b>需補強</b>　① 1F 無店面、大廳僅 72 ㎡　② A1／A2 西向　③ 合法公設少，賣點依賴二工　④ 未見機車位規劃　⑤ 多出 9 個車位的定價策略 {tag('評估')}</div>
</div>"""
    pages.append(page("戶型解讀與面積結構", "04 產品", body, "06"))

    # ---- P8 Parking & common
    body = f"""
<figure class="fig plan"><img src="{img('plan_1F.png')}" alt="一層平面圖"><figcaption>一層平面（1/100 二工家配圖）：法定／自設汽車位 31–53 號、單車道坡道（長 22.1 m，坡度 1/6.5）通往 B1、管委會空間規劃為接待大廳與包裹區。</figcaption></figure>
<div class="grid-2 mt">
  <table class="data">
    <thead><tr><th>停車</th><th class="r">數量</th></tr></thead>
    <tbody>
      <tr><td>B1 汽車位（防空避難室兼停車）</td><td class="r">30</td></tr>
      <tr><td>1F 汽車位</td><td class="r">23</td></tr>
      <tr class="sum"><td>合計（法定 26＋自設 27）</td><td class="r">53</td></tr>
      <tr><td>其中無障礙車位（350×600 cm）</td><td class="r">2</td></tr>
      <tr><td>車位尺寸</td><td class="r">250×550／230×550／250×600</td></tr>
      <tr><td>機車位</td><td class="r">圖說未見</td></tr>
    </tbody>
  </table>
  <table class="data">
    <thead><tr><th>公共空間（請照用途）</th><th class="r">面積</th></tr></thead>
    <tbody>
      <tr><td>1F 管委會空間</td><td class="r">72.36 ㎡</td></tr>
      <tr><td>1F 排煙室兼梯廳／電梯／安全梯／管道</td><td class="r">36.95 ㎡</td></tr>
      <tr><td>2F–12F 每層梯廳／電梯／安全梯／管道</td><td class="r">45.35 ㎡</td></tr>
      <tr><td>屋突一～三層（樓梯間、設備空間）</td><td class="r">99.76 ㎡ ×3</td></tr>
      <tr><td>B1 消防及發電機房、電信室、台電配電場所</td><td class="r">—</td></tr>
      <tr><td>2F 露台（1F 停車層屋頂）</td><td class="r">—</td></tr>
    </tbody>
  </table>
</div>
<p class="src">數量與尺寸 {tag('實際')}。車位比 53／44 = 1.20；宜蘭市大樓少見全平面車位配置，建議車位定價與戶別綁售策略於定價階段一併決定。{tag('評估')}</p>"""
    pages.append(page("停車與公共空間", "05 停車・公設", body, "07"))

    # ---- P9 二工 compliance
    rows = F["secondary_construction"]
    trs = "".join(
        f"<tr><td><b>{r['where']}</b></td><td>{r['permit']}</td><td>{r['plan']}</td><td><span class='lvl lvl-{r['level_cls']}'>{r['level']}</span></td><td>{r['advice']}</td></tr>"
        for r in rows)
    body = f"""
<p class="lead">圖檔另有「29_二工」圖層與 1/100「二工家配」平面組，內容與請照用途不同。以下逐項比對，作為廣告與銷售話術的合規底線。</p>
<table class="data risk">
  <thead><tr><th>位置</th><th>請照圖用途 {tag('實際')}</th><th>二工家配圖標示 {tag('實際')}</th><th>風險 {tag('評估')}</th><th>建議做法 {tag('評估')}</th></tr></thead>
  <tbody>{trs}</tbody>
</table>
<div class="grid-2 mt">
  <figure class="fig"><img src="{img('plan_roof1_furnished.png')}" alt="屋突一層二工家配"><figcaption>屋突一層（二工家配）：中央室內空間標示為「交誼廳／媽媽教室」，請照用途為樓梯間／屋頂平台。</figcaption></figure>
  <div class="callout risk"><b>法規依據與實務</b>　公平交易法第 21 條禁止對商品為虛偽不實或引人錯誤之表示。公平會歷年處分案中，將陽台、機電空間、露臺、水箱間等以室內空間表示於家具配置圖者，曾分別處 40–50 萬元罰鍰；另有「廣告坪數含二次施工違章建築」之處分。<br><br><b>本案建議</b>　①對外家配圖一律以請照圖為底，二工內容不入廣告　②屋突公設若要成為賣點，先評估變更設計或改以合法空間承載　③銷售人員話術與書面一致，不口頭承諾二工　④本頁法律判斷需專業人士最終確認。</div>
</div>"""
    pages.append(page("二工（二次施工）合規盤點", "06 風險", body, "08"))

    # ---- P10 Assessment
    body = f"""
<div class="grid-3">
  <div class="card col ok"><h3>優勢</h3><ul>
    <li>宜蘭市都市計畫住宅區，臨 12M 已開闢道路</li>
    <li>44 戶小規模、四戶一層、兩部電梯</li>
    <li>53 個平面汽車位，車位比 1.2</li>
    <li>層高 3.6 m、戶外安全梯、分戶隔音樓板</li>
    <li>清水模＋木色鋁格柵立面，識別度高</li>
    <li>塔樓退縮 12.4 m，喬木 21 株的前庭</li></ul></div>
  <div class="card col warn"><h3>待補強</h3><ul>
    <li>1F 以停車為主，入口門面需設計加值</li>
    <li>A1／A2 西向、A2 單面採光</li>
    <li>合法公設僅管委會空間與屋頂平台</li>
    <li>機車位、自行車位未見規劃</li>
    <li>B1 洗衣間、垃圾集中場位置需與法定用途核對</li>
    <li>三角形基地斜邊，需景觀轉化</li></ul></div>
  <div class="card col risk"><h3>風險</h3><ul>
    <li>二工內容入廣告的公平法風險</li>
    <li>建照仍在請照階段，預售時程受核照影響</li>
    <li>契約備查前刊登廣告或收訂即違規（平均地權條例）</li>
    <li>宜蘭縣 2025 首季預售屋解約量居全國第五（媒體報導），價格需保守</li>
    <li>地質改良與開挖支撐增加工期與成本變數</li></ul></div>
</div>
<div class="card mt"><h3>建議定位假說（待市調驗證）{tag('評估')}</h3>
<table class="data compact">
  <tr><th>客群假說</th><th>對應戶型</th><th>需要驗證的數據</th></tr>
  <tr><td>宜蘭市在地首購／小家庭（雙薪）</td><td>A1、A2 兩房</td><td>宜蘭市 2 房大樓實登總價帶、首購貸款成數</td></tr>
  <tr><td>在地換屋（透天換電梯）</td><td>B1、B2 三房＋車位</td><td>宜蘭市透天中古成交量、換屋客年齡層</td></tr>
  <tr><td>返鄉族／雙北置產</td><td>B2 邊間、A1 角戶</td><td>國道 5 號通勤客比例、春節檔來客結構</td></tr>
</table></div>"""
    pages.append(page("產品力評估", "07 評估", body, "09"))

    # ---- P11 Timeline
    body = f"""
<div class="card">{gantt()}</div>
<div class="grid-2 mt">
  <div class="callout"><b>A 軌（建議）</b>　建照於 2026/12 核發 → 2027/01 下旬完成預售契約與建案資訊備查（G1）→ 1/25 起潛銷，覆蓋 2027 春節返鄉人潮 → 3/8 公開。</div>
  <div class="callout warn"><b>B 軌（建照延後）</b>　建照晚於 2026/12/31 → 潛銷順延至清明連假後（2027/04 中），公開 2027/05–08；Phase 0–3 照常推進，銷售工具提前完成可縮短等待。</div>
</div>
<table class="data mt compact">
  <thead><tr><th>檢查點</th><th>時間 {tag('示意')}</th><th>通過條件 {tag('示意')}</th><th>未通過的動作</th><th>承接人</th></tr></thead>
  <tbody>
    <tr><td>CP0 資料到位</td><td>2026/11/15</td><td>P1 資料到位 ≥ 80%</td><td>暫停 Phase 1 以外工作，重排時程</td><td>璞域專案經理</td></tr>
    <tr><td>CP1 定位定價共識</td><td>2026/12/13</td><td>客群、產品組合、價格區間三項書面確認</td><td>視覺製作延後開工</td><td>建商負責人＋璞域企劃總監</td></tr>
    <tr><td>G1 法規閘門</td><td>2027/01/22</td><td>建照核發＋預售契約與建案資訊備查（委託代銷者另需代銷備查）</td><td>不得刊登任何廣告、不收訂</td><td>建商法務／地政士</td></tr>
    <tr><td>CP3 潛銷檢查</td><td>潛銷第 4 週</td><td>有效來客 ≥ 100 組、意向登記 ≥ 25 組</td><td>調整價格帶、付款條件或主打戶型</td><td>璞域企劃總監</td></tr>
    <tr><td>CP4 公開檢查</td><td>公開第 8 週</td><td>成交 ≥ 13 戶（30%）</td><td>啟動價格與通路檢討</td><td>建商負責人＋璞域企劃總監</td></tr>
  </tbody>
</table>"""
    pages.append(page("銷售企劃時程建議", "08 時程", body, "10"))

    # ---- P12 Deliverables
    body = """
<table class="data">
  <thead><tr><th>階段</th><th>主要交付物</th><th>璞域承接人</th><th>建商配合</th></tr></thead>
  <tbody>
    <tr><td><b>0 合作確認</b><br><small>11/02–11/15</small></td><td>合作範疇與分工表、資料需求清單追蹤、基地踏勘紀錄（交通、學區、嫌惡設施、景觀）</td><td>專案經理</td><td>專案窗口提供 P1 資料</td></tr>
    <tr><td><b>1 市調定位</b><br><small>11/09–12/13</small></td><td>宜蘭市電梯大樓 24 個月實價登錄分析、競品 10 案比較、客群假說驗證、價格策略三情境、車位定價、產品微調建議</td><td>企劃總監</td><td>決策者參與定位會議</td></tr>
    <tr><td><b>2 品牌視覺</b><br><small>11/30–01/10</small></td><td>案名提案、主視覺、字標、文案庫、廣告合規檢核表（二工切割、示意圖標示）</td><td>設計主管＋文案</td><td>案名與主視覺拍板</td></tr>
    <tr><td><b>3 銷售工具</b><br><small>12/14–03/07</small></td><td>3D 外觀與公設示意、合規版家配圖、全案說明書、建材設備表、網站／Landing Page、DM、影片腳本</td><td>設計主管</td><td>建築 3D 模型、建材表、工務確認</td></tr>
    <tr><td><b>3b 接待中心</b><br><small>12/21–03/14</small></td><td>接待中心選址比較、動線與樣品屋規劃、施工監造</td><td>專案經理</td><td>選址決策、預算核定</td></tr>
    <tr><td><b>G1 法規閘門</b><br><small>≤ 01/22</small></td><td>廣告素材合規總檢、銷售話術手冊</td><td>企劃總監</td><td>建照、契約備查、履約保證、代銷備查</td></tr>
    <tr><td><b>4–5 潛銷・公開</b><br><small>01/25–06/30</small></td><td>媒體投放計畫與週報、來客分析、去化與價格追蹤、CP3／CP4 檢討報告</td><td>企劃總監＋數位</td><td>銷售現場、成交資料回傳</td></tr>
    <tr><td><b>6 續銷</b><br><small>2027/07 →</small></td><td>工程進度行銷（開工、結構體、封頂）、餘屋策略</td><td>專案經理</td><td>工程節點照片與資訊</td></tr>
  </tbody>
</table>
<div class="callout mt"><b>工期提醒</b>　地下 1 層、地上 12 層 RC，含地質改良與開挖支撐，一般工期約 30–36 個月（自開工起算），成屋交屋約落在 2030 年。續銷期長，建議以工程節點作為行銷節奏，並預留價格調整機制。<span class="tag t-judge">評估</span></div>"""
    pages.append(page("階段交付物與分工", "08 時程", body, "11"))

    # ---- P13-14 data request
    reqs = F["data_requests"]

    def req_table(items):
        return "<table class='data req'><thead><tr><th>#</th><th>資料項目</th><th>用途</th><th>格式</th><th>建商承接人</th></tr></thead><tbody>" + "".join(
            f"<tr><td>{r['no']}</td><td><b>{r['item']}</b></td><td>{r['purpose']}</td><td>{r['format']}</td><td>{r['owner']}</td></tr>" for r in items) + "</tbody></table>"

    p1 = [r for r in reqs if r["priority"] == "P1"]
    p2 = [r for r in reqs if r["priority"] == "P2"]
    p3 = [r for r in reqs if r["priority"] == "P3"]
    body = f"""
<p class="lead">依急迫性分三批。<b>P1 一週內</b>（決定定位與時程）、<b>P2 三週內</b>（製作銷售工具）、<b>P3 公開前</b>（契約與說明書）。另附可編輯追蹤表（試算表）。</p>
<h2 class="sec"><span class="pri p1">P1</span>一週內：定位與時程的前提</h2>
{req_table(p1)}"""
    pages.append(page("希望建商提供的資料（一）", "09 資料需求", body, "12"))
    body = f"""
<h2 class="sec"><span class="pri p2">P2</span>三週內：銷售工具製作</h2>
{req_table(p2)}
<h2 class="sec mt"><span class="pri p3">P3</span>公開前：契約、說明書與售後</h2>
{req_table(p3)}"""
    pages.append(page("希望建商提供的資料（二）", "09 資料需求", body, "13"))

    # ---- P15 Appendix
    sheets = "、".join(F["sheet_index"])
    body = f"""
<div class="grid-2">
  <div class="card"><h3>資料來源與解析方式</h3>
    <ul class="plain">
      <li>來源檔：建商提供之請照圖 DWG（2000 版格式，16.2 MB），建立日 2025/08/29，最後修改 2026/09/29。</li>
      <li>解析：讀取 70,048 個模型空間物件與 2,426 個圖塊，擷取 12,080 筆文字（含屬性），依圖層與座標比對樓層。</li>
      <li>平面、立面圖片由向量圖直接輸出，未經重繪；家具與二工內容依原圖層呈現。</li>
      <li>方位依一層平面圖指北針圖塊旋轉角（285.6°）推算，並與地籍配置圖之道路走向交叉核對。</li>
      <li>市場數據（宜蘭縣預售屋解約量）為媒體報導，未納入任何價格推算。</li>
    </ul></div>
  <div class="card"><h3>圖說內容索引（共 {len(F['sheet_index'])} 類）</h3><p class="small">{sheets}</p></div>
</div>
<div class="card mt"><h3>本文件的限制</h3>
  <ul class="plain">
    <li>本文件以單一請照圖檔為基礎，未取得建照、面積分配表、建材表與價格資料；所有 {tag('示意')} 數字待建商資料到位後於 v1.1 修正。</li>
    <li>二工合規與預售屋法規相關段落為企劃端風險提示，法律結論需專業人士（律師／地政士）最終確認。</li>
    <li>立面與平面圖片皆為設計圖面，非完工實景；對外使用時須標示「示意」。</li>
  </ul></div>"""
    pages.append(page("附錄：資料來源與限制", "10 附錄", body, "14"))

    html = build_cover() + "".join(pages)
    total = len(pages) + 1
    for n in range(2, total + 1):
        html = html.replace("{PG}", f"{n} / {total}", 1)
    return f"""<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><title>Shuangfu768 Building Analysis</title>
<style>{CSS}</style></head><body>{html}</body></html>"""


if __name__ == "__main__":
    BUILD.mkdir(exist_ok=True)
    (BUILD / "report.html").write_text(build_body(), encoding="utf-8")
    print(f"common ratio {common_ratio:.4f}  sellable {sellable_ping:.1f} ping  parking each {parking_ping_each:.2f} ping")
    for x in units:
        print(x["code"], round(x["interior_ping"], 2), round(x["balcony_avg"], 2), round(x["title_ping"], 1))
