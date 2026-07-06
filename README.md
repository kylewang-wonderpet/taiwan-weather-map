# 台灣日累積雨量地圖微服務

這是一個輕量級的 Python Flask 微型服務，用於接收雨量資料（JSON 格式），並繪製出台灣縣市漸層地圖圖片（PNG 格式）。

## 如何在本機端測試
1. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 執行服務：
   ```bash
   python app.py
   ```
3. 使用工具（如 Postman 或是寫個簡單的 curl）測試：
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"臺北市": 50, "高雄市": 150}' http://localhost:5000/generate_map --output map.png
   ```

## 如何部署至免費雲端平台 (例如 Render)
1. 在本資料夾中將專案上傳至 GitHub。
2. 登入 [Render](https://render.com/)，選擇建立一個新的 **Web Service**。
3. 連接您的 GitHub Repository。
4. 在 Render 的設定中：
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. 點擊 `Create Web Service`，部署完成後，您會獲得一組對外網址（例如 `https://taiwan-rain-map.onrender.com`）。
6. 請將這組網址加上 `/generate_map` 填入您 GAS 程式碼的 API URL 設定中！
