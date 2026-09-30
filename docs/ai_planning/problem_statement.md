# myBBS 代理 — ASCII（Big5）處理問題說明文件

> 數據來源：實測抓包 `_ptt_capture.bin`（4397 bytes）與診斷腳本 `_analyze_iac.py` / `_cmp_codecs.py` / `_cmp_codecs2.py` / `_cmp_uao3.py`。

## 一、系統目標回顧
1. FastAPI + `websockets` 建立 WebSocket 中繼：瀏覽器 ⇄ 本代理 ⇄ `wss://ws.ptt.cc/bbs`（或 ptt2）。
2. PTT 端只送 Big5(Big5UAO) 裸位元組流（含 Telnet IAC 協商與 ANSI/ESC 控制碼）。
3. 前端用 xterm.js 當作終端機模擬器，需在 80×24 網格下維持 ASCII 美術對齊。

## 二、抓包所得的客觀事實

### 事實 1：首個 frame 內含 19 bytes 的 HTTP 狀態行
`48 54 54 50 2f 31 2e 31 20 32 30 30 20 4f 4b 0d 0a 0d 0a` = `HTTP/1.1 200 OK\r\n\r\n`，其後才是畫面（`a7 f4` = `纂`）。雨次獨立抓包一致：
```
raw[0:19]  = b'HTTP/1.1 200 OK\r\n\r\n'
raw[19:35] = b'\xa7\xf4\x1b[6n\x1b[H\x1b[2J\r'
```

### 事實 2：IAC 協商以裸位元組混在畫面資料中（本體偏移 1046–1069）
```
0408  a2 65 a2 64 a2 63 a2 62 1b 5b 6d 0d 0a 00 ff fd
0418  18 ff fa 18 01 ff f0 ff fd 1f ff fb 01 ff fb 03
0428  ff fb 00 ff fd 00 0d c4 a1 1b 5b 36 6e 1b 5b 48
```
| 偏移 | 序列 | 意義 |
|---|---|---|
| 1046 | `FF FD 18` | IAC DO 24（Terminal Type） |
| 1049 | `FF FA 18 01 FF F0` | IAC SB 24 01 IAC SE（型號 VT100） |
| 1055 | `FF FD 1F` | IAC DO 31（NAWS） |
| 1058 / 1061 / 1064 | `FF FB 01` / `03` / `00` | IAC WILL ECHO / SGA / BINARY |
| 1067 | `FF FD 00` | IAC DO BINARY |

其後：`00`（NUL 行尾填補）、`0D`、`C4 A1`=`纂`、`ESC[6n`、`ESC[H`、`ESC[2J`。

### 事實 3：同一份抓包的五種解碼結果
| 方案 | 步驟 | 長度 | U+FFFD |
|---|---|---|---|
| A | 現況：直接 `big5-uao` 整批解 | 4021 | 0（但含標頭與 `ÿý` 亂碼） |
| B | 僅剝除 HTTP 標頭 + `big5-uao` | 4002 | 0 |
| **C** | **剝除標頭 + IAC 過濾 + `big5-uao`** | **3978** | **0（最乾淨）** |
| D | 剝除 + IAC 過濾 + 內建 `big5` | 3982 | 134 |
| E | 剝除 + IAC 過濾 + 內建 `cp950` | 3978 | 126 |

### 事實 4：codec 對關鍵位元組的支援
| 位元組 | `big5` | `cp950` | `big5-uao` |
|---|---|---|---|
| `F9 DE` | `��` | `╦` | `╦` |
| `F9 E0` | `��` | `╠` | `╠` |
| `F9 E2` | `��` | `╣` | `╣` |
| `FF F0` | `��` | `��` | `ÿð`（FF 當單字節） |

### 事實 5：分批解碼會影響結果；uao 無 IncrementalDecoder
- 整批解：3978 字元；每 7 bytes 切批：4039 字元且內容不同（雙字節被拆成兩個單寬字 → 80 欄錯位）。
- `uao` 只暴露兩張 dict：`uao.b2u.b2u_table`（19782 筆）、`uao.u2b.u2b_table`（25916 筆），鍵為 16 位整數；ASCII 與 `0xFF` 不在表內。
- `codecs.getincrementaldecoder('big5-uao')` 在 Py3.9 拋 `LookupError`，需 alias 到 `big5uao`。

