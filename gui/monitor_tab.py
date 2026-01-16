"""
Aba de monitoramento do bot
"""
import customtkinter as ctk
import asyncio
import threading
from typing import Optional
from datetime import datetime

from config.settings import Settings
from core.sniper import Sniper, SniperState


class MonitorTab(ctk.CTkFrame):
    """Aba de monitoramento e controle do bot"""

    def __init__(self, parent, settings: Settings):
        super().__init__(parent)

        self.settings = settings
        self.sniper: Optional[Sniper] = None
        self.sniper_thread: Optional[threading.Thread] = None
        self.buy_count = 0
        self.last_ca = ""

        self._create_widgets()

    def _create_widgets(self):
        """Cria widgets"""
        # Titulo
        title = ctk.CTkLabel(
            self,
            text="Monitor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=10)

        # Status Frame
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=10, pady=5)

        # Status
        status_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(status_row, text="Status:", width=100, anchor="w").pack(side="left")
        self.status_label = ctk.CTkLabel(
            status_row,
            text="PARADO",
            font=ctk.CTkFont(weight="bold"),
            text_color="gray"
        )
        self.status_label.pack(side="left")

        # Pixel monitorado
        pixel_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        pixel_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(pixel_row, text="Pixel base:", width=100, anchor="w").pack(side="left")
        self.pixel_label = ctk.CTkLabel(pixel_row, text="-", text_color="gray")
        self.pixel_label.pack(side="left")

        # Ultimo CA
        ca_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        ca_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(ca_row, text="Ultimo CA:", width=100, anchor="w").pack(side="left")
        self.ca_label = ctk.CTkLabel(ca_row, text="-", text_color="gray")
        self.ca_label.pack(side="left")

        # Compras
        buy_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        buy_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(buy_row, text="Compras:", width=100, anchor="w").pack(side="left")
        self.buy_label = ctk.CTkLabel(buy_row, text="0", font=ctk.CTkFont(weight="bold"))
        self.buy_label.pack(side="left")

        # Botoes de controle
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="INICIAR",
            command=self._start_sniper,
            fg_color="green",
            hover_color="darkgreen",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="PARAR",
            command=self._stop_sniper,
            fg_color="red",
            hover_color="darkred",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

        # Log Frame
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(log_frame, text="Log:", anchor="w").pack(fill="x", padx=5, pady=2)

        self.log_text = ctk.CTkTextbox(log_frame, height=200)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

        # Botao limpar log
        clear_btn = ctk.CTkButton(
            log_frame,
            text="Limpar Log",
            command=self._clear_log,
            width=100
        )
        clear_btn.pack(anchor="e", padx=5, pady=5)

    def _log(self, msg: str):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        """Limpa o log"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _update_status(self, state: SniperState):
        """Atualiza status visual"""
        status_map = {
            SniperState.STOPPED: ("PARADO", "gray"),
            SniperState.MONITORING: ("MONITORANDO PIXEL...", "green"),
            SniperState.CLICKING_VIEW_COIN: ("CLICANDO VIEW COIN", "orange"),
            SniperState.WAITING_CHART: ("AGUARDANDO GRAFICO", "orange"),
            SniperState.COPYING_CA: ("COPIANDO CA", "orange"),
            SniperState.BUYING: ("COMPRANDO!", "blue"),
        }
        text, color = status_map.get(state, ("DESCONHECIDO", "gray"))
        self.status_label.configure(text=text, text_color=color)

    def _on_ca_found(self, ca: str):
        """Callback quando CA eh encontrado"""
        self.last_ca = ca
        display = ca[:16] + "..." + ca[-8:] if len(ca) > 24 else ca
        self.ca_label.configure(text=display, text_color="green")

    def _on_buy_result(self, result):
        """Callback quando compra eh feita"""
        if result.success:
            self.buy_count += 1
            self.buy_label.configure(text=str(self.buy_count))

    def _start_sniper(self):
        """Inicia o sniper"""
        # Recarregar settings
        self.settings = Settings.load()

        # Verificar API key
        if not self.settings.api_key:
            self._log("ERRO: API Key nao configurada!")
            return

        # Criar sniper
        self.sniper = Sniper(
            api_key=self.settings.api_key,
            buy_amount=self.settings.buy_amount,
            slippage=self.settings.slippage,
            priority_fee=self.settings.priority_fee,
            num_attempts=self.settings.num_attempts,
            delay_between=self.settings.delay_between,
            view_coin_x=self.settings.view_coin_x,
            view_coin_y=self.settings.view_coin_y,
            ca_area_x=self.settings.ca_area_x,
            ca_area_y=self.settings.ca_area_y
        )

        # Callbacks
        self.sniper.on_log = lambda msg: self.after(0, lambda: self._log(msg))
        self.sniper.on_state_change = lambda state: self.after(0, lambda: self._update_status(state))
        self.sniper.on_ca_found = lambda ca: self.after(0, lambda: self._on_ca_found(ca))
        self.sniper.on_buy_result = lambda r: self.after(0, lambda: self._on_buy_result(r))

        # Atualizar UI
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Mostrar pixel que sera monitorado
        self.pixel_label.configure(
            text=f"({self.settings.view_coin_x}, {self.settings.view_coin_y})",
            text_color="green"
        )

        # Iniciar em thread separada
        def run_sniper():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.sniper.run())
            finally:
                loop.close()

        self.sniper_thread = threading.Thread(target=run_sniper, daemon=True)
        self.sniper_thread.start()

    def _stop_sniper(self):
        """Para o sniper"""
        if self.sniper:
            self.sniper.stop()

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._update_status(SniperState.STOPPED)

    def on_tab_selected(self):
        """Chamado quando a aba eh selecionada"""
        self.settings = Settings.load()
