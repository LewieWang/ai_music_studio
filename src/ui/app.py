"""
主应用窗口
"""

import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from src.config import COLORS
from src.ui.components import ModernLogText
from src.ui.tabs.music_tab import MusicTab
from src.ui.tabs.cover_tab import CoverTab


class AICreativeStudio(ctk.CTk):
    """AI Creative Studio 主窗口"""

    def __init__(self):
        super().__init__()
        self.title("AI Creative Studio - 音乐生成")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_dark"])
        self.center_window()
        self._build_ui()

    def center_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 1280) // 2
        y = (screen_h - 800) // 2
        self.geometry(f"1280x800+{x}+{y}")

    def _build_ui(self):
        # 顶部导航栏
        self._build_navbar()

        # 主内容区域
        self._build_main_content()

        # 状态栏
        self._build_status_bar()

        # 初始日志
        self.log("🎉 AI Creative Studio 启动成功!", "success")
        self.log("欢迎使用 AI 音乐生成工具", "info")
        self.log("请在 ⚙️ 设置 中配置 API Key 后开始创作", "muted")
        self.log("", "muted")

    def _build_navbar(self):
        """构建导航栏"""
        navbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=0)
        navbar.pack(fill="x", side="top")
        navbar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(navbar, fg_color="transparent")
        logo_frame.pack(side="left", padx=24)
        ctk.CTkLabel(logo_frame, text="✨", font=("Segoe UI", 22),
                     text_color=COLORS["accent_primary"]).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(logo_frame, text="AI Creative Studio", font=("Segoe UI Black", 18),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" v1.0", font=("Segoe UI", 10),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(4, 0))

        # 设置按钮
        settings_btn = ctk.CTkButton(
            navbar, text="⚙️ 设置", width=80, height=34, corner_radius=8,
            font=("Segoe UI", 12), fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            border_width=1, border_color=COLORS["border"],
            command=self._open_settings
        )
        settings_btn.pack(side="right", padx=24)

        # API Key 变量
        self.api_key_var = tk.StringVar(value=os.getenv("MINIMAX_API_KEY", ""))

    def _build_main_content(self):
        """构建主内容区域"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=16, pady=12)

        content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        content_area.pack(fill="both", expand=True)

        # 左侧内容区
        left_panel = ctk.CTkFrame(content_area, fg_color="transparent")
        left_panel.pack(side="left", fill="both", expand=True)

        # 自定义 Tab 导航栏
        tab_bar = ctk.CTkFrame(left_panel, fg_color="transparent", height=44)
        tab_bar.pack(fill="x", pady=(0, 8))
        tab_bar.pack_propagate(False)

        self.tab_buttons = {}
        tab_items = [
            ("music", "🎵 音乐生成", COLORS["accent_primary"]),
            ("cover", "🎤 翻唱", COLORS["accent_secondary"]),
        ]
        for key, label, color in tab_items:
            btn = ctk.CTkButton(
                tab_bar, text=label, font=("Segoe UI Semibold", 13),
                fg_color="transparent", text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_hover"], corner_radius=8, height=38,
                anchor="center", width=160,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", padx=(0, 4))
            self.tab_buttons[key] = (btn, color)

        # Tab 内容容器
        self.tab_container = ctk.CTkFrame(left_panel, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True)

        # 音乐生成 Tab
        self.music_tab = MusicTab(self.tab_container, self.api_key_var, self.log)

        # 翻唱 Tab
        self.cover_tab = CoverTab(self.tab_container, self.api_key_var, self.log)
        self.cover_tab.save_dir_var = self.music_tab.save_dir_var  # 共享存储目录

        # 默认显示音乐生成
        self._current_tab = None
        self._switch_tab("music")

        # 右侧日志面板
        self._build_log_panel(content_area)

    def _switch_tab(self, tab_key: str):
        """切换 Tab 页"""
        if self._current_tab == tab_key:
            return

        # 隐藏当前 tab
        if self._current_tab == "music":
            self.music_tab.pack_forget()
        elif self._current_tab == "cover":
            self.cover_tab.pack_forget()

        # 显示目标 tab
        if tab_key == "music":
            self.music_tab.pack(fill="both", expand=True, in_=self.tab_container)
        elif tab_key == "cover":
            self.cover_tab.pack(fill="both", expand=True, in_=self.tab_container)

        # 更新按钮样式
        for key, (btn, color) in self.tab_buttons.items():
            if key == tab_key:
                btn.configure(fg_color=color, text_color="#000000" if color == COLORS["accent_primary"] else "#ffffff",
                              hover_color=color)
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"],
                              hover_color=COLORS["bg_hover"])

        self._current_tab = tab_key

    def _build_log_panel(self, parent):
        """构建日志面板"""
        right_panel = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=16, width=420)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)

        log_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        log_header.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(log_header, text="📋 Output Log", font=("Segoe UI Semibold", 15),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            log_header, text="清空", width=50, height=26, corner_radius=6, font=("Segoe UI", 10),
            fg_color="transparent", text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_hover"], border_color=COLORS["border"], border_width=1,
            command=lambda: self.log_text.clear()
        ).pack(side="right")

        ctk.CTkFrame(right_panel, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=18)
        self.log_text = ModernLogText(right_panel)
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(8, 16))

    def _build_status_bar(self):
        """构建状态栏"""
        status_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=32, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        ctk.CTkLabel(status_bar, text="✅ 就绪", font=("Segoe UI", 10),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=16)
        ctk.CTkLabel(status_bar, text="Powered by MiniMax AI", font=("Segoe UI", 10),
                     text_color=COLORS["text_muted"]).pack(side="right", padx=16)

    def _open_settings(self):
        """打开设置窗口"""
        win = ctk.CTkToplevel(self)
        win.title("设置")
        win.geometry("480x260")
        win.resizable(False, False)
        win.configure(fg_color=COLORS["bg_card"])
        win.transient(self)
        win.grab_set()
        win.attributes("-topmost", True)
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 240
        y = self.winfo_y() + (self.winfo_height() // 2) - 130
        win.geometry(f"480x260+{x}+{y}")

        # API Key
        ctk.CTkLabel(win, text="🔑 MiniMax API Key", font=("Segoe UI Semibold", 13),
                     text_color=COLORS["text_primary"], anchor="w"
                     ).pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkEntry(
            win, height=36, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="输入 MiniMax API Key...", show="●",
            textvariable=self.api_key_var
        ).pack(fill="x", padx=24, pady=(0, 14))

        # 存储目录
        ctk.CTkLabel(win, text="📂 默认存储目录", font=("Segoe UI Semibold", 13),
                     text_color=COLORS["text_primary"], anchor="w"
                     ).pack(fill="x", padx=24, pady=(0, 6))

        dir_row = ctk.CTkFrame(win, fg_color="transparent")
        dir_row.pack(fill="x", padx=24, pady=(0, 20))
        dir_entry = ctk.CTkEntry(
            dir_row, height=36, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            textvariable=self.music_tab.save_dir_var
        )
        dir_entry.pack(side="left", fill="both", expand=True, padx=(0, 8))

        def _browse():
            d = filedialog.askdirectory(initialdir=dir_entry.get(), parent=win)
            if d:
                dir_entry.delete(0, tk.END)
                dir_entry.insert(0, d)
                self.music_tab.save_dir_var.set(d)

        ctk.CTkButton(
            dir_row, text="浏览...", width=70, height=36, corner_radius=6, font=("Segoe UI", 11),
            fg_color=COLORS["bg_hover"], hover_color=COLORS["accent_primary"],
            text_color=COLORS["text_primary"], command=_browse
        ).pack(side="right")

        # 按钮
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkButton(
            btn_row, text="✅ 保存", width=100, height=36, corner_radius=8,
            font=("Segoe UI Semibold", 12), fg_color=COLORS["accent_primary"],
            hover_color=COLORS["bg_hover"], text_color="#000000",
            command=win.destroy
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row, text="取消", width=80, height=36, corner_radius=8, font=("Segoe UI", 12),
            fg_color=COLORS["bg_hover"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"], command=win.destroy
        ).pack(side="right")

    def log(self, message: str, level: str = "info"):
        """输出日志"""
        self.log_text.log(message, level)