"""
FULL Servis AGENT uygulaması — Mac/Windows client'larda ÇİFT TIKLANAN giriş noktası.

Son kullanıcı akışı: uygulamaya çift tıklar →
  1) uygulama kendi DOSYA ADINDAN hangi bilgisayar olduğunu çözer
     (FULLSERVIS-MAC-WIFI → mac_wifi, FULLSERVIS-MAC-KABLO → mac_cable,
      FULLSERVIS-WINDOWS-WIFI → win_wifi),
  2) o portta takılı kalmış eski örnek kapatılır,
  3) sunucuya kaydolur (heartbeat) ve panelde YEŞİL görünür,
  4) sunucudan gelen "Başlat" komutuyla kendi testlerini koşar.

Eskiden elle yazılan `python run_agent.py mac_wifi http://192.168.1.10:8770`
komutunun yerine geçer. Kimlik/adres çözümü (dosya adı → ayarlar/agent.json →
FS_NODE_ID / FS_SERVER_URL) `common/config.py` içindedir.

Bu dosya PyInstaller'ın giriş scriptidir (`fullservis_agent.spec`). Kaynaktan da
çalışır: `python launchers/build/agent_app.py mac_wifi`.
"""
import os
import sys

# Kaynaktan çalışırken backend paketlerini (common/, agent/) import yoluna ekle.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.abspath(os.path.join(_HERE, "..", "..", "fullservice-backend"))
if os.path.isdir(_BACKEND) and _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _fail_unknown_node(config):
    """node_id çözülemediğinde son kullanıcıya ne yapacağını anlatıp çıkar."""
    names = [f"{n['id']:<12} → {n.get('label', '')}"
             for n in config.get("nodes", []) if not n.get("is_server")]
    print("\n" + "!" * 62)
    print("Bu uygulamanin HANGI bilgisayara ait oldugu anlasilamadi.")
    print("!" * 62)
    print("\nCozum 1 — dosya adini duzeltin (onerilen):")
    print("    FULLSERVIS-MAC-WIFI      → MAC (Wi-Fi)")
    print("    FULLSERVIS-MAC-KABLO     → MAC (Kablo)")
    print("    FULLSERVIS-WINDOWS-WIFI  → WINDOWS (Wi-Fi)")
    print("\nCozum 2 — uygulamanin yanina 'ayarlar/agent.json' koyun:")
    print('    { "node_id": "mac_wifi", "server_url": "http://192.168.1.10:8770" }')
    print("\nGecerli node_id degerleri:")
    for line in names:
        print(f"    {line}")
    print("\nKapatmak icin ENTER'a basin...")
    try:
        input()
    except Exception:
        pass
    sys.exit(1)


def main():
    """Agent'ı başlatır: kimliği çöz → eski örneği kapat → sunucuya kaydol → uvicorn."""
    from common import app_boot
    from common.config import (
        APP_DIR, CONFIG_PATH, LOGS_DIR,
        load_agent_settings, load_config, resolve_node_id, resolve_server_url,
    )

    config = load_config()
    explicit = sys.argv[1] if len(sys.argv) > 1 else None
    node_id = resolve_node_id(explicit, config)
    if not node_id:
        _fail_unknown_node(config)

    server_url = (sys.argv[2] if len(sys.argv) > 2 else "") or resolve_server_url(config)
    settings = load_agent_settings()
    port = int(
        (sys.argv[3] if len(sys.argv) > 3 else "")
        or os.environ.get("FS_AGENT_PORT")
        or settings.get("agent_port")
        or config.get("agent_port", 7531)
    )

    node = next((n for n in config.get("nodes", []) if n.get("id") == node_id), {})
    app_boot.banner(f"FULL SERVIS — AGENT [{node.get('label', node_id)}]", [
        f"Bilgisayar : {node_id}  (loglar: {node.get('log_name', node_id.upper())})",
        f"Sunucu     : {server_url}",
        f"Testler    : {', '.join(node.get('roles', [])) or '-'}",
        f"Ayarlar    : {CONFIG_PATH}",
        f"Loglar     : {LOGS_DIR}",
        f"Klasor     : {APP_DIR}",
        "",
        "Sunucu panelinde bu makine YESIL yaninca hazirsiniz.",
        "Bu pencereyi KAPATMAYIN — kapatirsaniz makine panelden duser.",
    ])

    # agent.main bu ortam değişkenlerini import anında okur → önce ayarla, sonra import et.
    os.environ["FS_NODE_ID"] = node_id
    os.environ["FS_SERVER_URL"] = server_url
    os.environ["FS_AGENT_PORT"] = str(port)

    app_boot.free_port(port)

    import uvicorn
    from agent.main import app, LAN_IP

    print(f"[AGENT] node_id={node_id} port={port} server={server_url} lan_ip={LAN_IP}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[AGENT] Kapatildi.")
    except BaseException as e:          # pencere anında kapanmasın, hata okunsun
        from common import app_boot
        app_boot.hold_on_error(e)
