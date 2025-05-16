import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import os
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import re

class LoginFrame(ttk.Frame):
    """Modern ve kullanıcı dostu giriş ekranı."""

    def __init__(self, parent, auth, on_login_success, on_register_click=None):
        super().__init__(parent)
        self.parent = parent
        self.auth = auth
        self.on_login_success = on_login_success
        self.on_register_click = on_register_click
        
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self._draw_background()
        self._create_ui()
        parent.bind('<Configure>', self._on_resize)
    
    def _draw_background(self):
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        if width <= 1 or height <= 1:
            width = self.parent.winfo_screenwidth()
            height = self.parent.winfo_screenheight()
        
        self.canvas.delete("all")
        
        gradient_colors = ["#0D47A1", "#1976D2", "#2196F3"]
        for i in range(height):
            percent = i / height
            if percent < 0.5:
                t = percent * 2
                r1, g1, b1 = int(gradient_colors[0][1:3], 16), int(gradient_colors[0][3:5], 16), int(gradient_colors[0][5:7], 16)
                r2, g2, b2 = int(gradient_colors[1][1:3], 16), int(gradient_colors[1][3:5], 16), int(gradient_colors[1][5:7], 16)
            else:
                t = (percent - 0.5) * 2
                r1, g1, b1 = int(gradient_colors[1][1:3], 16), int(gradient_colors[1][3:5], 16), int(gradient_colors[1][5:7], 16)
                r2, g2, b2 = int(gradient_colors[2][1:3], 16), int(gradient_colors[2][3:5], 16), int(gradient_colors[2][5:7], 16)
            
            r = int(r1 * (1 - t) + r2 * t)
            g = int(g1 * (1 - t) + g2 * t)
            b = int(b1 * (1 - t) + b2 * t)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, width, i, fill=color)
        
        self.canvas.create_oval(width-200, height-200, width+100, height+100, fill="#64B5F6", outline="")
        self.canvas.create_oval(-50, -50, 100, 100, fill="#90CAF9", outline="")
        self.canvas.create_oval(width-150, height//2-75, width-50, height//2+75, fill="#E1F5FE", outline="")
    
    def _on_resize(self, event):
        if event.widget == self.parent:
            self._draw_background()
            if hasattr(self, 'login_card'):
                self.login_card.place(relx=0.5, rely=0.5, anchor="center")
    
    def _add_shadow_to_frame(self, frame):
        frame.configure(highlightbackground="#CCCCCC", highlightthickness=1)
    
    def _create_ui(self):
        self.login_card = tk.Frame(self, bg="#FFFFFF", padx=40, pady=40, borderwidth=0)
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")
        
        self._add_shadow_to_frame(self.login_card)
        
        title_frame = tk.Frame(self.login_card, bg="#FFFFFF")
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.2)
                img = img.resize((120, 120), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(title_frame, image=logo_photo, bg="#FFFFFF")
                logo_label.image = logo_photo
                logo_label.pack(pady=(0, 15))
        except Exception as e:
            logging.warning(f"Logo yüklenemedi: {str(e)}")
        
        app_name = tk.Label(title_frame, text="Guard", font=("Segoe UI", 28, "bold"), fg="#1976D2", bg="#FFFFFF")
        app_name.pack()
        
        app_desc = tk.Label(title_frame, text="Düşme Algılama Sistemi", font=("Segoe UI", 16), fg="#757575", bg="#FFFFFF")
        app_desc.pack(pady=(5, 20))
        
        form_frame = tk.Frame(self.login_card, bg="#FFFFFF")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        email_frame = tk.Frame(form_frame, bg="#FFFFFF")
        email_frame.pack(fill=tk.X, pady=(0, 20))
        
        email_label = tk.Label(email_frame, text="E-posta", font=("Segoe UI", 12, "bold"), fg="#2c3e50", bg="#FFFFFF")
        email_label.pack(anchor=tk.W)
        
        email_entry_frame = tk.Frame(email_frame, bg="#F5F5F5", padx=10, pady=5)
        email_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        email_icon = tk.Label(email_entry_frame, text="@", font=("Segoe UI", 12), fg="#757575", bg="#F5F5F5")
        email_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(email_entry_frame, textvariable=self.email_var, font=("Segoe UI", 12), fg="#2c3e50", bg="#F5F5F5", relief="flat", highlightthickness=0, width=35)
        self.email_entry.pack(fill=tk.X, expand=True)
        self.email_entry.bind("<FocusOut>", self._validate_email)
        
        password_frame = tk.Frame(form_frame, bg="#FFFFFF")
        password_frame.pack(fill=tk.X, pady=(0, 20))
        
        password_label = tk.Label(password_frame, text="Şifre", font=("Segoe UI", 12, "bold"), fg="#2c3e50", bg="#FFFFFF")
        password_label.pack(anchor=tk.W)
        
        password_entry_frame = tk.Frame(password_frame, bg="#F5F5F5", padx=10, pady=5)
        password_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        password_icon = tk.Label(password_entry_frame, text="🔒", font=("Segoe UI", 12), fg="#757575", bg="#F5F5F5")
        password_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(password_entry_frame, textvariable=self.password_var, show="•", font=("Segoe UI", 12), fg="#2c3e50", bg="#F5F5F5", relief="flat", highlightthickness=0, width=35)
        self.password_entry.pack(fill=tk.X, expand=True)
        self.password_entry.bind("<FocusOut>", self._validate_password)

        buttons_frame = tk.Frame(form_frame, bg="#FFFFFF")
        buttons_frame.pack(fill=tk.X, pady=20)
        
        login_btn = tk.Button(buttons_frame, text="Giriş Yap", font=("Segoe UI", 12, "bold"), fg="#FFFFFF", bg="#1976D2", activebackground="#1565C0", activeforeground="#FFFFFF", relief="flat", padx=15, pady=10, cursor="hand2", command=self._on_submit)
        login_btn.pack(fill=tk.X)
        
        toggle_frame = tk.Frame(form_frame, bg="#FFFFFF")
        toggle_frame.pack(fill=tk.X, pady=10)
        
        register_label = tk.Label(toggle_frame, text="Hesabınız yok mu? Kayıt olun.", font=("Segoe UI", 10, "underline"), fg="#1976D2", bg="#FFFFFF", cursor="hand2")
        register_label.pack()
        register_label.bind("<Button-1>", self._on_register_click)
        
        separator_frame = tk.Frame(form_frame, bg="#FFFFFF")
        separator_frame.pack(fill=tk.X, pady=15)
        
        separator_left = tk.Frame(separator_frame, bg="#E0E0E0", height=1)
        separator_left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        separator_text = tk.Label(separator_frame, text="veya", font=("Segoe UI", 10), fg="#757575", bg="#FFFFFF")
        separator_text.pack(side=tk.LEFT)
        
        separator_right = tk.Frame(separator_frame, bg="#E0E0E0", height=1)
        separator_right.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        google_frame = tk.Frame(form_frame, bg="#FFFFFF")
        google_frame.pack(fill=tk.X, pady=10)
        
        google_btn = tk.Button(google_frame, text="Google ile Giriş Yap", font=("Segoe UI", 12), fg="#757575", bg="#F5F5F5", activebackground="#E0E0E0", activeforeground="#757575", relief="flat", padx=15, pady=10, cursor="hand2", command=self._google_login)
        
        try:
            google_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "google_icon.png")
            if os.path.exists(google_icon_path):
                google_img = Image.open(google_icon_path).resize((24, 24), Image.LANCZOS)
                google_icon = ImageTk.PhotoImage(google_img)
                google_btn.config(image=google_icon, compound=tk.LEFT, padx=10)
                google_btn.image = google_icon
        except Exception as e:
            logging.warning(f"Google ikonu yüklenemedi: {str(e)}")
        
        google_btn.pack(fill=tk.X)
        
        self.progress_frame = tk.Frame(self.login_card, bg="#FFFFFF")
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(self.progress_frame, variable=self.progress_var, mode="indeterminate")
        self.progress.pack(fill=tk.X)
        self.progress_frame.pack_forget()

    def _validate_email(self, event=None):
        email = self.email_var.get().strip()
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            self.email_entry.configure(fg="#E53935")
            return False
        else:
            self.email_entry.configure(fg="#2c3e50")
            return True

    def _validate_password(self, event=None):
        password = self.password_var.get()
        if len(password) >= 6:
            self.password_entry.configure(fg="#2c3e50")
            return True
        else:
            self.password_entry.configure(fg="#E53935")
            return False

    def _on_submit(self):
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        if not email or not password:
            self._show_error("Hata", "E-posta ve şifre alanları boş olamaz.")
            return
        
        if not self._validate_email():
            self._show_error("Hata", "Geçerli bir e-posta adresi giriniz.")
            return
        
        if not self._validate_password():
            self._show_error("Hata", "Şifre en az 6 karakter olmalıdır.")
            return
        
        self._show_progress(True)
        threading.Thread(target=self._login, args=(email, password), daemon=True).start()

    def _login(self, email, password):
        try:
            user = self.auth.sign_in_with_email_password(email, password)
            self.after(0, lambda: self._login_success(user))
        except Exception as e:
            self.after(0, lambda error=str(e): self._show_error("Giriş Hatası", error))
        finally:
            self.after(0, lambda: self._show_progress(False))

    def _google_login(self):
        self._show_progress(True)
        threading.Thread(target=self._perform_google_login, daemon=True).start()

    def _perform_google_login(self):
        try:
            auth_url, auth_code = self.auth.sign_in_with_google()
            self.after(100, lambda: self._get_auth_response(auth_code))
        except Exception as e:
            self.after(0, lambda error=str(e): self._show_error("Giriş Hatası", f"Google ile giriş başarısız: {error}"))
            self.after(0, lambda: self._show_progress(False))

    def _get_auth_response(self, auth_code):
        if not auth_code:
            self.after(0, lambda: self._show_progress(False))
            return
        
        try:
            user = self.auth.complete_google_sign_in(None, auth_code)
            self.after(0, lambda: self._login_success(user))
        except Exception as e:
            self.after(0, lambda error=str(e): self._show_error("Giriş Hatası", f"Google giriş tamamlanamadı: {error}"))
            self.after(0, lambda: self._show_progress(False))

    def _on_register_click(self, event=None):
        logging.info("Kayıt ol bağlantısına tıklandı")
        try:
            if self.on_register_click:
                self.on_register_click()
            else:
                logging.warning("on_register_click callback tanımlı değil.")
                self._show_error("Hata", "Kayıt ekranı açılamadı: Callback tanımlı değil.")
        except Exception as e:
            logging.error(f"Kayıt ekranı açılırken hata: {str(e)}")
            self._show_error("Hata", f"Kayıt ekranı açılamadı: {str(e)}")

    def _login_success(self, user):
        logging.info(f"Kullanıcı giriş yaptı: {user.get('email', '')}")
        self._show_progress(False)
        
        self._show_success_animation()
        if self.on_login_success:
            self.after(1000, lambda: self.on_login_success(user))

    def _show_success_animation(self):
        for widget in self.login_card.winfo_children():
            widget.pack_forget()
        
        success_frame = tk.Frame(self.login_card, bg="#FFFFFF")
        success_frame.pack(expand=True, fill=tk.BOTH)
        
        success_icon = tk.Label(success_frame, text="✓", font=("Segoe UI", 72, "bold"), fg="#4CAF50", bg="#FFFFFF")
        success_icon.pack(pady=(30, 20))
        
        success_label = tk.Label(success_frame, text="Giriş Başarılı!", font=("Segoe UI", 20, "bold"), fg="#1976D2", bg="#FFFFFF")
        success_label.pack(pady=(0, 20))
        
        loading_label = tk.Label(success_frame, text="Yönlendiriliyorsunuz...", font=("Segoe UI", 12), fg="#757575", bg="#FFFFFF")
        loading_label.pack(pady=(0, 30))

    def _show_error(self, title, message):
        messagebox.showerror(title, message)

    def _show_progress(self, show=True):
        if show:
            self.progress_frame.pack(fill=tk.X, pady=(15, 0))
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress_frame.pack_forget()