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
        self.geometry("500x250")
        self.resizable(False, False)

        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 250) // 2
        self.geometry(f"+{x}+{y}")

        # Prevent closing
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.grab_set()

        self._create_widgets()

        # Check dependencies after window is shown
        self.after(100, self._check_dependencies)

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
        self.btn_frame.pack(fill="x", padx=20, pady=15)

        self.continue_btn = ctk.CTkButton(
            self.btn_frame,
            text="Continue",
            state="disabled",
            command=self._on_continue
        )
        self.continue_btn.pack(side="right", padx=5)

    def _check_dependencies(self):
        """Check dependencies in background thread"""
        def check():
            try:
                # Check Tesseract
                tesseract_path = self.checker.find_tesseract()

                # Update UI from main thread
                self.after(0, lambda: self._on_check_complete(tesseract_path))
            except Exception as e:
                print(f"Error checking dependencies: {e}")
                self.after(0, lambda: self._on_check_complete(None))

        threading.Thread(target=check, daemon=True).start()

    def _on_check_complete(self, tesseract_path: Optional[str]):
        """Called when dependency check is complete"""
        if tesseract_path:
            self.tesseract_status.configure(text="Installed", text_color="green")
            self.tesseract_btn.configure(state="disabled")
            self.result["tesseract_path"] = tesseract_path
            self.continue_btn.configure(state="normal")
        else:
            self.tesseract_status.configure(text="Not found", text_color="red")
            self.tesseract_btn.configure(state="normal")

    def _install_tesseract(self):
        """Install Tesseract"""
        self.tesseract_btn.configure(state="disabled")
        self.tesseract_status.configure(text="Installing...", text_color="orange")
        self.progress_label.configure(text="Connecting to GitHub...")

        def on_progress(progress: float, status: str):
            self.after(0, lambda p=progress, s=status: self._update_progress(p, s))

        def on_complete(success: bool):
            self.after(0, lambda: self._on_install_complete(success))

        self.tesseract_installer.download_and_install_async(on_progress, on_complete)

    def _update_progress(self, progress: float, status: str):
        """Update progress bar and label"""
        self.progress_bar.set(progress / 100)
        self.progress_label.configure(text=status)

    def _on_install_complete(self, success: bool):
        """Called when installation is complete"""
        if success:
            self.tesseract_status.configure(text="Installed", text_color="green")
            self.tesseract_btn.configure(state="disabled")
            self.progress_label.configure(text="Tesseract installed successfully!")
            self.result["tesseract_path"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            self.continue_btn.configure(state="normal")
        else:
            self.tesseract_status.configure(text="Failed", text_color="red")
            self.tesseract_btn.configure(state="normal")
            self.progress_label.configure(text="Installation failed. Try again.")

    def _on_continue(self):
        """Continue to main app"""
        self.grab_release()
        self.destroy()
        self.on_complete(self.result)
