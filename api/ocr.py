from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import re
import numpy as np
import cv2
from PIL import Image
import pytesseract
import io

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # 1. Read Body
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Empty body")
                
            body = self.rfile.read(content_length)
            req_data = json.loads(body)
            files = req_data.get('images', [])
            
            if not files:
                raise ValueError("No images provided")
                
            all_extracted_stocks = []
            
            for img_obj in files:
                img_bytes = base64.b64decode(img_obj['data'])
                # Convert bytes to numpy array for OpenCV
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    continue
                
                # --- Preprocessing ---
                # 1. Grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # 2. Rescaling (DPI increase simulation)
                gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                # 3. Bilateral Filter (Noise reduction keeping edges)
                gray = cv2.bilateralFilter(gray, 9, 75, 75)
                # 4. Adaptive Thresholding
                thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
                
                # --- OCR Execution ---
                # Use both Traditional Chinese and English
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(thresh, lang='chi_tra+eng', config=custom_config)
                
                # --- Data Extraction (Regex) ---
                stocks = self.parse_text_for_stocks(text)
                all_extracted_stocks.extend(stocks)
                
            # Deduplicate by code
            unique_stocks = {}
            for s in all_extracted_stocks:
                code = s['code']
                if code not in unique_stocks:
                    unique_stocks[code] = s
                else:
                    # Update if current has more info
                    if not unique_stocks[code]['name'] and s['name']:
                        unique_stocks[code]['name'] = s['name']
                    if unique_stocks[code]['shares'] == 0 and s['shares'] > 0:
                        unique_stocks[code]['shares'] = s['shares']
                    if unique_stocks[code]['cost'] == 0 and s['cost'] > 0:
                        unique_stocks[code]['cost'] = s['cost']
            
            final_result = list(unique_stocks.values())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(final_result, ensure_ascii=False).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def parse_text_for_stocks(self, text):
        """
        Parses raw OCR text to find Taiwan stock patterns.
        Heuristic: Look for 4-digit codes and associated numbers.
        """
        results = []
        lines = text.split('\n')
        
        # Pattern for 4-digit stock code (usually at start of row or followed by name)
        code_pattern = re.compile(r'\b([1-9]\d{3}|00\d{2,3})\b')
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            codes = code_pattern.findall(line)
            if not codes: continue
            
            for code in codes:
                # Basic cleanup of line for this code
                # Try to extract name: usually follows the code or is near it
                # Logic: Find code in line, check string next to it
                name = ""
                # Simple heuristic: any CJK characters in the line
                cjk_match = re.search(r'[\u4e00-\u9fa5]{2,}', line)
                if cjk_match:
                    name = cjk_match.group(0)
                
                # Try to find numbers (shares and cost)
                # Removing non-numeric/period/comma
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                # Filter out the code itself from numbers
                numbers = [n.replace(',', '') for n in numbers if n.replace(',', '') != code]
                
                shares = 0
                cost = 0.0
                
                # Usually shares is a large integer, cost is a decimal or smaller number
                for n in numbers:
                    try:
                        val = float(n)
                        if val > 1000: # Heuristic for shares
                            shares = int(val)
                        elif 0 < val < 2000: # Heuristic for cost
                            cost = val
                    except: continue
                
                results.append({
                    "code": code,
                    "name": name,
                    "shares": shares,
                    "cost": cost
                })
        
        return results