### 事實 6：實測欄／列尺寸（`_line_stats.py` / `_width2.py`）
以方案 C 解碼後 `split("\r\n")` → **34 列**；游標定位碼為 `ESC[21;1H`（第 21 列），與 24 列頁面相容。
跳過 ESC 序列後的「可見字元數」：

| 行區 | 顯示寬度（依 `app.js` provider：CJK/全形=2、NUL=0） |
|---|---|
| 1–10（Logo／選單） | 62 / 57 / 54 / 46 / 51 / 44 / 55 / 47 / 41 / 47 |
| 11–20 | 2 / 71 / 73 / 74 / 75 / 79 / 76 / 75 / 78 / 72 |
| 21–30（方塊美術） | 73 / 72 / 69 / 67 / 70 / 68 / 72 / 74 / 75 / 79 |
| 31–34 | 0 / 0 / 73 / 58 |

**最大值 79、全部 34 列皆 ≤ 80** → `app.js` 的雙寬範圍（`U+1100-115F`、`U+2E80-A4CF`、`U+AC00-D7A3`、`U+F900-FAFF`、`U+FE30-FE6F`、`U+FF00-FF60`、`U+FFE0-FFE6` = 2）與 PTT 的 80 欄排版一致，不需再校準。
（先前 89/93/103/155 等數值是診斷腳本的 CSI 正則不完整所致，未把 `ESC[n;mH`、`ESC[47m` 完全剔除；`_width4.py` 以 `\x1b\[[0-9;]*[A-Za-z]` 重算後即為上表。）

### 事實 8：握手參數（實測 `wss://ws.ptt.cc/bbs`，websockets 15.0.1）
| 項目 | 實測 |
|---|---|
| 必要標頭 | `Origin: https://term.ptt.cc`（缺此標頭即 `HTTP 403`） |
| 子協定 | `Sec-WebSocket-Protocol: 1.1` |
| 第 1 個 frame | 1089 bytes，`b'HTTP/1.1 200 OK\r\n\r\n   '`（標頭＋畫面同一 frame） |
| 第 2 個 frame | 3308 bytes，`b'\r\xc4\xa1\x1b[6n\x1b[H\x1b[2J\r\n\x1b[1;33...'` |
| 兩 frame 合計 | 4397 bytes，與 `_ptt_capture.bin` 完全相同 |


### 事實 7：官方 `term.ptt.cc` 的內部實作（由 `_pttweb_bundle.js` 反查）
| 機制 | bundle 內證據（字元偏移） | 對應本專案 |
|---|---|---|
| UAO 對照表以 `Uint8Array(131072)` 暴露為 `window.lib.b2uArray` / `u2bArray`，未命中補 `65533`(=U+FFFD) | ~44224 | 對應 `uao.b2u_table` |
| 缺區間用內建 `new TextDecoder('big5')` 逐字節組合補表：`(250..254,64..)→57344`、`(142..160,64..)→58129`、`(129..141,64..)→61112`、`(198..200,161..)→63153`，並跳過 41920–41982、50849–51454、63998 | ~43157 | 與 `uao` 表的補貼邏輯相同 |
| IAC 以狀態機處理：`case 251/252/253/254`（WILL/WONT/DO/DONT）、`case 250`（SB，`iac_sb=[]`）、`case 241`（NOP）、`case 255`→`push(Uint8Array([255]))` | ~266751 | 與本專案 `strip_iac` 一致 |
| 自寫終端模擬器：`ESC[2J/3J`→clear、`J/H/f/K/L/M/P/r/s/u`、`scrollStart/scrollEnd`、`cur_x_sav` | ~74618 | xterm.js 已內建 |
| 網格預設 **80 欄 / 24 列**：`e?e.cols:80`、`getLastRowNum()` 預設 `23`（= 第 24 列） | ~89682 / ~92653 | `fitAddon` + wcwidth provider |
| 自帶 `wcwidth()`：`<65536` 查表 `mn[e]`，`127744–129791`、`131072–262141` 計 2，其余計 1，非字串回 0 | ~69151 | `static/app.js` provider |
| 美術用 `<span class="term-ascii">` 包裹、`isPassScreen()` 以第 24 列（或 `rows>24` 時第 24 列）比對 `Space/Return` | ~89682 / ~92653 | 分頁判斷可照抄 |
| 連線位址預設 `wss://ws.ptt.cc/bbs`，`site/type` 由 `localStorage` 讀取 | ~557302 | 與 `app.py` 相同 |

## 三、目前實際遭遇的問題

