"""
歌词生成模块
"""

import re
import tkinter as tk
from tkinter import messagebox
import threading
import customtkinter as ctk

from src.config import COLORS
from src.ui.components import GlowButton
from src.api.minimax import MiniMaxAPI


class LyricsGenerator:
    """歌词生成器"""

    MODE_MAP = {
        "write_full_song(完整歌曲)": "write_full_song",
        "write_verse(主歌段落)": "write_verse",
        "write_chorus(副歌段落)": "write_chorus"
    }

    def __init__(self, api_key_var, log_callback):
        self.api_key_var = api_key_var
        self.log_callback = log_callback

    def generate(self, prompt: str, mode: str) -> tuple:
        """
        生成歌词

        Returns:
            (lyrics, title, error_message)
        """
        api_key = self.api_key_var.get().strip()
        if not api_key:
            return "", "", "请先输入 API Key！"

        mode = self.MODE_MAP.get(mode, "write_full_song")

        try:
            api = MiniMaxAPI(api_key)
            result = api.generate_lyrics(prompt, mode)
            return self._parse_result(result)
        except Exception as e:
            return "", "", str(e)

    def _parse_result(self, result: dict) -> tuple:
        """解析 API 返回结果"""
        lyrics_text = ""
        title = ""

        if isinstance(result, dict):
            if "data" in result and result["data"]:
                data = result["data"]
                lyrics_text = data.get("lyrics", "") or data.get("text", "") or data.get("content", "")
                if isinstance(data, str):
                    lyrics_text = data
            elif "base_resp" in result:
                sc = result["base_resp"].get("status_code")
                if sc != 0:
                    return "", "", result['base_resp'].get('status_msg', '未知错误')

        if not lyrics_text:
            lyrics_text = result.get("lyrics", "") or result.get("text", "")

        # 提取标题
        if isinstance(result, dict):
            d = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
            title = d.get("title") or d.get("song_title") or d.get("name") or ""
            if not title:
                title = result.get("title") or result.get("song_title") or ""

        return lyrics_text, title, ""


