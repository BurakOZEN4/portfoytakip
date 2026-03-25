"""
TEFAS Günlük & Yılbaşı Fiyat Çekici
─────────────────────────────────────
Her çalıştığında:
  1. Güncel fiyatları çeker
  2. Her yılın 01 Ocak fiyatlarını çeker (portföyde fonun olduğu yıllar)
  3. fiyatlar.json'u günceller → portfolyo.html otomatik okur
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# ─── AYARLAR ────────────────────────────────────
FONLAR = ["KBJ", "HMK", "HKP"]   # Portföydeki fon kodları
CIKTI_DOSYA = Path(__file__).parent / "fiyatlar.json"
MAX_DENEME = 4
BEKLEME_SN = 5
# ────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

def fiyat_cek(fon_kodu: str, tarih: str) -> float | None:
    """Belirli bir tarihteki fon fiyatını çeker. Hafta sonu/tatilse geriye gider."""
    tarih_dt = datetime.strptime(tarih, "%Y-%m-%d")
    for delta in range(7):
        deneme_dt = tarih_dt - timedelta(days=delta)
        deneme_str = deneme_dt.strftime("%d.%m.%Y")
        url = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
        payload = {
            "fontip": "YAT",
            "bastarih": deneme_str,
            "bittarih": deneme_str,
            "fonkod": fon_kodu,
        }
        for deneme in range(1, MAX_DENEME + 1):
            try:
                r = requests.post(url, data=payload, headers=HEADERS, timeout=20)
                r.raise_for_status()
                data = r.json()
                kayitlar = data.get("data", [])
                if kayitlar:
                    return float(kayitlar[0].get("FIYAT", 0)), deneme_str
            except Exception:
                if deneme < MAX_DENEME:
                    time.sleep(BEKLEME_SN)
    return None, None

def guncel_fiyat_cek(fon_kodu: str):
    """Fonun en güncel fiyatını çeker."""
    bugun = datetime.now().strftime("%Y-%m-%d")
    return fiyat_cek(fon_kodu, bugun)

def yilbasi_fiyatlari_cek(fon_kodu: str, mevcut: dict) -> dict:
    """
    Fonun portföyde olduğu her yıl için 01 Ocak fiyatını çeker.
    Zaten çekilmişse tekrar çekmez (gereksiz istek yapmaz).
    """
    buYil = datetime.now().year
    ilkYil = 2024  # Portföyünüzün başladığı yıl

    yil_fiyatlar = {}
    mevcut_yil_fiy = mevcut.get("yillikFiyatlar", {}).get(fon_kodu, {})

    for yil in range(ilkYil, buYil + 1):
        tarih_key = f"{yil}-01-01"

        # Zaten varsa ve yıl geçmişse tekrar çekme
        if tarih_key in mevcut_yil_fiy and yil < buYil:
            yil_fiyatlar[tarih_key] = mevcut_yil_fiy[tarih_key]
            print(f"   📂 {tarih_key}: {mevcut_yil_fiy[tarih_key]:.6f} TL (önbellekten)")
            continue

        print(f"   ⏳ {tarih_key} fiyatı çekiliyor...", end=" ", flush=True)
        fiyat, gercek_tarih = fiyat_cek(fon_kodu, tarih_key)
        if fiyat:
            yil_fiyatlar[tarih_key] = fiyat
            print(f"✅ {fiyat:.6f} TL ({gercek_tarih})")
        else:
            # Eski değeri koru
            if tarih_key in mevcut_yil_fiy:
                yil_fiyatlar[tarih_key] = mevcut_yil_fiy[tarih_key]
                print(f"⚠️  Alınamadı, eski değer korundu")
            else:
                print(f"❌ Alınamadı")
        time.sleep(1)  # Sunucuya yük verme

    return yil_fiyatlar

def main():
    print("=" * 50)
    print(f"  TEFAS Fiyat Çekici")
    print(f"  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 50)

    # Mevcut JSON'u yükle
    if CIKTI_DOSYA.exists():
        with open(CIKTI_DOSYA, "r", encoding="utf-8") as f:
            mevcut = json.load(f)
    else:
        mevcut = {"guncellendi": "", "fiyatlar": {}, "yillikFiyatlar": {}}

    if "yillikFiyatlar" not in mevcut:
        mevcut["yillikFiyatlar"] = {}

    yeni_fiyatlar = {}
    yeni_yillik = {}

    for fon in FONLAR:
        print(f"\n{'─'*40}")
        print(f"  {fon}")
        print(f"{'─'*40}")

        # 1. Güncel fiyat
        print(f"📡 Güncel fiyat çekiliyor...", end=" ", flush=True)
        fiyat, tarih = guncel_fiyat_cek(fon)
        if fiyat:
            print(f"✅ {fiyat:.6f} TL ({tarih})")
            yeni_fiyatlar[fon] = {"fiyat": fiyat, "tarih": tarih, "ccy": "TRY"}
        else:
            print(f"❌ Alınamadı")
            if fon in mevcut.get("fiyatlar", {}):
                yeni_fiyatlar[fon] = mevcut["fiyatlar"][fon]
                print(f"   → Eski fiyat korundu: {mevcut['fiyatlar'][fon]['fiyat']}")

        # 2. Yılbaşı fiyatları
        print(f"\n📅 Yılbaşı fiyatları:")
        yil_fiy = yilbasi_fiyatlari_cek(fon, mevcut)
        yeni_yillik[fon] = yil_fiy

    # JSON'u güncelle ve kaydet
    mevcut["guncellendi"] = datetime.now().isoformat()
    mevcut["fiyatlar"] = yeni_fiyatlar
    mevcut["yillikFiyatlar"] = yeni_yillik

    with open(CIKTI_DOSYA, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ fiyatlar.json güncellendi!")
    print(f"📁 {CIKTI_DOSYA}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
