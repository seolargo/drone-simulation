"""
Drone simülasyonu — giriş noktası.

Drone'a yalnızca yerçekimi etki eder ve yukarıdan aşağıya düşer.

Çalıştırma:
    ~/Downloads/simulation/.venv/bin/python main.py

Kontroller:
    BOŞLUK : duraklat / devam et
    R      : sıfırla (drone'u tepeye geri al)
    ESC/Q  : çıkış

Kod yapısı:
    config.py    -> ayarlar/sabitler
    physics/     -> fizik modelleri (yerçekimi, entegrasyon)
    entities/    -> drone gibi nesneler
    rendering/   -> çizim
    simulation/  -> uygulama döngüsü
"""

from simulation import App


def main():
    App().run()


if __name__ == "__main__":
    main()
