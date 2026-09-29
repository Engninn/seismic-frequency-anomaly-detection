import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import detrend

def saf_mseed_okuyucu(dosya_yolu):
    try:
        with open(dosya_yolu, 'rb') as f:
            veri_bloklari = []
            sample_rate = 100.0
            header = f.read(48)
            f.seek(0)
            while True:
                h = f.read(48)
                if len(h) < 48: break
                num_samples = int.from_bytes(h[30:32], byteorder='big')
                ham_data = f.read(464)
                if len(ham_data) < 464: break
                blok_verisi = np.frombuffer(ham_data, dtype='>i4', count=min(num_samples, 116))
                veri_bloklari.extend(blok_verisi)
        return np.array(veri_bloklari), sample_rate
    except:
        return None, None

def timeline_ciz(klasor_yolu="."):
    sismik_dosyalar = glob.glob(os.path.join(klasor_yolu, "*.mseed")) + glob.glob(os.path.join(klasor_yolu, "*.miniseed"))
    if not sismik_dosyalar:
        print("Hata: .mseed dosyası bulunamadı!")
        return

    print(f"--- 3. ETAP: Marmara Mikro-Kadraj Timeline Motoru Tetiklendi ({len(sismik_dosyalar)} Dosya) ---")
    
    gecerli_veriler = []
    for dosya in sismik_dosyalar:
        data, fs = saf_mseed_okuyucu(dosya)
        if data is None or len(data) < 10000: continue
        gecerli_veriler.append((data, fs, os.path.basename(dosya)))

    # MARMARA MİKRO DEPREM SABİTLERİ (60 Saniye Öncül Süre Odaklı Dar Kadraj)
    ortak_zaman = np.linspace(-100, 200, 400)
    tarama_oncesi, tarama_sonrasi = 110, 210
    pencere_boyutu, kayma_adimi = int(2.56 * 100), int(0.5 * 100)
    otomatik_delta_t_sn = 60.0
    drop_faz_sn = 25.0
    x_min, x_max = -100.0, 200.0

    plt.figure(figsize=(14, 7))
    ax = plt.gca()
    ax.set_facecolor('#FFF8F0')
    butun_frekans_trendleri = []

    for data, fs, dosya_adi in gecerli_veriler:
        try:
            data_clean = detrend(data - np.mean(data), type='linear')
            deprem_merkez_idx = np.argmax(np.abs(data_clean))
            
            baslangic = max(0, deprem_merkez_idx - int(tarama_oncesi * fs))
            bitis = min(len(data_clean), deprem_merkez_idx + int(tarama_sonrasi * fs))
            
            zamanlar_xp, baskin_frekanslar_fp = [], []
            for idx in range(baslangic, bitis - pencere_boyutu, kayma_adimi):
                p_verisi = data_clean[idx:idx + pencere_boyutu]
                N = len(p_verisi)
                fft_res = np.fft.fft(p_verisi - np.mean(p_verisi))
                fft_genlik = np.abs(fft_res)[:N//2]
                frekanslar = np.fft.fftfreq(N, d=1/fs)[:N//2]
                sismik_idx = np.where((frekanslar >= 0.5) & (frekanslar <= 15.0))
                if len(sismik_idx) == 0: continue
                baskin_f = frekanslar[sismik_idx][np.argmax(fft_genlik[sismik_idx])]
                goreli_sn = (idx + pencere_boyutu/2 - deprem_merkez_idx) / fs
                zamanlar_xp.append(goreli_sn)
                baskin_frekanslar_fp.append(baskin_f)
                
            zamanlar_xp = np.array(zamanlar_xp).ravel()
            baskin_frekanslar_fp = np.array(baskin_frekanslar_fp).ravel()
            
            if len(zamanlar_xp) == len(baskin_frekanslar_fp) and len(zamanlar_xp) > 5:
                iz_interp = np.interp(ortak_zaman, zamanlar_xp, baskin_frekanslar_fp)
                plt.plot(ortak_zaman, iz_interp, color='crimson', alpha=0.15, linewidth=0.5)
                butun_frekans_trendleri.append(iz_interp)
        except Exception as e:
            continue

    if not butun_frekans_trendleri:
        print("Hata: Cizilebilecek ortak iz uretilemedi.")
        return

    medyan_trend = np.median(butun_frekans_trendleri, axis=0)
    plt.plot(ortak_zaman, medyan_trend, color='darkred', linewidth=3, label='Bölgesel Ağ Ortak Hâkim Frekans Yolu (Kolektif fd)')
    
    ofset = 5
    plt.axvspan(-otomatik_delta_t_sn, 0, color='blue', alpha=0.04)
    
    plt.axvline(x=-otomatik_delta_t_sn, color='orange', linestyle='-.', linewidth=2)
    plt.text(-otomatik_delta_t_sn + ofset, 5.0, f'Phase 2: Stress Jump Inception\n(t = -{otomatik_delta_t_sn:.0f} s)', color='orange', fontsize=10, fontweight='bold', rotation=90, va='bottom')
    
    plt.axvline(x=-drop_faz_sn, color='blue', linestyle='--', linewidth=2)
    plt.text(-drop_faz_sn + ofset, 5.0, f'Phase 3: The Drop\n(t = -{drop_faz_sn:.0f} s)', color='blue', fontsize=10, fontweight='bold', rotation=90, va='bottom')
    
    plt.axvline(x=0, color='black', linestyle='-', linewidth=2.5)
    plt.text(0 + ofset, 6.0, 'Phase 4: Mainshock (T0)\n(t = 0 s)', color='black', fontsize=10, fontweight='bold', rotation=90, va='bottom')

    plt.title(f"Figure 4: Marmara Local Network Timeline Tracking (Ml 3.5) - {len(butun_frekans_trendleri)} Channels", fontsize=12, fontweight='bold')
    plt.xlabel("Relative Time (Seconds) [0 = Mainshock Rupture Time]", fontsize=11)
    plt.ylabel("Predominant Frequency (Hz)", fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.5)
    
    plt.xlim(x_min, x_max)
    plt.ylim(0.5, 15.0)
    plt.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig("Figure_4_Empirical_Timeline_Tracking.png", dpi=300)
    print("\n-> BAŞARILI: Marmara mikro deprem odaklı dar kadraj grafiği üretildi!")
    plt.show()

if __name__ == "__main__":
    timeline_ciz(".")
