"""
翻唱生成模块 - 两步翻唱流程
步骤1: 翻唱前处理 (cover_preprocess) → 获取 cover_feature_id + formatted_lyrics
步骤2: 翻唱生成 (generate_cover) → 传入 cover_feature_id + 修改后歌词 → 生成翻唱
"""

import re
import base64
import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import threading
import datetime
import urllib.request
from pathlib import Path
import json

import customtkinter as ctk

from src.config import COLORS
from src.ui.components import GlowButton
from src.api.minimax import MiniMaxAPI


class CoverTab(ctk.CTkScrollableFrame):
    """翻唱生成标签页 UI"""

    def __init__(self, parent, api_key_var, log_callback):
        super().__init__(parent, fg_color="transparent",
                         scrollbar_button_color=COLORS["accent_secondary"],
                         scrollbar_button_hover_color=COLORS["accent_primary"])
        self.api_key_var = api_key_var
        self.log_callback = log_callback
        self.save_dir_var = tk.StringVar(value="D:/AIMusicData")
        self.cover_feature_id = ""
        self.audio_duration = 0.0
        self._build_ui()

    def _build_ui(self):
        # ===== 流程说明 =====
        self._build_flow_info()

        # ===== 步骤1: 上传参考音频 =====
        self._build_audio_upload_section()

        # ===== 步骤2: 翻唱前处理 =====
        self._build_preprocess_section()

        # ===== 步骤3: 编辑歌词 & 设置参数 =====
        self._build_lyrics_and_params_section()

        # ===== 生成按钮 =====
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))
        self.generate_btn = GlowButton(
            btn_frame, text="🎤 生成翻唱", glow_color=COLORS["accent_secondary"],
            fg_color=COLORS["accent_secondary"], text_color="#ffffff", height=46,
            command=self._generate_cover
        )
        self.generate_btn.pack(fill="x")

    # ──────────────── 流程说明 ────────────────
    def _build_flow_info(self):
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        info_frame.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(info_frame, text="🎵 翻唱流程说明", font=("Segoe UI Semibold", 13),
                     text_color=COLORS["accent_secondary"]).pack(anchor="w", padx=14, pady=(12, 6))

        steps = [
            "1️⃣  上传或输入参考音频 URL",
            "2️⃣  点击「预处理」提取音频特征和歌词",
            "3️⃣  编辑歌词 / 设置翻唱风格参数",
            "4️⃣  点击「生成翻唱」获得翻唱作品",
        ]
        for step in steps:
            ctk.CTkLabel(info_frame, text=step, font=("Segoe UI", 11),
                         text_color=COLORS["text_secondary"], anchor="w"
                         ).pack(fill="x", padx=14, pady=1)
        ctk.CTkLabel(info_frame, text="", height=6).pack()

    # ──────────────── 音频上传 ────────────────
    def _build_audio_upload_section(self):
        ctk.CTkLabel(self, text="▎步骤1: 参考音频", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_primary"], anchor="w").pack(fill="x", pady=(0, 10))

        # 音频来源选择 - 使用 SegmentedButton 切换
        source_row = ctk.CTkFrame(self, fg_color="transparent")
        source_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(source_row, text="音频来源", font=("Segoe UI", 11),
                     text_color=COLORS["text_muted"]).pack(side="left")
        self.audio_source_var = tk.StringVar(value="URL")
        self.source_seg = ctk.CTkSegmentedButton(
            source_row, values=["URL", "本地文件"],
            variable=self.audio_source_var, font=("Segoe UI", 11),
            selected_color=COLORS["accent_primary"], selected_hover_color=COLORS["accent_primary"],
            unselected_color=COLORS["bg_hover"], unselected_hover_color=COLORS["border"],
            command=self._on_source_change
        )
        self.source_seg.pack(side="right")

        # ── 音频输入容器 ──
        self.audio_input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.audio_input_frame.pack(fill="x", pady=(0, 8))

        # URL 输入行
        self.url_row = ctk.CTkFrame(self.audio_input_frame, fg_color="transparent")
        self.url_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(self.url_row, text="🔗", font=("Segoe UI", 13)).pack(side="left", padx=(0, 6))
        self.audio_url_entry = ctk.CTkEntry(
            self.url_row, height=38, corner_radius=8, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="输入参考音频的 URL 地址（mp3/wav/flac）"
        )
        self.audio_url_entry.pack(side="left", fill="both", expand=True)

        # 本地文件行 (初始隐藏)
        self.file_row = ctk.CTkFrame(self.audio_input_frame, fg_color="transparent")
        # 不 pack，默认显示 URL

        self.file_info_label = ctk.CTkLabel(self.file_row, text="📂", font=("Segoe UI", 13))
        self.file_info_label.pack(side="left", padx=(0, 6))
        self.file_path_entry = ctk.CTkEntry(
            self.file_row, height=38, corner_radius=8, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="选择本地音频文件..."
        )
        self.file_path_entry.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkButton(
            self.file_row, text="浏览", width=60, height=38, corner_radius=8,
            font=("Segoe UI", 11), fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent_primary"], text_color=COLORS["text_primary"],
            command=self._browse_audio_file
        ).pack(side="right")

        # 文件信息展示行 (初始隐藏)
        self.file_detail_frame = ctk.CTkFrame(self.audio_input_frame, fg_color=COLORS["bg_input"], corner_radius=8)
        self.file_detail_label = ctk.CTkLabel(
            self.file_detail_frame, text="", font=("Segoe UI", 10),
            text_color=COLORS["text_muted"], anchor="w"
        )
        self.file_detail_label.pack(fill="x", padx=10, pady=6)

        # 音频要求提示
        hint = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=6)
        hint.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(hint, text="💡 音频要求: 时长 6秒~6分钟 | 最大 50MB | 格式 mp3/wav/flac",
                     font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(padx=10, pady=6)

    # ──────────────── 翻唱前处理 ────────────────
    def _build_preprocess_section(self):
        ctk.CTkLabel(self, text="▎步骤2: 翻唱前处理", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_warning"], anchor="w").pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(
            self,
            text="预处理将提取音频特征、歌词及歌曲结构，cover_feature_id 有效期 24 小时",
            font=("Segoe UI", 10), text_color=COLORS["text_muted"], anchor="w"
        ).pack(fill="x", pady=(0, 8))

        preprocess_btn_row = ctk.CTkFrame(self, fg_color="transparent")
        preprocess_btn_row.pack(fill="x", pady=(0, 10))
        self.preprocess_btn = GlowButton(
            preprocess_btn_row, text="🔧 开始预处理", glow_color=COLORS["accent_warning"],
            fg_color=COLORS["accent_warning"], text_color="#000000", height=38,
            command=self._run_preprocess
        )
        self.preprocess_btn.pack(side="left")
        self.preprocess_status = ctk.CTkLabel(
            preprocess_btn_row, text="", font=("Segoe UI", 11),
            text_color=COLORS["text_muted"]
        )
        self.preprocess_status.pack(side="left", padx=(12, 0))

        # 预处理结果展示
        result_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8)
        result_frame.pack(fill="x", pady=(0, 16))
        result_header = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(result_header, text="📋 预处理结果", font=("Segoe UI Semibold", 11),
                     text_color=COLORS["accent_warning"]).pack(side="left")
        self.feature_id_label = ctk.CTkLabel(
            result_header, text="feature_id: (未获取)", font=("Consolas", 10),
            text_color=COLORS["text_muted"]
        )
        self.feature_id_label.pack(side="right")

        self.preprocess_result_text = ctk.CTkTextbox(
            result_frame, height=80, corner_radius=6, font=("Consolas", 10),
            fg_color=COLORS["bg_dark"], border_width=0,
            text_color=COLORS["text_secondary"], wrap=tk.WORD, state="disabled"
        )
        self.preprocess_result_text.pack(fill="x", padx=8, pady=(0, 10))

    # ──────────────── 歌词编辑 & 参数 ────────────────
    def _build_lyrics_and_params_section(self):
        # 翻唱风格
        ctk.CTkLabel(self, text="▎步骤3: 翻唱设置", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_success"], anchor="w").pack(fill="x", pady=(4, 10))

        # 风格标签 + AI按钮
        style_header = ctk.CTkFrame(self, fg_color="transparent")
        style_header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(style_header, text="🎵 翻唱风格描述 (必填, 10-300字)", font=("Segoe UI Semibold", 12),
                     text_color=COLORS["accent_primary"]).pack(side="left")
        self.ai_style_btn = GlowButton(
            style_header, text="🤖 AI 推荐风格", glow_color=COLORS["accent_secondary"],
            fg_color=COLORS["accent_secondary"], text_color="#ffffff",
            height=30, width=130, font=("Segoe UI", 11),
            command=self._recommend_styles
        )
        self.ai_style_btn.pack(side="right")

        self.cover_prompt_text = ctk.CTkTextbox(
            self, height=80, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["accent_primary"],
            border_width=1, text_color=COLORS["text_primary"], wrap=tk.WORD
        )
        self.cover_prompt_text.insert("1.0", "爵士风格,慵懒,酒吧氛围,萨克斯,低沉男声")
        self.cover_prompt_text.pack(fill="x", pady=(0, 8))

        # AI 推荐风格卡片容器（初始隐藏）
        self.style_cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        # 不 pack，等有推荐结果再显示

        # 歌词编辑
        lyrics_header = ctk.CTkFrame(self, fg_color="transparent")
        lyrics_header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(lyrics_header, text="📝 歌词内容 (可编辑预处理提取的歌词)", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        ctk.CTkLabel(lyrics_header, text="10-1000字", font=("Segoe UI", 10),
                     text_color=COLORS["text_muted"]).pack(side="right")

        self.lyrics_text = ctk.CTkTextbox(
            self, height=200, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"], wrap=tk.WORD
        )
        self.lyrics_text.pack(fill="x", pady=(0, 14))

        # 高级参数
        ctk.CTkLabel(self, text="▎高级参数", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_secondary"], anchor="w").pack(fill="x", pady=(4, 10))

        # 模型选择
        model_row = ctk.CTkFrame(self, fg_color="transparent")
        model_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(model_row, text="模型版本", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.model_var = tk.StringVar(value="music-cover")
        ctk.CTkOptionMenu(
            model_row, values=["music-cover", "music-cover-free"],
            variable=self.model_var, width=180, height=32, corner_radius=6,
            font=("Segoe UI", 11), fg_color=COLORS["bg_input"],
            button_color=COLORS["bg_hover"], button_hover_color=COLORS["accent_primary"],
            dropdown_fg_color=COLORS["bg_card"], text_color=COLORS["text_primary"]
        ).pack(side="right")

        # 音频设置
        audio_settings = ctk.CTkFrame(self, fg_color="transparent")
        audio_settings.pack(fill="x", pady=(0, 12))

        sr_col = ctk.CTkFrame(audio_settings, fg_color="transparent")
        sr_col.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(sr_col, text="采样率 (Hz)", font=("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.sample_rate_var = tk.StringVar(value="44100")
        ctk.CTkOptionMenu(
            sr_col, values=["44100", "48000"], variable=self.sample_rate_var,
            height=32, corner_radius=6, font=("Segoe UI", 11),
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"]
        ).pack(fill="x", pady=(4, 0))

        br_col = ctk.CTkFrame(audio_settings, fg_color="transparent")
        br_col.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ctk.CTkLabel(br_col, text="比特率 (bps)", font=("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.bitrate_var = tk.StringVar(value="256000")
        ctk.CTkOptionMenu(
            br_col, values=["128000", "192000", "256000", "320000"],
            variable=self.bitrate_var, height=32, corner_radius=6,
            font=("Segoe UI", 11), fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"]
        ).pack(fill="x", pady=(4, 0))

        # 输出格式
        fmt_row = ctk.CTkFrame(self, fg_color="transparent")
        fmt_row.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(fmt_row, text="输出格式", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.format_var = tk.StringVar(value="mp3")
        ctk.CTkOptionMenu(
            fmt_row, values=["mp3", "wav", "flac"], variable=self.format_var,
            width=140, height=32, corner_radius=6, font=("Segoe UI", 11),
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"]
        ).pack(side="right")

    # ──────────────── 事件处理 ────────────────
    def _on_source_change(self, value):
        """切换音频来源: URL / 本地文件"""
        if value == "URL":
            self.file_row.pack_forget()
            self.file_detail_frame.pack_forget()
            self.url_row.pack(fill="x", pady=(0, 4))
        else:
            self.url_row.pack_forget()
            self.file_row.pack(fill="x", pady=(0, 4))
            # 如果已有文件路径，显示详情
            path = self.file_path_entry.get().strip()
            if path:
                self._show_file_detail(path)

    def _browse_audio_file(self):
        """浏览选择本地音频文件"""
        file_path = filedialog.askopenfilename(
            title="选择参考音频",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a"),
                ("MP3 文件", "*.mp3"),
                ("WAV 文件", "*.wav"),
                ("FLAC 文件", "*.flac"),
                ("所有文件", "*.*"),
            ]
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self._show_file_detail(file_path)

    def _show_file_detail(self, file_path: str):
        """展示本地文件详情（大小、格式、base64 转换状态）"""
        try:
            p = Path(file_path)
            if not p.exists():
                self.file_detail_label.configure(text="❌ 文件不存在", text_color=COLORS["accent_error"])
                self.file_detail_frame.pack(fill="x", pady=(4, 0))
                return

            size_bytes = p.stat().st_size
            ext = p.suffix.lower()
            size_mb = size_bytes / (1024 * 1024)

            # 检查大小限制
            if size_mb > 50:
                detail = f"❌ {p.name} | {size_mb:.1f} MB — 超过 50MB 限制！"
                self.file_detail_label.configure(text=detail, text_color=COLORS["accent_error"])
            else:
                detail = f"✅ {p.name} | {size_mb:.1f} MB | {ext} — 将转为 Base64 上传"
                self.file_detail_label.configure(text=detail, text_color=COLORS["accent_success"])

            self.file_detail_frame.pack(fill="x", pady=(4, 0))

        except Exception as e:
            self.file_detail_label.configure(text=f"❌ 读取失败: {e}", text_color=COLORS["accent_error"])
            self.file_detail_frame.pack(fill="x", pady=(4, 0))

    def _get_audio_source(self) -> dict:
        """获取音频来源参数，返回 {'audio_url': ...} 或 {'audio_base64': ...}"""
        if self.audio_source_var.get() == "URL":
            url = self.audio_url_entry.get().strip()
            if not url:
                return {"error": "请输入音频 URL！"}
            return {"audio_url": url}
        else:
            file_path = self.file_path_entry.get().strip()
            if not file_path:
                return {"error": "请选择本地音频文件！"}
            try:
                p = Path(file_path)
                if not p.exists():
                    return {"error": "文件不存在！"}
                size_bytes = p.stat().st_size
                if size_bytes > 50 * 1024 * 1024:
                    return {"error": f"音频文件超过 50MB 限制！({size_bytes / (1024*1024):.1f} MB)"}

                # 读取并转为 base64
                self.log_callback(f"📂 读取本地文件: {p.name} ({size_bytes / (1024*1024):.1f} MB)", "info")
                self.log_callback("🔄 正在转换为 Base64 编码...", "info")

                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
                b64 = base64.b64encode(audio_bytes).decode("utf-8")

                self.log_callback(f"✅ Base64 编码完成 (编码后 {len(b64) / 1024:.0f} KB)", "success")
                return {"audio_base64": b64}
            except Exception as e:
                return {"error": f"读取文件失败: {e}"}

    # ──────────────── 预处理 ────────────────
    def _run_preprocess(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        source = self._get_audio_source()
        if "error" in source:
            messagebox.showwarning("提示", source["error"])
            return

        self.preprocess_btn.configure(state="disabled", text="⏳ 预处理中...")
        self.preprocess_status.configure(text="正在提取音频特征...", text_color=COLORS["accent_primary"])
        self.log_callback("🔧 开始翻唱前处理...", "info")

        thread = threading.Thread(target=self._call_preprocess_api, args=(api_key, source), daemon=True)
        thread.start()

    def _call_preprocess_api(self, api_key: str, source: dict):
        try:
            api = MiniMaxAPI(api_key)
            result = api.cover_preprocess(
                audio_url=source.get("audio_url"),
                audio_base64=source.get("audio_base64")
            )
            self.after(0, lambda r=result: self._handle_preprocess_result(r))
        except Exception as e:
            self.after(0, lambda err=str(e): self._preprocess_error(f"预处理请求失败: {err}"))

    def _handle_preprocess_result(self, result: dict):
        self.log_callback("-" * 50, "muted")
        self.log_callback(json.dumps(result, ensure_ascii=False, indent=2), "info")
        self.log_callback("-" * 50, "muted")

        # 检查错误
        if "error" in result:
            self._preprocess_error(result["error"])
            return

        base_resp = result.get("base_resp", {})
        status_code = base_resp.get("status_code", -1)
        if status_code != 0:
            msg = base_resp.get("status_msg", "未知错误")
            self._preprocess_error(f"API 错误 [{status_code}]: {msg}")
            return

        # 提取关键信息
        feature_id = result.get("cover_feature_id", "")
        formatted_lyrics = result.get("formatted_lyrics", "")
        structure_result = result.get("structure_result", "")
        audio_duration = result.get("audio_duration", 0)

        if not feature_id:
            self._preprocess_error("未获取到 cover_feature_id")
            return

        self.cover_feature_id = feature_id
        self.audio_duration = audio_duration

        # 更新 UI
        self.preprocess_btn.configure(state="normal", text="🔧 开始预处理")
        self.preprocess_status.configure(text="✅ 预处理完成", text_color=COLORS["accent_success"])
        self.feature_id_label.configure(
            text=f"feature_id: {feature_id[:20]}...",
            text_color=COLORS["accent_success"]
        )

        # 显示预处理结果
        duration_str = f"时长: {audio_duration:.1f}s" if audio_duration else ""
        structure_info = ""
        if structure_result:
            try:
                structure = json.loads(structure_result)
                num_seg = structure.get("num_segments", 0)
                labels = [s.get("label", "") for s in structure.get("segments", [])]
                structure_info = f"\n段落: {num_seg} 个 ({' → '.join(labels)})"
            except (json.JSONDecodeError, TypeError):
                pass

        preview_text = f"✅ cover_feature_id 已获取{f' ({duration_str})' if duration_str else ''}{structure_info}"
        self._update_preprocess_preview(preview_text)

        # 填充歌词
        if formatted_lyrics:
            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", formatted_lyrics)
            self.log_callback(f"📝 已提取歌词 ({len(formatted_lyrics)} 字)，可编辑后用于翻唱生成", "accent")

        self.log_callback(f"✅ 预处理完成! cover_feature_id: {feature_id[:20]}...", "success")
        self.log_callback("💡 可在下方编辑歌词，然后点击「生成翻唱」", "info")

    def _preprocess_error(self, message: str):
        self.preprocess_btn.configure(state="normal", text="🔧 开始预处理")
        self.preprocess_status.configure(text="❌ 预处理失败", text_color=COLORS["accent_error"])
        self._update_preprocess_preview(f"❌ 错误: {message}")
        self.log_callback(f"❌ 翻唱预处理失败: {message}", "error")

    def _update_preprocess_preview(self, text: str):
        self.preprocess_result_text.configure(state="normal")
        self.preprocess_result_text.delete("1.0", tk.END)
        self.preprocess_result_text.insert("1.0", text)
        self.preprocess_result_text.configure(state="disabled")

    # ──────────────── 翻唱生成 ────────────────
    def _generate_cover(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        prompt = self.cover_prompt_text.get("1.0", tk.END).strip()
        if not prompt or len(prompt) < 10:
            messagebox.showwarning("提示", "翻唱风格描述必填，且至少10个字符！")
            return

        lyrics = self.lyrics_text.get("1.0", tk.END).strip()

        # 判断翻唱模式
        if self.cover_feature_id:
            # 两步翻唱模式
            if not lyrics or len(lyrics) < 10:
                messagebox.showwarning("提示", "使用 cover_feature_id 翻唱时，歌词必填且至少10个字符！")
                return
            mode_desc = "两步翻唱 (cover_feature_id)"
        else:
            # 一步翻唱模式
            source = self._get_audio_source()
            if "error" in source:
                messagebox.showwarning("提示", source["error"])
                return
            mode_desc = "一步翻唱 (直接传入音频)"

        self.generate_btn.configure(state="disabled", text="⏳ 生成中...")
        self.log_callback(f"🎤 开始翻唱生成 ({mode_desc})...", "info")
        self.log_callback(f"模型: {self.model_var.get()} | 风格: {prompt[:50]}", "accent")

        params = {
            "api_key": api_key,
            "prompt": prompt,
            "lyrics": lyrics,
            "model": self.model_var.get(),
            "sample_rate": int(self.sample_rate_var.get()),
            "bitrate": int(self.bitrate_var.get()),
            "format": self.format_var.get(),
        }

        if self.cover_feature_id:
            params["cover_feature_id"] = self.cover_feature_id
        else:
            params.update(self._get_audio_source())

        thread = threading.Thread(target=self._call_cover_api, args=(params,), daemon=True)
        thread.start()

    def _call_cover_api(self, params: dict):
        try:
            api = MiniMaxAPI(params.pop("api_key"))
            result = api.generate_cover(
                prompt=params["prompt"],
                model=params["model"],
                cover_feature_id=params.get("cover_feature_id"),
                audio_url=params.get("audio_url"),
                audio_base64=params.get("audio_base64"),
                lyrics=params.get("lyrics", ""),
                sample_rate=params["sample_rate"],
                bitrate=params["bitrate"],
                output_format=params["format"]
            )
            self.after(0, lambda r=result: self._handle_cover_result(r))
        except requests.exceptions.Timeout:
            self.after(0, lambda: (
                self.log_callback("❌ 翻唱生成超时，服务器处理时间过长，请稍后重试", "error"),
                self._reset_button()
            ))
        except Exception as e:
            self.after(0, lambda err=str(e): (
                self.log_callback(f"翻唱生成失败: {err}", "error"),
                self._reset_button()
            ))

    def _handle_cover_result(self, result: dict):
        self.log_callback("-" * 50, "muted")
        self.log_callback(json.dumps(result, ensure_ascii=False, indent=2), "info")
        self.log_callback("-" * 50, "muted")

        if isinstance(result, dict):
            base_resp = result.get("base_resp", {})
            status_code = base_resp.get("status_code", -1)

            if "data" in result and result["data"]:
                audio = result["data"].get("audio") or result["data"].get("audio_url") or result["data"].get("url")
                if audio:
                    self.log_callback("\n✅ 翻唱生成成功！", "success")
                    self._download_audio(audio, result)
                elif status_code != 0:
                    msg = base_resp.get("status_msg", "未知错误")
                    self.log_callback(f"❌ API 错误 [{status_code}]: {msg}", "error")
                else:
                    self.log_callback("⚠️ 未获取到音频数据", "warning")
            elif status_code != 0:
                msg = base_resp.get("status_msg", "未知错误")
                self.log_callback(f"❌ API 错误 [{status_code}]: {msg}", "error")
            else:
                self.log_callback("⚠️ 响应格式异常", "warning")

        self._reset_button()

    def _download_audio(self, url: str, api_result: dict = None):
        save_dir = Path(self.save_dir_var.get())
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = ".wav" if "wav" in url.lower() else ".flac" if "flac" in url.lower() else ".mp3"
        audio_filename = f"cover_{timestamp}{ext}"
        save_path = save_dir / audio_filename

        try:
            self.log_callback(f"📥 正在下载翻唱音频到: {save_path}", "info")
            urllib.request.urlretrieve(url, str(save_path))
            self.log_callback(f"✅ 翻唱音频已保存: {audio_filename}", "success")

            # 保存歌词
            lyrics_content = self.lyrics_text.get("1.0", tk.END).strip()
            if lyrics_content:
                lyrics_filename = f"cover_{timestamp}.txt"
                (save_dir / lyrics_filename).write_text(lyrics_content, encoding="utf-8")
                self.log_callback(f"✅ 歌词已保存: {lyrics_filename}", "success")

            # 保存元数据
            meta_data = {
                "type": "cover",
                "generated_at": datetime.datetime.now().isoformat(),
                "filename": audio_filename,
                "prompt": self.cover_prompt_text.get("1.0", tk.END).strip(),
                "model": self.model_var.get(),
                "cover_feature_id": self.cover_feature_id,
                "has_lyrics": bool(lyrics_content)
            }
            if api_result and api_result.get("extra_info"):
                meta_data["audio_info"] = api_result["extra_info"]
            meta_filename = f"cover_{timestamp}_meta.json"
            (save_dir / meta_filename).write_text(
                json.dumps(meta_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self.log_callback(f"✅ 元数据已保存: {meta_filename}", "accent")

        except Exception as e:
            self.log_callback(f"下载失败: {e}", "error")

    def _reset_button(self):
        self.generate_btn.configure(state="normal", text="🎤 生成翻唱")

    # ──────────────── AI 风格推荐 ────────────────
    def _recommend_styles(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        self.ai_style_btn.configure(state="disabled", text="⏳ AI 生成中...")
        self.log_callback("🤖 正在调用 AI 推荐翻唱风格...", "info")

        thread = threading.Thread(target=self._call_recommend_api, args=(api_key,), daemon=True)
        thread.start()

    def _call_recommend_api(self, api_key: str):
        try:
            api = MiniMaxAPI(api_key)
            result = api.recommend_cover_styles()
            self.after(0, lambda r=result: self._handle_recommend_result(r))
        except Exception as e:
            self.after(0, lambda err=str(e): self._recommend_error(f"推荐失败: {err}"))

    def _handle_recommend_result(self, result: dict):
        self.ai_style_btn.configure(state="normal", text="🤖 AI 推荐风格")

        if "error" in result:
            self._recommend_error(result["error"])
            return

        styles = result.get("styles", [])
        if not styles:
            self._recommend_error("未获取到推荐风格")
            return

        self.log_callback(f"✅ 获取到 {len(styles)} 种推荐风格", "success")

        # 清空并重建卡片
        for widget in self.style_cards_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.style_cards_frame,
            text="✨ AI 推荐风格（点击选择）",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["accent_secondary"], anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # 卡片网格: 2列 x 3行
        grid_frame = ctk.CTkFrame(self.style_cards_frame, fg_color="transparent")
        grid_frame.pack(fill="x")

        for i, style in enumerate(styles):
            row, col = divmod(i, 2)
            card = self._create_style_card(grid_frame, style)
            card.grid(row=row, column=col, padx=(0, 6), pady=(0, 6), sticky="nsew")

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # 插入到风格输入框后面
        self.style_cards_frame.pack(fill="x", pady=(0, 14), after=self.cover_prompt_text)

    def _create_style_card(self, parent, style: dict) -> ctk.CTkFrame:
        """创建单个风格推荐卡片"""
        name = style.get("name", "未知")
        emoji = style.get("emoji", "🎵")
        prompt = style.get("prompt", "")
        desc = style.get("desc", "")

        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=10,
                             border_width=1, border_color=COLORS["border"],
                             cursor="hand2")
        card.pack_propagate(True)

        # 顶部: emoji + 名称
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(top_row, text=f"{emoji} {name}", font=("Segoe UI Semibold", 12),
                     text_color=COLORS["accent_primary"]).pack(side="left")

        # 描述
        ctk.CTkLabel(card, text=desc, font=("Segoe UI", 10),
                     text_color=COLORS["text_muted"], anchor="w", wraplength=240
                     ).pack(fill="x", padx=10, pady=(0, 4))

        # prompt 预览（截断显示）
        prompt_preview = prompt if len(prompt) <= 60 else prompt[:57] + "..."
        ctk.CTkLabel(card, text=prompt_preview, font=("Consolas", 9),
                     text_color=COLORS["text_secondary"], anchor="w", wraplength=240
                     ).pack(fill="x", padx=10, pady=(0, 8))

        # 点击选中效果
        def on_click(event=None):
            self.cover_prompt_text.delete("1.0", tk.END)
            self.cover_prompt_text.insert("1.0", prompt)
            self.log_callback(f"🎨 已选择风格: {emoji} {name}", "accent")

            # 高亮选中卡片
            for w in parent.winfo_children():
                w.configure(border_color=COLORS["border"])
            card.configure(border_color=COLORS["accent_primary"])

        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)

        return card

    def _recommend_error(self, message: str):
        self.ai_style_btn.configure(state="normal", text="🤖 AI 推荐风格")
        self.log_callback(f"❌ 风格推荐失败: {message}", "error")
        self.style_cards_frame.pack_forget()
