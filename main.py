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
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def send_discord_ping(quantity, cost):
    payload = {
        "content": f"{PING_TARGET} **RESTOCK ALARM**\nXanax has restocked!\nQuantity: {quantity}\nPrice: ${cost:,}"
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Webhook: {e}")

def run_live_tracker():
    last_update = 0
    was_in_stock = False

    while True:
        payload = fetch_japan_data()
        if payload:
            try:
                jap_data = payload["stocks"]["jap"]
                jap_stocks = jap_data["stocks"]
                current_update = jap_data.get("update", 0)

                if current_update != last_update:
                    last_update = current_update
                    
                    for item in jap_stocks:
                        if item.get("id") == TARGET_ITEM_ID:
                            quantity = item.get("quantity", 0)
                            cost = item.get("cost", 0)
                            
                            if quantity > 0:
                                if not was_in_stock:
                                    print(f"Phát hiện restock: {quantity} items. Đang ping Discord...")
                                    send_discord_ping(quantity, cost)
                                    was_in_stock = True
                            else:
                                was_in_stock = False
                            break
            except KeyError:
                pass
        time.sleep(POLL_INTERVAL)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Tracker is active.")

def run_dummy_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    tracker_thread = threading.Thread(target=run_live_tracker, daemon=True)
    tracker_thread.start()
    
    run_dummy_server()