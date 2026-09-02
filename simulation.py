import numpy as np
import matplotlib.pyplot as plt

# Zaman dizisi: Depreme son 48 saat (Dakika bazında)
hours = 48
minutes = hours * 60
t = np.linspace(-hours, 0, minutes) # 0 anı deprem anıdır

# 1. Normal Arka Plan Frekansı (Baz Çizgisi)
base_freq = 2.5
noise = np.random.normal(0, 0.15, minutes)
freq_series = base_freq + noise

# 2. Öncül Sinyal Oluşturma (48 saatten itibaren artış)
# Stres artışı: Son 24 saatte hızlanan bir logaritmik/üstel artış varsayımı
stress_effect = np.where(t > -48, (np.exp((t + 48) / 15) * 0.2), 0)
freq_series += stress_effect

# 3. Son 3 Saatteki "Sismik Sessizlik/Kilitlenme" (Düşüş)
freq_series[t > -3] -= (np.exp((t[t > -3] + 3)) * 0.4)

# Kritik Eşik (Z=3 seviyesi yaklaşık 3.0 Hz olsun)
threshold = 3.1

# Görselleştirme
plt.figure(figsize=(14, 7))
plt.plot(t, freq_series, color='gray', alpha=0.5, label='Anlık Dominant Frekans (Hz)')

# Hareketli Ortalama (Trendi görmek için)
rolling_avg = np.convolve(freq_series, np.ones(60)/60, mode='same')
plt.plot(t, rolling_avg, color='darkred', linewidth=2, label='Trend (1 Saatlik Ort.)')

# Kritik Eşik Çizgisi
plt.axhline(y=threshold, color='orange', linestyle='--', label='Kritik Eşik (Z > 3)')

# Önemli Zaman İşaretleri
plt.axvline(x=-24, color='green', alpha=0.3, linestyle=':')
plt.text(-24.5, 4.5, 'Stres Hızlanma Fazı', rotation=90, color='green')

plt.axvline(x=-6, color='red', alpha=0.3, linestyle=':')
plt.text(-6.5, 4.5, 'Kritik Risk Penceresi', rotation=90, color='red')

plt.title("Deprem Öncesi Hakim Frekans Değişimi (Zaman Serisi Analizi)", fontsize=14)
plt.xlabel("Depreme Kalan Süre (Saat)", fontsize=12)
plt.ylabel("Dominant Frekans (Hz)", fontsize=12)
plt.xlim(-48, 0)
plt.ylim(2, 5.5)
plt.legend(loc='upper left')
plt.grid(True, which='both', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()
