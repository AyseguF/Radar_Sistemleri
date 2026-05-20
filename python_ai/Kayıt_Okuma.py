import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import stepic

def dosya_sec_pencereli():
    """
    Kullanıcıya dosya gezginini açarak bir PNG dosyası seçtirir.
    """
    # Tkinter altyapısını görünmez olarak başlatıyoruz (boş pencere açılmasın diye)
    root = tk.Tk()
    root.withdraw()
    
    # Her zaman en üstte açılması için güvenliğe alalım
    root.attributes('-topmost', True)
    
    print("📂 Dosya Gezgini açıldı... Lütfen analiz edilecek tehdit resmini seçin.")
    
    # Sadece PNG dosyalarını filtreleyerek gezgini açıyoruz
    dosya_yolu = filedialog.askopenfilename(
        title="Analiz Edilecek Tehdit Görselini Seçin",
        filetypes=[("PNG Görselleri", "*.png"), ("Tüm Dosyalar", "*.*")]
    )
    
    return dosya_yolu

def gizli_veriyi_oku(resim_yolu):
    """
    Seçilen görselin içerisindeki stepic ile gizlenmiş metni çözer.
    """
    try:
        img = Image.open(resim_yolu)
        gizli_veri_bayt = stepic.decode(img)

        # Eğer gelen veri byte ise decode et, zaten string ise doğrudan yazdır
        if isinstance(gizli_veri_bayt, bytes):
            gizli_mesaj = gizli_veri_bayt.decode('utf-8')
        else:
            gizli_mesaj = gizli_veri_bayt
            return gizli_mesaj.strip('\x00').strip()
    except Exception as e:
        return f"HATA (Veri okunurken sorun oluştu): {e}"

def raporu_yazdir(dosya_yolu, mesaj):
    """
    Çözülen veriyi parçalayıp terminale şık bir rapor halinde basar.
    """
    dosya_adi = os.path.basename(dosya_yolu)
    print("\n" + "=" * 60)
    print(f"📁 DOSYA: {dosya_adi}")
    print(f"📍 YOL: {dosya_yolu}")
    print("=" * 60)
    
    # Örnek format: "Etiket:Ucak|Hiz:12.45m/s|Aci:85|Mesafe:32cm|Yon:YAKLASIYOR"
    if "|" in mesaj:
        parcalar = mesaj.split("|")
        print("📊 TELEMETRİ VE TESPİT RAPORU:")
        for parca in parcalar:
            if ":" in parca:
                anahtar, deger = parca.split(":", 1)
                
                # 🌟 DÜZELTME: Sağındaki solundaki görünmez boşlukları temizliyoruz
                anahtar = anahtar.strip()
                deger = deger.strip()

                # Türkçe etiket eşleştirmeleri
                if anahtar == "Etiket": anahtar = "Tehdit Sınıfı"
                elif anahtar == "Hiz": anahtar = "Hesaplanan Hız"
                elif anahtar == "Aci": anahtar = "Radar Algılama Açısı"
                elif anahtar == "Mesafe": anahtar = "Hedef Uzaklığı"
                elif anahtar == "Yon": anahtar = "Hareket Yönü" # Yeni eklenen alan     
                
                # Eğer yaklaşan bir tehditse terminalde dikkat çeksin
                if anahtar == "Hareket Yönü" and "YAKLASIYOR" in deger:
                    print(f"   🚨 {anahtar}: {deger} ⚠️")
                else:
                    print(f"   ⚡ {anahtar}: {deger}")
    else:
        print(f"   📝 Sistem Notu: {mesaj}")
    print("=" * 60 + "\n")

def ana_fonksiyon():

    import sys
    if sys.platform == "win32":
        os.system('chcp 65001 > nul')  # Windows'ta UTF-8 desteği için kod sayfasını değiştir

    print("============================================================")
    print("     AI-RADAR SİSTEMİ DOSYA GEZGİNİ ANALİZ MODÜLÜ (v2.0)    ")
    print("============================================================\n")
    
    # Kullanıcıdan dosya seçmesini iste
    secilen_resim = dosya_sec_pencereli() 
    if not secilen_resim:
        print("❌ Dosya seçimi iptal edildi. Program kapatılıyor.")
        return
        
    # Gizli metni sök ve raporla
    cozulen_mesaj = gizli_veriyi_oku(secilen_resim)
    raporu_yazdir(secilen_resim, cozulen_mesaj)

if __name__ == "__main__":
    ana_fonksiyon()