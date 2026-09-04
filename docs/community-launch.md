# Community launch draft

Do not post this until real-hardware validation is complete, the repository is
public and `v0.1.0` exists.

## English

**MSI GF63 Auto Profile — an open-source MSI Center-style controller for Linux**

I built a small GPL-3.0 userspace controller for MSI Thin GF63 12VE laptops
running Linux. It uses the upstream `msi-ec` driver and adds an Fn+F7 profile
OSD, automatic native Steam/Proton game detection, fixed Turbo + Cooler Boost
during games, delayed return to Balanced, and optional GameMode/NVIDIA PRIME
integration.

Safety is intentionally strict: the first release only writes on Thin GF63
12VE with EC firmware 16R8IMS1.107, never writes raw EC addresses, does not
overclock, and keeps firmware thermal protections enabled.

I am looking for code review, packaging help, desktop/OSD testing and benchmark
feedback from owners of the exact supported hardware. Please read the safety
notes before testing and never post unredacted EC dumps or Steam files.

## Türkçe

**MSI GF63 Auto Profile — Linux için özgür MSI Center tarzı profil aracı**

MSI Thin GF63 12VE için GPL-3.0 lisanslı bir kullanıcı alanı denetleyicisi
geliştirdim. Upstream `msi-ec` sürücüsünü kullanıyor; Fn+F7 profil OSD’si,
Steam/Proton oyun algılama, oyun boyunca sabit Turbo + Cooler Boost, oyun
kapanınca Dengeli moda dönüş ve isteğe bağlı GameMode/NVIDIA PRIME desteği
ekliyor.

İlk sürüm yalnız Thin GF63 12VE / 16R8IMS1.107 üzerinde yazma yapıyor; ham EC
adreslerine dokunmuyor, hız aşırtmıyor ve firmware termal korumalarını açık
tutuyor. Kod incelemesi, paketleme, masaüstü testi ve aynı donanım sahiplerinden
ölçümlü geri bildirim arıyorum.
