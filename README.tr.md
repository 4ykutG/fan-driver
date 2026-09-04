# MSI GF63 Otomatik Profil

MSI Thin GF63 12VE için Linux üzerinde çalışan özgür bir MSI Center
alternatifidir. Fn+F7 profil ekranı, otomatik oyun algılama, oyun sırasında
maksimum fan ve GameMode/RTX 4050 entegrasyonu sağlar.

> **Dikkat:** 0.1.0 sürümü yalnız `Thin GF63 12VE` ve
> `16R8IMS1.107` EC firmware’i için yazma yapar. Başka bir model veya firmware
> algılarsa güvenlik amacıyla çalışmayı reddeder.

## Davranış

- Fn+F7: Süper Pil → Sessiz → Dengeli → Performans kartlarını gösterir.
- Steam/Proton oyunu açılınca: Turbo + Cooler Boost sabitlenir.
- Oyun sırasında yazılımsal ısı eşiği profil veya fan modunu değiştirmez.
- Son oyun kapandıktan 8 saniye sonra Dengeli moda döner.
- BIOS/EC sıcaklık kısma ve acil kapanma korumalarına dokunulmaz.
- Bilinmeyen firmware’e EC yazması yapılmaz.

Bu proje yeni bir çekirdek fan sürücüsü değildir; açık kaynak
[`msi-ec`](https://github.com/BeardOverflow/msi-ec) sürücüsünün güvenli kullanıcı
alanı denetleyicisidir.

## Kurulum

```bash
git clone https://github.com/4ykutG/fan-driver.git
cd fan-driver
sudo ./install-system.sh
gnome-extensions enable msi-gf63-profile-osd@4ykutg.github.io
```

CachyOS/Arch üzerinde GameMode, MangoHud, NVIDIA PRIME ve CS2 ayarı:

```bash
sudo ./gaming-setup.sh --configure-cs2
```

CS2 Steam başlatma seçeneği `msi-game-run %command%` olur. Steam dosyası
değiştirilmeden önce zaman damgalı yedek alınır.

Steam dışı oyunların çalıştırılabilir dosya adlarını
`/etc/msi-profile-games.conf` dosyasına birer satır olarak ekleyebilirsiniz.

Oyun tarama, kapanış gecikmesi ve günlük termal kontrol süreleri
`/etc/msi-profile-control.conf` dosyasından güvenli sınırlar içinde
değiştirilebilir. Sonrasında `sudo systemctl restart msi-profile-hotkeyd`
çalıştırılır.

Destek isterken kişisel veri toplamayan salt-okunur tanı çıktısı:

```bash
msi-profile-doctor --json
```

## Kaldırma ve test

```bash
make test
sudo ./uninstall.sh
```

Windows’tan daha yüksek FPS garanti edilemez. Bu araç yanlış GPU/profil
seçimini düzeltir; GPU’ya hız aşırtma yapmaz ve 45 W firmware sınırını aşmaz.

Lisans: GPL-3.0-or-later. Ayrıntılar için [LICENSE](LICENSE).
