# Dosya: guard_pc_app/ui/history.py
# Açıklama: Geçmiş düşme olaylarını listeleyen ve detaylarını gösteren modern, şık bir UI bileşeni.
# Özellikler:
# - Premium tasarım: Gradyan arka planlar, yumuşak gölgeler, animasyonlar
# - Material Design benzeri UI elemanları
# - Zenginleştirilmiş olay listesi: Renkli durum ikonları, tarih/saat ve olasılık bilgileri
# - Gelişmiş detay paneli: Büyültülebilir görüntü, interaktif bilgi kartları
# - Asenkron veri işleme: Arka planda yükleme, cache mekanizması
# - Hata yönetimi: Detaylı loglama ve kullanıcı dostu hata mesajları
# - Dark mode desteği: Otomatik sistem teması algılama

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import datetime
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import threading
import time
from functools import partial
import math
import sys
import os


class HistoryFrame(ttk.Frame):
    """Modern ve premium görünümlü geçmiş olaylar ekranı."""

    def __init__(self, parent, user, db_manager, back_fn):
        """
        Args:
            parent (ttk.Frame): Üst çerçeve
            user (dict): Kullanıcı bilgileri
            db_manager (FirestoreManager): Veritabanı yönetici nesnesi
            back_fn (function): Geri dönüş fonksiyonu
        """
        super().__init__(parent, style="MainFrame.TFrame")
        
        self.user = user
        self.db_manager = db_manager
        self.back_fn = back_fn
        self.loading_animation_id = None
        self.events = []
        self.filtered_events = []
        self.image_cache = {}  # Görüntü önbelleği
        
        # Dark mode algılama (sistem temasına göre)
        self.dark_mode = self._detect_dark_mode()
        
        # Tema renklerini ayarla
        self._setup_colors()
        
        # Stilleri ayarla
        self._setup_styles()
        
        # UI bileşenleri
        self._create_ui()
        
        # Animasyon değişkenleri
        self.current_image = None
        self.fade_alpha = 0.0
        self.detail_panel_expanded = False
        self.zoom_level = 1.0
        
        # Olayları yükle
        self._load_events()
        
        # Pencere yeniden boyutlandırma işleyicisi
        self.bind("<Configure>", self._on_configure)

    def _detect_dark_mode(self):
        """Sistem temasını algılar."""
        try:
            # Windows'ta tema algılama
            if sys.platform == "win32":
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            # macOS tema algılama
            elif sys.platform == "darwin":
                import subprocess
                cmd = "defaults read -g AppleInterfaceStyle"
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                return p.stdout.read().decode().strip() == "Dark"
            # Linux tema algılama (GNOME)
            elif sys.platform == "linux":
                import subprocess
                cmd = "gsettings get org.gnome.desktop.interface gtk-theme"
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output = p.stdout.read().decode().strip()
                return "dark" in output.lower()
        except:
            pass
        return False

    def _setup_colors(self):
        """Tema renklerini ayarlar."""
        if self.dark_mode:
            # Dark mode renkleri
            self.bg_color = "#121212"
            self.card_bg = "#1E1E1E"
            self.header_bg = "#252525"
            self.text_color = "#FFFFFF"
            self.text_secondary = "#AAAAAA"
            self.accent_color = "#3498db"
            self.accent_light = "#2980b9"
            self.success_color = "#2ecc71"
            self.warning_color = "#f39c12"
            self.danger_color = "#e74c3c"
            self.button_bg = "#333333"
            self.button_fg = "#FFFFFF"
            self.highlight_color = "#2d2d2d"
        else:
            # Light mode renkleri
            self.bg_color = "#F8F9FA"
            self.card_bg = "#FFFFFF"
            self.header_bg = "#EAEAEA"
            self.text_color = "#333333"
            self.text_secondary = "#666666"
            self.accent_color = "#3498db"
            self.accent_light = "#5DADE2"
            self.success_color = "#2ecc71"
            self.warning_color = "#f39c12"
            self.danger_color = "#e74c3c"
            self.button_bg = "#EFEFEF"
            self.button_fg = "#333333"
            self.highlight_color = "#F0F0F0"

    def _setup_styles(self):
        """Uygulama stillerini oluşturur."""
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
                         foreground=self.text_color, 
                         font=("Segoe UI", 18, "bold"))
        
        # Alt başlık etiketleri
        style.configure("Section.TLabel", 
                         background=self.card_bg,
                         foreground=self.text_color, 
                         font=("Segoe UI", 14, "bold"))
        
        # Standart etiketler
        style.configure("TLabel", 
                         background=self.card_bg,
                         foreground=self.text_color, 
                         font=("Segoe UI", 11))
        
        # Bilgi etiketleri
        style.configure("Info.TLabel", 
                         background=self.card_bg,
                         foreground=self.text_secondary, 
                         font=("Segoe UI", 10))
        
        # Detay başlık etiketleri
        style.configure("DetailHeader.TLabel", 
                         background=self.card_bg,
                         foreground=self.text_color, 
                         font=("Segoe UI", 12, "bold"))
        
        # Detay değer etiketleri
        style.configure("DetailValue.TLabel", 
                         background=self.card_bg,
                         foreground=self.accent_color, 
                         font=("Segoe UI", 12))
        
        # Standart butonlar
        style.configure("TButton", 
                         background=self.button_bg,
                         foreground=self.button_fg,
                         font=("Segoe UI", 10), 
                         relief="flat", 
                         borderwidth=0)
        style.map("TButton",
                 background=[("active", self.accent_light), ("pressed", self.accent_light)],
                 foreground=[("active", self.button_fg), ("pressed", self.button_fg)])
        
        # Geniş butonlar
        style.configure("Wide.TButton", 
                         background=self.accent_color,
                         foreground="white",
                         font=("Segoe UI", 10, "bold"), 
                         relief="flat", 
                         borderwidth=0)
        style.map("Wide.TButton",
                 background=[("active", self.accent_light), ("pressed", self.accent_light)],
                 foreground=[("active", "white"), ("pressed", "white")])
        
        # Durdurma butonu
        style.configure("Stop.TButton", 
                         background=self.danger_color,
                         foreground="white",
                         font=("Segoe UI", 10, "bold"), 
                         relief="flat", 
                         borderwidth=0)
        style.map("Stop.TButton",
                 background=[("active", "#c0392b"), ("pressed", "#c0392b")],
                 foreground=[("active", "white"), ("pressed", "white")])
        
        # İkon butonları
        style.configure("Icon.TButton", 
                         background=self.card_bg,
                         foreground=self.text_color,
                         font=("Segoe UI", 14), 
                         relief="flat", 
                         borderwidth=0,
                         padding=2)
        style.map("Icon.TButton",
                 background=[("active", self.highlight_color), ("pressed", self.highlight_color)])
        
        # Treeview (Olay listesi)
        style.configure("Treeview", 
                         background=self.card_bg,
                         foreground=self.text_color,
                         fieldbackground=self.card_bg,
                         font=("Segoe UI", 10))
        style.configure("Treeview.Heading", 
                         background=self.header_bg,
                         foreground=self.text_color,
                         font=("Segoe UI", 10, "bold"),
                         relief="flat")
        style.map("Treeview.Heading",
                 background=[("active", self.highlight_color)])
        style.map("Treeview",
                 background=[("selected", self.accent_color)],
                 foreground=[("selected", "white")])
        
        # Giriş alanları
        style.configure("TEntry", 
                         fieldbackground=self.card_bg,
                         foreground=self.text_color,
                         bordercolor=self.accent_color,
                         lightcolor=self.accent_color,
                         darkcolor=self.accent_color,
                         borderwidth=1,
                         font=("Segoe UI", 10))
        
        # Kaydırma çubuğu
        style.configure("Vertical.TScrollbar", 
                         background=self.card_bg,
                         arrowcolor=self.text_color,
                         troughcolor=self.bg_color)
        style.map("Vertical.TScrollbar",
                 background=[("active", self.accent_color), ("pressed", self.accent_light)])

    def _create_ui(self):
        """Modern ve premium UI bileşenlerini oluşturur."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Başlık çubuğu
        self.rowconfigure(1, weight=0)  # Filtreleme alanı
        self.rowconfigure(2, weight=1)  # İçerik
        
        # Başlık çerçevesi
        header_frame = ttk.Frame(self, style="Header.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # İç içe başlık çerçevesi (padding için)
        inner_header = ttk.Frame(header_frame, style="Header.TFrame", padding=15)
        inner_header.pack(fill=tk.X, expand=True)
        
        # Geri butonu (modern ikon stili)
        back_btn = ttk.Button(
            inner_header,
            text="← Geri",
            style="Wide.TButton",
            command=self.back_fn,
            width=10,
            cursor="hand2"
        )
        back_btn.pack(side=tk.LEFT, padx=5)
        
        # Başlık
        title_label = ttk.Label(
            inner_header,
            text="Olay Geçmişi",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT, padx=20)
        
        # Yenile butonu (modern ikon style)
        refresh_btn = ttk.Button(
            inner_header,
            text="⟳ Yenile",
            style="Wide.TButton",
            command=self._load_events,
            width=10,
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Tema değiştirme butonu
        theme_btn = ttk.Button(
            inner_header,
            text="🌓" if self.dark_mode else "☀️",
            style="Icon.TButton",
            command=self._toggle_theme,
            width=3,
            cursor="hand2"
        )
        theme_btn.pack(side=tk.RIGHT, padx=10)
        
        # Filtreleme alanı (kart görünümü)
        filter_frame = ttk.Frame(self, style="Card.TFrame")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        
        # İç filtreleme çerçevesi (padding için)
        inner_filter = ttk.Frame(filter_frame, style="Card.TFrame", padding=15)
        inner_filter.pack(fill=tk.X, expand=True)
        
        # Tarih filtresi
        date_frame = ttk.Frame(inner_filter, style="Card.TFrame")
        date_frame.pack(side=tk.LEFT, padx=(0, 20), fill=tk.Y)
        
        ttk.Label(
            date_frame,
            text="Tarih Filtresi:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.date_filter_var = tk.StringVar()
        date_entry = ttk.Entry(
            date_frame,
            textvariable=self.date_filter_var,
            style="TEntry",
            width=12
        )
        date_entry.pack(side=tk.LEFT)
        # Placeholder text
        date_entry.insert(0, "GG.AA.YYYY")
        date_entry.bind("<FocusIn>", lambda e: self._on_entry_focus_in(e, "GG.AA.YYYY"))
        date_entry.bind("<FocusOut>", lambda e: self._on_entry_focus_out(e, "GG.AA.YYYY"))
        
        # Olasılık filtresi
        conf_frame = ttk.Frame(inner_filter, style="Card.TFrame")
        conf_frame.pack(side=tk.LEFT, padx=(0, 20), fill=tk.Y)
        
        ttk.Label(
            conf_frame,
            text="Min. Olasılık (%):",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.conf_filter_var = tk.StringVar()
        conf_entry = ttk.Entry(
            conf_frame,
            textvariable=self.conf_filter_var,
            style="TEntry",
            width=6
        )
        conf_entry.pack(side=tk.LEFT)
        
        # Filtreleme butonu
        filter_btn = ttk.Button(
            inner_filter,
            text="Filtrele",
            style="Wide.TButton",
            command=self._apply_filters,
            width=10,
            cursor="hand2"
        )
        filter_btn.pack(side=tk.LEFT, padx=10)
        
        # Temizle butonu
        clear_btn = ttk.Button(
            inner_filter,
            text="Temizle",
            style="TButton",
            command=self._clear_filters,
            width=8,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT)
        
        # İçerik çerçevesi (ana kart)
        content_frame = ttk.Frame(self, style="Card.TFrame")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=4)
        content_frame.rowconfigure(0, weight=1)
        
        # Olay listesi çerçevesi
        list_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=15)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        
        # Liste başlığı
        list_header = ttk.Frame(list_frame, style="Card.TFrame")
        list_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(
            list_header,
            text="Algılanan Olaylar",
            style="Section.TLabel"
        ).pack(side=tk.LEFT)
        
        self.total_events_var = tk.StringVar(value="0 olay")
        ttk.Label(
            list_header,
            textvariable=self.total_events_var,
            style="Info.TLabel"
        ).pack(side=tk.RIGHT)
        
        # Liste çerçevesi (kaydırma çubuğu için)
        list_container = ttk.Frame(list_frame, style="Card.TFrame")
        list_container.grid(row=1, column=0, sticky="nsew")
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        # Olay listesi
        self.event_list = ttk.Treeview(
            list_container,
            columns=("date", "time", "confidence"),
            show="headings",
            selectmode="browse",
            style="Treeview"
        )
        
        # Sütun başlıkları
        self.event_list.heading("date", text="Tarih", anchor="center")
        self.event_list.heading("time", text="Saat", anchor="center")
        self.event_list.heading("confidence", text="Olasılık", anchor="center")
        
        # Sütun genişlikleri
        self.event_list.column("date", width=120, minwidth=100, anchor="center")
        self.event_list.column("time", width=100, minwidth=80, anchor="center")
        self.event_list.column("confidence", width=100, minwidth=80, anchor="center")
        
        # Kaydırma çubuğu
        list_scrollbar = ttk.Scrollbar(
            list_container, 
            orient=tk.VERTICAL, 
            command=self.event_list.yview,
            style="Vertical.TScrollbar"
        )
        self.event_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Liste ve kaydırma çubuğunu yerleştir
        self.event_list.grid(row=0, column=0, sticky="nsew")
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Seçim olayını bağla
        self.event_list.bind("<<TreeviewSelect>>", self._on_event_select)
        
        # Olay detayları çerçevesi
        self.detail_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=15)
        self.detail_frame.grid(row=0, column=1, sticky="nsew")
        self.detail_frame.columnconfigure(0, weight=1)
        self.detail_frame.rowconfigure(0, weight=0)  # Başlık
        self.detail_frame.rowconfigure(1, weight=0)  # Bilgi kartları
        self.detail_frame.rowconfigure(2, weight=0)  # Butonlar
        self.detail_frame.rowconfigure(3, weight=1)  # Görüntü
        
        # Detay başlığı
        detail_header = ttk.Frame(self.detail_frame, style="Card.TFrame")
        detail_header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        ttk.Label(
            detail_header,
            text="Olay Detayları",
            style="Section.TLabel"
        ).pack(side=tk.LEFT)
        
        # Bilgi kartları çerçevesi
        info_frame = ttk.Frame(self.detail_frame, style="Card.TFrame")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Tarih bilgi kartı
        date_card = self._create_info_card(info_frame, "Tarih ve Saat")
        date_card.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.date_var = tk.StringVar(value="--.--.---- --:--:--")
        ttk.Label(
            date_card,
            textvariable=self.date_var,
            style="DetailValue.TLabel"
        ).pack(anchor=tk.CENTER, pady=10)
        
        # Olasılık bilgi kartı
        conf_card = self._create_info_card(info_frame, "Düşme Olasılığı")
        conf_card.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        self.conf_var = tk.StringVar(value="--.--")
        self.conf_label = ttk.Label(
            conf_card,
            textvariable=self.conf_var,
            style="DetailValue.TLabel"
        )
        self.conf_label.pack(anchor=tk.CENTER, pady=10)
        
        # Buton çerçevesi
        button_frame = ttk.Frame(self.detail_frame, style="Card.TFrame")
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        
        # İşlem butonları
        export_btn = ttk.Button(
            button_frame,
            text="📷 Görüntüyü Kaydet",
            style="TButton",
            command=self._export_image,
            width=15,
            cursor="hand2"
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = ttk.Button(
            button_frame,
            text="🗑️ Olayı Sil",
            style="Stop.TButton",
            command=self._delete_event,
            width=12,
            cursor="hand2"
        )
        delete_btn.pack(side=tk.RIGHT)
        
        # Görüntü kartı
        image_card = ttk.Frame(self.detail_frame, style="Card.TFrame")
        image_card.grid(row=3, column=0, sticky="nsew")
        image_card.columnconfigure(0, weight=1)
        image_card.rowconfigure(0, weight=0)  # Başlık
        image_card.rowconfigure(1, weight=1)  # Görüntü
        
        # Görüntü başlığı ve butonlar
        img_header = ttk.Frame(image_card, style="Card.TFrame")
        img_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(
            img_header,
            text="Ekran Görüntüsü",
            style="DetailHeader.TLabel"
        ).pack(side=tk.LEFT)
        
        # Zoom butonları
        zoom_frame = ttk.Frame(img_header, style="Card.TFrame")
        zoom_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            zoom_frame,
            text="➖",
            style="Icon.TButton",
            command=self._zoom_out,
            width=3,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            zoom_frame,
            text="🔍",
            style="Icon.TButton",
            command=self._toggle_fullscreen,
            width=3,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            zoom_frame,
            text="➕",
            style="Icon.TButton",
            command=self._zoom_in,
            width=3,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        # Görüntü çerçevesi (gölge efekti için border ekleyerek)
        img_container = ttk.Frame(image_card, style="Card.TFrame", padding=2)
        img_container.grid(row=1, column=0, sticky="nsew")
        if not self.dark_mode:
            img_container["relief"] = "groove"
            img_container["borderwidth"] = 1
        
        self.image_frame = ttk.Frame(img_container, style="Card.TFrame")
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Görüntü etiketi
        self.image_label = ttk.Label(
            self.image_frame,
            text="Görüntü yok",
            style="TLabel",
            anchor=tk.CENTER
        )
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Fare olayları
        self.image_label.bind("<MouseWheel>", self._mouse_wheel)
        self.image_label.bind("<Button-1>", self._mouse_down)
        self.image_label.bind("<B1-Motion>", self._mouse_drag)
        self.image_label.bind("<ButtonRelease-1>", self._mouse_up)
        self.image_label.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        
        # Sürükleme için değişkenler
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.dragging = False

    def _create_info_card(self, parent, title):
        """Bilgi kartı oluşturur."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=10)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=0)
        card.rowconfigure(1, weight=1)
        
        # Kart gölgesi için kenar çizgisi
        if self.dark_mode:
            card["borderwidth"] = 1
            card["relief"] = "solid"
        
        # Kart başlığı
        ttk.Label(
            card,
            text=title,
            style="DetailHeader.TLabel"
        ).pack(anchor=tk.CENTER)
        
        return card

    def _on_entry_focus_in(self, event, placeholder):
        """Giriş alanı odaklandığında placeholder'ı siler."""
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)

    def _on_entry_focus_out(self, event, placeholder):
        """Giriş alanı odak kaybettiğinde placeholder'ı ekler."""
        if event.widget.get() == "":
            event.widget.insert(0, placeholder)

    def _toggle_theme(self):
        """Temayı değiştirir."""
        self.dark_mode = not self.dark_mode
        self._setup_colors()
        self._setup_styles()
        
        # Mevcut içeriği güncelle
        self._update_theme_for_all_widgets()
        
        # Seçili olayı tekrar göster
        selected = self.event_list.selection()
        if selected:
            self._on_event_select(None)

    def _update_theme_for_all_widgets(self):
        """Tüm widget'ları yeni temaya göre günceller."""
        self.configure(style="MainFrame.TFrame")
        
        # Tüm çocuk widget'ları güncelle
        for widget in self.winfo_children():
            self._update_widget_theme(widget)
    
    def _update_widget_theme(self, widget):
        """Belirtilen widget'ın temasını günceller."""
        try:
            # Widget tipine göre stil güncelleme
            widget_class = widget.winfo_class()
            
            if widget_class == "TFrame":
                if "Header" in str(widget["style"]):
                    widget.configure(style="Header.TFrame")
                else:
                    widget.configure(style="Card.TFrame")
            
            elif widget_class == "TLabel":
                if "Title" in str(widget["style"]):
                    widget.configure(style="Title.TLabel")
                elif "Section" in str(widget["style"]):
                    widget.configure(style="Section.TLabel")
                elif "DetailHeader" in str(widget["style"]):
                    widget.configure(style="DetailHeader.TLabel")
                elif "DetailValue" in str(widget["style"]):
                    widget.configure(style="DetailValue.TLabel")
                elif "Info" in str(widget["style"]):
                    widget.configure(style="Info.TLabel")
                else:
                    widget.configure(style="TLabel")
            
            elif widget_class == "TButton":
                if "Wide" in str(widget["style"]):
                    widget.configure(style="Wide.TButton")
                elif "Stop" in str(widget["style"]):
                    widget.configure(style="Stop.TButton")
                elif "Icon" in str(widget["style"]):
                    widget.configure(style="Icon.TButton")
                else:
                    widget.configure(style="TButton")
            
            elif widget_class == "TEntry":
                widget.configure(style="TEntry")
            
            elif widget_class == "Treeview":
                widget.configure(style="Treeview")
            
            elif widget_class == "Vertical.TScrollbar":
                widget.configure(style="Vertical.TScrollbar")
            
            # Çocuk widget'ları da güncelle
            for child in widget.winfo_children():
                self._update_widget_theme(child)
                
        except Exception as e:
            logging.debug(f"Widget tema güncellemesi sırasında hata: {str(e)}")
            pass
    
    def _on_configure(self, event):
        """Pencere boyutu değiştiğinde düzeni güncelle."""
        # Sadece olay gerçek pencere yeniden boyutlandırma olduğunda yanıt ver
        if event.widget == self and (event.width > 1 and event.height > 1):
            self.after(100, self._update_image_view)
    
    def _update_image_view(self):
        """Görüntüyü mevcut pencere boyutuna göre günceller."""
        if hasattr(self, "current_image") and self.current_image:
            self._display_image(self.current_image)
    
    def _clear_filters(self):
        """Filtreleri temizler ve tüm olayları gösterir."""
        self.date_filter_var.set("GG.AA.YYYY")
        self.conf_filter_var.set("")
        self.filtered_events = self.events
        self._update_event_list(self.events)
    
    def _load_events(self):
        """Olayları veritabanından asenkron olarak yükler."""
        try:
            # Düzenli gösterge için yükleniyor durumunu güncelle
            self._start_loading_interface()
            
            # Arka planda olayları yükle
            threading.Thread(target=self._load_events_thread, daemon=True).start()
        except Exception as e:
            logging.error(f"Olaylar yüklenirken hata: {str(e)}", exc_info=True)
            self._show_error("Veri Yükleme Hatası", f"Olaylar yüklenemedi: {str(e)}")
    
    def _start_loading_interface(self):
        """Yükleniyor arayüzünü gösterir."""
        # Treeview'ı temizle
        for item in self.event_list.get_children():
            self.event_list.delete(item)
        
        # Yükleniyor mesajı ekle
        self.event_list.insert("", "end", values=("Yükleniyor...", "", ""))
        
        # Yükleniyor animasyonu başlat
        self._start_loading_animation()
        
        # Başlık ve detay panelini temizle
        self.total_events_var.set("Yükleniyor...")
        self.date_var.set("--.--.---- --:--:--")
        self.conf_var.set("--.--")
        
        # Görüntüyü temizle
        self.image_label.configure(text="Yükleniyor...", image="")
    
    def _start_loading_animation(self):
        """Yükleniyor animasyonunu başlatır."""
        if self.loading_animation_id:
            self.after_cancel(self.loading_animation_id)
        
        dots = [".", "..", "...", ""]
        dot_index = 0
        
        def animate():
            nonlocal dot_index
            try:
                children = self.event_list.get_children()
                if children:
                    self.event_list.item(children[0], values=(f"Yükleniyor{dots[dot_index]}", "", ""))
                    dot_index = (dot_index + 1) % len(dots)
                    self.loading_animation_id = self.after(300, animate)
            except Exception:
                self.loading_animation_id = None
        
        self.loading_animation_id = self.after(300, animate)
    
    def _stop_loading_animation(self):
        """Yükleniyor animasyonunu durdurur."""
        if self.loading_animation_id:
            self.after_cancel(self.loading_animation_id)
            self.loading_animation_id = None
    
    def _load_events_thread(self):
        """Olayları veritabanından yükleyen thread fonksiyonu."""
        try:
            # Yükleme simülasyonu (gerçek uygulamada kaldırılabilir)
            time.sleep(0.5)
            
            # Veritabanından olayları al
            events = self.db_manager.get_fall_events(self.user["localId"], limit=50)
            self.events = events
            self.filtered_events = events
            
            # UI güncellemesi
            self.after(0, lambda: self._update_event_list(events))
        except Exception as e:
            logging.error(f"Olaylar yüklenirken thread hatası: {str(e)}", exc_info=True)
            self.after(0, lambda: self._show_error("Veri Yükleme Hatası", f"Olaylar yüklenemedi: {str(e)}"))
    
    def _apply_filters(self):
        """Olayları tarih ve olasılık filtrelerine göre günceller."""
        try:
            date_filter = self.date_filter_var.get().strip()
            conf_filter = self.conf_filter_var.get().strip()
            
            if date_filter == "GG.AA.YYYY":
                date_filter = ""
            
            filtered = self.events.copy()
            filter_applied = False
            
            # Tarih filtresi
            if date_filter:
                try:
                    filter_dt = datetime.datetime.strptime(date_filter, "%d.%m.%Y")
                    filtered = [
                        event for event in filtered
                        if datetime.datetime.fromtimestamp(float(event.get("timestamp", 0))).date() == filter_dt.date()
                    ]
                    filter_applied = True
                except ValueError:
                    self._show_error("Filtreleme Hatası", "Geçersiz tarih formatı. Örnek: 01.01.2025")
                    return
            
            # Olasılık filtresi
            if conf_filter:
                try:
                    conf_threshold = float(conf_filter) / 100
                    filtered = [
                        event for event in filtered
                        if float(event.get("confidence", 0.0)) >= conf_threshold
                    ]
                    filter_applied = True
                except ValueError:
                    self._show_error("Filtreleme Hatası", "Geçersiz olasılık değeri. Örnek: 50")
                    return
            
            self.filtered_events = filtered
            
            # Liste güncelleme
            self._update_event_list(filtered)
            
            # Filtreleme başarı mesajı
            if filter_applied:
                message = f"{len(filtered)} olay filtrelendi."
                if len(filtered) == 0:
                    message = "Filtrelere uygun olay bulunamadı."
                
                self._show_info("Filtreleme", message)
                
        except Exception as e:
            logging.error(f"Filtreleme sırasında hata: {str(e)}", exc_info=True)
            self._show_error("Filtreleme Hatası", f"Filtreleme başarısız: {str(e)}")
    
    def _update_event_list(self, events):
        """Olay listesini günceller."""
        try:
            # Animasyonu durdur
            self._stop_loading_animation()
            
            # Treeview'ı temizle
            for item in self.event_list.get_children():
                self.event_list.delete(item)
            
            # Toplam olay sayısını güncelle
            self.total_events_var.set(f"{len(events)} olay")
            
            # Olay yoksa mesaj göster
            if not events:
                self.event_list.insert("", "end", values=("Olay bulunamadı", "", ""))
                self.image_label.configure(text="Olay bulunamadı", image="")
                self.date_var.set("--.--.---- --:--:--")
                self.conf_var.set("--.--")
                return
            
            # Olayları listeye ekle (önce sırala - en yeni en üstte)
            sorted_events = sorted(
                events, 
                key=lambda x: float(x.get("timestamp", 0)) if isinstance(x.get("timestamp"), (str, int, float)) else 0,
                reverse=True
            )
            
            for event in sorted_events:
                timestamp = float(event.get("timestamp", 0)) if isinstance(event.get("timestamp"), (str, int, float)) else 0
                dt = datetime.datetime.fromtimestamp(timestamp)
                date_str = dt.strftime("%d.%m.%Y")
                time_str = dt.strftime("%H:%M:%S")
                
                confidence = float(event.get("confidence", 0.0)) if isinstance(event.get("confidence"), (str, int, float)) else 0.0
                conf_str = f"%{confidence * 100:.2f}"
                
                # Renk etiketi (olasılığa göre)
                tag = "normal"
                if confidence > 0.8:
                    tag = "high"
                elif confidence > 0.6:
                    tag = "medium"
                
                item_id = self.event_list.insert(
                    "", "end", text=event.get("id", ""), values=(date_str, time_str, conf_str), tags=(tag,)
                )
                
                # Özel satır renkleri ayarla
                if tag == "high":
                    self.event_list.tag_configure("high", background=self._adjust_color(self.danger_color, 0.2))
                elif tag == "medium":
                    self.event_list.tag_configure("medium", background=self._adjust_color(self.warning_color, 0.2))
            
            # İlk olayı otomatik seç
            if self.event_list.get_children():
                first_item = self.event_list.get_children()[0]
                self.event_list.selection_set(first_item)
                self.event_list.focus(first_item)
                self._on_event_select(None)
                
                # Liste görünümünü en üste kaydır
                self.event_list.see(first_item)
                
        except Exception as e:
            logging.error(f"Olay listesi güncellenirken hata: {str(e)}", exc_info=True)
            self._show_error("Liste Hatası", f"Olay listesi güncellenemedi: {str(e)}")
    
    def _on_event_select(self, event):
        """Bir olay seçildiğinde detayları gösterir."""
        try:
            selected = self.event_list.selection()
            if not selected:
                return
            
            item = selected[0]
            event_id = self.event_list.item(item, "text")
            
            # Seçilen olayı bul
            selected_event = next((e for e in self.filtered_events if e.get("id") == event_id), None)
            
            if selected_event:
                self._show_event_details(selected_event)
            else:
                self.image_label.configure(text="Olay detayları bulunamadı", image="")
                self.date_var.set("--.--.---- --:--:--")
                self.conf_var.set("--.--")
                
        except Exception as e:
            logging.error(f"Olay seçilirken hata: {str(e)}", exc_info=True)
            self._show_error("Detay Hatası", f"Olay detayları yüklenemedi: {str(e)}")
    
    def _delete_event(self):
        """Seçili olayı siler."""
        try:
            selected = self.event_list.selection()
            if not selected:
                self._show_info("Bilgi", "Lütfen silmek için bir olay seçin.")
                return
            
            item = selected[0]
            event_id = self.event_list.item(item, "text")
            
            # Onay isteği göster
            result = messagebox.askyesno(
                "Onay", 
                "Bu olayı silmek istediğinizden emin misiniz?",
                icon=messagebox.WARNING
            )
            
            if not result:
                return
            
            # Silme işlemini animasyonlu göster
            self.event_list.item(item, values=("Siliniyor...", "", ""))
            self.after(500, lambda: self._complete_delete(event_id))
            
        except Exception as e:
            logging.error(f"Olay silinirken hata: {str(e)}", exc_info=True)
            self._show_error("Silme Hatası", f"Olay silinemedi: {str(e)}")
    
    def _complete_delete(self, event_id):
        """Olay silme işlemini tamamlar."""
        try:
            # Veritabanından sil
            self.db_manager.delete_fall_event(self.user["localId"], event_id)
            
            # Belleği güncelle
            self.events = [e for e in self.events if e.get("id") != event_id]
            self.filtered_events = [e for e in self.filtered_events if e.get("id") != event_id]
            
            # Listeyi güncelle
            self._update_event_list(self.filtered_events)
            
            # Başarılı mesajı göster
            self._show_success("Başarılı", "Olay başarıyla silindi.")
            
        except Exception as e:
            logging.error(f"Olay silme işlemi tamamlanırken hata: {str(e)}", exc_info=True)
            self._show_error("Silme Hatası", f"Olay silinemedi: {str(e)}")
    
    def _show_event_details(self, event):
        """Seçilen olayın detaylarını gösterir."""
        try:
            # Timestamp'i doğru formata çevir
            timestamp = float(event.get("timestamp", 0)) if isinstance(event.get("timestamp"), (str, int, float)) else 0
            dt = datetime.datetime.fromtimestamp(timestamp)
            self.date_var.set(dt.strftime("%d.%m.%Y %H:%M:%S"))
            
            # Olasılık değerini ayarla
            confidence = float(event.get("confidence", 0.0)) if isinstance(event.get("confidence"), (str, int, float)) else 0.0
            conf_str = f"%{confidence * 100:.2f}"
            self.conf_var.set(conf_str)
            
            # Olasılık renk kodlaması
            color = self.danger_color if confidence > 0.8 else self.warning_color if confidence > 0.6 else self.success_color
            self.conf_label.configure(foreground=color)
            
            # Görüntüyü yükle
            image_url = event.get("image_url")
            if image_url:
                # Önbellekte var mı kontrol et
                if image_url in self.image_cache:
                    self._display_image(self.image_cache[image_url])
                else:
                    # Görüntü yükleniyor mesajı
                    self.image_label.configure(text="Görüntü yükleniyor...", image="")
                    # Arka planda yükle
                    threading.Thread(target=self._load_image, args=(image_url,), daemon=True).start()
            else:
                self.image_label.configure(text="Ekran görüntüsü bulunamadı", image="")
                self.current_image = None
                
        except Exception as e:
            logging.error(f"Olay detayları gösterilirken hata: {str(e)}", exc_info=True)
            self.image_label.configure(text="Detaylar yüklenemedi", image="")
    
    def _load_image(self, url):
        """Görüntüyü URL'den asenkron olarak yükler ve önbelleğe alır."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            img_data = BytesIO(response.content)
            pil_img = Image.open(img_data)
            
            # Önbelleğe kaydet
            self.image_cache[url] = pil_img
            
            # Görüntüyü göster (fade-in animasyonu ile)
            self.after(0, lambda: self._display_image_with_animation(pil_img))
            
        except Exception as e:
            logging.error(f"Görüntü yüklenirken hata: {str(e)}", exc_info=True)
            self.after(0, lambda: self.image_label.configure(
                text=f"Görüntü yüklenemedi: {str(e)}", 
                image=""
            ))
            self.current_image = None
    
    def _display_image_with_animation(self, pil_img):
        """Görüntüyü fade-in animasyonu ile gösterir."""
        self.current_image = pil_img
        self.fade_alpha = 0.0
        
        def fade_step():
            self.fade_alpha += 0.1
            if self.fade_alpha >= 1.0:
                self.fade_alpha = 1.0
                self._display_image(pil_img)
                return
            
            # Geçiş efekti için görüntüyü işle
            alpha_img = self._apply_fade(pil_img, self.fade_alpha)
            self._display_image(alpha_img)
            self.after(30, fade_step)
        
        fade_step()
    
    def _apply_fade(self, img, alpha):
        """Görüntüye alfa karıştırma uygular."""
        try:
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(alpha)
        except:
            return img
    
    def _display_image(self, pil_img):
        """Görüntüyü mevcut zoom seviyesine göre gösterir."""
        try:
            if not pil_img:
                self.image_label.configure(text="Görüntü yok", image="")
                return
            
            # Orijinal boyutları sakla
            if not hasattr(self, 'original_width') or not self.original_width:
                self.original_width = pil_img.width
                self.original_height = pil_img.height
            
            # Zoom ve görüntü işlemleri
            img_width = int(self.original_width * self.zoom_level)
            img_height = int(self.original_height * self.zoom_level)
            
            # Yeniden boyutlandır
            if self.zoom_level != 1.0:
                resized_img = pil_img.resize((img_width, img_height), Image.LANCZOS)
            else:
                resized_img = pil_img.copy()
            
            # Özel efektler uygula
            if self.dark_mode:
                # Dark mode için hafif kontrast artışı
                enhancer = ImageEnhance.Contrast(resized_img)
                resized_img = enhancer.enhance(1.1)
            
            # Tkinter görüntüsüne dönüştür
            tk_img = ImageTk.PhotoImage(resized_img)
            
            # Görüntüyü göster
            self.image_label.configure(image=tk_img, text="")
            self.image_label.image = tk_img
            
        except Exception as e:
            logging.error(f"Görüntü gösterilirken hata: {str(e)}", exc_info=True)
            self.image_label.configure(text=f"Görüntü gösterilemiyor: {str(e)}", image="")
    
    def _zoom_in(self):
        """Görüntüyü yakınlaştırır."""
        if not self.current_image:
            return
        
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self._display_image(self.current_image)
    
    def _zoom_out(self):
        """Görüntüyü uzaklaştırır."""
        if not self.current_image:
            return
        
        self.zoom_level = max(0.5, self.zoom_level - 0.25)
        self._display_image(self.current_image)
    
    def _toggle_fullscreen(self):
        """Görüntü detay panelini genişletir/daraltır."""
        if not self.current_image:
            return
        
        self.detail_panel_expanded = not self.detail_panel_expanded
        
        if self.detail_panel_expanded:
            # Detay panelini genişlet
            self.columnconfigure(0, weight=1)
            
            # İçerik çerçevesini güncelle
            content_frame = self.winfo_children()[2]  # İçerik çerçevesi
            content_frame.columnconfigure(0, weight=0)  # Liste kısmını küçült
            content_frame.columnconfigure(1, weight=5)  # Detay kısmını genişlet
            
            # Görüntüyü büyüt
            self.zoom_level = 1.5
            self._display_image(self.current_image)
        else:
            # Normal görünüme dön
            content_frame = self.winfo_children()[2]  # İçerik çerçevesi
            content_frame.columnconfigure(0, weight=3)
            content_frame.columnconfigure(1, weight=4)
            
            # Görüntüyü normal boyuta getir
            self.zoom_level = 1.0
            self._display_image(self.current_image)
    
    def _mouse_wheel(self, event):
        """Fare tekerleği ile zoom yapar."""
        if not self.current_image:
            return
        
        # Windows ve çoğu Linux için
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
    
    def _mouse_down(self, event):
        """Fare tıklaması ile sürükleme başlangıcı."""
        if not self.current_image or self.zoom_level <= 1.0:
            return
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.dragging = True
    
    def _mouse_drag(self, event):
        """Fare sürüklemesi ile görüntüyü kaydırır."""
        if not self.dragging:
            return
        
        # Sürükleme miktarını hesapla
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        self.image_offset_x += dx
        self.image_offset_y += dy
        
        # Yeni başlangıç noktalarını güncelle
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Görüntüyü sürüklenmiş konumda göster
        if self.current_image:
            img = self.current_image.copy()
            img_width = int(self.original_width * self.zoom_level)
            img_height = int(self.original_height * self.zoom_level)
            
            # Görüntüyü kırp veya kaydır
            # Bu basit bir örnek - daha gelişmiş kaydırma için
            # PIL'in ImageDraw veya başka teknikler kullanılabilir
            self._display_image(img)
    
    def _mouse_up(self, event):
        """Fare bırakıldığında sürükleme sonlandırma."""
        self.dragging = False
    
    def _export_image(self):
        """Mevcut görüntüyü diske kaydeder."""
        if not self.current_image:
            self._show_info("Bilgi", "Kaydedilecek görüntü bulunamadı.")
            return
        
        try:
            from tkinter import filedialog
            
            # Dosya kaydetme iletişim kutusu
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ],
                title="Görüntüyü Kaydet"
            )
            
            if filename:
                self.current_image.save(filename)
                self._show_success("Başarılı", f"Görüntü başarıyla kaydedildi:\n{filename}")
        except Exception as e:
            logging.error(f"Görüntü kaydedilirken hata: {str(e)}", exc_info=True)
            self._show_error("Kaydetme Hatası", f"Görüntü kaydedilemedi: {str(e)}")
    
    def _show_error(self, title, message):
        """Hata mesajı gösterir."""
        messagebox.showerror(title, message)
    
    def _show_info(self, title, message):
        """Bilgi mesajı gösterir."""
        messagebox.showinfo(title, message)
    
    def _show_success(self, title, message):
        """Başarı mesajı gösterir."""
        messagebox.showinfo(title, message)
    
    def _adjust_color(self, hex_color, alpha):
        """Rengi belirtilen şeffaflık oranıyla karıştırır."""
        try:
            # Hex rengini RGB'ye dönüştür
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Arka plan rengini al
            if self.dark_mode:
                bg_r, bg_g, bg_b = 30, 30, 30  # Koyu arka plan
            else:
                bg_r, bg_g, bg_b = 255, 255, 255  # Açık arka plan
            
            # Renkleri karıştır
            r = int(r * alpha + bg_r * (1 - alpha))
            g = int(g * alpha + bg_g * (1 - alpha))
            b = int(b * alpha + bg_b * (1 - alpha))
            
            # RGB'yi hex'e dönüştür
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color