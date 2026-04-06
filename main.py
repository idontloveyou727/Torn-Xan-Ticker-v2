import requests
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta

TARGET_ITEM_ID = 206
POLL_INTERVAL = 70
WEBHOOK_URL = "https://discord.com/api/webhooks/1489957213626962050/kqmc7LedtFdoTowqyL7osHeaXqI2zCgUfoZWS-xDAvSxXSY2vX1ncBMqjsiUT02sSSRL"
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
    now_tct = datetime.utcnow()
    now_ts = int(time.time())
    
    # Tính toán TCT (Để hiển thị tham chiếu gốc)
    restock_1_tct = now_tct + timedelta(minutes=130)
    restock_2_tct = now_tct + timedelta(minutes=260)

    # Tính toán Unix Timestamp (Để Discord tự động render Local Time)
    restock_1_ts = now_ts + (130 * 60)
    restock_2_ts = now_ts + (260 * 60)
    
    airstrip_depart_ts = restock_2_ts - (158 * 60)
    wlt_depart_ts = restock_1_ts - (113 * 60)
    bct_depart_ts = restock_1_ts - (68 * 60)

    time_format = "%H:%M"

    content_str = (
        f"{PING_TARGET} **RESTOCK ALARM**\n"
        f"Xanax has restocked!\n"
        f"Quantity: {quantity}\n"
        f"Price: ${cost:,}\n\n"
        f"**Estimated Restock time:**\n"
        f"- Batch 1: {restock_1_tct.strftime(time_format)} TCT | Local: <t:{restock_1_ts}:t>\n"
        f"- Batch 2: {restock_2_tct.strftime(time_format)} TCT | Local: <t:{restock_2_ts}:t>\n\n"
        f"**Suggested Flight Schedule to Japan:**\n"
        f"**[Recommended] Air Strip (ETA <t:{restock_2_ts}:t>): Departure at <t:{airstrip_depart_ts}:t>**\n"
        f"*Private Jet (WLT) (ETA <t:{restock_1_ts}:t>): Departure at <t:{wlt_depart_ts}:t>*\n"
        f"*Business Class (BCT) (ETA <t:{restock_1_ts}:t>): Departure at <t:{bct_depart_ts}:t>*"
    )

    payload = {"content": content_str}

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 429:
            try:
                error_data = response.json()
                retry_after = error_data.get('retry_after', 10)
                print(f"[LOG] Bị Discord chặn IP tạm thời. Cần chờ {retry_after} giây để mở khóa.", flush=True)
            except:
                print("[LOG] Lỗi 429 từ Discord. Không thể phân tách JSON thời gian chờ.", flush=True)
            return
            
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
                        was_in_stock = False
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