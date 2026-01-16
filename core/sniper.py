"""
Pixel-based sniper
Monitors pixel color change on View Coin and executes buys
"""
import asyncio
import time
import re
import ctypes
from ctypes import wintypes
from typing import Optional, Callable, Tuple
from enum import Enum, auto
from PIL import ImageGrab
import subprocess

from .api import PumpPortalAPI, BuyResult


# Solana CA regex
CA_PATTERN = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')


class SniperState(Enum):
    """Sniper states"""
    STOPPED = auto()
    MONITORING = auto()
    CLICKING_VIEW_COIN = auto()
    WAITING_CHART = auto()
    COPYING_CA = auto()
    BUYING = auto()


def get_pixel_color(x: int, y: int) -> Tuple[int, int, int]:
    """Capture pixel color on screen"""
    # Capture 1x1 pixel area
    img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    return img.getpixel((0, 0))


def colors_different(c1: Tuple[int, int, int], c2: Tuple[int, int, int], tolerance: int = 10) -> bool:
    """Check if two colors are different (with tolerance)"""
    diff = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])
    return diff > tolerance


def windows_click(x: int, y: int):
    """Simulate mouse click on Windows"""
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.02)

    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def get_clipboard() -> str:
    """Read Windows clipboard"""
    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip()
    except:
        return ""


def clear_clipboard():
    """Clear clipboard"""
    try:
        subprocess.run(
            ["powershell", "-command", "Set-Clipboard -Value $null"],
            capture_output=True,
            timeout=2
        )
    except:
        pass