class LyricsTab(ctk.CTkFrame):
    """歌词生成标签页 UI"""

    def __init__(self, parent, api_key_var, log_callback):
        super().__init__(parent, fg_color="transparent")
        self.api_key_var = api_key_var
        self.log_callback = log_callback
        self.lyrics_generator = LyricsGenerator(api_key_var, log_callback)
        self.current_title = ""
        self._build_ui()

    def _build_ui(self):
        # 提示词输入
        ctk.CTkLabel(self, text="▎AI 歌词生成", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_success"], anchor="w").pack(fill="x", pady=(4, 12))

        lyrics_prompt_row = ctk.CTkFrame(self, fg_color="transparent")
        lyrics_prompt_row.pack(fill="x", pady=(0, 10))
        self.lyrics_prompt_entry = ctk.CTkEntry(
            lyrics_prompt_row, height=36, corner_radius=6, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="描述想要生成的歌词主题、风格、参考歌手等..."
        )
        self.lyrics_prompt_entry.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.gen_lyrics_btn = GlowButton(
            lyrics_prompt_row, text="✍️ 生成", glow_color=COLORS["accent_success"],
            fg_color=COLORS["accent_success"], text_color="#000000",
            width=90, height=36, command=self._generate_lyrics
        )
        self.gen_lyrics_btn.pack(side="right")

        # 生成模式选择
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(mode_row, text="生成模式", font=("Segoe UI", 11),
                     text_color=COLORS["text_muted"]).pack(side="left")
        self.lyrics_mode_var = tk.StringVar(value="write_full_song")
        ctk.CTkOptionMenu(
            mode_row,
            values=["write_full_song(完整歌曲)", "write_verse(主歌段落)", "write_chorus(副歌段落)"],
            variable=self.lyrics_mode_var, width=200, height=30, corner_radius=6,
            font=("Segoe UI", 11), fg_color=COLORS["bg_input"],
            dropdown_fg_color=COLORS["bg_card"], text_color=COLORS["text_primary"]
        ).pack(side="right")

        # 歌词编辑区
        ctk.CTkLabel(self, text="歌词内容（可手动编辑或由 AI 生成）", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 6))
        self.lyrics_text = ctk.CTkTextbox(
            self, height=220, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"], wrap=tk.WORD
        )
        self.lyrics_text.pack(fill="x", pady=(0, 14))

        # 操作按钮
        lyrics_btn_row = ctk.CTkFrame(self, fg_color="transparent")
        lyrics_btn_row.pack(fill="x", pady=(0, 14))
        GlowButton(
            lyrics_btn_row, text="💾 保存歌词", glow_color=COLORS["accent_success"],
            fg_color=COLORS["bg_input"], text_color=COLORS["accent_success"],
            height=34, width=140, command=self._save_lyrics_to_file
        ).pack(side="left", padx=(0, 8))
        GlowButton(
            lyrics_btn_row, text="📋 复制歌词", glow_color=COLORS["text_muted"],
            fg_color=COLORS["bg_input"], text_color=COLORS["text_secondary"],
            height=34, width=120, command=self._copy_lyrics
        ).pack(side="left")

    def _generate_lyrics(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        prompt = self.lyrics_prompt_entry.get().strip() or "写一首关于爱情的中文流行歌曲歌词"
        mode_raw = self.lyrics_mode_var.get()
        mode = self.lyrics_generator.MODE_MAP.get(mode_raw, "write_full_song")

        self.gen_lyrics_btn.configure(state="disabled", text="⏳ 生成中...")
        self.log_callback(f"正在调用 AI 歌词生成 API (模式: {mode})...", "info")
        self.log_callback(f"提示词: {prompt}", "accent")

        thread = threading.Thread(
            target=self._call_lyrics_api,
            args=(prompt, mode, api_key),
            daemon=True
        )
        thread.start()

    def _call_lyrics_api(self, prompt: str, mode: str, api_key: str):
        lyrics, title, error = self.lyrics_generator.generate(prompt, mode)

        if error:
            self.after(0, lambda: self.log_callback(f"歌词生成失败: {error}", "error"))
        else:
            self.after(0, lambda: self._handle_lyrics_result(lyrics, title))

        self.after(0, lambda: self.gen_lyrics_btn.configure(state="normal", text="✍️ 生成"))

    def _handle_lyrics_result(self, lyrics: str, title: str):
        if lyrics:
            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", lyrics)
            self.log_callback(f"\n✅ 歌词生成成功！(共 {len(lyrics)} 字)", "success")
            self.log_callback("📝 歌词已自动填入下方编辑框，可直接用于音乐生成", "accent")
        else:
            self.log_callback("⚠️ 未获取到有效的歌词内容", "warning")

        if title:
            self.current_title = self._sanitize_filename(title)
            self.log_callback(f"🎼 已提取歌曲标题: 「{self.current_title}」", "accent")

    def _save_lyrics_to_file(self):
        from tkinter import filedialog
        from pathlib import Path
        import datetime

        lyrics_content = self.lyrics_text.get("1.0", tk.END).strip()
        if not lyrics_content:
            messagebox.showwarning("提示", "歌词内容为空！")
            return

        save_dir = Path("D:/AIMusicData")
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"lyrics_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            title="保存歌词", initialdir=str(save_dir), initialfile=default_name,
            defaultextension=".txt", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            Path(file_path).write_text(lyrics_content, encoding="utf-8")
            self.log_callback(f"💾 歌词已保存至: {file_path}", "success")

    def _copy_lyrics(self):
        lyrics_content = self.lyrics_text.get("1.0", tk.END).strip()
        if not lyrics_content:
            messagebox.showwarning("提示", "歌词内容为空！")
            return

        self.clipboard_clear()
        self.clipboard_append(lyrics_content)
        self.update_idletasks()
        self.log_callback("📋 歌词已复制到剪贴板", "success")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        name = re.sub(r'_+', '_', name)
        return name[:60] or "unnamed"

    def get_lyrics(self) -> str:
        return self.lyrics_text.get("1.0", tk.END).strip()

    def set_lyrics(self, lyrics: str):
        self.lyrics_text.delete("1.0", tk.END)
        self.lyrics_text.insert("1.0", lyrics)

    def get_title(self) -> str:
        return self.current_title

    def set_title(self, title: str):
        self.current_title = self._sanitize_filename(title)