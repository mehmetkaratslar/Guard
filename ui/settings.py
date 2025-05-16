# Dosya: guard_pc_app/ui/settings.py
# Açıklama: Kullanıcı ayarlarını yöneten modern ve şık bir UI bileşeni.
# Özellikler:
# - Şık ve renkli tasarım: Canlı renk paleti, belirgin butonlar, akıcı animasyonlar.
# - Sekmeli arayüz: Kullanıcı Bilgileri, Bildirim Ayarları ve Görünüm Ayarları sekmeleri.
# - Kullanıcı bilgileri: Profil avatarı, ad soyad ve e-posta düzenleme.
# - Bildirim ayarları: E-posta, SMS ve Telegram bildirim seçenekleri, test butonları.
# - Görünüm ayarları: Açık/koyu tema seçimi, renk paleti özelleştirme.
# - Animasyonlar: Tema geçiş animasyonu, sekme seçimi animasyonu.
# - Hata yönetimi: Sağlam try-except blokları ve kullanıcı dostu mesajlar.
# - Uyumluluk: app.py, dashboard.py, login.py ile stil ve renk uyumu (#2196f3, #ffffff).
# Bağımlılıklar: tkinter, PIL, winreg (Windows için), subprocess

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import logging
import threading
import os
import time
from PIL import Image, ImageTk, ImageEnhance, ImageFilter


