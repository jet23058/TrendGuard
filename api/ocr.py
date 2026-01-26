from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import google.generativeai as genai

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # 1. Check API Key
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Server missing GOOGLE_API_KEY"}).encode())
            return
            
        genai.configure(api_key=api_key)
        
        # 2. Read Body
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Empty body")
                
            body = self.rfile.read(content_length)
            req_data = json.loads(body)
            files = req_data.get('images', [])
            
            if not files:
                raise ValueError("No images provided")
                
            image_parts = []
            for img_obj in files:
                img_bytes = base64.b64decode(img_obj['data'])
                image_parts.append({
                    "mime_type": img_obj['mime_type'],
                    "data": img_bytes
                })
                
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # 3. Call Gemini
        prompt = """
        你是一個台灣股市券商 App 截圖的解析專家。
        使用者上傳了一組庫存截圖（可能包含多張，且內容可能有重疊）。
        
        請執行以下任務：
        1. **提取資訊**：找出每一列的「股票代碼」、「股票名稱」、「庫存股數」、「平均成本」。
        2. **去重合併**：因為截圖是連續的，上下兩張圖可能會顯示同一檔股票。請依據「股票代碼」去除重複項目，保留一份即可。
        3. **容錯處理**：
           - 股票代碼通常是 4 碼數字。
           - 股數與成本請轉換為純數字（去除逗號）。
           - 如果有無法辨識的欄位，請盡量推斷或標記 null。
        
        請直接回傳一個 **純 JSON 陣列**，不要包含任何 Markdown 格式 (如 ```json ... ```)。
        格式範例：
        [
          {"code": "2330", "name": "台積電", "shares": 2000, "cost": 502.5},
          {"code": "0050", "name": "元大台灣50", "shares": 1500, "cost": 120.1}
        ]
        """
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, *image_parts])
            raw_text = response.text
            
            # Clean up Markdown
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            result_json = json.loads(cleaned_text.strip())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result_json).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
