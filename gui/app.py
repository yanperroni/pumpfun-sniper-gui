"""
Aplicacao principal com abas
"""
import customtkinter as ctk
from typing import Optional

from config.settings import Settings, get_settings
from .settings_tab import SettingsTab
from .coordinates_tab import CoordinatesTab
from .monitor_tab import MonitorTab


class App(ctk.CTk):
    """Janela principal da aplicacao"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__()

        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Carregar settings
        self.settings = settings or get_settings()

        # Configurar janela
        self.title("PumpFun Visual Sniper")
        self.geometry("550x680")
        self.minsize(500, 600)

        # Centralizar
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 550) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self):
        """Cria widgets"""
        # Header
        header = ctk.CTkFrame(self, height=50)
        header.pack(fill="x", padx=10, pady=5)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="PumpFun Visual Sniper",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", padx=10, pady=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        # Adicionar abas
        self.tabview.add("Monitor")
        self.tabview.add("Configuracoes")
        self.tabview.add("Coordenadas")

        # Criar conteudo das abas
        self.monitor_tab = MonitorTab(
            self.tabview.tab("Monitor"),
            self.settings
        )
        self.monitor_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(
            self.tabview.tab("Configuracoes"),
            self.settings,
            on_save=self._on_settings_saved
        )
        self.settings_tab.pack(fill="both", expand=True)

        self.coordinates_tab = CoordinatesTab(
            self.tabview.tab("Coordenadas"),
            self.settings,
            on_save=self._on_settings_saved
        )
        self.coordinates_tab.pack(fill="both", expand=True)

        # Footer
        footer = ctk.CTkFrame(self, height=30, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=5)

        version = ctk.CTkLabel(
            footer,
            text="v1.0.0",
            text_color="gray"
        )
        version.pack(side="right", padx=10)

    def _on_settings_saved(self):
        """Callback quando settings sao salvas"""
        # Recarregar settings no monitor
        self.monitor_tab.settings = self.settings

    def run(self):
        """Executa a aplicacao"""
        self.mainloop()
