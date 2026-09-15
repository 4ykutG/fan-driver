# MSI GF63 Fan Control

MSI Thin GF63 12VE için GPL-3.0 lisanslı, yalnız fan denetimi yapan Linux
yazılımıdır. Fn+F7 ile Otomatik, Sessiz ve Maksimum Fan modları arasında
geçilir. Yalnız Otomatik mod CPU 90°C'ye ulaştığında Cooler Boost'u açar ve
75°C'ye soğuyunca kapatır. Sessiz ve Maksimum Fan sabit seçimlerdir.

## Güç ayarlarından tamamen bağımsız

Yazılım yalnız şu iki `msi-ec` arayüzüne yazar:

- `/sys/devices/platform/msi-ec/fan_mode`
- `/sys/devices/platform/msi-ec/cooler_boost`

`powerprofilesctl` çalıştırmaz; GNOME/KDE güç moduna, MSI `shift_mode` ve
`super_battery` ayarlarına, CPU/GPU güç limitlerine dokunmaz. Oyun algılamaz ve
GameMode başlatmaz. Bilgisayarın güç/performance seçimi tamamen sende kalır.

Tek istisna denetleyicide değil, kurulum betiğindedir. 0.1.x sürümü
`shift_mode` ve `super_battery` ayarlarını yönetiyordu. 0.2.0 bu kapsamı
bıraktığı için geri de alamaz; yükseltme, EC'yi 0.1.x'in en son yazdığı
değerde bırakır ve en zararlısı olan `turbo`'yu sıfırlayabilecek hiçbir şey
kalmaz. `install-system.sh`, yerinde bir 0.1.x backend bulursa bu kalıntıyı
bir kez serbest bırakır (`turbo` veya `eco` -> `comfort`, `super_battery` ->
`off`) ve bir daha ikisine de dokunmaz.

## Fan modları

| Fn+F7 modu | EC fan ayarı | Cooler Boost |
|---|---|---|
| Otomatik | `auto` | normalde kapalı, 90°C'de zorunlu açık |
| Sessiz | `silent` | daima kapalı |
| Maksimum Fan | `auto` | sürekli açık |

Sessiz mod, 90°C üzerinde bile Cooler Boost açmaz; bu nedenle bilgisayar daha
erken termal yavaşlatma yapabilir. Firmware'in termal yavaşlatma ve acil
kapanma korumaları devre dışı bırakılmaz.

## Desteklenen sistem

- MSI Thin GF63 12VE
- EC firmware `16R8IMS1.107`
- `fan_mode` ve `cooler_boost` arayüzlerini sunan uyumlu `msi-ec` sürücüsü
- Python 3; yedek OSD için GTK 4/PyGObject

## Kurulum

```bash
git clone git@github.com:4ykutG/fan-driver.git
cd fan-driver
make test
sudo ./install-system.sh
```

GNOME eklentisini gerekirse bir kez etkinleştir:

```bash
gnome-extensions enable msi-gf63-profile-osd@4ykutg.github.io
```

Fn+F7 eşlemesi hemen yenilenmezse oturumu kapatıp tekrar aç.
GNOME'da yalnız Shell eklentisi çalışır; GTK yedek OSD ikinci bir panel açmadan
kapanır. Güncelleme sırasında eski dört profilli `msi-profile-osd@local`
eklentisi, kullanıcı oturumu erişilebiliyorsa otomatik kapatılır.

## Elle kullanım

```bash
sudo msi-profile-control set auto
sudo msi-profile-control set silent
sudo msi-profile-control set max
sudo msi-profile-control status
msi-profile-doctor
```

Servis sıcaklığı varsayılan olarak 15 saniyede bir kontrol eder. Aralık
`/etc/msi-profile-control.conf` içinde 5-120 saniye arasında değiştirilebilir.

`make test`, fan işlemleri sırasında sahte `shift_mode` ve güç profili
değerlerinin hiç değişmediğini de doğrular.
