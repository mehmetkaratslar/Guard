
# Dosya: guard_pc_app/main.py
# Açıklama: Guard PC uygulamasını başlatan ana giriş noktası.
# Özellikler:
# - Modern ve güvenli yapı: Detaylı hata yönetimi, bağımlılık kontrolü.
# - Splash ekran entegrasyonu: Uygulama başlatılırken şık bir splash ekran gösterir.
# - Bağımlılık kontrolü: Kritik bağımlılıkların varlığını kontrol eder.
# - Çalışma dizini ayarı: Proje kök dizinine geçiş yaparak dosya yollarıyla ilgili sorunları önler.
# - Uygulama ikon ve başlık: Tkinter penceresine özel başlık ve ikon ekler.
# - Uyumluluk: splash.py, app.py, dashboard.py, login.py, history.py, auth.py ile tam uyumlu.
# Bağımlılıklar: tkinter, logging, os, sys, utils.logger, splash, ui.app
import tkinter as tk
from ui.app import GuardApp
import sys
import os
import logging
from utils.logger import setup_logger
from splash import SplashScreen
import traceback

def main():
    """
    Guard PC uygulamasını başlatır.
    """
    setup_logger()
    logging.info("Guard PC Uygulaması başlatılıyor...")

    try:
        root = tk.Tk()
        root.title("Guard - Düşme Algılama Sistemi")
        root.configure(bg="#f5f5f5")
        
        try:
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "resources",
                "icons",
                "logo.png"
            )
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
            else:
                logging.warning(f"Uygulama ikonu bulunamadı: {icon_path}")
        except Exception as e:
            logging.warning(f"Uygulama ikonu yüklenirken hata: {str(e)}")
        
        logging.info("Splash ekranı başlatılıyor...")
        splash = SplashScreen(root, duration=3.0)
        
        logging.info("Ana uygulama başlatılıyor...")
        app = GuardApp(root)
        
        logging.info("Tkinter ana döngüsü başlatılıyor...")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Uygulama çalışırken hata oluştu: {str(e)}", exc_info=True)
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            root.destroy()
            logging.info("Tkinter kaynakları temizlendi.")
        except:
            pass
        logging.info("Uygulama kapanıyor...")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.info(f"Çalışma dizini: {os.getcwd()}")
    
    required_modules = ["PIL", "cv2", "numpy", "pyrebase", "requests"]
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            logging.error(f"Bağımlılık eksik: {module}. Lütfen 'pip install {module}' komutunu çalıştırın.")
            sys.exit(1)
    
    main()