"""
Initial setup wizard
"""
import customtkinter as ctk
import threading
from typing import Callable, Optional

from installer.dependency_checker import DependencyChecker
from installer.tesseract_installer import TesseractInstaller


class SetupWizard(ctk.CTkToplevel):
    """Wizard to configure dependencies on first run"""

    def __init__(self, parent, on_complete: Callable[[dict], None]):
        super().__init__(parent)

        self.on_complete = on_complete
        self.checker = DependencyChecker()
        self.tesseract_installer = TesseractInstaller()
        self.result = {}

        self.title("PumpFun Sniper - Setup")
        self.geometry("500x300")
        self.resizable(False, False)

        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"+{x}+{y}")

        # Prevent closing
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.grab_set()

        self._create_widgets()
        self._check_dependencies()

    def _create_widgets(self):
        """Create widgets"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Initial Setup",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # Status frame
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
            text="Checking...",
            text_color="gray"
        )
        self.tesseract_status.pack(side="left", padx=5)

        self.tesseract_btn = ctk.CTkButton(
            self.tesseract_frame,
            text="Install",
            width=80,
            state="disabled",
            command=self._install_tesseract
        )
        self.tesseract_btn.pack(side="right", padx=5)

        # Progress bar
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

        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=20)

        self.continue_btn = ctk.CTkButton(
            self.btn_frame,
            text="Continue",
            state="disabled",
            command=self._on_continue
        )
        self.continue_btn.pack(side="right", padx=5)

    def _check_dependencies(self):
        """Check dependencies"""
        def check():
            # Check Tesseract
            tesseract_path = self.checker.find_tesseract()
            if tesseract_path:
                self.after(0, lambda: self._update_tesseract_status(True, tesseract_path))
            else:
                self.after(0, lambda: self._update_tesseract_status(False, None))

            # Check if can continue
            self.after(0, self._check_can_continue)

        threading.Thread(target=check, daemon=True).start()

    def _update_tesseract_status(self, installed: bool, path: Optional[str]):
        """Update Tesseract status"""
        if installed:
            self.tesseract_status.configure(text="Installed", text_color="green")
            self.tesseract_btn.configure(state="disabled")
            self.result["tesseract_path"] = path
        else:
            self.tesseract_status.configure(text="Not found", text_color="red")
            self.tesseract_btn.configure(state="normal")

    def _check_can_continue(self):
        """Check if can continue"""
        tesseract_ok = "tesseract_path" in self.result
        if tesseract_ok:
            self.continue_btn.configure(state="normal")

    def _install_tesseract(self):
        """Install Tesseract"""
        self.tesseract_btn.configure(state="disabled")
        self.progress_label.configure(text="Downloading Tesseract...")

        def on_progress(progress: float, status: str):
            self.after(0, lambda: self.progress_bar.set(progress / 100))
            self.after(0, lambda: self.progress_label.configure(text=status))

        def on_complete(success: bool):
            if success:
                self.after(0, lambda: self._update_tesseract_status(
                    True,
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                ))
                self.after(0, lambda: self.progress_label.configure(text="Tesseract installed!"))
            else:
                self.after(0, lambda: self.tesseract_btn.configure(state="normal"))
                self.after(0, lambda: self.progress_label.configure(text="Installation failed"))

            self.after(0, self._check_can_continue)

        self.tesseract_installer.download_and_install_async(on_progress, on_complete)

    def _on_continue(self):
        """Continue to main app"""
        self.grab_release()
        self.destroy()
        self.on_complete(self.result)
