# Yusha Assistant — Mimari

Kişisel Telegram botu. Tek kullanıcı (proje sahibi). Bir Linux VPS üzerinde çalışan
Docker servislerini Telegram üzerinden izlemek ve kontrol etmek için.

## Hedefler

- Telegram'dan VPS'i izlemek: CPU / RAM / disk / uptime, container durumları.
- `telemetria` ve `iposi` API'lerinin çalışıp çalışmadığını hızlıca görmek.
- Çalışmıyorsa **neden** çalışmadığını görmek: log görüntüleme, `inspect` (çıkış kodu,
  restart sayısı, health).
- Gerekirse aksiyon almak: whitelist'teki servisleri yeniden başlatmak, önceden
  tanımlanmış komutları çalıştırmak.
- İleride (Faz 2): aynı VPS'te modlu bir Minecraft sunucusu yayınlayıp bot üzerinden
  başlat/durdur/RCON.

## Hedef olmayanlar (bilinçli)

- Hatırlatıcı / not / görev yönetimi.
- LLM sohbet.
- **Serbest shell** (`/sh <herhangi bir komut>`). Aksiyonlar config'te isimle tanımlı
  komutlarla sınırlı — bkz. "Açık kararlar".
- Çok kullanıcılı / rol tabanlı erişim.

## Genel yapı

```
                 Telegram  (long polling — VPS'e gelen port GEREKMEZ)
                         │
              ┌──────────▼───────────────┐
              │  yusha-assistant (bot)   │  Python container, non-root
              │  python-telegram-bot     │
              │  - auth: tek user ID     │
              │  - /status /ps /logs     │
              │  - /inspect              │
              │  - /restart (onaylı)     │
              │  - /run <isim>           │
              └───┬──────────────┬───────┘
       Docker API │              │ SSH (opsiyonel, /run target: host)
       (kısıtlı)  │              │
        ┌─────────▼──────────┐   │
        │ docker-socket-proxy │  │   host'a: host.docker.internal
        │ tecnativa/...       │  │
        │ izin verilen:       │  │
        │  containers, post,  │  │
        │  exec, tasks        │  │
        │ RO: docker.sock     │  │
        └─────────┬──────────┘   │
                  │ yönetir/okur │
    ┌─────────────┼──────────────┼──────────────┐
 website      telemetria       iposi      (mevcut compose stack — dokunulmaz)
                                                 ▼
                                          (Faz 2) minecraft + mc-backup
```

## Bileşen kararları

| Konu | Karar | Gerekçe |
|---|---|---|
| Platform | Telegram | Resmi Bot API ücretsiz, numara gerektirmez, buton/komut menüsü hazır |
| Dil | Python 3.12+ | Proje sahibi tercihi; zengin ekosistem |
| Bot kütüphanesi | `python-telegram-bot` v21 (async) | En olgun dokümantasyon, stabil |
| Bağlantı modu | Long polling | VPS'te 80/443 web stack'te; gelen port / webhook TLS istemez |
| Docker erişimi | `tecnativa/docker-socket-proxy` üzerinden | Bot doğrudan `docker.sock` görmesin; proxy yalnız `containers` + `post` + `exec` endpoint'lerine izin verir |
| Docker istemcisi | `aiodocker` | Async-native, proxy'ye TCP ile bağlanır |
| Host komutları | `asyncssh` ile VPS'e SSH (opsiyonel) | Container içinden host'ta komut çalıştırmanın temiz yolu; anahtar yoksa özellik kapalı |
| Host metrikleri | `psutil` + host `/proc`, `/` read-only mount | CPU/RAM/disk; container'lar için proxy `stats` |
| Config | `.env` (sırlar + admin ID) + `config.yaml` (servisler + komutlar) | Yeni servis/komut = kod değişikliği yok; sırlar git'e girmez |
| Bağımlılık yönetimi | `uv` | Hızlı, tek `uv.lock` |
| Deploy | Ayrı `docker-compose.yml` projesi | Mevcut stack'ten bağımsız deploy/restart |

