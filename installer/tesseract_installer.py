"""
Baixa e instala Tesseract OCR automaticamente
"""
import os
import subprocess
import tempfile
import threading
from typing import Callable, Optional
import requests


class TesseractInstaller:
    """Baixa e instala Tesseract OCR"""

    # URL do instalador
    DOWNLOAD_URL = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
    FILENAME = "tesseract-ocr-w64-setup-5.4.0.20240606.exe"
    EXPECTED_SIZE = 50331648  # ~48MB aproximado

    def __init__(self):
        self.download_progress: float = 0.0
        self.status: str = ""
        self.is_downloading: bool = False
        self.is_installing: bool = False
        self._cancel_flag: bool = False

    def download(
        self,
        dest_dir: Optional[str] = None,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> Optional[str]:
        """
        Baixa o instalador do Tesseract

        Args:
            dest_dir: Diretorio de destino (default: temp)
            on_progress: Callback(progress: 0-100, status: str)

        Returns:
            Caminho do arquivo baixado ou None se falhou
        """
        if dest_dir is None:
            dest_dir = tempfile.gettempdir()

        dest_path = os.path.join(dest_dir, self.FILENAME)

        self.is_downloading = True
        self._cancel_flag = False

        def update_status(progress: float, status: str):
            self.download_progress = progress
            self.status = status
            if on_progress:
                on_progress(progress, status)

        try:
            update_status(0, "Conectando ao GitHub...")

            response = requests.get(self.DOWNLOAD_URL, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                total_size = self.EXPECTED_SIZE

            update_status(0, f"Baixando Tesseract ({total_size / 1024 / 1024:.1f} MB)...")

            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancel_flag:
                        update_status(0, "Download cancelado")
                        return None

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        update_status(progress, f"Baixando... {downloaded / 1024 / 1024:.1f} MB")

            update_status(100, "Download concluido!")
            self.is_downloading = False
            return dest_path

        except Exception as e:
            update_status(0, f"Erro no download: {e}")
            self.is_downloading = False
            return None

    def install(
        self,
        installer_path: str,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Executa instalacao silenciosa do Tesseract

        Args:
            installer_path: Caminho do instalador .exe
            on_progress: Callback(progress: 0-100, status: str)

        Returns:
            True se instalou com sucesso
        """
        if not os.path.exists(installer_path):
            if on_progress:
                on_progress(0, "Arquivo instalador nao encontrado")
            return False

        self.is_installing = True

        def update_status(progress: float, status: str):
            self.status = status
            if on_progress:
                on_progress(progress, status)

        try:
            update_status(50, "Instalando Tesseract (pode demorar)...")

            # Instalacao silenciosa
            # /S = Silent, /D = Diretorio de instalacao
            result = subprocess.run(
                [installer_path, "/S"],
                capture_output=True,
                timeout=300  # 5 minutos timeout
            )

            if result.returncode == 0:
                update_status(100, "Tesseract instalado com sucesso!")
                self.is_installing = False
                return True
            else:
                update_status(0, f"Erro na instalacao (codigo {result.returncode})")
                self.is_installing = False
                return False

        except subprocess.TimeoutExpired:
            update_status(0, "Instalacao demorou demais (timeout)")
            self.is_installing = False
            return False
        except Exception as e:
            update_status(0, f"Erro na instalacao: {e}")
            self.is_installing = False
            return False

    def download_and_install(
        self,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Baixa e instala Tesseract em uma operacao

        Args:
            on_progress: Callback(progress: 0-100, status: str)

        Returns:
            True se instalou com sucesso
        """
        # Ajustar progresso para considerar download (0-50) e install (50-100)
        def download_progress(progress: float, status: str):
            if on_progress:
                on_progress(progress / 2, status)

        def install_progress(progress: float, status: str):
            if on_progress:
                on_progress(50 + progress / 2, status)

        # Download
        installer_path = self.download(on_progress=download_progress)
        if not installer_path:
            return False

        # Install
        success = self.install(installer_path, on_progress=install_progress)

        # Limpar arquivo temporario
        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
        except:
            pass

        return success

    def download_and_install_async(
        self,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[bool], None]] = None
    ):
        """
        Baixa e instala em thread separada

        Args:
            on_progress: Callback(progress: 0-100, status: str)
            on_complete: Callback(success: bool)
        """
        def worker():
            success = self.download_and_install(on_progress)
            if on_complete:
                on_complete(success)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def cancel(self):
        """Cancela download em andamento"""
        self._cancel_flag = True
