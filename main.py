"""
PumpFun Visual Sniper - Entry Point
Check dependencies and start GUI application
"""
import sys
import os

# Add directory to path
if getattr(sys, 'frozen', False):
    # Running as exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)


def check_and_install_dependencies():
    """Check and install Python dependencies if needed"""
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
        print(f"Missing modules: {missing}")
        print("Run: pip install customtkinter pillow opencv-python numpy pytesseract aiohttp requests")
        return False

    return True


def main():
    """Main function"""
    # Check Python dependencies
    if not check_and_install_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)

    # Import modules after check
    from installer.dependency_checker import DependencyChecker
    from config.settings import Settings, get_settings

    # Check system dependencies
    checker = DependencyChecker()
    paths = checker.get_paths()

    # Load or create settings
    settings = get_settings()

    # Update Tesseract path if found
    if paths["tesseract"] and not settings.tesseract_path:
        settings.tesseract_path = paths["tesseract"]

    settings.save()

    # Check if Tesseract is installed
    if not checker.is_tesseract_installed():
        print("Tesseract OCR not found!")
        print("Setup wizard will open...")

        import customtkinter as ctk
        from gui.setup_wizard import SetupWizard

        # Create temporary root window
        root = ctk.CTk()
        root.withdraw()

        def on_wizard_complete(result):
            if "tesseract_path" in result:
                settings.tesseract_path = result["tesseract_path"]
            settings.save()
            root.destroy()

        wizard = SetupWizard(root, on_wizard_complete)
        root.wait_window(wizard)

        # Reload settings
        settings = get_settings()

    # Start main application
    from gui.app import App

    app = App(settings)
    app.run()


if __name__ == "__main__":
    main()
