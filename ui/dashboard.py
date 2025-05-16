# Dosya: guard_pc_app/ui/dashboard.py
# Açıklama: Ana gösterge panelini oluşturan modern ve şık bir UI bileşeni.
# Özellikler:
# - Canlı ve modern tasarım: Renkli kartlar, belirgin butonlar, akıcı animasyonlar.
# - Kamera görüntüsü: Canlı kamera akışı, FPS göstergesi ve canlı durumu.
# - Sistem kontrolü: Başlat/Durdur butonları, sistem durumu göstergesi.
# - Son olay: Son düşme olayının detaylarını (zaman, olasılık, ekran görüntüsü) gösterir.
# - Menü: Ayarlar ve Olay Geçmişi'ne geçiş butonları.
# - Düşme uyarısı: Şık bir pop-up penceresi ile risk seviyesine göre renk kodlaması.
# - Asenkron işlem: Kamera güncellemeleri ve görüntü yüklemeleri arka planda çalışır.
# - Uyumluluk: app.py, login.py, history.py ile stil ve renk uyumu (#2196f3, #ffffff).
# Bağımlılıklar: tkinter, PIL, cv2, numpy, threading

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import cv2
from PIL import Image, ImageTk
import numpy as np
import threading
import time
import datetime
import os


class DashboardFrame(tk.Frame):
    """Modern ve şık ana gösterge paneli sınıfı."""

    def __init__(self, parent, user, camera, start_fn, stop_fn, settings_fn, history_fn, logout_fn):
        """
        DashboardFrame sınıfını başlatır ve gerekli parametreleri ayarlar.

        Args:
            parent (ttk.Frame): Üst çerçeve
            user (dict): Kullanıcı bilgileri
            camera (Camera): Kamera nesnesi
            start_fn (function): Algılama başlatma fonksiyonu
            stop_fn (function): Algılama durdurma fonksiyonu
            settings_fn (function): Ayarlar ekranına geçiş fonksiyonu
            history_fn (function): Geçmiş ekranına geçiş fonksiyonu
            logout_fn (function): Çıkış yapma fonksiyonu
        """
        super().__init__(parent)
        
        self.user = user
        self.camera = camera
        self.start_fn = start_fn
        self.stop_fn = stop_fn
        self.settings_fn = settings_fn  # Düzeltildi: 'setin' yerine 'settings_fn'
        self.history_fn = history_fn
        self.logout_fn = logout_fn
        
        # Durum değişkenleri
        self.system_running = False
        self.last_frame = None
        self.last_detection = None
        self.last_detection_time = None
        self.last_detection_confidence = None
        
        # Frame güncelleme kilidi
        self.frame_lock = threading.Lock()
        
        # İkonları yükle
        self.load_icons()
        
        # UI bileşenleri
        self._create_ui()
        
        # Kamera görüntü güncellemesi
        self.update_id = None
        self._start_camera_updates()

    def load_icons(self):
        """
        UI için gerekli ikonları yükler ve ikonları bir sözlüğe kaydeder.
        """
        self.icons = {}
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")
        icons_to_load = {
            "settings": "settings.png",
            "history": "history.png",
            "logout": "logout.png",
            "start": "play.png",
            "stop": "stop.png",
            "user": "user.png",
            "camera": "camera.png",
            "alert": "alert.png",
            "logo": "logo.png"
        }
        
        for name, filename in icons_to_load.items():
            try:
                path = os.path.join(icon_dir, filename)
                if os.path.exists(path):
                    img = Image.open(path).resize((24, 24), Image.LANCZOS)
                    self.icons[name] = ImageTk.PhotoImage(img)
                else:
                    logging.warning(f"İkon dosyası bulunamadı: {path}")
            except Exception as e:
                logging.warning(f"İkon yüklenirken hata: {str(e)}")

    def _create_ui(self):
        """
        Modern ve şık UI bileşenlerini oluşturur ve düzenler.
        """
        self.configure(bg="#f5f5f5")
        self.columnconfigure(0, weight=1)  # Sol panel
        self.columnconfigure(1, weight=3)  # Sağ panel
        self.rowconfigure(0, weight=0)     # Başlık çubuğu
        self.rowconfigure(1, weight=1)     # Ana içerik
        
        # Üst çubuk
        self._create_header()
        
        # Sol ve sağ paneller
        self._create_left_panel()
        self._create_right_panel()

    def _create_header(self):
        """
        Şık ve modern bir üst başlık çubuğu oluşturur.
        Kullanıcı bilgilerini ve çıkış butonunu içerir.
        """
        header = tk.Frame(self, bg="#1a237e", height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="new")
        header.pack_propagate(False)
        
        # Logo ve başlık
        logo_frame = tk.Frame(header, bg="#1a237e")
        logo_frame.pack(side=tk.LEFT, padx=25, pady=10)
        
        if "logo" in self.icons:
            logo_label = tk.Label(logo_frame, image=self.icons["logo"], bg="#1a237e")
            logo_label.pack(side=tk.LEFT, padx=(0, 12))
        
        logo_text = tk.Label(
            logo_frame,
            text="Guard",
            font=("Segoe UI", 22, "bold"),
            fg="#ffffff",
            bg="#1a237e"
        )
        logo_text.pack(side=tk.LEFT)
        
        # Kullanıcı bilgileri ve çıkış butonu
        user_frame = tk.Frame(header, bg="#1a237e")
        user_frame.pack(side=tk.RIGHT, padx=25)
        
        if "user" in self.icons:
            user_icon = tk.Label(user_frame, image=self.icons["user"], bg="#1a237e")
            user_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        user_info = tk.Label(
            user_frame,
            text=self.user.get('displayName', 'Kullanıcı'),
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#1a237e"
        )
        user_info.pack(side=tk.LEFT, padx=(0, 20))
        
        logout_btn = tk.Button(
            user_frame,
            text="Çıkış Yap",
            font=("Segoe UI", 12, "bold"),
            bg="#ff5252",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.logout_fn,
            activebackground="#d32f2f",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        if "logout" in self.icons:
            logout_btn.config(image=self.icons["logout"], compound=tk.LEFT, padx=10)
        logout_btn.pack(side=tk.LEFT)

    def _create_left_panel(self):
        """
        Sol paneli modern ve kullanıcı dostu bir tasarımla oluşturur.
        Sistem kontrolü, menü ve son olay kartlarını içerir.
        """
        left_panel = tk.Frame(self, bg="#f5f5f5")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(25, 15), pady=25)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure((0, 1, 2), weight=0)
        left_panel.rowconfigure(3, weight=1)
        
        # Sistem kontrol kartı
        control_card = self._create_card(left_panel, "Sistem Kontrolü")
        control_card.pack(fill=tk.BOTH, pady=(0, 25))
        
        # Durum göstergesi
        status_frame = tk.Frame(control_card, bg="#ffffff")
        status_frame.pack(fill=tk.X, pady=12)
        
        self.status_var = tk.StringVar(value="Sistem Durduruldu")
        status_text = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 16, "bold"),
            fg="#ff5252",
            bg="#ffffff"
        )
        status_text.pack(side=tk.LEFT, padx=12)
        
        self.status_canvas = tk.Canvas(status_frame, width=24, height=24, bg="#ffffff", highlightthickness=0)
        self.status_canvas.pack(side=tk.RIGHT, padx=12)
        self.status_indicator = self.status_canvas.create_oval(4, 4, 20, 20, fill="#ff5252", outline="")
        
        # Başlat/Durdur butonu
        self.control_var = tk.StringVar(value="Sistemi Başlat")
        self.control_button = tk.Button(
            control_card,
            textvariable=self.control_var,
            font=("Segoe UI", 14, "bold"),
            bg="#00c853",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=12,
            command=self._toggle_system,
            activebackground="#00a742",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        if "start" in self.icons:
            self.control_button.config(image=self.icons["start"], compound=tk.LEFT, padx=12)
        self.control_button.pack(fill=tk.X, pady=12)
        
        # Sistem bilgisi
        info_frame = tk.Frame(control_card, bg="#bbdefb", padx=12, pady=12)
        info_frame.pack(fill=tk.X, pady=12)
        
        tk.Label(
            info_frame,
            text="Sistem Bilgisi",
            font=("Segoe UI", 12, "bold"),
            fg="#0d47a1",
            bg="#bbdefb"
        ).pack(anchor=tk.W)
        
        tk.Label(
            info_frame,
            text="Guard, yapay zeka ile düşme olaylarını algılar ve anında bildirim gönderir.",
            font=("Segoe UI", 10),
            fg="#0d47a1",
            bg="#bbdefb",
            wraplength=260,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
        
        # Menü kartı
        menu_card = self._create_card(left_panel, "Menü")
        menu_card.pack(fill=tk.BOTH, pady=(0, 25))
        
        for text, cmd, icon in [
            ("Ayarlar", self.settings_fn, "settings"),
            ("Olay Geçmişi", self.history_fn, "history")
        ]:
            btn = tk.Button(
                menu_card,
                text=text,
                font=("Segoe UI", 12, "bold"),
                bg="#ffffff",
                fg="#2196f3",
                relief=tk.FLAT,
                padx=20,
                pady=10,
                command=cmd,
                activebackground="#e3f2fd",
                activeforeground="#1976d2",
                cursor="hand2",
                anchor="w"
            )
            if icon in self.icons:
                btn.config(image=self.icons[icon], compound=tk.LEFT, padx=12)
            btn.pack(fill=tk.X, pady=8)
        
        # Son olay kartı
        event_card = self._create_card(left_panel, "Son Algılanan Olay")
        event_card.pack(fill=tk.BOTH)
        
        self.event_time_var = tk.StringVar(value="Henüz olay algılanmadı")
        tk.Label(
            event_card,
            text="Zaman:",
            font=("Segoe UI", 11, "bold"),
            fg="#2c3e50",
            bg="#ffffff"
        ).pack(anchor=tk.W, padx=12, pady=(8, 0))
        tk.Label(
            event_card,
            textvariable=self.event_time_var,
            font=("Segoe UI", 11),
            fg="#2c3e50",
            bg="#ffffff"
        ).pack(anchor=tk.W, padx=12, pady=(0, 8))
        
        self.event_conf_var = tk.StringVar(value="")
        tk.Label(
            event_card,
            text="Olasılık:",
            font=("Segoe UI", 11, "bold"),
            fg="#2c3e50",
            bg="#ffffff"
        ).pack(anchor=tk.W, padx=12, pady=(8, 0))
        tk.Label(
            event_card,
            textvariable=self.event_conf_var,
            font=("Segoe UI", 11),
            fg="#2c3e50",
            bg="#ffffff"
        ).pack(anchor=tk.W, padx=12, pady=(0, 8))
        
        self.event_image_frame = tk.Frame(event_card, bg="#ffffff")
        self.event_image_frame.pack(fill=tk.X, padx=12, pady=12)
        
        self.event_image_container = tk.Frame(
            self.event_image_frame,
            bg="#e0e0e0",
            width=250,
            height=180
        )
        self.event_image_container.pack(fill=tk.X)
        self.event_image_container.pack_propagate(False)
        
        self.no_image_label = tk.Label(
            self.event_image_container,
            text="Henüz düşme algılanmadı",
            font=("Segoe UI", 11),
            fg="#999999",
            bg="#e0e0e0"
        )
        self.no_image_label.pack(expand=True)
        
        self.event_image_label = tk.Label(self.event_image_container, bg="#e0e0e0")

    def _create_right_panel(self):
        """
        Sağ paneli modern ve akıcı bir tasarımla oluşturur.
        Canlı kamera görüntüsünü ve durum göstergesini içerir.
        """
        right_panel = tk.Frame(self, bg="#f5f5f5")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(15, 25), pady=25)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Kamera kartı
        camera_card = self._create_card(right_panel, "Canlı Kamera Görüntüsü")
        camera_card.pack(fill=tk.BOTH, expand=True)
        
        camera_inner = tk.Frame(
            camera_card,
            bg="#000000",
            width=680,
            height=510
        )
        camera_inner.pack(padx=12, pady=12, expand=True)
        camera_inner.pack_propagate(False)
        
        self.camera_label = tk.Label(camera_inner, bg="#000000")
        self.camera_label.pack(expand=True)
        
        # Kamera durumu
        status_frame = tk.Frame(camera_card, bg="#ffffff")
        status_frame.pack(fill=tk.X, padx=12, pady=12)
        
        self.live_canvas = tk.Canvas(status_frame, width=16, height=16, bg="#ffffff", highlightthickness=0)
        self.live_canvas.pack(side=tk.LEFT, padx=8)
        self.live_indicator = self.live_canvas.create_oval(3, 3, 13, 13, fill="#ff5252", outline="")
        
        tk.Label(
            status_frame,
            text="CANLI",
            font=("Segoe UI", 12, "bold"),
            fg="#ff5252",
            bg="#ffffff"
        ).pack(side=tk.LEFT, padx=8)
        
        self.fps_var = tk.StringVar(value="30 FPS")
        tk.Label(
            status_frame,
            textvariable=self.fps_var,
            font=("Segoe UI", 12),
            fg="#999999",
            bg="#ffffff"
        ).pack(side=tk.RIGHT, padx=8)
        
        self._animate_live_indicator()

    def _create_card(self, parent, title):
        """
        Modern ve şık bir kart bileşeni oluşturur.

        Args:
            parent (tk.Frame): Üst çerçeve
            title (str): Kart başlığı

        Returns:
            tk.Frame: Oluşturulan kart çerçevesi
        """
        card = tk.Frame(parent, bg="#ffffff", padx=15, pady=15)
        card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 16, "bold"),
            fg="#2196f3",
            bg="#ffffff"
        ).pack(anchor=tk.W, pady=(0, 12))
        
        return card

    def _animate_live_indicator(self):
        """
        Canlı gösterge için akıcı bir yanıp sönme animasyonu oluşturur.
        """
        try:
            if self.system_running:
                self.live_canvas.itemconfig(self.live_indicator, fill="#ff5252" if time.time() % 0.8 < 0.4 else "#ffffff")
            else:
                self.live_canvas.itemconfig(self.live_indicator, fill="#b0bec5")
        except:
            pass
        self.after(400, self._animate_live_indicator)

    def _start_camera_updates(self):
        """
        Kamera görüntüsünü güncelleme döngüsünü başlatır.
        """
        if self.update_id is not None:
            self.after_cancel(self.update_id)
        self._update_camera_frame()

    def _update_camera_frame(self):
        """
        Kamera karesini akıcı bir şekilde günceller ve FPS değerini hesaplar.
        """
        try:
            if self.camera and self.system_running:
                frame = self.camera.get_frame()
                if frame is not None and frame.size > 0:
                    with self.frame_lock:
                        self.last_frame = frame.copy()
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb).resize((680, 510), Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.camera_label.configure(image=tk_img)
                    self.camera_label.image = tk_img
                    
                    # FPS hesapla
                    self.fps_var.set(f"{int(1000 / 33)} FPS")
        
        except Exception as e:
            logging.error(f"Kamera güncellenirken hata: {str(e)}")
        
        self.update_id = self.after(33, self._update_camera_frame)

    def _toggle_system(self):
        """
        Sistemin başlatılmasını veya durdurulmasını sağlar.
        """
        try:
            if not self.system_running:
                self.start_fn()
            else:
                self.stop_fn()
        except Exception as e:
            logging.error(f"Sistem başlatılırken/durdurulurken hata: {str(e)}")
            messagebox.showerror("Hata", "Sistem başlatılamadı veya durdurulamadı.")

    def update_system_status(self, running):
        """
        Sistem durumunu modern bir şekilde günceller.

        Args:
            running (bool): Sistemin çalışıp çalışmadığı
        """
        self.system_running = running
        self.status_var.set("Sistem Aktif" if running else "Sistem Durduruldu")
        self.status_canvas.itemconfig(self.status_indicator, fill="#00c853" if running else "#ff5252")
        self.control_var.set("Sistemi Durdur" if running else "Sistemi Başlat")
        self.control_button.config(
            bg="#ff5252" if running else "#00c853",
            activebackground="#d32f2f" if running else "#00a742",
            image=self.icons["stop" if running else "start"] if "stop" in self.icons else None
        )

    def update_fall_detection(self, screenshot, confidence, event_data):
        """
        Düşme olayını şık bir şekilde günceller ve kullanıcıyı bilgilendirir.

        Args:
            screenshot (numpy.ndarray): Düşme anındaki ekran görüntüsü
            confidence (float): Düşme olasılığı (0-1 arası)
            event_data (dict): Olay verileri (örneğin, timestamp)
        """
        try:
            with self.frame_lock:
                self.last_detection = screenshot.copy()
                self.last_detection_time = event_data.get("timestamp", time.time())
                self.last_detection_confidence = confidence
            
            # Zaman güncelle
            dt = datetime.datetime.fromtimestamp(self.last_detection_time)
            self.event_time_var.set(dt.strftime("%d.%m.%Y %H:%M:%S"))
            
            # Olasılık güncelle
            self.event_conf_var.set(f"%{confidence * 100:.2f}")
            
            # Ekran görüntüsü güncelle
            self.no_image_label.pack_forget()
            detection_rgb = cv2.cvtColor(self.last_detection, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(detection_rgb).resize((250, 180), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            self.event_image_label.configure(image=tk_img)
            self.event_image_label.image = tk_img
            self.event_image_label.pack(fill=tk.BOTH, expand=True)
            
            # Düşme uyarısı göster
            self._show_fall_alert(confidence)
        
        except Exception as e:
            logging.error(f"Düşme olayı güncellenirken hata: {str(e)}")

    def _show_fall_alert(self, confidence):
        """
        Şık ve modern bir düşme uyarısı pop-up penceresi gösterir.

        Args:
            confidence (float): Düşme olasılığı (0-1 arası)
        """
        alert = tk.Toplevel(self)
        alert.title("Düşme Algılandı!")
        alert.geometry("450x360+500+200")
        alert.configure(bg="#ffffff")
        alert.transient(self)
        alert.grab_set()
        
        # Başlık
        header = tk.Frame(alert, bg="#ff5252", height=90)
        header.pack(fill=tk.X)
        
        if "alert" in self.icons:
            tk.Label(header, image=self.icons["alert"], bg="#ff5252").pack(pady=12)
        
        tk.Label(
            header,
            text="DÜŞME ALGILANDI!",
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#ff5252"
        ).pack()
        
        # İçerik
        content = tk.Frame(alert, bg="#ffffff", padx=25, pady=25)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            content,
            text="Sistem bir düşme olayı tespit etti!",
            font=("Segoe UI", 14, "bold"),
            fg="#2c3e50",
            bg="#ffffff"
        ).pack(pady=12)
        
        tk.Label(
            content,
            text=f"Düşme Olasılığı: %{confidence * 100:.2f}",
            font=("Segoe UI", 12),
            fg="#ff5252",
            bg="#ffffff"
        ).pack()
        
        risk = "Yüksek" if confidence > 0.8 else "Orta" if confidence > 0.6 else "Düşük"
        risk_color = "#ff5252" if confidence > 0.8 else "#ffab40" if confidence > 0.6 else "#00c853"
        tk.Label(
            content,
            text=f"Risk Seviyesi: {risk}",
            font=("Segoe UI", 12),
            fg=risk_color,
            bg="#ffffff"
        ).pack(pady=8)
        
        tk.Label(
            content,
            text="Bildirimler ilgili kişilere gönderildi.",
            font=("Segoe UI", 11),
            fg="#555555",
            bg="#ffffff"
        ).pack(pady=12)
        
        tk.Button(
            content,
            text="Tamam",
            font=("Segoe UI", 12, "bold"),
            bg="#2196f3",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=25,
            pady=10,
            command=alert.destroy,
            activebackground="#1976d2",
            activeforeground="#ffffff",
            cursor="hand2"
        ).pack(pady=12)
        
        # Sesli uyarı (Windows için)
        try:
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
        except:
            logging.warning("Sesli uyarı çalınamadı.")

    def on_destroy(self):
        """
        Temizlik işlemleri için çağrılır.
        Kamera güncelleme döngüsünü durdurur.
        """
        try:
            if self.update_id is not None:
                self.after_cancel(self.update_id)
                self.update_id = None
        except Exception as e:
            logging.error(f"Dashboard kapatılırken hata: {str(e)}")