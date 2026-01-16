"""
Aba de configuracoes
"""
import customtkinter as ctk
from typing import Callable, Optional

from config.settings import Settings


class SettingsTab(ctk.CTkFrame):
    """Aba de configuracoes do bot"""

    def __init__(self, parent, settings: Settings, on_save: Optional[Callable[[], None]] = None):
        super().__init__(parent)

        self.settings = settings
        self.on_save = on_save

        self._create_widgets()
        self._load_values()

    def _create_widgets(self):
        """Cria widgets"""
        # Titulo
        title = ctk.CTkLabel(
            self,
            text="Configuracoes",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=10)

        # Frame principal com scroll
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=350)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # === API Key ===
        api_frame = ctk.CTkFrame(self.scroll_frame)
        api_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(api_frame, text="API Key PumpPortal:", anchor="w").pack(fill="x", padx=5, pady=2)
        self.api_key_entry = ctk.CTkEntry(api_frame, width=400, show="*")
        self.api_key_entry.pack(fill="x", padx=5, pady=2)

        self.show_api_var = ctk.BooleanVar(value=False)
        show_api_cb = ctk.CTkCheckBox(
            api_frame,
            text="Mostrar",
            variable=self.show_api_var,
            command=self._toggle_api_visibility,
            width=80
        )
        show_api_cb.pack(anchor="e", padx=5)

        # === Buy Settings ===
        buy_frame = ctk.CTkFrame(self.scroll_frame)
        buy_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            buy_frame,
            text="Configuracoes de Compra",
            font=ctk.CTkFont(weight="bold")
        ).pack(fill="x", padx=5, pady=5)

        # Buy Amount
        amount_frame = ctk.CTkFrame(buy_frame, fg_color="transparent")
        amount_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(amount_frame, text="Buy Amount (SOL):", width=150, anchor="w").pack(side="left")
        self.buy_amount_entry = ctk.CTkEntry(amount_frame, width=100)
        self.buy_amount_entry.pack(side="left", padx=5)

        # Slippage
        slip_frame = ctk.CTkFrame(buy_frame, fg_color="transparent")
        slip_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(slip_frame, text="Slippage (%):", width=150, anchor="w").pack(side="left")
        self.slippage_slider = ctk.CTkSlider(slip_frame, from_=1, to=50, width=150)
        self.slippage_slider.pack(side="left", padx=5)
        self.slippage_label = ctk.CTkLabel(slip_frame, text="49%", width=50)
        self.slippage_label.pack(side="left")
        self.slippage_slider.configure(command=self._update_slippage_label)

        # Priority Fee
        fee_frame = ctk.CTkFrame(buy_frame, fg_color="transparent")
        fee_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(fee_frame, text="Priority Fee (SOL):", width=150, anchor="w").pack(side="left")
        self.priority_fee_entry = ctk.CTkEntry(fee_frame, width=100)
        self.priority_fee_entry.pack(side="left", padx=5)

        # Num Attempts
        attempts_frame = ctk.CTkFrame(buy_frame, fg_color="transparent")
        attempts_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(attempts_frame, text="Tentativas:", width=150, anchor="w").pack(side="left")
        self.attempts_entry = ctk.CTkEntry(attempts_frame, width=100)
        self.attempts_entry.pack(side="left", padx=5)

        # Delay Between
        delay_frame = ctk.CTkFrame(buy_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(delay_frame, text="Delay entre (seg):", width=150, anchor="w").pack(side="left")
        self.delay_entry = ctk.CTkEntry(delay_frame, width=100)
        self.delay_entry.pack(side="left", padx=5)

        # Info pool=auto
        ctk.CTkLabel(
            buy_frame,
            text="Pool: auto (fixo)",
            text_color="gray"
        ).pack(fill="x", padx=5, pady=5)

        # === Botao Salvar ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Salvar Configuracoes",
            command=self._save
        )
        self.save_btn.pack(side="right")

        self.status_label = ctk.CTkLabel(btn_frame, text="", text_color="green")
        self.status_label.pack(side="left", padx=10)

    def _toggle_api_visibility(self):
        """Mostra/esconde API key"""
        if self.show_api_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")

    def _update_slippage_label(self, value):
        """Atualiza label do slippage"""
        self.slippage_label.configure(text=f"{int(value)}%")

    def _load_values(self):
        """Carrega valores das settings"""
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, self.settings.api_key)

        self.buy_amount_entry.delete(0, "end")
        self.buy_amount_entry.insert(0, str(self.settings.buy_amount))

        self.slippage_slider.set(self.settings.slippage)
        self.slippage_label.configure(text=f"{self.settings.slippage}%")

        self.priority_fee_entry.delete(0, "end")
        self.priority_fee_entry.insert(0, str(self.settings.priority_fee))

        self.attempts_entry.delete(0, "end")
        self.attempts_entry.insert(0, str(self.settings.num_attempts))

        self.delay_entry.delete(0, "end")
        self.delay_entry.insert(0, str(self.settings.delay_between))

    def _save(self):
        """Salva configuracoes"""
        try:
            self.settings.api_key = self.api_key_entry.get()
            self.settings.buy_amount = float(self.buy_amount_entry.get())
            self.settings.slippage = int(self.slippage_slider.get())
            self.settings.priority_fee = float(self.priority_fee_entry.get())
            self.settings.num_attempts = int(self.attempts_entry.get())
            self.settings.delay_between = float(self.delay_entry.get())

            self.settings.save()

            self.status_label.configure(text="Salvo!", text_color="green")
            self.after(2000, lambda: self.status_label.configure(text=""))

            if self.on_save:
                self.on_save()

        except ValueError as e:
            self.status_label.configure(text=f"Erro: valor invalido", text_color="red")

    def get_settings(self) -> Settings:
        """Retorna settings atuais"""
        return self.settings
