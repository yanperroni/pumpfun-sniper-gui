"""
Coordinate calibration tab with crosshair overlay
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import ctypes
import time

from config.settings import Settings


def windows_click(x: int, y: int):
    """Simulate mouse click on Windows using ctypes"""
    # Move mouse to position
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.05)

    # Simulate click (mouse down + mouse up)
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class CrosshairOverlay(tk.Toplevel):
    """Overlay for selecting coordinates on full screen"""

    def __init__(self, on_click: Callable[[int, int], None], on_cancel: Callable[[], None]):
        super().__init__()

        self.on_click_callback = on_click
        self.on_cancel = on_cancel
        self.selected = False

        # Get screen size
        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        # Configure fullscreen window
        self.title("Select position - ESC to cancel")
        self.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.4)  # Semi-transparent
        self.configure(bg='gray20')
        self.overrideredirect(True)  # Remove borders

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self,
            width=self.screen_w,
            height=self.screen_h,
            bg='gray20',
            highlightthickness=0
        )
        self.canvas.pack()

        # Instruction text
        self.canvas.create_rectangle(
            self.screen_w // 2 - 250, 30,
            self.screen_w // 2 + 250, 80,
            fill='black', outline='white', width=2
        )
        self.canvas.create_text(
            self.screen_w // 2, 55,
            text="CLICK ON DESIRED LOCATION | ESC = CANCEL",
            fill='white',
            font=('Arial', 16, 'bold')
        )

        # Crosshair
        self.h_line = self.canvas.create_line(0, 0, self.screen_w, 0, fill='red', width=2)
        self.v_line = self.canvas.create_line(0, 0, 0, self.screen_h, fill='red', width=2)

        # Coordinate text
        self.coord_bg = self.canvas.create_rectangle(0, 0, 0, 0, fill='black', outline='yellow')
        self.coord_text = self.canvas.create_text(0, 0, text="", fill='yellow', font=('Arial', 12, 'bold'), anchor='nw')

        # Bindings
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Button-1>', self._on_click)
        self.bind('<Escape>', self._on_escape)
        self.bind('<Button-3>', self._on_escape)  # Right click also cancels

        # Focus
        self.focus_force()
        self.grab_set()

    def _on_motion(self, event):
        """Update crosshair"""
        x, y = event.x, event.y

        # Crosshair lines
        self.canvas.coords(self.h_line, 0, y, self.screen_w, y)
        self.canvas.coords(self.v_line, x, 0, x, self.screen_h)

        # Coordinate text (adjust position to not go off screen)
        text_x = x + 15 if x < self.screen_w - 120 else x - 115
        text_y = y - 25 if y > 30 else y + 15

        self.canvas.coords(self.coord_bg, text_x - 5, text_y - 2, text_x + 100, text_y + 20)
        self.canvas.coords(self.coord_text, text_x, text_y)
        self.canvas.itemconfig(self.coord_text, text=f"X: {x}  Y: {y}")

    def _on_click(self, event):
        """Capture click"""
        if self.selected:
            return
        self.selected = True

        x, y = event.x, event.y
        self.grab_release()
        self.destroy()
        self.on_click_callback(x, y)

    def _on_escape(self, event=None):
        """Cancel"""
        if self.selected:
            return
        self.selected = True

        self.grab_release()
        self.destroy()
        self.on_cancel()


class CoordinatesTab(ctk.CTkFrame):
    """Tab for calibrating click coordinates"""

    def __init__(self, parent, settings: Settings, on_save: Optional[Callable[[], None]] = None):
        super().__init__(parent)

        self.settings = settings
        self.on_save = on_save

        self._create_widgets()

    def _create_widgets(self):
        """Create widgets"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Calibrate Coordinates",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=10)

        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text="Click 'Select on Screen' and then click on the desired location.\n"
                 "Use 'Test Click' to verify if the position is correct.",
            text_color="gray"
        )
        instructions.pack(pady=5)

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # === View Coin ===
        vc_frame = ctk.CTkFrame(main_frame)
        vc_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(
            vc_frame,
            text="'View Coin' Button",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        ctk.CTkLabel(
            vc_frame,
            text="Click on the View Coin button from the notification",
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
            text="Select on Screen",
            command=self._select_view_coin,
            fg_color="green",
            hover_color="darkgreen",
            width=150
        )
        self.vc_select_btn.pack(side="left", padx=5)

        self.vc_test_btn = ctk.CTkButton(
            vc_btns,
            text="Test Click",
            command=self._test_view_coin,
            width=120
        )
        self.vc_test_btn.pack(side="left", padx=5)

        # === CA Area ===
        ca_frame = ctk.CTkFrame(main_frame)
        ca_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(
            ca_frame,
            text="Contract Address Area",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        ctk.CTkLabel(
            ca_frame,
            text="Click where the CA is to copy it",
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
            text="Select on Screen",
            command=self._select_ca_area,
            fg_color="blue",
            hover_color="darkblue",
            width=150
        )
        self.ca_select_btn.pack(side="left", padx=5)

        self.ca_test_btn = ctk.CTkButton(
            ca_btns,
            text="Test Click",
            command=self._test_ca_area,
            width=120
        )
        self.ca_test_btn.pack(side="left", padx=5)

        # === Status and Save ===
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(bottom_frame, text="", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        self.save_btn = ctk.CTkButton(
            bottom_frame,
            text="Save Coordinates",
            command=self._save,
            width=150
        )
        self.save_btn.pack(side="right")

        # Load current values
        self._load_values()

    def _load_values(self):
        """Load values from settings"""
        self.vc_x_entry.delete(0, "end")
        self.vc_x_entry.insert(0, str(self.settings.view_coin_x))

        self.vc_y_entry.delete(0, "end")
        self.vc_y_entry.insert(0, str(self.settings.view_coin_y))

        self.ca_x_entry.delete(0, "end")
        self.ca_x_entry.insert(0, str(self.settings.ca_area_x))

        self.ca_y_entry.delete(0, "end")
        self.ca_y_entry.insert(0, str(self.settings.ca_area_y))

    def _select_view_coin(self):
        """Open overlay to select View Coin"""
        self.status_label.configure(text="Select the View Coin button...", text_color="orange")

        # Minimize main window
        self.winfo_toplevel().iconify()
        self.after(300, lambda: self._open_crosshair("view_coin"))

    def _select_ca_area(self):
        """Open overlay to select CA Area"""
        self.status_label.configure(text="Select the CA area...", text_color="orange")

        # Minimize main window
        self.winfo_toplevel().iconify()
        self.after(300, lambda: self._open_crosshair("ca_area"))

    def _open_crosshair(self, mode: str):
        """Open crosshair overlay"""
        def on_click(x, y):
            # Restore main window
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
            self.status_label.configure(text="Cancelled", text_color="gray")

        CrosshairOverlay(on_click, on_cancel)

    def _test_view_coin(self):
        """Test click on View Coin - simulates mouse click"""
        try:
            x = int(self.vc_x_entry.get())
            y = int(self.vc_y_entry.get())

            self.status_label.configure(text=f"Clicking on ({x}, {y})...", text_color="orange")
            self.update()

            # Minimize to not interfere
            self.winfo_toplevel().iconify()
            self.after(200, lambda: self._do_test_click(x, y))

        except ValueError:
            self.status_label.configure(text="Error: invalid coordinates", text_color="red")

    def _test_ca_area(self):
        """Test click on CA area - simulates mouse click"""
        try:
            x = int(self.ca_x_entry.get())
            y = int(self.ca_y_entry.get())

            self.status_label.configure(text=f"Clicking on ({x}, {y})...", text_color="orange")
            self.update()

            # Minimize to not interfere
            self.winfo_toplevel().iconify()
            self.after(200, lambda: self._do_test_click(x, y))

        except ValueError:
            self.status_label.configure(text="Error: invalid coordinates", text_color="red")

    def _do_test_click(self, x: int, y: int):
        """Execute the test click"""
        windows_click(x, y)

        # Restore window after click
        self.after(500, lambda: self.winfo_toplevel().deiconify())
        self.after(600, lambda: self.winfo_toplevel().lift())
        self.after(600, lambda: self.status_label.configure(
            text=f"Click sent to ({x}, {y})",
            text_color="green"
        ))

    def _save(self):
        """Save coordinates"""
        try:
            self.settings.view_coin_x = int(self.vc_x_entry.get())
            self.settings.view_coin_y = int(self.vc_y_entry.get())
            self.settings.ca_area_x = int(self.ca_x_entry.get())
            self.settings.ca_area_y = int(self.ca_y_entry.get())

            self.settings.save()

            self.status_label.configure(text="Coordinates saved!", text_color="green")

            if self.on_save:
                self.on_save()

        except ValueError:
            self.status_label.configure(text="Error: invalid values", text_color="red")
