import customtkinter as ctk
from tkinter import messagebox
from . import pin_manager

class LoginUI:
    def __init__(self, app):
        self.app = app

    def create_login_screen(self):
        """Crée l'interface de connexion par code PIN."""
        self.app.login_frame.grid_columnconfigure(0, weight=1)
        self.app.login_frame.grid_rowconfigure((0, 5), weight=1)

        ctk.CTkLabel(self.app.login_frame, text="Application Verrouillée", font=self.app.font_title).grid(row=1, column=0, pady=20)
        
        self.app.pin_entry = ctk.CTkEntry(self.app.login_frame, placeholder_text="Code PIN", show="*", width=200, justify="center", font=self.app.font_large)
        self.app.pin_entry.grid(row=2, column=0, pady=10)
        self.app.pin_entry.bind("<Return>", self._check_pin)
        self.app.pin_entry.focus()

        # --- Pad Numérique ---
        numpad_frame = ctk.CTkFrame(self.app.login_frame, fg_color="transparent")
        numpad_frame.grid(row=3, column=0, pady=10)

        numpad_buttons = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            'C', '0', '⌫'
        ]

        for i, btn_text in enumerate(numpad_buttons):
            row, col = divmod(i, 3)
            
            action = None
            if btn_text.isdigit():
                action = lambda t=btn_text: self._on_numpad_press(t)
            elif btn_text == 'C':
                action = self._on_numpad_clear
            elif btn_text == '⌫':
                action = self._on_numpad_backspace
                
            btn = ctk.CTkButton(numpad_frame, text=btn_text, width=70, height=70, font=self.app.font_large, command=action, fg_color="transparent", border_width=1, text_color=("#1E1E1E", "#E0E0E0"))
            btn.grid(row=row, column=col, padx=5, pady=5)

        ctk.CTkButton(self.app.login_frame, text="Déverrouiller", command=self._check_pin, width=230, height=40, font=self.app.font_button).grid(row=4, column=0, pady=20)

    def _check_pin(self, event=None):
        """Vérifie le code PIN saisi."""
        pin = self.app.pin_entry.get()
        if pin_manager.verify_pin(pin):
            self.app.login_frame.grid_forget()
            self.app.menu_frame.grid(row=0, column=0, sticky="nsew")
            # Import différé pour éviter les cycles si dashboard a besoin de app
            from .dashboard import update_dashboard_kpis
            update_dashboard_kpis(self.app)
            
            # Vérification des frais automatiques (1er du mois)
            self.app.check_automatic_expenses()
        else:
            self.app.pin_entry.delete(0, 'end')
            messagebox.showerror("Erreur", "Code PIN incorrect.")

    def _on_numpad_press(self, digit):
        self.app.pin_entry.insert(ctk.END, digit)

    def _on_numpad_clear(self):
        self.app.pin_entry.delete(0, ctk.END)

    def _on_numpad_backspace(self):
        current_text = self.app.pin_entry.get()
        self.app.pin_entry.delete(len(current_text) - 1, ctk.END)
