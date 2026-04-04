import requests
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TARGET_ITEM_ID = 206
POLL_INTERVAL = 70
WEBHOOK_URL = "https://discord.com/api/webhooks/1489863463114113074/KaMdOwn5rBBiVJb9fIH4aFrOnNZ4FFh4I8EfdsN5R8F9qBzLk-iGburOsO93sgV_CuqI"
PING_TARGET = "<@&1489251181451808922>" 

def fetch_japan_data():
    url = "https://yata.yt/api/v1/travel/export/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Lỗi truy xuất API YATA: {e}")
        return None

def send_discord_ping(quantity, cost):
    payload = {
        "content": f"{PING_TARGET} **RESTOCK ALARM**\nXanax has restocked!\nQuantity: {quantity}\nPrice: ${cost:,}"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Ping thành công. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"Lỗi gửi Webhook: {e}")

def run_live_tracker():
    last_update = 0
    was_in_stock = False

    while True:
        payload = fetch_japan_data()
        if payload is None:
            print("[LOG] Truy xuất thất bại. Payload rỗng. Khả năng cao do chặn IP hoặc lỗi mạng.")
        else:
            try:
                jap_data = payload["stocks"]["jap"]
                jap_stocks = jap_data["stocks"]
                current_update = jap_data.get("update", 0)

                print(f"[LOG] Kết nối API thành công. Update ID: {current_update} | Last ID: {last_update}")

                if current_update != last_update:
                    last_update = current_update
                    
                    target_item = next((item for item in jap_stocks if item.get("id") == TARGET_ITEM_ID), None)
                    
                    if target_item is None:
                        print(f"[LOG] Cảnh báo: Vật phẩm ID {TARGET_ITEM_ID} không có mặt trong chuỗi dữ liệu YATA trả về.")
                    else:
                        quantity = target_item.get("quantity", 0)
                        cost = target_item.get("cost", 0)
                        print(f"[LOG] Quét thành công ID {TARGET_ITEM_ID}. Số lượng kho hiện hành: {quantity}")
                        
                        if quantity > 0:
                            if not was_in_stock:
                                send_discord_ping(quantity, cost)
                                was_in_stock = True
                        else:
                            was_in_stock = False
            except KeyError as e:
                print(f"[LOG] Lỗi phân tách JSON. Cấu trúc bị sai lệch tại khóa: {e}")
        time.sleep(POLL_INTERVAL)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Tracker is active.")
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    tracker_thread = threading.Thread(target=run_live_tracker, daemon=True)
    tracker_thread.start()
    
    run_dummy_server()