class SettingsFrame(tk.Frame):
    """Modern ve şık görünümlü ayarlar ekranı sınıfı."""

    def __init__(self, parent, user, db_manager, back_fn):
        """
        SettingsFrame sınıfını başlatır ve gerekli parametreleri ayarlar.

        Args:
            parent (tk.Frame): Üst çerçeve
            user (dict): Kullanıcı bilgileri
            db_manager (FirestoreManager): Veritabanı yönetici nesnesi
            back_fn (function): Geri dönüş fonksiyonu
        """
        super().__init__(parent)
        
        self.user = user
        self.db_manager = db_manager
        self.back_fn = back_fn
        
        # Kullanıcı ayarlarını yükle
        self.user_data = self.db_manager.get_user_data(user["localId"])
        self.settings = self.user_data.get("settings", {}) if self.user_data else {}
        
        # İkonları yükle
        self.load_icons()
        
        # Dark mode algılama
        self.dark_mode = self._detect_dark_mode()
        
        # Tema renklerini ayarla
        self._setup_colors()
        
        # Stilleri ayarla
        self._setup_styles()
        
        # UI bileşenleri
        self._create_ui()
        
        # Kayıt hareketlerini saklamak için değişken
        self.is_modified = False
        
        # Pencere yeniden boyutlandırma işleyicisi
        self.bind("<Configure>", self._on_configure)

    def _detect_dark_mode(self):
        """
        Sistem temasını algılar (açık/koyu mod).

        Returns:
            bool: True eğer koyu mod aktifse, aksi halde False.
        """
        try:
            if os.name == "nt":  # Windows
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            elif os.name == "posix" and os.uname().sysname == "Darwin":  # macOS
                import subprocess
                cmd = "defaults read -g AppleInterfaceStyle"
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                return p.stdout.read().decode().strip() == "Dark"
            elif os.name == "posix":  # Linux (GNOME)
                import subprocess
                cmd = "gsettings get org.gnome.desktop.interface gtk-theme"
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output = p.stdout.read().decode().strip()
                return "dark" in output.lower()
        except Exception as e:
            logging.warning(f"Tema algılama sırasında hata: {str(e)}")
        return False
    
    def _setup_colors(self):
        """
        Tema renklerini ayarlar (açık veya koyu mod).
        """
        if self.dark_mode:
            self.bg_color = "#121212"
            self.card_bg = "#1E1E1E"
            self.header_bg = "#0288d1"
            self.accent_color = "#2196f3"
            self.accent_light = "#42a5f5"
            self.text_color = "#FFFFFF"
            self.text_secondary = "#B0BEC5"
            self.input_bg = "#2A2A2A"
            self.success_color = "#00c853"
            self.warning_color = "#ffab40"
            self.danger_color = "#ff5252"
            self.button_bg = "#333333"
            self.button_fg = "#FFFFFF"
            self.highlight_color = "#2d2d2d"
            self.info_bg = "#0d47a1"
            self.info_fg = "#90caf9"
        else:
            self.bg_color = "#F8F9FA"
            self.card_bg = "#FFFFFF"
            self.header_bg = "#2196f3"
            self.accent_color = "#2196f3"
            self.accent_light = "#42a5f5"
            self.text_color = "#2c3e50"
            self.text_secondary = "#78909c"
            self.input_bg = "#F0F0F0"
            self.success_color = "#00c853"
            self.warning_color = "#ffab40"
            self.danger_color = "#ff5252"
            self.button_bg = "#EFEFEF"
            self.button_fg = "#2c3e50"
            self.highlight_color = "#e3f2fd"
            self.info_bg = "#bbdefb"
            self.info_fg = "#0d47a1"
    
    def _setup_styles(self):
        """
        Uygulama stillerini oluşturur ve tanımlar.
        """
        style = ttk.Style()
        
        # Ana çerçeve stili
        style.configure("MainFrame.TFrame", background=self.bg_color)
        
        # Kart stili
        style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        
        # Header stili
        style.configure("Header.TFrame", background=self.header_bg)
        
        # Başlık etiketleri
        style.configure("Title.TLabel", 
                        background=self.header_bg,
                        foreground="#ffffff", 
                        font=("Segoe UI", 20, "bold"))
        
        # Alt başlık etiketleri
        style.configure("Section.TLabel", 
                        background=self.card_bg,
                        foreground=self.text_color, 
                        font=("Segoe UI", 16, "bold"))
        
        # Standart etiketler
        style.configure("TLabel", 
                        background=self.card_bg,
                        foreground=self.text_color, 
                        font=("Segoe UI", 12))
        
        # Bilgi etiketleri
        style.configure("Info.TLabel", 
                        background=self.card_bg,
                        foreground=self.text_secondary, 
                        font=("Segoe UI", 11))
        
        # Başlık etiketleri
        style.configure("Header.TLabel", 
                        background=self.header_bg,
                        foreground="#ffffff", 
                        font=("Segoe UI", 14, "bold"))
        
        # Info kart etiketleri
        style.configure("InfoCard.TLabel", 
                        background=self.info_bg,
                        foreground=self.info_fg, 
                        font=("Segoe UI", 12))
        
        # Standart butonlar
        style.configure("TButton", 
                        background=self.button_bg,
                        foreground=self.button_fg,
                        font=("Segoe UI", 12), 
                        relief="flat", 
                        borderwidth=0,
                        padding=8)
        style.map("TButton",
                 background=[("active", self.accent_light), ("pressed", self.accent_light)],
                 foreground=[("active", self.button_fg), ("pressed", self.button_fg)])
        
        # Geniş butonlar
        style.configure("Wide.TButton", 
                        background=self.accent_color,
                        foreground="#ffffff",
                        font=("Segoe UI", 12, "bold"), 
                        relief="flat", 
                        borderwidth=0,
                        padding=10)
        style.map("Wide.TButton",
                 background=[("active", self.accent_light), ("pressed", self.accent_light)],
                 foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])
        
        # Başarı butonu
        style.configure("Success.TButton", 
                        background=self.success_color,
                        foreground="#ffffff",
                        font=("Segoe UI", 12, "bold"), 
                        relief="flat", 
                        borderwidth=0,
                        padding=10)
        style.map("Success.TButton",
                 background=[("active", "#00a742"), ("pressed", "#00a742")],
                 foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])
        
        # Durdurma butonu
        style.configure("Danger.TButton", 
                        background=self.danger_color,
                        foreground="#ffffff",
                        font=("Segoe UI", 12, "bold"), 
                        relief="flat", 
                        borderwidth=0,
                        padding=10)
        style.map("Danger.TButton",
                 background=[("active", "#d32f2f"), ("pressed", "#d32f2f")],
                 foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])
        
        # Tab butonları
        style.configure("Tab.TButton", 
                        background=self.card_bg,
                        foreground=self.text_color,
                        font=("Segoe UI", 13), 
                        relief="flat", 
                        borderwidth=0,
                        padding=12)
        style.map("Tab.TButton",
                 background=[("active", self.highlight_color), ("pressed", self.highlight_color)],
                 foreground=[("active", self.accent_color), ("pressed", self.accent_color)])
        
        # Aktif tab butonları
        style.configure("TabActive.TButton", 
                        background=self.highlight_color,
                        foreground=self.accent_color,
                        font=("Segoe UI", 13, "bold"), 
                        relief="flat", 
                        borderwidth=0,
                        padding=12)
        
        # Giriş alanları
        style.configure("TEntry", 
                        fieldbackground=self.input_bg,
                        foreground=self.text_color,
                        bordercolor=self.accent_color,
                        lightcolor=self.accent_color,
                        darkcolor=self.accent_color,
                        borderwidth=1,
                        font=("Segoe UI", 12),
                        padding=8)
        
        # Checkbox stili
        style.configure("TCheckbutton", 
                        background=self.card_bg,
                        foreground=self.text_color,
                        font=("Segoe UI", 12))
        style.map("TCheckbutton",
                  background=[("active", self.card_bg)])
        
        # Radiobutton stili
        style.configure("TRadiobutton", 
                        background=self.card_bg,
                        foreground=self.text_color,
                        font=("Segoe UI", 12))
        style.map("TRadiobutton",
                  background=[("active", self.card_bg)])
    
    def load_icons(self):
        """
        UI için gerekli ikonları yükler ve bir sözlüğe kaydeder.
        """
        self.icons = {}
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")
        icons_to_load = {
            "user": "user.png",
            "notification": "notification.png",
            "email": "email.png",
            "sms": "sms.png",
            "telegram": "telegram.png",
            "theme": "theme.png",
            "save": "save.png",
            "cancel": "cancel.png",
            "test": "test.png",
            "back": "back.png",
            "info": "info.png"
        }
        
        for name, filename in icons_to_load.items():
            try:
                path = os.path.join(icon_dir, filename)
                if os.path.exists(path):
                    img = Image.open(path).resize((24, 24), Image.LANCZOS)
                    self.icons[name] = ImageTk.PhotoImage(img)
                else:
                    logging.warning(f"İkon dosyası bulunamadı: {path}")
                    default_icons = {
                        "user": "👤",
                        "notification": "🔔",
                        "email": "✉️",
                        "sms": "📱",
                        "telegram": "📨",
                        "theme": "🎨",
                        "save": "💾",
                        "cancel": "❌",
                        "test": "🧪",
                        "back": "⬅️",
                        "info": "ℹ️"
                    }
                    if name in default_icons:
                        self.icons[name] = default_icons[name]
            except Exception as e:
                logging.warning(f"İkon yüklenirken hata: {str(e)}")
                fallback_icons = {
                    "user": "👤",
                    "notification": "🔔",
                    "email": "✉️",
                    "sms": "📱",
                    "telegram": "📨",
                    "theme": "🎨",
                    "save": "💾",
                    "cancel": "❌",
                    "test": "🧪",
                    "back": "⬅️",
                    "info": "ℹ️"
                }
                if name in fallback_icons:
                    self.icons[name] = fallback_icons[name]
    
    def _create_ui(self):
        """
        UI bileşenlerini oluşturur ve düzenler.
        """
        # Ana grid düzeni
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Başlık
        self.rowconfigure(1, weight=1)  # İçerik
        
        # Üst çubuk
        self._create_header()
        
        # İçerik kısmı
        self._create_content()
    
    def _create_header(self):
        """
        Üst başlık çubuğunu oluşturur.
        Geri, Tema Değiştir, İptal ve Kaydet butonlarını içerir.
        """
        header = ttk.Frame(self, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        
        inner_header = ttk.Frame(header, style="Header.TFrame", padding=(20, 15, 20, 15))
        inner_header.pack(fill=tk.X, expand=True)
        
        # Geri butonu
        back_button = ttk.Button(
            inner_header,
            text="⬅️ Geri",
            style="Wide.TButton",
            command=self._on_back,
            cursor="hand2",
            width=12
        )
        back_button.pack(side=tk.LEFT, padx=5)
        
        # Başlık
        title_label = ttk.Label(
            inner_header,
            text="Kullanıcı Ayarları",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT, padx=20)
        
        # Tema değiştirme butonu
        theme_btn = ttk.Button(
            inner_header,
            text="🌓" if self.dark_mode else "☀️",
            style="TButton",
            command=self._toggle_theme,
            width=4,
            cursor="hand2"
        )
        theme_btn.pack(side=tk.RIGHT, padx=5)
        
        # Kaydet butonu
        save_button = ttk.Button(
            inner_header,
            text="💾 Kaydet",
            style="Success.TButton",
            command=self._save_settings,
            cursor="hand2",
            width=12
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # İptal butonu
        cancel_button = ttk.Button(
            inner_header,
            text="❌ İptal",
            style="Danger.TButton",
            command=self._on_back,
            cursor="hand2",
            width=12
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _create_content(self):
        """
        İçerik panelini oluşturur.
        Sekmeli arayüz ve ilgili panelleri içerir.
        """
        main_content = tk.Frame(self, bg=self.bg_color)
        main_content.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        main_content.columnconfigure(0, weight=1)
        main_content.columnconfigure(1, weight=3)
        main_content.rowconfigure(0, weight=1)
        
        # Sol sekme paneli
        self._create_tab_panel(main_content)
        
        # Sağ içerik paneli
        self.content_container = tk.Frame(main_content, bg=self.bg_color)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        
        # İçerik panelleri
        self.panels = {}
        
        # Kullanıcı bilgisi paneli
        self.panels["user"] = self._create_user_panel(self.content_container)
        
        # Bildirim ayarları paneli
        self.panels["notifications"] = self._create_notification_panel(self.content_container)
        
        # Görünüm ayarları paneli
        self.panels["appearance"] = self._create_appearance_panel(self.content_container)
        
        # Aktif sekmeyi izlemek için değişken
        self.active_tab = "user"
        
        # Kullanıcı bilgisi panelini göster (varsayılan)
        self._show_panel("user")
    
    def _create_tab_panel(self, parent):
        """
        Sol sekme panelini oluşturur.
        Sekme butonları ve versiyon bilgisini içerir.

        Args:
            parent (tk.Frame): Üst çerçeve
        """
        tab_panel = tk.Frame(parent, bg=self.card_bg, padx=20, pady=20)
        tab_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 25))
        tab_panel.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # Sekme başlığı
        tab_header = ttk.Label(
            tab_panel,
            text="Ayarlar",
            style="Section.TLabel"
        )
        tab_header.pack(fill=tk.X, pady=(0, 25))
        
        # Sekmeler için çerçeve
        tabs_container = ttk.Frame(tab_panel, style="Card.TFrame")
        tabs_container.pack(fill=tk.BOTH, expand=True)
        
        # Sekme butonları
        self.tab_buttons = {}
        
        # Kullanıcı bilgileri sekmesi
        self.tab_buttons["user"] = self._create_tab_button(
            tabs_container, 
            "👤 Kullanıcı Bilgileri", 
            "user"
        )
        self.tab_buttons["user"].pack(fill=tk.X, pady=(0, 8))
        
        # Bildirim ayarları sekmesi
        self.tab_buttons["notifications"] = self._create_tab_button(
            tabs_container, 
            "🔔 Bildirim Ayarları", 
            "notification"
        )
        self.tab_buttons["notifications"].pack(fill=tk.X, pady=(0, 8))
        
        # Görünüm ayarları sekmesi
        self.tab_buttons["appearance"] = self._create_tab_button(
            tabs_container, 
            "🎨 Görünüm Ayarları", 
            "theme"
        )
        self.tab_buttons["appearance"].pack(fill=tk.X, pady=(0, 8))
        
        # Versiyon bilgisi
        version_frame = ttk.Frame(tab_panel, style="Card.TFrame")
        version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(25, 0))
        
        version_label = ttk.Label(
            version_frame,
            text="Guard v1.0.0",
            style="Info.TLabel"
        )
        version_label.pack(side=tk.RIGHT)
        
        return tab_panel
    
    def _create_tab_button(self, parent, text, icon_key):
        """
        Sekme butonu oluşturur.

        Args:
            parent (ttk.Frame): Üst çerçeve
            text (str): Buton metni
            icon_key (str): İkon anahtarı

        Returns:
            ttk.Button: Oluşturulan sekme butonu
        """
        tab = ttk.Button(
            parent,
            text=text,
            style="Tab.TButton",
            command=lambda key=icon_key: self._select_tab(key),
            cursor="hand2"
        )
        return tab
    
    def _select_tab(self, tab_key):
        """
        Sekme seçimini işler ve ilgili paneli gösterir.

        Args:
            tab_key (str): Seçilen sekmenin anahtarı
        """
        tab_mapping = {
            "user": "user",
            "notification": "notifications",
            "theme": "appearance"
        }
        
        # Önceki aktif sekme butonunu normale döndür
        if self.active_tab in self.tab_buttons:
            self.tab_buttons[self.active_tab].configure(style="Tab.TButton")
        
        # Yeni aktif sekmeyi ayarla
        self.active_tab = tab_key
        
        # Aktif sekme butonunu vurgula
        if tab_key in self.tab_buttons:
            self.tab_buttons[tab_key].configure(style="TabActive.TButton")
        
        # İlgili paneli göster
        if tab_key in tab_mapping:
            self._show_panel(tab_mapping[tab_key])
    
    def _create_user_panel(self, parent):
        """
        Kullanıcı bilgileri panelini oluşturur.

        Args:
            parent (tk.Frame): Üst çerçeve

        Returns:
            tk.Frame: Kullanıcı bilgileri paneli
        """
        panel = tk.Frame(parent, bg=self.bg_color)
        
        # Başlık
        title = ttk.Label(
            panel,
            text="Kullanıcı Bilgileri",
            style="Section.TLabel"
        )
        title.pack(anchor=tk.W, pady=(0, 25))
        
        # Kullanıcı kart çerçevesi
        user_card = tk.Frame(panel, bg=self.card_bg, padx=20, pady=20)
        user_card.pack(fill=tk.BOTH, expand=True)
        user_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # Kullanıcı avatarı ve bilgileri
        avatar_frame = ttk.Frame(user_card, style="Card.TFrame")
        avatar_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Kullanıcı isminin baş harflerini al
        initials = "".join([name[0].upper() for name in self.user.get("displayName", "?").split() if name])
        if not initials:
            initials = "?"
        
        # Avatar arkaplan rengi
        avatar_color = self.accent_color
        
        # Dairesel avatar oluşturma
        avatar_size = 90
        avatar_canvas = tk.Canvas(
            avatar_frame, 
            width=avatar_size, 
            height=avatar_size, 
            bg=self.card_bg, 
            highlightthickness=0
        )
        avatar_canvas.pack(side=tk.LEFT)
        
        # Dairesel avatar çiz
        avatar_canvas.create_oval(5, 5, avatar_size-5, avatar_size-5, fill=avatar_color, outline="#ffffff", width=2)
        avatar_canvas.create_text(avatar_size/2, avatar_size/2, text=initials, fill="#ffffff", font=("Segoe UI", 28, "bold"))
        
        # Kullanıcı adı ve e-posta
        user_info_frame = ttk.Frame(avatar_frame, style="Card.TFrame")
        user_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(25, 0))
        
        # Kullanıcı adı
        user_name = ttk.Label(
            user_info_frame,
            text=self.user.get("displayName", "Kullanıcı"),
            style="Section.TLabel"
        )
        user_name.pack(anchor=tk.W)
        
        # E-posta
        user_email = ttk.Label(
            user_info_frame,
            text=self.user.get("email", ""),
            style="Info.TLabel"
        )
        user_email.pack(anchor=tk.W)
        
        # Kullanıcı bilgileri formu
        form_frame = ttk.Frame(user_card, style="Card.TFrame")
        form_frame.pack(fill=tk.X, pady=(25, 0))
        
        # Ad Soyad alanı
        name_frame = ttk.Frame(form_frame, style="Card.TFrame")
        name_frame.pack(fill=tk.X, pady=(0, 15))
        
        name_label = ttk.Label(
            name_frame,
            text="Ad Soyad",
            style="TLabel"
        )
        name_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.name_var = tk.StringVar(value=self.user.get("displayName", ""))
        name_entry = ttk.Entry(
            name_frame,
            textvariable=self.name_var,
            style="TEntry"
        )
        name_entry.pack(fill=tk.X, ipady=5)
        
        # E-posta alanı (sadece gösterim için)
        email_frame = ttk.Frame(form_frame, style="Card.TFrame")
        email_frame.pack(fill=tk.X)
        
        email_label = ttk.Label(
            email_frame,
            text="E-posta (değiştirilemez)",
            style="TLabel"
        )
        email_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.email_var = tk.StringVar(value=self.user.get("email", ""))
        email_entry = ttk.Entry(
            email_frame,
            textvariable=self.email_var,
            style="TEntry",
            state="readonly"
        )
        email_entry.pack(fill=tk.X, ipady=5)
        
        # Şifre değiştirme kartı
        password_card = tk.Frame(panel, bg=self.card_bg, padx=20, pady=20)
        password_card.pack(fill=tk.BOTH, expand=True, pady=(25, 0))
        password_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        password_title = ttk.Label(
            password_card,
            text="Şifre Değiştirme",
            style="Section.TLabel"
        )
        password_title.pack(anchor=tk.W, pady=(0, 10))
        
        password_frame = ttk.Frame(password_card, style="Card.TFrame")
        password_frame.pack(fill=tk.X)
        
        # Şifre değiştirme linki
        password_link = ttk.Label(
            password_frame,
            text="Şifrenizi değiştirmek için e-posta gönderin",
            foreground=self.accent_color,
            background=self.card_bg,
            font=("Segoe UI", 12, "underline"),
            cursor="hand2"
        )
        password_link.pack(anchor=tk.W)
        password_link.bind("<Button-1>", self._send_password_reset)
        
        # Açıklama
        password_info = ttk.Label(
            password_frame,
            text="E-posta adresinize şifre sıfırlama bağlantısı gönderilecektir.",
            style="Info.TLabel"
        )
        password_info.pack(anchor=tk.W, pady=(5, 0))
        
        return panel
    
    def _create_notification_panel(self, parent):
        """
        Bildirim ayarları panelini oluşturur.

        Args:
            parent (tk.Frame): Üst çerçeve

        Returns:
            tk.Frame: Bildirim ayarları paneli
        """
        panel = tk.Frame(parent, bg=self.bg_color)
        
        # Başlık
        title = ttk.Label(
            panel,
            text="Bildirim Ayarları",
            style="Section.TLabel"
        )
        title.pack(anchor=tk.W, pady=(0, 25))
        
        # Bildirim türleri kartı
        notification_card = tk.Frame(panel, bg=self.card_bg, padx=20, pady=20)
        notification_card.pack(fill=tk.BOTH, expand=True)
        notification_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # E-posta bildirimi
        email_frame = ttk.Frame(notification_card, style="Card.TFrame")
        email_frame.pack(fill=tk.X, pady=(0, 15))
        
        email_header = ttk.Frame(email_frame, style="Card.TFrame")
        email_header.pack(fill=tk.X)
        
        # E-posta bildirim onay kutusu
        self.email_notification_var = tk.BooleanVar(value=self.settings.get("email_notification", True))
        
        email_check = ttk.Checkbutton(
            email_header,
            text="E-posta Bildirimleri",
            variable=self.email_notification_var,
            style="TCheckbutton",
            command=lambda: self._set_modified()
        )
        email_check.pack(side=tk.LEFT)
        
        # E-posta bilgi etiketi
        email_info = ttk.Label(
            email_header,
            text=f"({self.user.get('email', '')})",
            style="Info.TLabel"
        )
        email_info.pack(side=tk.LEFT, padx=(5, 0))
        
        # Test butonu
        email_test_btn = ttk.Button(
            email_header,
            text="🧪 Test",
            style="TButton",
            command=self._test_email,
            cursor="hand2",
            width=8
        )
        email_test_btn.pack(side=tk.RIGHT)
        
        # SMS bildirimi
        sms_frame = ttk.Frame(notification_card, style="Card.TFrame")
        sms_frame.pack(fill=tk.X, pady=(0, 10))
        
        sms_header = ttk.Frame(sms_frame, style="Card.TFrame")
        sms_header.pack(fill=tk.X)
        
        # SMS bildirim onay kutusu
        self.sms_notification_var = tk.BooleanVar(value=self.settings.get("sms_notification", False))
        
        sms_check = ttk.Checkbutton(
            sms_header,
            text="SMS Bildirimleri",
            variable=self.sms_notification_var,
            style="TCheckbutton",
            command=self._toggle_sms
        )
        sms_check.pack(side=tk.LEFT)
        
        # SMS test butonu
        self.sms_test_btn = ttk.Button(
            sms_header,
            text="🧪 Test",
            style="TButton",
            command=self._test_sms,
            cursor="hand2",
            width=8
        )
        self.sms_test_btn.pack(side=tk.RIGHT)
        self.sms_test_btn.configure(state="disabled")
        
        # Telefon numarası alanı
        phone_frame = ttk.Frame(sms_frame, style="Card.TFrame")
        phone_frame.pack(fill=tk.X, padx=(25, 0), pady=(5, 0))
        
        phone_label = ttk.Label(
            phone_frame,
            text="Telefon Numarası:",
            style="TLabel"
        )
        phone_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.phone_var = tk.StringVar(value=self.settings.get("phone_number", ""))
        self.phone_entry = ttk.Entry(
            phone_frame,
            textvariable=self.phone_var,
            style="TEntry",
            state="disabled",
            width=20
        )
        self.phone_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Telefon bilgisi
        phone_info = ttk.Label(
            phone_frame,
            text="Örnek: +905551234567",
            style="Info.TLabel"
        )
        phone_info.pack(side=tk.LEFT)
        
        # Telegram bildirimi
        telegram_frame = ttk.Frame(notification_card, style="Card.TFrame")
        telegram_frame.pack(fill=tk.X, pady=10)
        
        telegram_header = ttk.Frame(telegram_frame, style="Card.TFrame")
        telegram_header.pack(fill=tk.X)
        
        # Telegram bildirim onay kutusu
        self.telegram_notification_var = tk.BooleanVar(value=self.settings.get("telegram_notification", False))
        
        telegram_check = ttk.Checkbutton(
            telegram_header,
            text="Telegram Bildirimleri",
            variable=self.telegram_notification_var,
            style="TCheckbutton",
            command=self._toggle_telegram
        )
        telegram_check.pack(side=tk.LEFT)
        
        # Telegram test butonu
        self.telegram_test_btn = ttk.Button(
            telegram_header,
            text="🧪 Test",
            style="TButton",
            command=self._test_telegram,
            cursor="hand2",
            width=8
        )
        self.telegram_test_btn.pack(side=tk.RIGHT)
        self.telegram_test_btn.configure(state="disabled")
        
        # Telegram Chat ID alanı
        telegram_id_frame = ttk.Frame(telegram_frame, style="Card.TFrame")
        telegram_id_frame.pack(fill=tk.X, padx=(25, 0), pady=(5, 0))
        
        telegram_id_label = ttk.Label(
            telegram_id_frame,
            text="Telegram Chat ID:",
            style="TLabel"
        )
        telegram_id_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.telegram_var = tk.StringVar(value=self.settings.get("telegram_chat_id", ""))
        self.telegram_entry = ttk.Entry(
            telegram_id_frame,
            textvariable=self.telegram_var,
            style="TEntry",
            state="disabled",
            width=20
        )
        self.telegram_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Telegram ID bilgisi
        telegram_info = ttk.Label(
            telegram_id_frame,
            text="Telegram botunuzla iletişime geçin ve /start komutunu yazın",
            style="Info.TLabel"
        )
        telegram_info.pack(side=tk.LEFT)
        
        # Bildirim ayarları hakkında bilgi kartı
        info_card = tk.Frame(panel, bg=self.info_bg, padx=15, pady=15)
        info_card.pack(fill=tk.BOTH, expand=True, pady=(25, 0))
        info_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # Bilgi simgesi ve metni
        info_title = ttk.Label(
            info_card,
            text="ℹ️ Bildirimler Ne Zaman Gönderilir?",
            style="InfoCard.TLabel"
        )
        info_title.pack(anchor=tk.W)
        
        info_text = ttk.Label(
            info_card,
            text=(
                "Düşme tespit edildiğinde, seçtiğiniz bildirim kanallarına anında uyarı gönderilir. "
                "Bu uyarılar, olayın tarih ve saati, düşme olasılığı ve ekran görüntüsünü içerir. "
                "Lütfen en az bir bildirimi aktif tutunuz."
            ),
            background=self.info_bg,
            foreground=self.info_fg,
            font=("Segoe UI", 11),
            wraplength=600,
            justify=tk.LEFT
        )
        info_text.pack(anchor=tk.W, pady=(5, 0))
        
        return panel
    
    def _create_appearance_panel(self, parent):
        """
        Görünüm ayarları panelini oluşturur.

        Args:
            parent (tk.Frame): Üst çerçeve

        Returns:
            tk.Frame: Görünüm ayarları paneli
        """
        panel = tk.Frame(parent, bg=self.bg_color)
        
        # Başlık
        title = ttk.Label(
            panel,
            text="Görünüm Ayarları",
            style="Section.TLabel"
        )
        title.pack(anchor=tk.W, pady=(0, 25))
        
        # Tema kartı
        theme_card = tk.Frame(panel, bg=self.card_bg, padx=20, pady=20)
        theme_card.pack(fill=tk.BOTH, expand=True)
        theme_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # Tema başlığı
        theme_title = ttk.Label(
            theme_card,
            text="Uygulama Teması",
            style="Section.TLabel"
        )
        theme_title.pack(anchor=tk.W, pady=(0, 25))
        
        # Tema seçenekleri
        theme_options = ttk.Frame(theme_card, style="Card.TFrame")
        theme_options.pack(fill=tk.X)
        
        # Tema radyo butonları
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "light"))
        
        # Açık tema seçeneği
        light_theme_frame = ttk.Frame(theme_options, style="Card.TFrame")
        light_theme_frame.pack(side=tk.LEFT, padx=(0, 20), pady=12)
        
        # Açık tema önizleme
        light_preview = tk.Canvas(light_theme_frame, width=140, height=70, bg="#f5f5f5", highlightthickness=1, highlightbackground="#dddddd")
        light_preview.pack(pady=(0, 8))
        
        # Mini UI elemanları çiz
        light_preview.create_rectangle(0, 0, 140, 15, fill="#2196f3", outline="")
        light_preview.create_rectangle(10, 25, 130, 45, fill="white", outline="#dddddd")
        light_preview.create_rectangle(10, 50, 80, 60, fill="#2196f3", outline="")
        
        # Açık tema butonu
        light_radio = ttk.Radiobutton(
            light_theme_frame,
            text="Açık Tema",
            variable=self.theme_var,
            value="light",
            style="TRadiobutton",
            command=self._update_theme_preview
        )
        light_radio.pack()
        
        # Koyu tema seçeneği
        dark_theme_frame = ttk.Frame(theme_options, style="Card.TFrame")
        dark_theme_frame.pack(side=tk.LEFT, pady=12)
        
        # Koyu tema önizleme
        dark_preview = tk.Canvas(dark_theme_frame, width=140, height=70, bg="#2c3e50", highlightthickness=1, highlightbackground="#1a2530")
        dark_preview.pack(pady=(0, 8))
        
        # Mini UI elemanları çiz
        dark_preview.create_rectangle(0, 0, 140, 15, fill="#0288d1", outline="")
        dark_preview.create_rectangle(10, 25, 130, 45, fill="#34495e", outline="#1a2530")
        dark_preview.create_rectangle(10, 50, 80, 60, fill="#2196f3", outline="")
        
        # Koyu tema butonu
        dark_radio = ttk.Radiobutton(
            dark_theme_frame,
            text="Koyu Tema",
            variable=self.theme_var,
            value="dark",
            style="TRadiobutton",
            command=self._update_theme_preview
        )
        dark_radio.pack()
        
        # Renk seçimi kartı
        color_card = tk.Frame(panel, bg=self.card_bg, padx=20, pady=20)
        color_card.pack(fill=tk.BOTH, expand=True, pady=(25, 0))
        color_card.configure(highlightbackground="#d0d0d0", highlightthickness=3)
        
        # Renk başlığı
        color_title = ttk.Label(
            color_card,
            text="Uygulama Ana Rengi",
            style="Section.TLabel"
        )
        color_title.pack(anchor=tk.W, pady=(0, 25))
        
        # Renk seçenekleri
        color_options = ttk.Frame(color_card, style="Card.TFrame")
        color_options.pack(fill=tk.X)
        
        # Renk radyo butonları
        self.color_var = tk.StringVar(value=self.settings.get("color", "blue"))
        
        # Mavi renk seçeneği
        blue_color_frame = self._create_color_option(color_options, "Mavi", "#2196f3", "blue")
        blue_color_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Yeşil renk seçeneği
        green_color_frame = self._create_color_option(color_options, "Yeşil", "#00c853", "green")
        green_color_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Mor renk seçeneği
        purple_color_frame = self._create_color_option(color_options, "Mor", "#ab47bc", "purple")
        purple_color_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Turuncu renk seçeneği
        orange_color_frame = self._create_color_option(color_options, "Turuncu", "#ff6d00", "orange")
        orange_color_frame.pack(side=tk.LEFT)
        
        # Özel renk seçeneği
        custom_frame = ttk.Frame(color_card, style="Card.TFrame")
        custom_frame.pack(fill=tk.X, pady=(20, 0))
        
        custom_button = ttk.Button(
            custom_frame,
            text="🎨 Özel Renk Seç",
            style="TButton",
            command=self._choose_custom_color,
            cursor="hand2"
        )
        custom_button.pack(side=tk.LEFT)
        
        # Özel renk önizlemesi
        self.custom_color_var = tk.StringVar(value=self.settings.get("custom_color", "#2196f3"))
        self.custom_preview = tk.Canvas(
            custom_frame, 
            width=35, 
            height=35, 
            bg=self.custom_color_var.get(), 
            highlightthickness=1,
            highlightbackground="#dddddd"
        )
        self.custom_preview.pack(side=tk.LEFT, padx=(10, 0))
        
        # Ayarları uygulama butonu
        apply_frame = ttk.Frame(color_card, style="Card.TFrame")
        apply_frame.pack(fill=tk.X, pady=(20, 0))
        
        apply_button = ttk.Button(
            apply_frame,
            text="👁️ Ayarları Önizle",
            style="Wide.TButton",
            command=self._preview_appearance,
            cursor="hand2"
        )
        apply_button.pack(side=tk.LEFT)
        
        # Bilgi notu
        note_label = ttk.Label(
            apply_frame,
            text="Not: Ayarları tamamen uygulamak için 'Kaydet' butonuna basın.",
            style="Info.TLabel"
        )
        note_label.pack(side=tk.LEFT, padx=(15, 0))
        
        return panel
    
    def _create_color_option(self, parent, name, color, value):
        """
        Renk seçeneği oluşturur.

        Args:
            parent (ttk.Frame): Üst çerçeve
            name (str): Renk adı
            color (str): Renk hex kodu
            value (str): Renk değeri

        Returns:
            ttk.Frame: Renk seçeneği çerçevesi
        """
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Renk önizlemesi
        color_canvas = tk.Canvas(
            frame, 
            width=35, 
            height=35, 
            bg=color, 
            highlightthickness=1,
            highlightbackground="#dddddd"
        )
        color_canvas.pack(pady=(0, 5))
        
        # Renk radyo butonu
        radio = ttk.Radiobutton(
            frame,
            text=name,
            variable=self.color_var,
            value=value,
            style="TRadiobutton",
            command=lambda: self._set_modified()
        )
        radio.pack()
        
        return frame
    
    def _update_theme_preview(self):
        """
        Tema önizlemesini günceller.
        """
        self._set_modified()
    
    def _choose_custom_color(self):
        """
        Özel renk seçimi için renk seçiciyi açar.
        """
        color = colorchooser.askcolor(initialcolor=self.custom_color_var.get())
        if color[1]:  # [1] hex string değerini içerir
            self.custom_color_var.set(color[1])
            self.custom_preview.config(bg=color[1])
            self.color_var.set("custom")
            self._set_modified()
    
    def _preview_appearance(self):
        """
        Görünüm ayarlarını önizler ve kullanıcıya bilgi verir.
        """
        self._toggle_theme(preview=True)
        messagebox.showinfo(
            "Önizleme", 
            "Tema ve renk ayarlarınız geçici olarak önizleniyor. Kalıcı olması için 'Kaydet' butonuna basın."
        )
    
    def _show_panel(self, panel_name):
        """
        Belirtilen paneli gösterir, diğerlerini gizler.

        Args:
            panel_name (str): Gösterilecek panelin adı
        """
        for name, panel in self.panels.items():
            panel.pack_forget()  # Tüm panelleri gizle
        if panel_name in self.panels:
            self.panels[panel_name].pack(fill=tk.BOTH, expand=True)  # Seçili paneli göster
    
    def _toggle_sms(self):
        """
        SMS bildirim durumunu değiştirir ve ilgili alanları aktif/pasif yapar.
        """
        if self.sms_notification_var.get():
            self.phone_entry.config(state="normal")
            self.sms_test_btn.config(state="normal")
        else:
            self.phone_entry.config(state="disabled")
            self.sms_test_btn.config(state="disabled")
        self._set_modified()
    
    def _toggle_telegram(self):
        """
        Telegram bildirim durumunu değiştirir ve ilgili alanları aktif/pasif yapar.
        """
        if self.telegram_notification_var.get():
            self.telegram_entry.config(state="normal")
            self.telegram_test_btn.config(state="normal")
        else:
            self.telegram_entry.config(state="disabled")
            self.telegram_test_btn.config(state="disabled")
        self._set_modified()
    
    def _toggle_theme(self, preview=False):
        """
        Temayı değiştirir ve UI'yi günceller.

        Args:
            preview (bool): Eğer True ise, tema sadece önizleme için değiştirilir.
        """
        if not preview:
            self.dark_mode = not self.dark_mode
        else:
            self.dark_mode = self.theme_var.get() == "dark"
        
        self._setup_colors()
        self._setup_styles()
        self._update_theme_for_all_widgets()
    
    def _update_theme_for_all_widgets(self):
        """
        Tüm widget'ları yeni temaya göre günceller.
        """
        self.configure(bg=self.bg_color)
        for widget in self.winfo_children():
            self._update_widget_theme(widget)
    
    def _update_widget_theme(self, widget):
        """
        Belirtilen widget'ın temasını günceller.

        Args:
            widget: Güncellenecek widget
        """
        try:
            widget_class = widget.winfo_class()
            
            if widget_class == "Frame":
                if "Header" in str(widget.cget("style")):
                    widget.configure(bg=self.header_bg)
                else:
                    widget.configure(bg=self.card_bg)
            
            elif widget_class == "TFrame":
                if "Header" in str(widget["style"]):
                    widget.configure(style="Header.TFrame")
                else:
                    widget.configure(style="Card.TFrame")
            
            elif widget_class == "TLabel":
                if "Title" in str(widget["style"]):
                    widget.configure(style="Title.TLabel")
                elif "Section" in str(widget["style"]):
                    widget.configure(style="Section.TLabel")
                elif "Info" in str(widget["style"]):
                    widget.configure(style="Info.TLabel")
                else:
                    widget.configure(style="TLabel")
            
            elif widget_class == "Label":
                widget.configure(bg=self.card_bg, fg=self.text_color)
            
            elif widget_class == "TButton":
                if "Wide" in str(widget["style"]):
                    widget.configure(style="Wide.TButton")
                elif "Success" in str(widget["style"]):
                    widget.configure(style="Success.TButton")
                elif "Danger" in str(widget["style"]):
                    widget.configure(style="Danger.TButton")
                elif "Tab" in str(widget["style"]):
                    if "Active" in str(widget["style"]):
                        widget.configure(style="TabActive.TButton")
                    else:
                        widget.configure(style="Tab.TButton")
                else:
                    widget.configure(style="TButton")
            
            elif widget_class == "Button":
                widget.configure(bg=self.button_bg, fg=self.button_fg)
            
            elif widget_class == "TEntry":
                widget.configure(style="TEntry")
            
            elif widget_class == "TCheckbutton":
                widget.configure(style="TCheckbutton")
            
            elif widget_class == "TRadiobutton":
                widget.configure(style="TRadiobutton")
            
            # Çocuk widget'ları da güncelle
            for child in widget.winfo_children():
                self._update_widget_theme(child)
                
        except Exception as e:
            logging.debug(f"Widget tema güncellemesi sırasında hata: {str(e)}")
    
    def _on_configure(self, event):
        """
        Pencere boyutu değiştiğinde düzeni günceller.

        Args:
            event: Yeniden boyutlandırma olayı
        """
        if event.widget == self and (event.width > 1 and event.height > 1):
            pass
    
    def _set_modified(self):
        """
        Değişiklik yapıldığını işaretler.
        """
        self.is_modified = True
    
    def _test_email(self):
        """
        E-posta bildirimini test eder ve sonucu kullanıcıya bildirir.
        """
        if not self.email_notification_var.get():
            self._show_message("Uyarı", "E-posta bildirimleri aktif değil.", "warning")
            return
        
        try:
            user_data = {
                "email": self.user.get("email", ""),
                "settings": {
                    "email_notification": True
                }
            }
            event_data = {
                "timestamp": time.time(),
                "confidence": 0.85,
                "test": True
            }
            
            self._show_message(
                "Test Gönderiliyor", 
                f"Test e-postası {user_data['email']} adresine gönderiliyor...",
                "info"
            )
            
            from core.notification import NotificationManager
            notification_manager = NotificationManager(user_data)
            
            threading.Thread(
                target=notification_manager.send_email,
                args=(user_data["email"], event_data, None),
                daemon=True
            ).start()
            
            self._show_message(
                "Test Başarılı",
                f"Test e-postası {user_data['email']} adresine gönderildi. Lütfen gelen kutunuzu kontrol edin.",
                "success"
            )
            
        except Exception as e:
            self._show_message(
                "Test Hatası",
                f"E-posta testi sırasında bir hata oluştu: {str(e)}",
                "error"
            )
    
    def _test_sms(self):
        """
        SMS bildirimini test eder ve sonucu kullanıcıya bildirir.
        """
        if not self.sms_notification_var.get():
            self._show_message("Uyarı", "SMS bildirimleri aktif değil.", "warning")
            return
        
        phone = self.phone_var.get().strip()
        if not phone:
            self._show_message("Hata", "Telefon numarası girilmemiş.", "error")
            return
        
        try:
            user_data = {
                "phone_number": phone,
                "settings": {
                    "sms_notification": True
                }
            }
            event_data = {
                "timestamp": time.time(),
                "confidence": 0.85,
                "test": True
            }
            
            self._show_message(
                "Test Gönderiliyor", 
                f"Test SMS'i {phone} numarasına gönderiliyor...",
                "info"
            )
            
            from core.notification import NotificationManager
            notification_manager = NotificationManager(user_data)
            
            threading.Thread(
                target=notification_manager.send_sms,
                args=(phone, event_data),
                daemon=True
            ).start()
            
            self._show_message(
                "Test Başarılı",
                f"Test SMS'i {phone} numarasına gönderildi. Lütfen telefonunuzu kontrol edin.",
                "success"
            )
            
        except Exception as e:
            self._show_message(
                "Test Hatası",
                f"SMS testi sırasında bir hata oluştu: {str(e)}",
                "error"
            )
    
    def _test_telegram(self):
        """
        Telegram bildirimini test eder ve sonucu kullanıcıya bildirir.
        """
        if not self.telegram_notification_var.get():
            self._show_message("Uyarı", "Telegram bildirimleri aktif değil.", "warning")
            return
        
        chat_id = self.telegram_var.get().strip()
        if not chat_id:
            self._show_message("Hata", "Telegram Chat ID girilmemiş.", "error")
            return
        
        try:
            user_data = {
                "telegram_chat_id": chat_id,
                "settings": {
                    "telegram_notification": True
                }
            }
            event_data = {
                "timestamp": time.time(),
                "confidence": 0.85,
                "test": True
            }
            
            self._show_message(
                "Test Gönderiliyor", 
                f"Test Telegram mesajı {chat_id} ID'sine gönderiliyor...",
                "info"
            )
            
            from core.notification import NotificationManager
            notification_manager = NotificationManager(user_data)
            
            threading.Thread(
                target=notification_manager.send_telegram,
                args=(chat_id, event_data, None),
                daemon=True
            ).start()
            
            self._show_message(
                "Test Başarılı",
                f"Test Telegram mesajı {chat_id} ID'sine gönderildi. Lütfen Telegram'ı kontrol edin.",
                "success"
            )
            
        except Exception as e:
            self._show_message(
                "Test Hatası",
                f"Telegram testi sırasında bir hata oluştu: {str(e)}",
                "error"
            )
    
    def _send_password_reset(self, event=None):
        """
        Şifre sıfırlama e-postası gönderir.

        Args:
            event: Olay nesnesi (opsiyonel)
        """
        try:
            email = self.user.get("email", "")
            if not email:
                self._show_message("Hata", "E-posta adresi bulunamadı.", "error")
                return
            
            self.auth.send_password_reset_email(email)
            self._show_message(
                "Başarılı",
                f"Şifre sıfırlama bağlantısı {email} adresine gönderildi. Lütfen gelen kutunuzu kontrol edin.",
                "success"
            )
        except Exception as e:
            self._show_message(
                "Hata",
                f"Şifre sıfırlama e-postası gönderilirken hata: {str(e)}",
                "error"
            )
    
    def _save_settings(self):
        """
        Ayarları kaydeder ve kullanıcıyı bilgilendirir.
        """
        if not self.is_modified:
            self._on_back()
            return
        
        try:
            # Yeni ayarları hazırla
            settings = {
                "email_notification": self.email_notification_var.get(),
                "sms_notification": self.sms_notification_var.get(),
                "telegram_notification": self.telegram_notification_var.get(),
                "phone_number": self.phone_var.get().strip(),
                "telegram_chat_id": self.telegram_var.get().strip(),
                "theme": self.theme_var.get(),
                "color": self.color_var.get(),
                "custom_color": self.custom_color_var.get()
            }
            
            # Kullanıcı bilgilerini güncelle
            user_data = {
                "displayName": self.name_var.get().strip()
            }
            
            # Veritabanında güncelle
            self.db_manager.update_user_data(self.user["localId"], user_data)
            self.db_manager.save_user_settings(self.user["localId"], settings)
            
            # Kullanıcı nesnesini güncelle
            self.user["displayName"] = user_data["displayName"]
            
            self._show_message(
                "Başarılı",
                "Ayarlarınız başarıyla kaydedildi.",
                "success"
            )
            
            # Geri dön
            self._on_back()
            
        except Exception as e:
            self._show_message(
                "Hata",
                f"Ayarlar kaydedilirken bir hata oluştu: {str(e)}",
                "error"
            )
    
    def _on_back(self):
        """
        Geri dönüş işlemini gerçekleştirir.
        Değişiklik yapılmışsa kullanıcıya uyarı verir.
        """
        if self.is_modified:
            if not messagebox.askyesno(
                "Değişiklikler Kaydedilmedi",
                "Değişiklikleriniz kaydedilmedi. Yine de çıkmak istiyor musunuz?"
            ):
                return
        
        self.back_fn()
    
    def _show_message(self, title, message, icon_type):
        """
        Kullanıcıya mesaj gösterir.

        Args:
            title (str): Mesaj başlığı
            message (str): Mesaj içeriği
            icon_type (str): Mesaj türü ("info", "success", "warning", "error")
        """
        messagebox.showinfo(
            title,
            message,
            icon=icon_type,
            parent=self
        )