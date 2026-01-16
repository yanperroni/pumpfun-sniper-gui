"""
Verifica dependencias instaladas
"""
import os
import subprocess
from typing import Dict, Optional


class DependencyChecker:
    """Verifica se as dependencias estao instaladas"""

    # Caminhos comuns do Tesseract
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]

    def __init__(self):
        self.tesseract_path: Optional[str] = None

    def find_tesseract(self) -> Optional[str]:
        """Encontra Tesseract instalado"""
        for path in self.TESSERACT_PATHS:
            if os.path.exists(path):
                self.tesseract_path = path
                return path

        # Tentar no PATH
        try:
            result = subprocess.run(
                ["where", "tesseract"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                if os.path.exists(path):
                    self.tesseract_path = path
                    return path
        except:
            pass

        return None

    def is_tesseract_installed(self) -> bool:
        """Verifica se Tesseract esta instalado"""
        return self.find_tesseract() is not None

    def check_all(self) -> Dict[str, bool]:
        """Verifica todas as dependencias"""
        return {
            "tesseract": self.is_tesseract_installed()
        }

    def get_missing(self) -> list:
        """Retorna lista de dependencias faltando"""
        missing = []
        if not self.is_tesseract_installed():
            missing.append("tesseract")
        return missing

    def get_paths(self) -> Dict[str, Optional[str]]:
        """Retorna caminhos encontrados"""
        self.find_tesseract()
        return {
            "tesseract": self.tesseract_path
        }
