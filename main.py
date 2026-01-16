"""
PumpFun Visual Sniper - Entry Point
Verifica dependencias e inicia a aplicacao GUI
"""
import sys
import os

# Adicionar diretorio ao path
if getattr(sys, 'frozen', False):
    # Rodando como exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)


def check_and_install_dependencies():
    """Verifica e instala dependencias Python se necessario"""
    required = [
        'customtkinter',
        'PIL',
        'cv2',
        'numpy',
        'pytesseract',
        'aiohttp',
        'requests'
    ]

    missing = []
    for module in required:
        try:
            if module == 'PIL':
                __import__('PIL')
            elif module == 'cv2':
                __import__('cv2')
            else:
                __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print(f"Modulos faltando: {missing}")
        print("Execute: pip install customtkinter pillow opencv-python numpy pytesseract aiohttp requests")
        return False

    return True


def main():
    """Funcao principal"""
    # Verificar dependencias Python
    if not check_and_install_dependencies():
        input("Pressione Enter para sair...")
        sys.exit(1)

    # Importar modulos apos verificacao
    from installer.dependency_checker import DependencyChecker
    from config.settings import Settings, get_settings

    # Verificar dependencias do sistema
    checker = DependencyChecker()
    paths = checker.get_paths()

    # Carregar ou criar settings
    settings = get_settings()

    # Atualizar path do Tesseract se encontrado
    if paths["tesseract"] and not settings.tesseract_path:
        settings.tesseract_path = paths["tesseract"]

    settings.save()

    # Verificar se Tesseract esta instalado
    if not checker.is_tesseract_installed():
        print("Tesseract OCR nao encontrado!")
        print("O wizard de instalacao sera aberto...")

        import customtkinter as ctk
        from gui.setup_wizard import SetupWizard

        # Criar janela root temporaria
        root = ctk.CTk()
        root.withdraw()

        def on_wizard_complete(result):
            if "tesseract_path" in result:
                settings.tesseract_path = result["tesseract_path"]
            settings.save()
            root.destroy()

        wizard = SetupWizard(root, on_wizard_complete)
        root.wait_window(wizard)

        # Recarregar settings
        settings = get_settings()

    # Iniciar aplicacao principal
    from gui.app import App

    app = App(settings)
    app.run()


if __name__ == "__main__":
    main()
