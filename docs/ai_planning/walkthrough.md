# myBBS PTT 加密跳板開發完成說明

本專案已開發完成並通過自動化測試驗證！我們建立了一個安全、快速、外觀精美的 PTT 加密網頁跳板，能讓您在限制外網連線的辦公室環境中，透過 Hugging Face 的加密域名（HTTPS/WSS）正常使用 PTT。

## 完成的變更內容

1. **`requirements.txt`**：引入 `fastapi`、`uvicorn`、`websockets` 等 Python 異步伺服器核心依賴。
2. **`Dockerfile`**：基於 `python:3.10-slim`，設定容器暴露於 port `7860`（Hugging Face Space 預設）。
3. **`app.py`**：
   - 建立代理路由與靜態檔案路由。
   - 後端邏輯採用 **CP950 增量解碼器**，防止中文字元網路傳輸時被截斷產生亂碼。
   - 支援 `PROXY_PASSCODE` 安全驗證功能。
4. **`static/index.html`**：整合 `xterm.js` 與毛玻璃樣式，具備完整控制側邊欄、虛擬鍵盤與長文章貼上對話盒。
5. **`static/style.css`**：
   - 調整 xterm 渲染字型為 `'Courier New', 'MingLiU', ...`，增加行高 (`lineHeight`) 至 **`1.25`** 以解決擁擠問題。
   - **版面壓縮 Bug 修復 (重要)**：由於 `flex` 佈局默認允許子元素縮小（`flex-shrink: 1`），當終端在全螢幕模式下擴大至 `100vw` 後返回時，寬度殘留會將側邊欄壓縮成幾像素寬的垂直窄條。我們已在 `.sidebar-panel` 加上 **`flex-shrink: 0;`**，並在 `.main-terminal-area` 加上 **`min-width: 0;`**，徹底解決此版面收縮異常，確保在縮放全螢幕後左側工具列能完美恢復 `340px` 寬度並正常互動。
6. **`static/app.js`**：
   - 處理連線控制、終端主題切换、字型調整與防洪長文章貼上機制。
   - 新增 `monochrome`（無色彩白色）主題，消除 ANSI 彩色代碼，只顯示純白與灰階字體。
7. **`.ai_rules.md`**：更新專案地圖。

---

## 部署至 Hugging Face Space 指南

若您要將此專案發布至 Hugging Face Space，請依照以下步驟操作：

1. **建立 Space**：選擇 **Docker** 作為 SDK（極度重要）。
2. **上傳程式碼**：將 `Dockerfile`、`requirements.txt`、`app.py` 還有整個 `static/` 資料夾上傳。
3. **設定存取密碼**：在 Space **Settings** -> **Variables and secrets** 中新增 Secret `PROXY_PASSCODE=您的自訂密碼` 以鎖定存取。
