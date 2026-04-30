"""
UI 组件模块 - 自定义组件
"""

import tkinter as tk
from tkinter import scrolledtext
import datetime
import customtkinter as ctk

from src.config import COLORS


class ModernLogText(scrolledtext.ScrolledText):
    """自定义日志输出组件"""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=COLORS["bg_input"],
            fg=COLORS["text_secondary"],
            font=("Consolas", 11),
            borderwidth=0,
            relief="flat",
            wrap=tk.WORD,
            padx=12,
            pady=12,
            **kwargs
        )
        self.configure(cursor="hand2")
        self.tag_configure("info", foreground=COLORS["text_secondary"])
        self.tag_configure("success", foreground=COLORS["accent_success"])
        self.tag_configure("warning", foreground=COLORS["accent_warning"])
        self.tag_configure("error", foreground=COLORS["accent_error"])
        self.tag_configure("accent", foreground=COLORS["accent_primary"])
        self.tag_configure("timestamp", foreground=COLORS["text_muted"])

    def log(self, message, level="info"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.insert(tk.END, f"{message}\n", level)
        self.see(tk.END)

    def clear(self):
        self.delete(1.0, tk.END)


class GlowButton(ctk.CTkButton):
    """带发光效果的按钮"""

    def __init__(self, parent, glow_color=None, **kwargs):
        self.glow_color = glow_color or COLORS["accent_primary"]
        super().__init__(
            parent,
            corner_radius=8,
            font=("Segoe UI Semibold", 13),
            **kwargs
        )
        self.configure(
            hover_color=self.glow_color,
            fg_color=(self.glow_color if kwargs.get("fg_color") is None else kwargs.get("fg_color")),
        )


class LabeledEntry(ctk.CTkFrame):
    """带标签的输入框组件"""

    def __init__(self, parent, label_text, default_value="", placeholder="", width=400, **entry_kwargs):
        super().__init__(parent, fg_color="transparent")

        self.label = ctk.CTkLabel(self, text=label_text, font=("Segoe UI", 12),
                                  text_color=COLORS["text_secondary"], anchor="w")
        self.label.pack(fill="x", pady=(0, 6))

        self.entry = ctk.CTkEntry(
            self, width=width, height=38, corner_radius=6, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"], placeholder_text=placeholder,
            **entry_kwargs
        )
        self.entry.pack(fill="x")
        if default_value:
            self.entry.insert(0, default_value)

    def get(self):
        return self.entry.get()

    def insert(self, value):
        self.entry.insert(0, value)