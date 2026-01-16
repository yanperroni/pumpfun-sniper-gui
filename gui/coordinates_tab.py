"""
Aba de calibracao de coordenadas com crosshair overlay
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import ctypes
import time

from config.settings import Settings


def windows_click(x: int, y: int):
    """Simula clique do mouse no Windows usando ctypes"""
    # Mover mouse para posicao
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.05)

    # Simular clique (mouse down + mouse up)
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class CrosshairOverlay(tk.Toplevel):
    """Overlay para selecionar coordenadas na tela inteira"""

    def __init__(self, on_click: Callable[[int, int], None], on_cancel: Callable[[], None]):
        super().__init__()

        self.on_click_callback = on_click
        self.on_cancel = on_cancel
        self.selected = False

        # Pegar tamanho da tela
        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        # Configurar janela fullscreen
        self.title("Selecione a posicao - ESC para cancelar")
        self.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.4)  # Semi-transparente
        self.configure(bg='gray20')
        self.overrideredirect(True)  # Remove bordas

        # Canvas para desenhar
        self.canvas = tk.Canvas(
            self,
            width=self.screen_w,
            height=self.screen_h,
            bg='gray20',
            highlightthickness=0
        )
        self.canvas.pack()

        # Texto de instrucao
        self.canvas.create_rectangle(
            self.screen_w // 2 - 250, 30,
            self.screen_w // 2 + 250, 80,
            fill='black', outline='white', width=2
        )
        self.canvas.create_text(
            self.screen_w // 2, 55,
            text="CLIQUE NO LOCAL DESEJADO | ESC = CANCELAR",
            fill='white',
            font=('Arial', 16, 'bold')
        )

        # Crosshair
        self.h_line = self.canvas.create_line(0, 0, self.screen_w, 0, fill='red', width=2)
        self.v_line = self.canvas.create_line(0, 0, 0, self.screen_h, fill='red', width=2)

        # Texto de coordenadas
        self.coord_bg = self.canvas.create_rectangle(0, 0, 0, 0, fill='black', outline='yellow')
        self.coord_text = self.canvas.create_text(0, 0, text="", fill='yellow', font=('Arial', 12, 'bold'), anchor='nw')

        # Bindings
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Button-1>', self._on_click)
        self.bind('<Escape>', self._on_escape)
        self.bind('<Button-3>', self._on_escape)  # Right click also cancels

        # Focar
        self.focus_force()
        self.grab_set()

    def _on_motion(self, event):
        """Atualiza crosshair"""
        x, y = event.x, event.y

        # Linhas do crosshair
        self.canvas.coords(self.h_line, 0, y, self.screen_w, y)
        self.canvas.coords(self.v_line, x, 0, x, self.screen_h)

        # Texto de coordenadas (ajustar posicao para nao sair da tela)
        text_x = x + 15 if x < self.screen_w - 120 else x - 115
        text_y = y - 25 if y > 30 else y + 15

        self.canvas.coords(self.coord_bg, text_x - 5, text_y - 2, text_x + 100, text_y + 20)
        self.canvas.coords(self.coord_text, text_x, text_y)
        self.canvas.itemconfig(self.coord_text, text=f"X: {x}  Y: {y}")

    def _on_click(self, event):
        """Captura clique"""
        if self.selected:
            return
        self.selected = True

        x, y = event.x, event.y
        self.grab_release()
        self.destroy()
        self.on_click_callback(x, y)

    def _on_escape(self, event=None):
        """Cancela"""
        if self.selected:
            return
        self.selected = True

        self.grab_release()
        self.destroy()
        self.on_cancel()


class CoordinatesTab(ctk.CTkFrame):
    """Aba para calibrar coordenadas de clique"""

    def __init__(self, parent, settings: Settings, on_save: Optional[Callable[[], None]] = None):
        super().__init__(parent)

        self.settings = settings
        self.on_save = on_save

        self._create_widgets()

    def _create_widgets(self):
        """Cria widgets"""
        # Titulo
        title = ctk.CTkLabel(
            self,
            text="Calibrar Coordenadas",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=10)

        # Instrucoes
        instructions = ctk.CTkLabel(
            self,
            text="Clique em 'Selecionar na Tela' e depois clique no local desejado.\n"
                 "Use 'Testar Clique' para verificar se a posicao esta correta.",
            text_color="gray"
        )
        instructions.pack(pady=5)

        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # === View Coin ===
        vc_frame = ctk.CTkFrame(main_frame)
        vc_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(
            vc_frame,
            text="Botao 'View Coin'",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        ctk.CTkLabel(
            vc_frame,
            text="Clique no botao View Coin da notificacao",
            text_color="gray"
        ).pack()

        vc_coords = ctk.CTkFrame(vc_frame, fg_color="transparent")
        vc_coords.pack(pady=10)

        ctk.CTkLabel(vc_coords, text="X:", width=30).pack(side="left")
        self.vc_x_entry = ctk.CTkEntry(vc_coords, width=80)
        self.vc_x_entry.pack(side="left", padx=5)

        ctk.CTkLabel(vc_coords, text="Y:", width=30).pack(side="left", padx=(20, 0))
        self.vc_y_entry = ctk.CTkEntry(vc_coords, width=80)
        self.vc_y_entry.pack(side="left", padx=5)

        vc_btns = ctk.CTkFrame(vc_frame, fg_color="transparent")
        vc_btns.pack(pady=5)

        self.vc_select_btn = ctk.CTkButton(
            vc_btns,
            text="Selecionar na Tela",
            command=self._select_view_coin,
            fg_color="green",
            hover_color="darkgreen",
            width=150
        )
        self.vc_select_btn.pack(side="left", padx=5)

        self.vc_test_btn = ctk.CTkButton(
            vc_btns,
            text="Testar Clique",
            command=self._test_view_coin,
            width=120
        )
        self.vc_test_btn.pack(side="left", padx=5)

        # === CA Area ===
        ca_frame = ctk.CTkFrame(main_frame)
        ca_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(
            ca_frame,
            text="Area do Contract Address",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        ctk.CTkLabel(
            ca_frame,
            text="Clique onde esta o CA para copiar",
            text_color="gray"
        ).pack()

        ca_coords = ctk.CTkFrame(ca_frame, fg_color="transparent")
        ca_coords.pack(pady=10)

        ctk.CTkLabel(ca_coords, text="X:", width=30).pack(side="left")
        self.ca_x_entry = ctk.CTkEntry(ca_coords, width=80)
        self.ca_x_entry.pack(side="left", padx=5)

        ctk.CTkLabel(ca_coords, text="Y:", width=30).pack(side="left", padx=(20, 0))
        self.ca_y_entry = ctk.CTkEntry(ca_coords, width=80)
        self.ca_y_entry.pack(side="left", padx=5)

        ca_btns = ctk.CTkFrame(ca_frame, fg_color="transparent")
        ca_btns.pack(pady=5)

        self.ca_select_btn = ctk.CTkButton(
            ca_btns,
            text="Selecionar na Tela",
            command=self._select_ca_area,
            fg_color="blue",
            hover_color="darkblue",
            width=150
        )
        self.ca_select_btn.pack(side="left", padx=5)

        self.ca_test_btn = ctk.CTkButton(
            ca_btns,
            text="Testar Clique",
            command=self._test_ca_area,
            width=120
        )
        self.ca_test_btn.pack(side="left", padx=5)

        # === Status e Salvar ===
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(bottom_frame, text="", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        self.save_btn = ctk.CTkButton(
            bottom_frame,
            text="Salvar Coordenadas",
            command=self._save,
            width=150
        )
        self.save_btn.pack(side="right")

        # Carregar valores atuais
        self._load_values()

    def _load_values(self):
        """Carrega valores das settings"""
        self.vc_x_entry.delete(0, "end")
        self.vc_x_entry.insert(0, str(self.settings.view_coin_x))

        self.vc_y_entry.delete(0, "end")
        self.vc_y_entry.insert(0, str(self.settings.view_coin_y))

        self.ca_x_entry.delete(0, "end")
        self.ca_x_entry.insert(0, str(self.settings.ca_area_x))

        self.ca_y_entry.delete(0, "end")
        self.ca_y_entry.insert(0, str(self.settings.ca_area_y))

    def _select_view_coin(self):
        """Abre overlay para selecionar View Coin"""
        self.status_label.configure(text="Selecione o botao View Coin...", text_color="orange")

        # Minimizar janela principal
        self.winfo_toplevel().iconify()
        self.after(300, lambda: self._open_crosshair("view_coin"))

    def _select_ca_area(self):
        """Abre overlay para selecionar CA Area"""
        self.status_label.configure(text="Selecione a area do CA...", text_color="orange")

        # Minimizar janela principal
        self.winfo_toplevel().iconify()
        self.after(300, lambda: self._open_crosshair("ca_area"))

    def _open_crosshair(self, mode: str):
        """Abre crosshair overlay"""
        def on_click(x, y):
            # Restaurar janela principal
            self.after(100, lambda: self.winfo_toplevel().deiconify())
            self.after(150, lambda: self.winfo_toplevel().lift())

            if mode == "view_coin":
                self.vc_x_entry.delete(0, "end")
                self.vc_x_entry.insert(0, str(x))
                self.vc_y_entry.delete(0, "end")
                self.vc_y_entry.insert(0, str(y))
                self.status_label.configure(
                    text=f"View Coin: ({x}, {y})",
                    text_color="green"
                )
            else:
                self.ca_x_entry.delete(0, "end")
                self.ca_x_entry.insert(0, str(x))
                self.ca_y_entry.delete(0, "end")
                self.ca_y_entry.insert(0, str(y))
                self.status_label.configure(
                    text=f"CA Area: ({x}, {y})",
                    text_color="green"
                )

        def on_cancel():
            self.after(100, lambda: self.winfo_toplevel().deiconify())
            self.after(150, lambda: self.winfo_toplevel().lift())
            self.status_label.configure(text="Cancelado", text_color="gray")

        CrosshairOverlay(on_click, on_cancel)

    def _test_view_coin(self):
        """Testa clique no View Coin - simula clique do mouse"""
        try:
            x = int(self.vc_x_entry.get())
            y = int(self.vc_y_entry.get())

            self.status_label.configure(text=f"Clicando em ({x}, {y})...", text_color="orange")
            self.update()

            # Minimizar pra nao atrapalhar
            self.winfo_toplevel().iconify()
            self.after(200, lambda: self._do_test_click(x, y))

        except ValueError:
            self.status_label.configure(text="Erro: coordenadas invalidas", text_color="red")

    def _test_ca_area(self):
        """Testa clique na area do CA - simula clique do mouse"""
        try:
            x = int(self.ca_x_entry.get())
            y = int(self.ca_y_entry.get())

            self.status_label.configure(text=f"Clicando em ({x}, {y})...", text_color="orange")
            self.update()

            # Minimizar pra nao atrapalhar
            self.winfo_toplevel().iconify()
            self.after(200, lambda: self._do_test_click(x, y))

        except ValueError:
            self.status_label.configure(text="Erro: coordenadas invalidas", text_color="red")

    def _do_test_click(self, x: int, y: int):
        """Executa o clique de teste"""
        windows_click(x, y)

        # Restaurar janela apos o clique
        self.after(500, lambda: self.winfo_toplevel().deiconify())
        self.after(600, lambda: self.winfo_toplevel().lift())
        self.after(600, lambda: self.status_label.configure(
            text=f"Clique enviado em ({x}, {y})",
            text_color="green"
        ))

    def _save(self):
        """Salva coordenadas"""
        try:
            self.settings.view_coin_x = int(self.vc_x_entry.get())
            self.settings.view_coin_y = int(self.vc_y_entry.get())
            self.settings.ca_area_x = int(self.ca_x_entry.get())
            self.settings.ca_area_y = int(self.ca_y_entry.get())

            self.settings.save()

            self.status_label.configure(text="Coordenadas salvas!", text_color="green")

            if self.on_save:
                self.on_save()

        except ValueError:
            self.status_label.configure(text="Erro: valores invalidos", text_color="red")