class Sniper:
    """Pixel detection based sniper"""

    def __init__(
        self,
        api_key: str,
        buy_amount: float = 5.0,
        slippage: int = 49,
        priority_fee: float = 0.12,
        num_attempts: int = 5,
        delay_between: float = 0.5,
        view_coin_x: int = 764,
        view_coin_y: int = 344,
        ca_area_x: int = 440,
        ca_area_y: int = 198,
        **kwargs  # Ignore other parameters
    ):
        # Buy config
        self.api_key = api_key
        self.buy_amount = buy_amount
        self.slippage = slippage
        self.priority_fee = priority_fee
        self.num_attempts = num_attempts
        self.delay_between = delay_between

        # Coordinates
        self.view_coin_x = view_coin_x
        self.view_coin_y = view_coin_y
        self.ca_area_x = ca_area_x
        self.ca_area_y = ca_area_y

        # API
        self.api = PumpPortalAPI(api_key)

        # State
        self.state = SniperState.STOPPED
        self.bought_tokens: set = set()
        self._running = False
        self.base_pixel_color: Optional[Tuple[int, int, int]] = None

        # Callbacks
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_state_change: Optional[Callable[[SniperState], None]] = None
        self.on_ca_found: Optional[Callable[[str], None]] = None
        self.on_buy_result: Optional[Callable[[BuyResult], None]] = None

    def log(self, msg: str):
        """Emit log"""
        print(msg)
        if self.on_log:
            self.on_log(msg)

    def set_state(self, state: SniperState):
        """Change state"""
        self.state = state
        if self.on_state_change:
            self.on_state_change(state)

    async def buy_token(self, mint: str):
        """Execute buys"""
        if mint in self.bought_tokens:
            self.log(f"[SKIP] Token already bought: {mint}")
            return

        self.bought_tokens.add(mint)
        self.set_state(SniperState.BUYING)

        self.log("=" * 50)
        self.log(f"CA DETECTED: {mint}")
        self.log(f"BUYING: {self.num_attempts}x {self.buy_amount} SOL")
        self.log("=" * 50)

        if self.on_ca_found:
            self.on_ca_found(mint)

        results = await self.api.buy_multiple(
            mint=mint,
            amount=self.buy_amount,
            slippage=self.slippage,
            priority_fee=self.priority_fee,
            num_attempts=self.num_attempts,
            delay_between=self.delay_between,
            on_result=self._on_buy_result
        )

        self.log("=" * 50)
        self.log("BUYS COMPLETED")
        self.log("=" * 50)

        return results

    def _on_buy_result(self, result: BuyResult):
        """Buy result callback"""
        if result.success:
            self.log(f"[{result.attempt}/{self.num_attempts}] OK - TX: {result.signature[:20]}...")
        else:
            self.log(f"[{result.attempt}/{self.num_attempts}] ERROR: {result.error}")

        if self.on_buy_result:
            self.on_buy_result(result)

    async def run(self):
        """Main loop"""
        self._running = True
        self.set_state(SniperState.MONITORING)

        # Capture base pixel color
        self.base_pixel_color = get_pixel_color(self.view_coin_x, self.view_coin_y)

        self.log("=" * 50)
        self.log("SNIPER STARTED")
        self.log(f"View Coin: ({self.view_coin_x}, {self.view_coin_y})")
        self.log(f"CA Area: ({self.ca_area_x}, {self.ca_area_y})")
        self.log(f"Base pixel: RGB{self.base_pixel_color}")
        self.log(f"Config: {self.num_attempts}x {self.buy_amount} SOL")
        self.log("=" * 50)
        self.log("Monitoring pixel change...")

        # Clear clipboard before starting
        clear_clipboard()

        scan_count = 0

        while self._running:
            try:
                scan_count += 1

                # Capture current pixel color
                current_color = get_pixel_color(self.view_coin_x, self.view_coin_y)

                # Check if changed
                if colors_different(self.base_pixel_color, current_color, tolerance=15):
                    self.log(f"[!] PIXEL CHANGED! {self.base_pixel_color} -> {current_color}")
                    self.set_state(SniperState.CLICKING_VIEW_COIN)

                    # Wait 0.4s before clicking
                    self.log("[*] Waiting 0.4s...")
                    await asyncio.sleep(0.4)

                    # Click View Coin
                    self.log(f"[*] Clicking View Coin ({self.view_coin_x}, {self.view_coin_y})")
                    windows_click(self.view_coin_x, self.view_coin_y)

                    # Wait 2.5s for chart to load
                    self.set_state(SniperState.WAITING_CHART)
                    self.log("[*] Waiting 2.5s for chart to load...")
                    await asyncio.sleep(2.5)

                    # Clear clipboard before copying
                    clear_clipboard()

                    # Click 3x on CA with 1s interval
                    self.set_state(SniperState.COPYING_CA)
                    self.log(f"[*] Clicking 3x on CA ({self.ca_area_x}, {self.ca_area_y})")

                    for i in range(3):
                        windows_click(self.ca_area_x, self.ca_area_y)
                        self.log(f"    Click {i+1}/3")

                        # Check clipboard after each click
                        await asyncio.sleep(0.3)
                        clipboard = get_clipboard()

                        if clipboard:
                            ca_match = CA_PATTERN.search(clipboard)
                            if ca_match:
                                ca = ca_match.group()
                                if 32 <= len(ca) <= 44:
                                    self.log(f"[+] CA found: {ca}")
                                    await self.buy_token(ca)
                                    break

                        if i < 2:
                            await asyncio.sleep(0.7)  # Complete 1s

                    # Update base color for next detection
                    self.base_pixel_color = get_pixel_color(self.view_coin_x, self.view_coin_y)
                    self.log(f"[*] New base color: RGB{self.base_pixel_color}")
                    self.log("[*] Returning to monitoring...")
                    self.set_state(SniperState.MONITORING)

                # Periodic log
                if scan_count % 100 == 0:
                    self.log(f"[SCAN #{scan_count}] Pixel: RGB{current_color}")

                # Interval between scans (very fast)
                await asyncio.sleep(0.05)  # 50ms = 20 scans/sec

            except Exception as e:
                self.log(f"[ERROR] {e}")
                await asyncio.sleep(0.5)

        self.set_state(SniperState.STOPPED)

    def stop(self):
        """Stop the sniper"""
        self._running = False
        self.log("[!] Stopping sniper...")

    def is_running(self) -> bool:
        """Check if running"""
        return self._running
