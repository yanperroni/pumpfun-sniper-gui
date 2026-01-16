"""
Sniper baseado em deteccao de pixel
Monitora mudanca de cor no pixel do View Coin e executa compras
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


# Regex para CA Solana
CA_PATTERN = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}')


class SniperState(Enum):
    """Estados do sniper"""
    STOPPED = auto()
    MONITORING = auto()
    CLICKING_VIEW_COIN = auto()
    WAITING_CHART = auto()
    COPYING_CA = auto()
    BUYING = auto()


def get_pixel_color(x: int, y: int) -> Tuple[int, int, int]:
    """Captura cor de um pixel na tela"""
    # Captura area 1x1 pixel
    img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    return img.getpixel((0, 0))


def colors_different(c1: Tuple[int, int, int], c2: Tuple[int, int, int], tolerance: int = 10) -> bool:
    """Verifica se duas cores sao diferentes (com tolerancia)"""
    diff = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])
    return diff > tolerance


def windows_click(x: int, y: int):
    """Simula clique do mouse no Windows"""
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.02)

    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def get_clipboard() -> str:
    """Le clipboard do Windows"""
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
    """Limpa o clipboard"""
    try:
        subprocess.run(
            ["powershell", "-command", "Set-Clipboard -Value $null"],
            capture_output=True,
            timeout=2
        )
    except:
        pass


class Sniper:
    """Sniper baseado em pixel detection"""

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
        **kwargs  # Ignorar outros parametros
    ):
        # Config de compra
        self.api_key = api_key
        self.buy_amount = buy_amount
        self.slippage = slippage
        self.priority_fee = priority_fee
        self.num_attempts = num_attempts
        self.delay_between = delay_between

        # Coordenadas
        self.view_coin_x = view_coin_x
        self.view_coin_y = view_coin_y
        self.ca_area_x = ca_area_x
        self.ca_area_y = ca_area_y

        # API
        self.api = PumpPortalAPI(api_key)

        # Estado
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
        """Emite log"""
        print(msg)
        if self.on_log:
            self.on_log(msg)

    def set_state(self, state: SniperState):
        """Muda estado"""
        self.state = state
        if self.on_state_change:
            self.on_state_change(state)

    async def buy_token(self, mint: str):
        """Executa compras"""
        if mint in self.bought_tokens:
            self.log(f"[SKIP] Token ja comprado: {mint}")
            return

        self.bought_tokens.add(mint)
        self.set_state(SniperState.BUYING)

        self.log("=" * 50)
        self.log(f"CA DETECTADO: {mint}")
        self.log(f"COMPRANDO: {self.num_attempts}x {self.buy_amount} SOL")
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
        self.log("COMPRAS FINALIZADAS")
        self.log("=" * 50)

        return results

    def _on_buy_result(self, result: BuyResult):
        """Callback de resultado de compra"""
        if result.success:
            self.log(f"[{result.attempt}/{self.num_attempts}] OK - TX: {result.signature[:20]}...")
        else:
            self.log(f"[{result.attempt}/{self.num_attempts}] ERRO: {result.error}")

        if self.on_buy_result:
            self.on_buy_result(result)

    async def run(self):
        """Loop principal"""
        self._running = True
        self.set_state(SniperState.MONITORING)

        # Capturar cor base do pixel
        self.base_pixel_color = get_pixel_color(self.view_coin_x, self.view_coin_y)

        self.log("=" * 50)
        self.log("SNIPER INICIADO")
        self.log(f"View Coin: ({self.view_coin_x}, {self.view_coin_y})")
        self.log(f"CA Area: ({self.ca_area_x}, {self.ca_area_y})")
        self.log(f"Pixel base: RGB{self.base_pixel_color}")
        self.log(f"Config: {self.num_attempts}x {self.buy_amount} SOL")
        self.log("=" * 50)
        self.log("Monitorando mudanca de pixel...")

        # Limpar clipboard antes de comecar
        clear_clipboard()

        scan_count = 0

        while self._running:
            try:
                scan_count += 1

                # Capturar cor atual do pixel
                current_color = get_pixel_color(self.view_coin_x, self.view_coin_y)

                # Verificar se mudou
                if colors_different(self.base_pixel_color, current_color, tolerance=15):
                    self.log(f"[!] PIXEL MUDOU! {self.base_pixel_color} -> {current_color}")
                    self.set_state(SniperState.CLICKING_VIEW_COIN)

                    # Esperar 0.4s antes de clicar
                    self.log("[*] Aguardando 0.4s...")
                    await asyncio.sleep(0.4)

                    # Clicar no View Coin
                    self.log(f"[*] Clicando View Coin ({self.view_coin_x}, {self.view_coin_y})")
                    windows_click(self.view_coin_x, self.view_coin_y)

                    # Esperar 2.5s para carregar
                    self.set_state(SniperState.WAITING_CHART)
                    self.log("[*] Aguardando 2.5s para grafico carregar...")
                    await asyncio.sleep(2.5)

                    # Limpar clipboard antes de copiar
                    clear_clipboard()

                    # Clicar 3x no CA com 1s de intervalo
                    self.set_state(SniperState.COPYING_CA)
                    self.log(f"[*] Clicando 3x no CA ({self.ca_area_x}, {self.ca_area_y})")

                    for i in range(3):
                        windows_click(self.ca_area_x, self.ca_area_y)
                        self.log(f"    Clique {i+1}/3")

                        # Verificar clipboard apos cada clique
                        await asyncio.sleep(0.3)
                        clipboard = get_clipboard()

                        if clipboard:
                            ca_match = CA_PATTERN.search(clipboard)
                            if ca_match:
                                ca = ca_match.group()
                                if 32 <= len(ca) <= 44:
                                    self.log(f"[+] CA encontrado: {ca}")
                                    await self.buy_token(ca)
                                    break

                        if i < 2:
                            await asyncio.sleep(0.7)  # Completar 1s

                    # Atualizar cor base para proxima deteccao
                    self.base_pixel_color = get_pixel_color(self.view_coin_x, self.view_coin_y)
                    self.log(f"[*] Nova cor base: RGB{self.base_pixel_color}")
                    self.log("[*] Voltando a monitorar...")
                    self.set_state(SniperState.MONITORING)

                # Log periodico
                if scan_count % 100 == 0:
                    self.log(f"[SCAN #{scan_count}] Pixel: RGB{current_color}")

                # Intervalo entre scans (bem rapido)
                await asyncio.sleep(0.05)  # 50ms = 20 scans/sec

            except Exception as e:
                self.log(f"[ERRO] {e}")
                await asyncio.sleep(0.5)

        self.set_state(SniperState.STOPPED)

    def stop(self):
        """Para o sniper"""
        self._running = False
        self.log("[!] Parando sniper...")

    def is_running(self) -> bool:
        """Verifica se esta rodando"""
        return self._running
