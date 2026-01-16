"""
Motor de OCR usando Tesseract
"""
import re
import subprocess
import numpy as np
import cv2
from typing import Optional, List

# Regex para CA Solana
CA_PATTERN = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')


class OCREngine:
    """Motor de OCR para extrair texto de screenshots"""

    def __init__(self, tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        self.tesseract_path = tesseract_path
        self._pytesseract = None

    def _get_pytesseract(self):
        """Inicializa pytesseract com caminho correto"""
        if self._pytesseract is None:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            self._pytesseract = pytesseract
        return self._pytesseract

    def extract_text(self, img: np.ndarray, crop_top_only: bool = True) -> str:
        """Extrai texto da imagem usando OCR"""
        if img is None:
            return ""

        try:
            # Cortar so a parte de cima onde aparece a notificacao (mais rapido)
            if crop_top_only:
                height = img.shape[0]
                img = img[0:int(height * 0.35), :]

            # Converter para grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Threshold para melhor OCR
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            # OCR
            pytesseract = self._get_pytesseract()
            text = pytesseract.image_to_string(thresh, config='--psm 6 --oem 3')
            return text

        except Exception as e:
            print(f"[OCR ERRO] {e}")
            return ""

    def find_callout(self, text: str, keywords: List[str]) -> bool:
        """Verifica se ha callout no texto"""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def extract_ca(self, text: str) -> Optional[str]:
        """Extrai Contract Address do texto"""
        matches = CA_PATTERN.findall(text)

        # Priorizar CAs que terminam em 'pump'
        pump_cas = [m for m in matches if m.lower().endswith('pump') and 32 <= len(m) <= 44]
        if pump_cas:
            return pump_cas[0]

        # Qualquer CA valido
        for match in matches:
            if 32 <= len(match) <= 44:
                lower_match = match.lower()
                if not any(word in lower_match for word in ['view', 'coin', 'token', 'http', 'https', 'android']):
                    return match

        return None

    @staticmethod
    def get_windows_clipboard() -> str:
        """Le clipboard do Windows"""
        try:
            result = subprocess.run(
                ["powershell", "-command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"[CLIPBOARD ERRO] {e}")
            return ""

    def is_tesseract_installed(self) -> bool:
        """Verifica se Tesseract esta instalado"""
        import os
        return os.path.exists(self.tesseract_path)
