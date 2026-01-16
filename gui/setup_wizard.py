"""
Wizard de configuracao inicial
"""
import customtkinter as ctk
import threading
from typing import Callable, Optional

from installer.dependency_checker import DependencyChecker
from installer.tesseract_installer import TesseractInstaller


class SetupWizard(ctk.CTkToplevel):
    """Wizard para configurar dependencias na primeira execucao"""

    def __init__(self, parent, on_complete: Callable[[dict], None]):
        super().__init__(parent)

        self.on_complete = on_complete
        self.checker = DependencyChecker()
        self.tesseract_installer = TesseractInstaller()
        self.result = {}

        self.title("PumpFun Sniper - Setup")
        self.geometry("500x300")
        self.resizable(False, False)

        # Centralizar
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"+{x}+{y}")

        # Impedir fechar
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.grab_set()

        self._create_widgets()
        self._check_dependencies()

    def _create_widgets(self):
        """Cria widgets"""
        # Titulo
        self.title_label = ctk.CTkLabel(
            self,
            text="Configuracao Inicial",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # Frame de status
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=20, pady=10)

        # Tesseract
        self.tesseract_frame = ctk.CTkFrame(self.status_frame)
        self.tesseract_frame.pack(fill="x", padx=10, pady=5)

        self.tesseract_label = ctk.CTkLabel(
            self.tesseract_frame,
            text="Tesseract OCR:",
            width=120,
            anchor="w"
        )
        self.tesseract_label.pack(side="left", padx=5)

        self.tesseract_status = ctk.CTkLabel(
            self.tesseract_frame,
            text="Verificando...",
            text_color="gray"
        )
        self.tesseract_status.pack(side="left", padx=5)

        self.tesseract_btn = ctk.CTkButton(
            self.tesseract_frame,
            text="Instalar",
            width=80,
            state="disabled",
            command=self._install_tesseract
        )
        self.tesseract_btn.pack(side="right", padx=5)

        # Barra de progresso
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="x", padx=20, pady=10)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            text_color="gray"
        )
        self.progress_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # Botoes
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=20)

        self.continue_btn = ctk.CTkButton(
            self.btn_frame,
            text="Continuar",
            state="disabled",
            command=self._on_continue
        )
        self.continue_btn.pack(side="right", padx=5)

    def _check_dependencies(self):
        """Verifica dependencias"""
        def check():
            # Verificar Tesseract
            tesseract_path = self.checker.find_tesseract()
            if tesseract_path:
                self.after(0, lambda: self._update_tesseract_status(True, tesseract_path))
            else:
                self.after(0, lambda: self._update_tesseract_status(False, None))

            # Verificar se pode continuar
            self.after(0, self._check_can_continue)

        threading.Thread(target=check, daemon=True).start()

    def _update_tesseract_status(self, installed: bool, path: Optional[str]):
        """Atualiza status do Tesseract"""
        if installed:
            self.tesseract_status.configure(text="Instalado", text_color="green")
            self.tesseract_btn.configure(state="disabled")
            self.result["tesseract_path"] = path
        else:
            self.tesseract_status.configure(text="Nao encontrado", text_color="red")
            self.tesseract_btn.configure(state="normal")

    def _check_can_continue(self):
        """Verifica se pode continuar"""
        tesseract_ok = "tesseract_path" in self.result
        if tesseract_ok:
            self.continue_btn.configure(state="normal")

    def _install_tesseract(self):
        """Instala Tesseract"""
        self.tesseract_btn.configure(state="disabled")
        self.progress_label.configure(text="Baixando Tesseract...")

        def on_progress(progress: float, status: str):
            self.after(0, lambda: self.progress_bar.set(progress / 100))
            self.after(0, lambda: self.progress_label.configure(text=status))

        def on_complete(success: bool):
            if success:
                self.after(0, lambda: self._update_tesseract_status(
                    True,
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                ))
                self.after(0, lambda: self.progress_label.configure(text="Tesseract instalado!"))
            else:
                self.after(0, lambda: self.tesseract_btn.configure(state="normal"))
                self.after(0, lambda: self.progress_label.configure(text="Falha na instalacao"))

            self.after(0, self._check_can_continue)

        self.tesseract_installer.download_and_install_async(on_progress, on_complete)

    def _on_continue(self):
        """Continua para app principal"""
        self.grab_release()
        self.destroy()
        self.on_complete(self.result)
