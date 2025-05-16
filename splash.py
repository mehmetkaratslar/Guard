import tkinter as tk
import time
import threading
import os
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import math

class SplashScreen:
    """Modern ve etkileyici uygulama açılış ekranı."""
    
    def __init__(self, root, duration=3.0):
        """
        Args:
            root (tk.Tk): Ana pencere
            duration (float, optional): Açılış ekranı süresi (saniye)
        """
        self.root = root
        self.duration = duration
        self.splash_window = None
        
        # Ana pencereyi gizle
        self.root.withdraw()
        
        # Splash ekranını göster
        self._show_splash()
        
        # Belirli bir süre sonra ana pencereyi göster
        threading.Thread(target=self._show_main_after_delay, daemon=True).start()
    
    def _show_splash(self):
        """Modern ve etkileyici splash ekranını gösterir."""
        # Yeni bir pencere oluştur
        self.splash_window = tk.Toplevel(self.root)
        self.splash_window.title("Guard")
        
        # Pencereyi tam ekran yap
        width = self.splash_window.winfo_screenwidth()
        height = self.splash_window.winfo_screenheight()
        self.splash_window.geometry(f"{width//2}x{height//2}+{width//4}+{height//4}")
        
        # Pencere dekorasyonlarını kaldır ve borderless yap
        self.splash_window.overrideredirect(True)
        
        # Degrade arka plan oluştur
        self.canvas = tk.Canvas(self.splash_window, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Gradient arka plan için daha modern ve canlı renkler
        gradient_colors = [
            "#0D47A1",  # Koyu mavi (başlangıç)
            "#1976D2",  # Orta mavi
            "#2196F3",  # Açık mavi (bitiş)
        ]
        
        # Degrade efekti
        for i in range(height//2):
            # Yüzde olarak geçerli pozisyon
            percent = i / (height//2)
            
            # İki renk arasında geçiş yap
            if percent < 0.5:
                # İlk yarı - ilk iki renk arasında geçiş
                t = percent * 2  # 0 -> 1
                r1, g1, b1 = int(gradient_colors[0][1:3], 16), int(gradient_colors[0][3:5], 16), int(gradient_colors[0][5:7], 16)
                r2, g2, b2 = int(gradient_colors[1][1:3], 16), int(gradient_colors[1][3:5], 16), int(gradient_colors[1][5:7], 16)
            else:
                # İkinci yarı - ikinci iki renk arasında geçiş
                t = (percent - 0.5) * 2  # 0 -> 1
                r1, g1, b1 = int(gradient_colors[1][1:3], 16), int(gradient_colors[1][3:5], 16), int(gradient_colors[1][5:7], 16)
                r2, g2, b2 = int(gradient_colors[2][1:3], 16), int(gradient_colors[2][3:5], 16), int(gradient_colors[2][5:7], 16)
            
            # İki rengi karıştır
            r = int(r1 * (1 - t) + r2 * t)
            g = int(g1 * (1 - t) + g2 * t)
            b = int(b1 * (1 - t) + b2 * t)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, width//2, i, fill=color)
        
        # Saydam gölge efekti için çizgiler
        for i in range(20):
            opacity = 20 - i  # 20'den 1'e azalan opaklık
            shadow_color = f"#00000{opacity:01x}" if opacity < 16 else f"#0000{opacity:02x}"
            self.canvas.create_line(0, i, width//2, i, fill=shadow_color)
        
        # Dekoratif elemanlar
        # Sağ alt köşe daire
        self.canvas.create_oval(width//2-180, height//2-180, width//2+50, height//2+50, 
                              fill="#64B5F6", outline="")
        
        # Sol üst köşe daire
        self.canvas.create_oval(-50, -50, 100, 100, 
                              fill="#90CAF9", outline="")
        
        # Orta sağ daire
        self.canvas.create_oval(width//2-150, height//4-50, width//2-50, height//4+50, 
                              fill="#E1F5FE", outline="")
        
        # Logo
        try:
            logo_path = os.path.join(
                os.path.dirname(__file__), 
                "resources", 
                "icons", 
                "logo.png"
            )
            
            if os.path.exists(logo_path):
                # Logo'yu büyük ölçeklendir
                orig_img = Image.open(logo_path)
                # Görüntüyü keskinleştirme ve parlaklık artırma
                enhancer = ImageEnhance.Sharpness(orig_img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.2)
                
                logo_size = int(min(width//2, height//2) * 0.4)
                img = img.resize((logo_size, logo_size), Image.LANCZOS)
                
                # Hafif bir glow efekti ekle
                glow_img = img.filter(ImageFilter.GaussianBlur(radius=10))
                glow_img = ImageEnhance.Brightness(glow_img).enhance(1.5)
                
                # Ana resmi glow üzerine yerleştir
                # Glow'u bir kenara kaydet
                self.glow_img = ImageTk.PhotoImage(glow_img)
                # Ana resmi kaydet
                self.logo_img = ImageTk.PhotoImage(img)
                
                # Glow efekti arka planda
                self.glow_label = tk.Label(
                    self.splash_window,
                    image=self.glow_img,
                    bg='#1976D2'  # Gradient orta rengi
                )
                self.glow_label.place(relx=0.5, rely=0.35, anchor="center")
                
                # Ana logo üstte
                self.logo_label = tk.Label(
                    self.splash_window,
                    image=self.logo_img,
                    bg='#1976D2'  # Gradient orta rengi
                )
                self.logo_label.place(relx=0.5, rely=0.35, anchor="center")
                
                # Logo pulsing animasyonu
                self.pulse_direction = 1
                self.pulse_alpha = 0
                def animate_pulse():
                    self.pulse_alpha += 0.05 * self.pulse_direction
                    if self.pulse_alpha >= 1.0:
                        self.pulse_alpha = 1.0
                        self.pulse_direction = -1
                    elif self.pulse_alpha <= 0.0:
                        self.pulse_alpha = 0.0
                        self.pulse_direction = 1
                    
                    # Glow opacity'yi değiştir
                    opacity = int(self.pulse_alpha * 255)
                    self.glow_label.configure(bg=f"#1976D2")
                    self.splash_window.after(50, animate_pulse)
                
                animate_pulse()
                
        except Exception as e:
            print(f"Logo yüklenirken hata: {e}")
        
        # Ana başlık
        title_frame = tk.Frame(self.splash_window, bg="#1976D2")
        title_frame.place(relx=0.5, rely=0.65, anchor="center")
        
        # GUARD yazısı - büyük, kalın ve şık
        app_name = tk.Label(
            title_frame,
            text="GUARD",
            font=("Segoe UI", 48, "bold"),
            fg="#ffffff",
            bg="#1976D2"
        )
        app_name.pack()
        
        # Alt başlık - daha şık bir yazı tipi
        app_desc = tk.Label(
            title_frame,
            text="Akıllı Düşme Algılama Sistemi",
            font=("Segoe UI", 18, "italic"),
            fg="#E1F5FE",  # Açık mavi
            bg="#1976D2"
        )
        app_desc.pack(pady=(5, 0))
        
        # İlerleme çubuğu container'ı
        progress_container = tk.Frame(self.splash_window, bg="#1976D2", padx=50)
        progress_container.place(relx=0.5, rely=0.85, anchor="center", width=width//2-100)
        
        # İlerleme çubuğu etiket metni
        progress_text = tk.Label(
            progress_container,
            text="Yükleniyor...",
            font=("Segoe UI", 10),
            fg="#E1F5FE",
            bg="#1976D2"
        )
        progress_text.pack(anchor="w", pady=(0, 5))
        
        # İlerleme çubuğu
        progress_frame = tk.Frame(progress_container, bg="#1976D2")
        progress_frame.pack(fill="x")
        
        # Modern yuvarlak köşeli ilerleme çubuğu
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        progress_width = width//2 - 100
        progress_height = 10
        
        # İlerleme çubuğu arka planı
        progress_bg = tk.Canvas(
            progress_frame, 
            width=progress_width, 
            height=progress_height,
            bg="#0D47A1",  # Koyu mavi
            highlightthickness=0
        )
        progress_bg.pack(fill="x")
        
        # Yuvarlak köşeler için arka plan
        progress_bg.create_rectangle(
            2, 2, progress_width-2, progress_height-2,
            fill="#0D47A1", outline="",
            width=0
        )
        
        # İlerleme çubuğu animasyonu
        def update_progress():
            progress_value = self.progress_var.get()
            progress_value = (progress_value + 0.01) % 1.0
            self.progress_var.set(progress_value)
            
            progress_bg.delete("progress")
            bar_width = int(progress_width * progress_value)
            
            # Ana ilerleme çubuğu
            progress_bg.create_rectangle(
                2, 2, bar_width, progress_height-2,
                fill="#64B5F6",  # Açık mavi
                outline="",
                tags="progress"
            )
            
            # Parlama efekti
            if progress_value > 0:
                progress_bg.create_rectangle(
                    max(0, bar_width-15), 2, bar_width, progress_height-2,
                    fill="#90CAF9",  # Daha açık mavi
                    outline="",
                    tags="progress"
                )
            
            self.splash_window.after(30, update_progress)
        
        update_progress()
        
        # Versiyon ve telif bilgisi
        version = tk.Label(
            self.splash_window,
            text="Versiyon 1.0.0 | © 2025 Guard Technologies",
            font=("Segoe UI", 9),
            fg="#E1F5FE",  # Açık mavi
            bg="#1976D2"
        )
        version.place(relx=0.5, rely=0.95, anchor="center")
    
    def _show_main_after_delay(self):
        """Belirli bir süre sonra ana pencereyi gösterir."""
        time.sleep(self.duration)
        
        # Splash ekranını kapat
        self.root.after(0, self._close_splash)
    
    def _close_splash(self):
        """Yumuşak geçiş ile splash ekranını kapatır."""
        if self.splash_window:
            # Yumuşak kapanış animasyonu
            for alpha in range(10, -1, -1):
                self.splash_window.attributes('-alpha', alpha/10)
                self.splash_window.update()
                time.sleep(0.03)
            
            self.splash_window.destroy()
            self.splash_window = None
        
        # Ana pencereyi göster
        self.root.deiconify()