| 編號 | 問題 | 直接症狀 | 根因 |
|---|---|---|---|
| **P1** | 首 frame 混入 `HTTP/1.1 200 OK\r\n\r\n` | 第一行出現 `HTTP/1.1 200 OK`，Logo 往下擠 2 行 | PTT 閘道把 HTTP 狀態行寫進第一個 WS payload |
| **P2** | IAC 位元組未過濾 | 出現 `ÿý`、`ÿú`、`ÿû`；其後各行寬度總和不為 80 而錯位 | `0xFF` 在 uao 表被當單字節（單寬），與相鄰雙寬字形混排 |
| **P3** | 內建 `big5`/`cp950` 缺 UAO 字形 | 134 / 126 個 `U+FFFD`，`╦ ╠ ╣` 變方塊 | Big5UAO 擴充表不在標準表內 |
| **P4** | 分批與整批解碼結果不一致 | 選單右側邊框 `╖ ║ ╜` 跑位 | 斷在雙字節中間時沒有 pending lead byte 快取 |
| **P5** | `big5-uao` 名稱未註冊 | `LookupError: unknown encoding: big5-uao` | Py3.9 需 `codecs.register` alias → `big5uao` |

| **P6** | 控制字元混於正文 | `0x00`（NUL）出現在行尾；`ESC[6n` 需回覆 | PTT 以 NUL 做行尾填補，並用 `ESC[6n` 询问游標位置 |
| **P7** | 連線參數不一致 | `fitAddon.fit()` 後欄數非 80 時，PTT 重排畫面造成美術錯位 | PTT 固定以 80×24 排版（NAWS=31 協商） |

---

## 四、可選架構方案比較

| 代號 | 架構 | 解碼位置 | 依賴 | 優點 | 缺點 |
|---|---|---|---|---|---|
| **A**（推薦） | 現行三段式管線：①一次性剝除 HTTP 標頭 → ②位元組層 IAC 狀態機 → ③`big5-uao` + pending lead byte 快取 | 伺服器 | `fastapi`、`websockets`、`uao` | 改動最小；實測 3978 字元、`U+FFFD`=0；控制碼原樣交給 xterm.js | 需自行維護 3 個小演算法 |
| **B** | 純中繼：伺服器不解碼，`binaryType='arraybuffer'` 原樣轉發；JS 端做標頭剝除＋IAC 過濾＋`TextDecoder('cp950')`＋UAO 補貼表（約 20 對） | 瀏覽器 | 無 Python 編碼依賴 | Python 端最薄；無 codec 註冊問題 | 需自備 UAO 補貼表；雙邊除錯 |
| **C** | 表驅動解碼器：直接使用 `uao.b2u_table` / `uao.u2b_table` 兩張 dict 手寫解碼器（含 IAC/標頭過濾） | 伺服器 | `uao`（只取表格） | 真正增量化、免 `codecs` alias；速度快 | 需自行處理 ASCII（<0x100）與 0xFF 不在表內的規則 |
| **D** | 改走 PTT JSON API（`https://ptt.cc/app.json?n=1&r=0`） | 伺服器 | `httpx`/`requests` | 已是 JSON、無 IAC/Big5 狀態機 | 非終端機語意：無 ASCII 美術、無鍵控/分頁行為，與現有前端不相容 |

### 演算法層面的三種增量化策略（可與 A/B/C 組合）
1. **逐 frame 增量＋pending lead byte**（對應 P4，A/C 採用）。
2. **整段緩衝後一次解碼**：每個 frame 附加到 `bytearray`，收到 `\x1b[` 系列結束或空 packet 時整批解（與實測 3978 字元的基準一致）。
3. **表驅動單次掃描**：由 `(hi<<8)|lo` 直接查 `b2u_table`，未命中且 `hi<0x81` 時逐字節輸出（對應事實 5 的表格結構）。

---

## 五、建議（待使用者確認後實作）

1. 採用 **方案 A**（**已於 `app.py` 實作並通過第六節全部 DoD**），三個小演算法為模組化函式：

   - `strip_http_header(buf)`：僅在串流最開頭剝除一次 `HTTP/1.1 200 OK\r\n\r\n`（以 `\r\n\r\n` 為界）。
   - `strip_iac(buf)`：位元組層狀態機，`FF FB/FC/FD/FE` 吞 3 bytes、`FF FA … FF F0` 吞至 SE、`FF FF` 輸出字面 `0xFF`。
   - `Big5UAOIncrementalDecoder`：保留現有 `0x81≤b≤0xFE` 雙字節規則，並把尾端的 pending lead byte 正確帶到下一次 `decode()`。
