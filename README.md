# 宜蘭市雙福段 768 地號 住宅新建工程 — 建案合作前評估

> **起造人**：向信建設有限公司・瓏翔建設有限公司
> **設計**：林建隆建築師事務所
> **規模**：RC 地下 1 層、地上 12 層、屋突 3 層｜H-2 集合住宅 44 戶｜汽車位 53
> **企劃**：璞域國際企劃
> **最後整理**：2026-10-27（v1.0）

---

## 0. 一分鐘速覽

| 項目 | 結論 |
|---|---|
| 基地 | 1,676.29 ㎡（507 坪），都市計畫住宅區，臨宜興路三段 12M |
| 強度 | 建蔽 48.69%／容積 215.93%（含容移 603.46 ㎡，已用滿） |
| 產品 | A1、A2 兩房（室內約 20–21 坪）＋B1、B2 三房（約 24、32 坪），各 11 戶 |
| 車位 | 53 個全平面（B1 30＋1F 23），車位比 1.20 |
| 可售量體 | 住宅約 1,566 坪、公設比約 20.7%（車位另計）【示意】 |
| 最大風險 | 屋突交誼廳、健身房、視聽間等只存在於「二工」圖層，廣告須做合規切割 |
| 時程關鍵 | 建照核發＋預售契約備查（G1）；A 軌搶 2027 春節返鄉檔潛銷 |

## 1. 交付物（reports/）

| 檔案 | 說明 |
|---|---|
| `Shuangfu768_Building_Analysis_Proposal_v1.0.pdf` | A4 15 頁：建築基本資料分析、二工合規盤點、銷售企劃時程、資料需求清單 |
| `Shuangfu768_Data_Request_Tracker_v1.0.xlsx` | 可編輯追蹤表：資料需求（含 P1 到位率）、檢查點、二工盤點 |
| `dwg-extraction-shuangfu768.md` | DWG 解析紀錄與數據來源 |

## 2. 資料夾結構

```
├── reports/            交付物（PDF、試算表、解析紀錄）
├── assets/drawings/    由 DWG 向量直接輸出的平面、立面、配置圖
├── data/
│   ├── extracted_facts.json   PDF 與追蹤表共用的結構化數據
│   └── views.json             各圖片的世界座標裁切範圍
└── scripts/
    ├── dwg_to_json.mjs        DWG → JSON（libredwg WebAssembly）
    ├── dwg_to_svg.mjs         DWG → 全圖 SVG
    ├── render_views.mjs       依 views.json 輸出 PNG
    ├── extract_texts.py       擷取所有文字與屬性
    ├── build_report.py        產生報告 HTML（圖表為內嵌 SVG）
    ├── report.css             報告版型
    ├── print_pdf.mjs          HTML → A4 PDF
    └── build_tracker.py       產生資料需求追蹤表
```

## 3. 重建交付物

需中文字型（`fonts-noto-cjk`）、Node 20+、Playwright（Chromium）、Python 3 + openpyxl。

```bash
python3 scripts/build_report.py      # build/report.html
node scripts/print_pdf.mjs           # reports/Shuangfu768_Building_Analysis_Proposal_v1.0.pdf
python3 scripts/build_tracker.py     # reports/Shuangfu768_Data_Request_Tracker_v1.0.xlsx
```

重新解析 DWG（原始圖檔不入版控）：見 `reports/dwg-extraction-shuangfu768.md` 第 8 節。

## 4. 已知缺口

| 缺口 | 補救 | 承接人 |
|---|---|---|
| 建照核發狀態 | 建商提供字號或審查進度 | 建商專案窗口 |
| 面積分配表、公設比 | 建商與建築師提供，v1.1 修正示意數字 | 建商專案窗口＋建築師 |
| 宜蘭市電梯大樓實價登錄 | 內政部開放資料下載後分析（雲端環境無法直連政府端點） | 璞域企劃總監 |
| 二工合法化路徑 | 三方確認會 | 建商負責人＋建築師＋璞域企劃總監 |
| 學區、30M 道路 | 踏勘與門牌查詢 | 璞域專案經理 |

## 5. 版本紀錄

| 日期 | 版本 | 內容 |
|---|---|---|
| 2026-10-27 | v1.0 | 請照圖 DWG 解析、建築基本資料分析 PDF、資料需求追蹤表 |
