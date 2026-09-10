# Yusha Assistant

Kişisel Telegram botu — bir Linux VPS'teki Docker servislerini Telegram üzerinden
izlemek ve kontrol etmek için. Tek kullanıcılı.

Mimari ve kararlar: [ARCHITECTURE.md](ARCHITECTURE.md).

## Komutlar

| Komut | Açıklama |
|---|---|
| `/status` | Host CPU/RAM/disk/uptime + izlenen container'ların durumu |
| `/ps` | Tüm container'lar (durum tablosu) |
| `/logs <servis> [satır]` | Container logları (varsayılan son 80, en fazla 400 satır) |
| `/inspect <servis>` | Durum, çıkış kodu, restart sayısı, health |
| `/restart <servis>` | Yeniden başlat — inline onay ister |
| `/run <isim>` | `config.yaml`'da tanımlı komutu çalıştır |
| `/runs` | Tanımlı komutları listele |
| `/help` | Yardım |

"Servis" = `config.yaml` içinde tanımladığın isim; arkasındaki `container` gerçek
Docker container adı.

## Kurulum (VPS'te deploy)

```bash
git clone <repo-url> yusha-assistant
cd yusha-assistant

cp .env.example .env
#  YUSHA_BOT_TOKEN  -> BotFather'dan yeni bot aç, token'ı yapıştır
#  YUSHA_ADMIN_IDS  -> kendi Telegram numeric user ID'in (@userinfobot verir)

cp config.example.yaml config.yaml
#  services: kendi container adlarınla (telemetria, iposi, ...) güncelle
#  commands: /run ile çalıştırmak istediğin sabit komutları tanımla

docker compose up -d --build
docker compose logs -f bot        # "Bağlandı: @botadi" görmelisin
```

Telegram'da bota `/start` yaz.

### Host komutları (opsiyonel — `/run` target: host)

`target: host` olan komutlar VPS'e SSH ile bağlanır. Etkinleştirmek için:

```bash
mkdir -p secrets
ssh-keygen -t ed25519 -f secrets/id_ed25519 -N ""
cat secrets/id_ed25519.pub >> ~/.ssh/authorized_keys   # VPS kullanıcın
ssh-keyscan -H host.docker.internal > secrets/known_hosts  # ya da VPS IP'si
```

`.env` içinde:

```
YUSHA_SSH_HOST=host.docker.internal
YUSHA_SSH_USER=<vps-kullanıcın>
YUSHA_SSH_KEY_PATH=/app/secrets/id_ed25519
YUSHA_SSH_KNOWN_HOSTS=/app/secrets/known_hosts
```

SSH yapılandırılmazsa `target: host` komutları çalışmaz ve bot bunu açıkça söyler.
`target: container:<ad>` komutları SSH'siz de çalışır (`docker exec`).

## Yerel geliştirme

`uv` gerekir ([kurulum](https://docs.astral.sh/uv/getting-started/installation/)).

```bash
uv sync
cp .env.example .env && cp config.example.yaml config.yaml   # doldur
uv run yusha          # long polling başlar

uv run pytest         # testler
uv run ruff check .   # lint
uv run mypy src       # tip kontrolü
```

Docker Desktop yerelde çalışıyorsa `YUSHA_DOCKER_HOST` yerine
`unix:///var/run/docker.sock` verebilir ve socket proxy'siz test edebilirsin (yerelde,
prod'da DEĞİL).

## Yapılandırma referansı

### `.env`

| Değişken | Zorunlu | Varsayılan | Açıklama |
|---|---|---|---|
| `YUSHA_BOT_TOKEN` | ✅ | — | BotFather token |
| `YUSHA_ADMIN_IDS` | ✅ | — | İzinli Telegram user ID'leri, virgülle |
| `YUSHA_DOCKER_HOST` | | `tcp://docker-socket-proxy:2375` | Docker API adresi |
| `YUSHA_CONFIG_PATH` | | `config.yaml` | Servis/komut config yolu |
| `YUSHA_HOST_PROC` | | `/proc` | psutil için host procfs mount'u |
| `YUSHA_HOST_ROOT` | | `/` | Disk kullanımı ölçülen path |
| `YUSHA_SSH_*` | | — | Host komutları için (yukarı bkz.) |
| `YUSHA_LOG_TAIL_DEFAULT` | | `80` | `/logs` varsayılan satır |
| `YUSHA_LOG_TAIL_MAX` | | `400` | `/logs` üst sınır |
| `YUSHA_COMMAND_TIMEOUT` | | `30` | `/run` komut zaman aşımı (sn) |

### `config.yaml`

```yaml
services:
  - name: iposi            # /logs iposi  gibi kullanılır
    container: iposi        # gerçek docker container adı
    actions: [logs, inspect, restart]   # izin verilen aksiyonlar

commands:
  - name: disk             # /run disk
    description: "Disk kullanımı"
    target: host           # "host" | "container:<ad>"
    argv: ["df", "-h"]     # SABİT argüman listesi — kullanıcı metin giremez
    confirm: false         # true -> çalıştırmadan önce onay ister
```

## Güvenlik notu

- Bot yalnız `YUSHA_ADMIN_IDS`'teki kişilere yanıt verir; başkası yazarsa reddedilir
  ve loglanır.
- `/run` **serbest shell değildir** — sadece `config.yaml`'daki isimli komutları
  çalıştırır.
- `docker.sock` bota mount edilmez; erişim kısıtlı socket proxy üzerinden.
- `.env`, `config.yaml`, `secrets/` git'e girmez.
