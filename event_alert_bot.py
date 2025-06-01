import requests
import time
import os
from dotenv import load_dotenv

# === .env dosyasını yükle ===
load_dotenv()

# === AYARLAR ===
UID = os.getenv("UID")
SECRET = os.getenv("SECRET")
CAMPUS_ID = int(os.getenv("CAMPUS_ID", 21))
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
KEYWORDS_FILE = os.getenv("KEYWORDS_FILE", "keywords.txt")

# === Global değişken ===
known_event_ids = set()

# === 1. Token al ===
def get_token():
    url = "https://api.intra.42.fr/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": UID,
        "client_secret": SECRET
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

# === 2. Eventleri çek ===
def get_events(token):
    url = f"https://api.intra.42.fr/v2/campus/{CAMPUS_ID}/events"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

# === 3. Telegram spam mesaj gönder (her aralıkta 5 mesaj) ===
def send_spam_message(event_name, event_id, repeat=20, interval=15):
    try:
        clean_name = event_name.encode('ascii', 'ignore').decode()
    except:
        clean_name = event_name

    message = (
        "🚨🚨🚨\n"
        "‼️‼️ *DİKKAT! YENİ EVENT AÇILDI* ‼️‼️\n\n"
        f"*{clean_name}*\n"
        f"[📎 Etkinlik Sayfası](https://intra.42.fr/events/{event_id})\n\n"
        "@yourusername 📲\n"
        "⏰⏰⏰ UYAN! KAYIT AÇILDI ⏰⏰⏰"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    sent = 0
    while sent < repeat:
        for i in range(min(5, repeat - sent)):
            response = requests.post(url, data=data)
            print(f"[SPAM] Mesaj gönderildi {sent + 1}/{repeat}" if response.ok else f"[SPAM] Hata: {response.status_code}")
            sent += 1
        time.sleep(interval)

# === 4. Anahtar kelimeleri dosyadan yükle ===
def load_keywords():
    try:
        with open(KEYWORDS_FILE, "r") as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"[!] {KEYWORDS_FILE} bulunamadı. Anahtar kelime listesi boş.")
        return []

# === 5. Yeni etkinlik var mı kontrol et ===
def check_new_events():
    token = get_token()
    events = get_events(token)
    keywords = load_keywords()

    for event in events:
        name = event.get("name", "").lower()
        event_id = event.get("id")

        if event_id not in known_event_ids and any(keyword in name for keyword in keywords):
            known_event_ids.add(event_id)
            print(f"[+] Yeni event bulundu: {event['name']}")
            send_spam_message(event['name'], event_id, repeat=20, interval=15)  # 5'lik gruplarla mesaj

# === Ana döngü ===
if __name__ == "__main__":
    print("[START] 42 Event Alarm Botu Başladı.")
    while True:
        try:
            check_new_events()
        except Exception as e:
            print(f"[!] Hata: {e}")
        time.sleep(300)  # 5 dakika