2. NUL（`0x00`）保留給 xterm.js（其 wcwidth provider 已回傳寬度 0）。
3. `ESC[6n` 交由 xterm.js 自動回覆（經 `term.onData` 送回），不要在代理端硬造回覆值。
4. 維持 `PTT_TARGET=ptt|ptt2` 與 `PROXY_PASSCODE` 既有行為不變。
5. 連線參數：`websockets.connect(url, subprotocols=["1.1"], additional_headers={"Origin": <term URL>, "User-Agent": ...})`（缺 `Origin` 即 403）。
6. `static/app.js` 的 `wcwidth` provider 已校準為：控制字元 0、ASCII 1、方塊/區塊/幾何（`U+2500-25FF`、`U+2600-26FF`）1、Latin-1 Supplement 1、CJK／全形區間 2 → 實測 34 列最大 79，皆 ≤80。

### 實作偽碼（`app.py` 現況）
```
decode(new_bytes):
    buf = pending + new_bytes; pending = ""
    if not header_done:
        buf, header_done = strip_http_header(buf)      # 以 \r\n\r\n（或 \n\n）為界，只做一次
        if not header_done: pending = buf; return ""
    filt, used = strip_iac(buf)                         # FF FB/FC/FD/FE→3；FF FA…FF F0；FF FF→0xFF
    n = complete_pair_len(filt)                         # 尾端孤 lead byte(0x81–0xFE) 不計入
    pending = buf[used:] + filt[n:]
    return filt[:n].decode("big5-uao", errors="replace")
```


---

## 六、完成驗證方式（DoD）

| 檢查項 | 預期值 | 實測（`_validate_pipeline.py`） |
|---|---|---|
| 以 `_ptt_capture.bin` 走完整管線後字串長度 | 3978 | **3978** ✅ |
| `U+FFFD` 數量 | 0 | **0** ✅ |
| 首行 | 直接是 Logo（無 `HTTP/1.1 200 OK`） | `     ˙      PTT …`（無標頭）✅ |
| `ÿ`、`ý`、`ú` 等 Latin-1 亂碼 | 不再出現 | 未出現 ✅ |
| `ÿð`（IAC SE 殘跡） | 不再出現 | 未出現 ✅ |
| 逐 frame（1/3/7/19/64/512 bytes）與整批解碼結果 | 完全相同 | 全部 `True`，皆 3978／0 FFFD ✅ |
| UAO 專屬字形 `╦ ╠ ╣` | 存在 | 存在 ✅ |

### 寬度實測（`_width4.py`：以 `\x1b\[[0-9;]*[A-Za-z]` 剔除 CSI 後，依 `app.js` provider 計寬）
| 行 | 1 | 13 | 21 | 30 | 33 | 34 |
|---|---|---|---|---|---|---|
| 顯示寬度 | 62 | 71 | 73 | 79 | 73 | 58 |

全部 34 列最大 79 ≤ 80，與 PTT 的 80 欄基準吻合。

線上實測（`_live_check.py`，直連 `wss://ws.ptt.cc/bbs`）：`Origin` + `1.1` 子協定下，首個 frame 即解出 3978 字元、`U+FFFD`=0、`0xFF`=0，第 1 行直接是 Logo。

驗證指令：
```powershell
cd d:\MyLab\myBBS
.venv\Scripts\python.exe _validate_pipeline.py  # 三段式管線（整批 vs 1/3/7/19/64/512 bytes）
.venv\Scripts\python.exe _width4.py             # 逐列顯示寬度 + 線上手動握手對照
.venv\Scripts\python.exe _live_check.py         # 直連 PTT 的端到端解碼
```

---

## 七、目前專案相關檔案

| 檔案 | 用途 |
|---|---|
| `app.py` | FastAPI 代理（待按方案 A 修正 3 處） |
| `static/index.html` / `style.css` / `app.js` | 前端 xterm.js UI（含 BBS 寬度 provider） |
| `_ptt_capture.bin` | 實測抓包基準（4397 bytes） |
| `_analyze_iac.py` / `_cmp_codecs.py` / `_cmp_codecs2.py` / `_cmp_uao3.py` | 診斷腳本（本文件數據來源） |
| `requirements.txt` | `fastapi`、`uvicorn`、`websockets`、`uao` |
