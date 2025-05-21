import asyncio
import requests
from datetime import datetime
from telegram import Bot

# Bot ve diğer global değişkenlerin tanımlanması
BOT_TOKEN = "7593547471:AAFeCSNinanmIfU3KIuiZwS2YHiQDWMyRJo"
CHAT_ID = "-1002500404506"
gonderilen_deprem_imzalari = set()  # Küme tanımı

def kontrol_et():
    global gonderilen_deprem_imzalari
    bot = Bot(token=BOT_TOKEN)

    # Test mesajı
    try:
        bot.send_message(chat_id=CHAT_ID, text="✅ Deprem botu başlatıldı!")
    except Exception as e:
        print(f"Bot test mesajı hatası: {e}")
        return

    while True:
        try:
            # Kandilli API
            kandilli_url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
            kandilli_data = requests.get(kandilli_url).json().get('result', [])

            # EMSC API
            emsc_url = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=1&format=json"
            emsc_data = requests.get(emsc_url).json().get('features', [])

            deprem_listesi = []

            if kandilli_data:
                for item in kandilli_data[:1]:  # sadece son deprem
                    deprem_listesi.append({
                        'source': 'Kandilli',
                        'title': item.get('title'),
                        'date': item.get('date'),
                        'mag': item.get('mag'),
                        'depth': item.get('depth'),
                        'lat': item['geojson']['coordinates'][1],
                        'lon': item['geojson']['coordinates'][0]
                    })

                if emsc_data:
                    emsc_item = emsc_data[0]
                    props = emsc_item.get('properties', {})
                    coords = emsc_item.get('geometry', {}).get('coordinates', [0, 0])

                    time_iso = props.get('time', '')
                    try:
                        # Z varsa kaldır ve UTC olarak yorumla
                        if time_iso.endswith("Z"):
                            time_iso = time_iso.replace("Z", "+00:00")
                        dt_obj = datetime.fromisoformat(time_iso)
                        deprem_zamani = dt_obj.strftime('%Y.%m.%d %H:%M:%S')
                    except Exception as e:
                        print(f"Tarih dönüştürme hatası: {e}")
                        deprem_zamani = "Zaman okunamadı"

                    deprem_listesi.append({
                        'source': 'EMSC',
                        'title': props.get('flynn_region', 'Bilinmiyor'),
                        'date': deprem_zamani,
                        'mag': props.get('mag'),
                        'depth': props.get('depth'),
                        'lat': coords[1],
                        'lon': coords[0]
                    })

            for deprem in deprem_listesi:
                imza = f"{deprem['source']}_{deprem['title']}_{deprem['date']}_{deprem['mag']}"

                # Eğer daha önce gönderilmediyse
                if imza not in gonderilen_deprem_imzalari:
                    mesaj = (
                        f"🌍 Kaynak: {deprem['source']}\n"
                        f"📍 Yer: {deprem['title']}\n"
                        f"🕒 Zaman: {deprem['date']}\n"
                        f"📏 Büyüklük: {deprem['mag']} ML\n"
                        f"📍 Derinlik: {deprem['depth']} km\n"
                        f"🌐 Koordinatlar: {deprem['lat']}, {deprem['lon']}"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=mesaj)
                    gonderilen_deprem_imzalari.add(imza)
                    print(f"Bildirim gönderildi: {imza}")

        except Exception as e:
            print(f"Hata: {str(e)}")

        await asyncio.sleep(20)

# Ana fonksiyonu ekleyin
def main():
    kontrol_et()  # kontrol_et fonksiyonunu çağır

if __name__ == "__main__":
    asyncio.run(main())  # Asenkron fonksiyonu çalıştır