## Güvenlik modeli

- **Kimlik doğrulama:** `YUSHA_ADMIN_IDS` içindeki Telegram user ID'leri dışındaki
  herkes `TypeHandler` guard'ında (group -1) reddedilir; hiçbir handler çalışmaz.
- **Yıkıcı aksiyonlar** (`/restart`, `confirm: true` komutlar) inline "Evet / İptal"
  butonuyla onay ister.
- **Docker yüzeyi daraltıldı:** socket proxy yalnız gerekli endpoint'leri açar;
  `docker.sock` bot container'ına asla mount edilmez.
- **Serbest shell yok:** `/run` yalnız `config.yaml` içinde isimle tanımlı, sabit
  `argv` listesine sahip komutları çalıştırır. Kullanıcı Telegram'dan komut metni
  yazamaz, sadece komut *ismi* seçer.
- **SSH anahtarı** (opsiyonel) `./secrets/` altında, read-only mount, git-ignored.
- Yetkisiz erişim denemeleri `WARNING` seviyesinde loglanır.

## Sırlar

| Sır | Yer | Not |
|---|---|---|
| Bot token | `.env` → `YUSHA_BOT_TOKEN` | BotFather |
| Admin ID(ler) | `.env` → `YUSHA_ADMIN_IDS` | virgülle ayrık |
| SSH özel anahtarı | `./secrets/id_ed25519` | opsiyonel; `.env` → `YUSHA_SSH_KEY_PATH` |
| (Faz 2) RCON şifresi | `.env` → `YUSHA_RCON_PASSWORD` | henüz yok |

`.env`, `config.yaml`, `secrets/` → `.gitignore`'da. Şablonlar: `.env.example`,
`config.example.yaml`.

## Deploy

```bash
# VPS'te
git clone <repo> yusha-assistant && cd yusha-assistant
cp .env.example .env            # doldur: BOT_TOKEN, ADMIN_IDS
cp config.example.yaml config.yaml   # servis/komut isimlerini kendi kurulumuna göre düzenle
docker compose up -d --build
docker compose logs -f bot
```

Bot ayrı bir compose projesi (`name: yusha-assistant`); mevcut stack'e dokunmaz.
Socket proxy `yusha-internal` (internal) ağında; bot dışarıya yalnız `default`
ağından (Telegram API) çıkar.

## Faz planı

- **Faz 1 (bu iskelet):** bot + auth + `/status` `/ps` `/logs` `/inspect` `/restart`
  `/run` `/runs`. Socket proxy. Docker deploy.
- **Faz 2:** `docker-compose.mc.yml` — `itzg/minecraft-server` (NEOFORGE/FABRIC,
  modpack), `itzg/mc-backup`. Bot komutları: `/mc status|start|stop|restart|players|
  say|backup|cmd`. RCON (`aio-mc-rcon`) + `mcstatus` ping. `/mc start|stop` async +
  polling; stop = önce RCON `stop`, sonra container. `mem_limit: 9g`, `MEMORY=6G`,
  Aikar flags. VPS'e 2–4 GB swapfile.
- **Faz 3:** log akışı / uyarılar (container `exited` olduğunda push), MC-chat ↔
  Telegram köprüsü, yedek zamanlaması.

## Açık kararlar

1. **Serbest shell.** Şu an yok; `/run` allowlist'le sınırlı. İleride bilinçli bir
   opt-in olarak `YUSHA_ALLOW_RAW_SHELL=true` + `/sh` eklenebilir. Riski: Telegram
   hesabı ele geçerse VPS ele geçer. Varsayılan: kapalı.
2. **Minecraft loader:** NeoForge vs Fabric — Faz 2'de, seçilen modpack'e göre.
3. **Host disk mount:** `/` read-only mount ediliyor (disk kullanımı için). İstenirse
   yalnız veri bölümü path'iyle sınırlandırılabilir.
