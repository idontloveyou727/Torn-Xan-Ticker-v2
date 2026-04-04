import requests
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TARGET_ITEM_ID = 206
POLL_INTERVAL = 70
WEBHOOK_URL = "https://discord.com/api/webhooks/1489863463114113074/KaMdOwn5rBBiVJb9fIH4aFrOnNZ4FFh4I8EfdsN5R8F9qBzLk-iGburOsO93sgV_CuqI"
PING_TARGET = "<@&1489251181451808922>" 

def fetch_data():
    url = "https://yata.yt/api/v1/travel/export/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[LOG] Lỗi truy xuất API YATA: {e}", flush=True)
        return None

def send_discord_ping(quantity, cost):
    payload = {
        "content": f"{PING_TARGET} **RESTOCK ALARM**\nXanax has restocked in Japan!\nQuantity: {quantity}\nPrice: ${cost:,}"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[LOG] Ping thành công. HTTP Status: {response.status_code}", flush=True)
    except Exception as e:
        print(f"[LOG] Lỗi gửi Webhook: {e}", flush=True)

def run_live_tracker():
    last_update = 0
    was_in_stock = False

    while True:
        try:
            payload = fetch_data()
            if not payload or not isinstance(payload, dict):
                print(f"[LOG] Truy xuất thất bại hoặc sai định dạng. Payload: {payload}", flush=True)
            else:
                stocks_data = payload.get("stocks", {})
                country_data = stocks_data.get("jap", {})
                country_stocks = country_data.get("stocks", [])
                current_update = country_data.get("update", 0)

                print(f"[LOG] Quét API thành công. Update ID: {current_update} | Last ID: {last_update}", flush=True)

                if current_update != last_update:
                    last_update = current_update
                    
                    target_item = next((item for item in country_stocks if isinstance(item, dict) and item.get("id") == TARGET_ITEM_ID), None)
                    
                    if target_item is None:
                        print(f"[LOG] Cảnh báo: Vật phẩm ID {TARGET_ITEM_ID} không tồn tại trong kho hiện hành.", flush=True)
                    else:
                        quantity = target_item.get("quantity", 0)
                        cost = target_item.get("cost", 0)
                        print(f"[LOG] Phát hiện ID {TARGET_ITEM_ID}. Số lượng kho: {quantity}", flush=True)
                        
                        if quantity > 0:
                            if not was_in_stock:
                                send_discord_ping(quantity, cost)
                                was_in_stock = True
                        else:
                            was_in_stock = False
        except Exception as e:
            print(f"[FATAL LOG] Hệ thống quét sập do ngoại lệ không lường trước: {e}", flush=True)
        
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
    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    tracker_thread = threading.Thread(target=run_live_tracker, daemon=True)
    tracker_thread.start()
    
    run_dummy_server()