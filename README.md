# PumpFun Visual Sniper

A Windows-based automated trading bot with GUI for sniping new token launches on **PumpFun** (Solana blockchain).

## Features

- **Pixel Detection**: Monitors a specific pixel on screen for color changes indicating new token notifications
- **Automated Clicking**: Simulates mouse clicks via Windows API to interact with the PumpFun interface
- **Contract Address Extraction**: Automatically copies and validates Solana contract addresses from clipboard
- **PumpPortal API Integration**: Executes buy orders with configurable parameters
- **Modern GUI**: CustomTkinter interface with 3 tabs (Monitor, Settings, Coordinates)
- **Crosshair Overlay**: Visual coordinate calibration system for precise click positioning
- **Auto-Install Dependencies**: Automatically downloads and installs Tesseract OCR if missing

## Requirements

- Windows 10/11
- Python 3.8+ (if running from source)
- PumpPortal API key

## Installation

### Option 1: Run from Source

1. Clone the repository:
```bash
git clone https://github.com/yanperroni/pumpfun-sniper-gui.git
cd pumpfun-sniper-gui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Option 2: Build Executable

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
build.bat
```

3. Find the executable in the `dist/` folder

## Configuration

### 1. API Key
Enter your PumpPortal API key in the **Settings** tab.
Set up your wallet here: https://pumpportal.fun/trading-api/setup

### 2. Buy Parameters
- **Amount (SOL)**: Amount of SOL per buy order
- **Slippage (%)**: Price slippage tolerance
- **Priority Fee**: Network priority fee in SOL
- **Attempts**: Number of buy retries per token
- **Delay**: Delay between retry attempts

### 3. Coordinates Calibration
In the **Coordinates** tab:
1. Click "Select on Screen" for **View Coin** button
2. Click on the View Coin button location in your PumpFun interface
3. Repeat for **Contract Address** area
4. Use "Test Click" to verify positions
5. Save coordinates

## How It Works

```
1. Monitor pixel color at View Coin button location (20 scans/sec)
2. When color changes → New token detected
3. Wait 0.4s → Click View Coin button
4. Wait 2.5s → Chart loads
5. Click CA area 3x → Copy contract address to clipboard
6. Validate CA (Solana address format)
7. Execute buy orders via PumpPortal API
8. Return to monitoring
```

## Project Structure

```
pumpfun-sniper-gui/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── build.bat              # Build script
├── config/
│   └── settings.py        # Settings management (JSON)
├── core/
│   ├── sniper.py          # Main sniper logic
│   ├── api.py             # PumpPortal API client
│   └── ocr.py             # OCR engine (Tesseract)
├── gui/
│   ├── app.py             # Main application window
│   ├── monitor_tab.py     # Monitoring & control tab
│   ├── settings_tab.py    # Configuration tab
│   ├── coordinates_tab.py # Coordinate calibration
│   └── setup_wizard.py    # First-run setup
└── installer/
    ├── dependency_checker.py   # System dependency detection
    └── tesseract_installer.py  # Tesseract auto-installer
```

## Technologies

- **GUI**: CustomTkinter, Tkinter
- **Screen Capture**: PIL/Pillow
- **Mouse Simulation**: ctypes (Windows API)
- **Clipboard**: PowerShell
- **HTTP Client**: aiohttp
- **OCR**: Tesseract (optional)

## Disclaimer

This software is provided for educational purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk. The authors are not responsible for any financial losses incurred while using this software.

## License

MIT License
