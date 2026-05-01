"""
音乐生成模块
"""

import re
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import datetime
import urllib.request
from pathlib import Path
import json

import customtkinter as ctk

from src.config import COLORS
from src.ui.components import GlowButton
from src.api.minimax import MiniMaxAPI


class MusicGenerator:
    """音乐生成器"""

    def __init__(self, api_key_var, log_callback):
        self.api_key_var = api_key_var
        self.log_callback = log_callback

    def generate(self, model: str, prompt: str, lyrics: str = "",
                 sample_rate: int = 44100, bitrate: int = 256000,
                 output_format: str = "mp3") -> dict:
        """
        生成音乐

        Returns:
            API 响应结果
        """
        api_key = self.api_key_var.get().strip()
        if not api_key:
            return {"error": "请先输入 API Key！"}

        try:
            api = MiniMaxAPI(api_key)
            return api.generate_music(model, prompt, lyrics, sample_rate, bitrate, output_format)
        except Exception as e:
            return {"error": str(e)}

    def download_and_save(self, url: str, save_dir: Path, title: str,
                          lyrics: str = "", prompt: str = "", model: str = "") -> dict:
        """下载并保存音频"""
        try:
            save_dir.mkdir(parents=True, exist_ok=True)

            # 确定文件扩展名
            ext = ".wav" if "wav" in url.lower() else ".flac" if "flac" in url.lower() else ".mp3"

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_prefix = self._sanitize_filename(title) if title else "music"
            audio_filename = f"{file_prefix}_{timestamp}{ext}"
            save_path = save_dir / audio_filename

            # 下载音频
            urllib.request.urlretrieve(url, str(save_path))

            # 保存歌词
            if lyrics:
                lyrics_filename = f"{file_prefix}_{timestamp}.txt"
                (save_dir / lyrics_filename).write_text(lyrics, encoding="utf-8")

            # 保存元数据
            meta_data = {
                "generated_at": datetime.datetime.now().isoformat(),
                "filename": audio_filename,
                "prompt": prompt,
                "model": model,
                "has_lyrics": bool(lyrics)
            }
            meta_filename = f"{file_prefix}_{timestamp}_meta.json"
            (save_dir / meta_filename).write_text(
                json.dumps(meta_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            return {"success": True, "path": save_path, "filename": audio_filename}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        name = re.sub(r'_+', '_', name)
        return name[:60] or "unnamed"


class MusicTab(ctk.CTkScrollableFrame):
    """音乐生成标签页 UI"""

    def __init__(self, parent, api_key_var, log_callback):
        super().__init__(parent, fg_color="transparent", scrollbar_button_color=COLORS["accent_primary"], scrollbar_button_hover_color=COLORS["accent_secondary"])
        self.api_key_var = api_key_var
        self.log_callback = log_callback
        self.music_generator = MusicGenerator(api_key_var, log_callback)
        self.save_dir_var = tk.StringVar(value="D:/AIMusicData")
        self.current_title = ""
        self._build_ui()

    def _build_ui(self):
        # 歌曲智能分析区
        self._build_analysis_section()

        # 基础参数区
        self._build_basic_params_section()

        # AI 歌词生成区
        self._build_lyrics_section()

        # 高级参数区
        self._build_advanced_params_section()

        # 歌曲名称输入
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(title_row, text="🎼 歌曲名称", font=("Segoe UI", 11),
                     text_color=COLORS["accent_warning"]).pack(side="left", anchor="w")
        self.title_entry = ctk.CTkEntry(
            title_row, height=34, corner_radius=6, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color="#f59e0b",
            border_width=1, text_color=COLORS["accent_primary"],
            placeholder_text="歌词生成后自动填入，也可手动输入（用于文件命名）")
        self.title_entry.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # 生成按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))
        self.generate_btn = GlowButton(
            btn_frame, text="🚀 生成音乐", glow_color=COLORS["accent_primary"],
            fg_color=COLORS["accent_primary"], text_color="#000000", height=46,
            command=self._generate_music
        )
        self.generate_btn.pack(fill="x")

    def _build_analysis_section(self):
        """构建歌曲分析区域"""
        ctk.CTkLabel(self, text="▎🎵 歌曲智能分析", font=("Segoe UI Semibold", 14),
                     text_color="#f59e0b", anchor="w").pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            self, text="输入歌曲名和作者，AI 将分析歌曲特征并自动填充到下方参数中",
            font=("Segoe UI", 10), text_color=COLORS["text_muted"], anchor="w"
        ).pack(fill="x", pady=(0, 10))

        song_row1 = ctk.CTkFrame(self, fg_color="transparent")
        song_row1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(song_row1, text="🎤 歌曲名", font=("Segoe UI", 11),
                     text_color=COLORS["text_secondary"], width=70
                     ).pack(side="left", anchor="w")
        self.song_name_entry = ctk.CTkEntry(
            song_row1, height=36, corner_radius=6, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="例如: ilysb / through it all..."
        )
        self.song_name_entry.pack(side="left", fill="both", expand=True, padx=(4, 8))

        ctk.CTkLabel(song_row1, text="👤 作者/歌手", font=("Segoe UI", 11),
                     text_color=COLORS["text_secondary"], width=80
                     ).pack(side="left", anchor="w")
        self.song_artist_entry = ctk.CTkEntry(
            song_row1, height=36, corner_radius=6, font=("Segoe UI", 12),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"],
            placeholder_text="例如: LANY / Taylor Swift..."
        )
        self.song_artist_entry.pack(side="left", fill="both", expand=True, padx=(4, 0))

        analyze_btn_row = ctk.CTkFrame(self, fg_color="transparent")
        analyze_btn_row.pack(fill="x", pady=(0, 12))
        self.analyze_song_btn = GlowButton(
            analyze_btn_row, text="🔍 AI 分析歌曲特征", glow_color="#f59e0b",
            fg_color="#f59e0b", text_color="#000000", height=38,
            command=self._analyze_song
        )
        self.analyze_song_btn.pack(side="left")

        # 分析结果预览
        result_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8)
        result_frame.pack(fill="x", pady=(0, 16))
        result_header = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(result_header, text="📋 分析结果预览", font=("Segoe UI Semibold", 11),
                     text_color=COLORS["accent_warning"]).pack(side="left")
        self.analysis_status_label = ctk.CTkLabel(
            result_header, text="(等待分析)", font=("Segoe UI", 10),
            text_color=COLORS["text_muted"]
        )
        self.analysis_status_label.pack(side="right")
        self.analysis_result_text = ctk.CTkTextbox(
            result_frame, height=100, corner_radius=6, font=("Consolas", 10),
            fg_color=COLORS["bg_dark"], border_width=0,
            text_color=COLORS["text_secondary"], wrap=tk.WORD, state="disabled"
        )
        self.analysis_result_text.pack(fill="x", padx=8, pady=(0, 10))

    def _build_basic_params_section(self):
        """构建基础参数区域"""
        ctk.CTkLabel(self, text="▎基础参数", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_primary"], anchor="w").pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(self, text="🎵 音乐风格提示词", font=("Segoe UI Semibold", 12),
                     text_color=COLORS["accent_primary"], anchor="w").pack(fill="x", pady=(0, 6))
        self.prompt_text = ctk.CTkTextbox(
            self, height=180, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color="#00d4ff",
            border_width=1, text_color=COLORS["text_primary"], wrap=tk.WORD
        )
        self.prompt_text.insert("1.0", "流行 英文 男生 含贝斯和吉他 BPM:89")
        self.prompt_text.pack(fill="x", pady=(0, 14))

    def _build_lyrics_section(self):
        """构建歌词区域"""
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

        ctk.CTkLabel(self, text="歌词内容（可手动编辑或由 AI 生成）", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 6))
        self.lyrics_text = ctk.CTkTextbox(
            self, height=220, corner_radius=6, font=("Consolas", 11),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text_primary"], wrap=tk.WORD
        )
        self.lyrics_text.pack(fill="x", pady=(0, 14))

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

    def _build_advanced_params_section(self):
        """构建高级参数区域"""
        ctk.CTkLabel(self, text="▎高级参数", font=("Segoe UI Semibold", 14),
                     text_color=COLORS["accent_secondary"], anchor="w").pack(fill="x", pady=(4, 12))

        # 模型选择
        model_row = ctk.CTkFrame(self, fg_color="transparent")
        model_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(model_row, text="模型版本", font=("Segoe UI", 12),
                     text_color=COLORS["text_secondary"]).pack(side="left", anchor="w")
        self.model_var = tk.StringVar(value="music-2.6")
        ctk.CTkOptionMenu(
            model_row, values=["music-2.5", "music-2.6", "music-01-preview"],
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

    def _analyze_song(self):
        """分析歌曲"""
        from src.api.minimax import SongAnalyzer

        song_name = self.song_name_entry.get().strip()
        artist = self.song_artist_entry.get().strip()
        if not song_name:
            messagebox.showwarning("提示", "请输入歌曲名！")
            return
        if not artist:
            artist = "未知作者"

        self.analyze_song_btn.configure(state="disabled", text="⏳ Agent 分析中...")
        self.analysis_status_label.configure(text="Agent 运行中...", text_color=COLORS["accent_primary"])
        self._update_analysis_preview("🤖 Agent 正在工作...\n\n请稍候...")

        self.log_callback(f"🎵 开始 Agent 分析: 《{song_name}》 - {artist}", "info")
        self.log_callback("🤖 模型: MiniMax-M2.5 | 🔍 联网工具: DuckDuckGo", "accent")

        thread = threading.Thread(target=self._run_analysis, args=(song_name, artist), daemon=True)
        thread.start()

    def _run_analysis(self, song_name: str, artist: str):
        try:
            from src.api.minimax import SongAnalyzer

            analyzer = SongAnalyzer()
            result_text = analyzer.analyze(song_name, artist)

            self.after(0, lambda: self.log_callback("✅ Agent 执行完成", "success"))

            if result_text and len(result_text.strip()) > 10:
                self.after(0, lambda r=result_text: self._handle_analysis_success(r))
            else:
                self.after(0, lambda: self._analysis_error("Agent 未返回有效结果"))

        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            self.after(0, lambda m=missing: self._analysis_error(f"缺少依赖: {m}"))
        except Exception as e:
            self.after(0, lambda err=str(e): self._analysis_error(f"Agent 运行失败: {err}"))

    def _handle_analysis_success(self, result_text: str):
        self.analyze_song_btn.configure(state="normal", text="🔍 AI 分析歌曲特征")
        self.log_callback("\n🎉 歌曲分析完成！", "success")
        self.analysis_status_label.configure(text="✅ 分析完成", text_color=COLORS["accent_success"])
        self._update_analysis_preview(result_text)

        # 解析并填充参数
        extracted = self._parse_analysis_to_params(result_text)
        if extracted:
            fill_parts = []
            if extracted.get("prompt"):
                fill_parts.append(extracted["prompt"])
            if extracted.get("detail"):
                fill_parts.append(extracted["detail"])
            if fill_parts:
                self.prompt_text.delete("1.0", tk.END)
                self.prompt_text.insert("1.0", "\n".join(fill_parts))
                self.log_callback(f"\n📝 已自动填充提示词: {fill_parts[0]}", "accent")
            if extracted.get("bpm"):
                self.log_callback(f"🥁 检测到 BPM: {extracted['bpm']}", "info")
            if extracted.get("style"):
                self.log_callback(f"🎸 曲风: {extracted['style']}", "info")
            self.log_callback("💡 参数已填充到基础参数区域！", "success")
        else:
            self.log_callback("⚠️ 已获取分析结果但未能自动解析参数", "warning")

    def _parse_analysis_to_params(self, text: str) -> dict:
        """解析分析结果为参数"""
        import re
        result = {}
        full_text = text

        # 提取 BPM
        bpm_match = re.search(r'BPM\s*(\d+)', full_text)
        if bpm_match:
            result["bpm"] = bpm_match.group(1)

        # 提取曲风
        for pat in [r'曲风[：:]\s*([^,\n]+)', r'风格[：:]\s*([^\n]+)']:
            m = re.search(pat, full_text)
            if m:
                result["style"] = m.group(1).strip()
                break

        # 提取生成提示词
        for pat in [r'音乐生成提示词[（(][^）)]*[）)][\s\n]*(.+?)', r'生成提示词[：:]?\s*\n?\s*(.+?)']:
            m = re.search(pat, full_text, re.DOTALL)
            if m:
                pc = m.group(1).strip().strip('"\'').strip()
                if len(pc) > 5:
                    result["prompt"] = pc
                    break

        if not result.get("prompt"):
            parts = []
            if result.get("style"):
                parts.append(result["style"])
            if result.get("bpm"):
                parts.append(f"BPM:{result['bpm']}")
            arrange_section = re.search(r'编曲.*特点[\s\S]*?(?=\n##|$)', full_text)
            if arrange_section:
                arr_text = arrange_section.group(0)
                instruments = [kw for kw in ["吉他", "钢琴", "贝斯", "鼓", "合成器"] if kw in arr_text]
                if instruments:
                    parts.append(f"含{'和'.join(instruments[:3])}")
            if parts:
                result["prompt"] = " ".join(parts)

        # 提取详情
        detail_parts = [l.strip() for l in text.split('\n')
                        if l.strip() and not l.strip().startswith('#')
                        and len(l.strip()) > 10 and not l.strip().startswith('---')]
        if detail_parts:
            result["detail"] = "\n".join(detail_parts)

        return result

    def _update_analysis_preview(self, text: str):
        self.analysis_result_text.configure(state="normal")
        self.analysis_result_text.delete("1.0", tk.END)
        self.analysis_result_text.insert("1.0", text)
        self.analysis_result_text.configure(state="disabled")

    def _analysis_error(self, message: str):
        self.analyze_song_btn.configure(state="normal", text="🔍 AI 分析歌曲特征")
        self.analysis_status_label.configure(text="❌ 分析失败", text_color=COLORS["accent_error"])
        self._update_analysis_preview(f"❌ 错误: {message}")
        self.log_callback(f"❌ 歌曲分析失败: {message}", "error")

    def _generate_lyrics(self):
        from src.api.minimax import MiniMaxAPI

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        prompt = self.lyrics_prompt_entry.get().strip() or "写一首关于爱情的中文流行歌曲歌词"
        mode_raw = self.lyrics_mode_var.get()
        mode_map = {"write_full_song(完整歌曲)": "write_full_song",
                    "write_verse(主歌段落)": "write_verse", "write_chorus(副歌段落)": "write_chorus"}
        mode = mode_map.get(mode_raw, "write_full_song")

        self.gen_lyrics_btn.configure(state="disabled", text="⏳ 生成中...")
        self.log_callback(f"正在调用 AI 歌词生成 API (模式: {mode})...", "info")
        self.log_callback(f"提示词: {prompt}", "accent")

        thread = threading.Thread(target=self._call_lyrics_api, args=(prompt, mode, api_key), daemon=True)
        thread.start()

    def _call_lyrics_api(self, prompt: str, mode: str, api_key: str):
        try:
            from src.api.minimax import MiniMaxAPI

            api = MiniMaxAPI(api_key)
            result = api.generate_lyrics(prompt, mode)
            self.after(0, lambda r=result: self._handle_lyrics_result(r))
        except Exception as e:
            self.after(0, lambda err=str(e): self.log_callback(f"歌词生成失败: {err}", "error"))
            self.after(0, lambda: self.gen_lyrics_btn.configure(state="normal", text="✍️ 生成"))

    def _handle_lyrics_result(self, result: dict):
        self.log_callback("-" * 50, "muted")
        self.log_callback(json.dumps(result, ensure_ascii=False, indent=2), "info")
        self.log_callback("-" * 50, "muted")

        lyrics_text = ""
        if isinstance(result, dict):
            if "data" in result and result["data"]:
                data = result["data"]
                lyrics_text = data.get("lyrics", "") or data.get("text", "") or data.get("content", "")
                if isinstance(data, str):
                    lyrics_text = data
            elif "base_resp" in result:
                sc = result["base_resp"].get("status_code")
                if sc != 0:
                    self.log_callback(f"❌ API 错误 [{sc}]: {result['base_resp'].get('status_msg', '未知')}", "error")
                    self.gen_lyrics_btn.configure(state="normal", text="✍️ 生成")
                    return

        if not lyrics_text:
            lyrics_text = result.get("lyrics", "") or result.get("text", "")

        if lyrics_text:
            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", lyrics_text)
            self.log_callback(f"\n✅ 歌词生成成功！(共 {len(lyrics_text)} 字)", "success")
            self.log_callback("📝 歌词已自动填入下方编辑框，可直接用于音乐生成", "accent")

            # 提取标题
            extracted_title = ""
            if isinstance(result, dict):
                d = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
                extracted_title = d.get("title") or d.get("song_title") or d.get("name") or ""
            if not extracted_title and isinstance(result, dict):
                extracted_title = result.get("title") or result.get("song_title") or ""
            if extracted_title:
                self.current_title = self._sanitize_filename(extracted_title)
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, self.current_title)
                self.log_callback(f"🎼 已提取歌曲标题: 「{self.current_title}」", "accent")
        else:
            self.log_callback("⚠️ 未获取到有效的歌词内容", "warning")

        self.gen_lyrics_btn.configure(state="normal", text="✍️ 生成")

    def _generate_music(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip() or "流行音乐"
        lyrics = self.lyrics_text.get("1.0", tk.END).strip()

        params = {
            "model": self.model_var.get(),
            "prompt": prompt,
            "lyrics": lyrics or "",
            "sample_rate": int(self.sample_rate_var.get()),
            "bitrate": int(self.bitrate_var.get()),
            "format": self.format_var.get()
        }

        self.generate_btn.configure(state="disabled", text="⏳ 生成中...")
        self.log_callback("正在调用 MiniMax 音乐生成 API...", "info")
        self.log_callback(f"模型: {params['model']} | 格式: {params['format']}", "accent")

        thread = threading.Thread(target=self._call_api, args=(params,), daemon=True)
        thread.start()

    def _call_api(self, params: dict):
        try:
            from src.api.minimax import MiniMaxAPI

            api_key = self.api_key_var.get().strip()
            api = MiniMaxAPI(api_key)
            result = api.generate_music(
                params["model"], params["prompt"], params["lyrics"],
                params["sample_rate"], params["bitrate"], params["format"]
            )
            self.after(0, lambda r=result: self._handle_result(r))
        except Exception as e:
            self.after(0, lambda err=str(e): (self.log_callback(f"请求失败: {err}", "error"),
                                              self._reset_button()))

    def _handle_result(self, result: dict):
        self.log_callback("-" * 50, "muted")
        self.log_callback(json.dumps(result, ensure_ascii=False, indent=2), "info")
        self.log_callback("-" * 50, "muted")

        if isinstance(result, dict):
            if "data" in result and result["data"]:
                audio_url = result["data"].get("audio") or result["data"].get("audio_url") or result["data"].get("url")
                if audio_url:
                    task_id = result["data"].get("task_id", "")
                    self.log_callback(f"\n✅ 音乐生成成功！链接: {audio_url[:60]}...", "success")
                    self._download_audio(audio_url, task_id, result)
                elif "base_resp" in result:
                    sc = result["base_resp"].get("status_code")
                    self.log_callback(f"❌ API 错误 [{sc}]: {result['base_resp'].get('status_msg')}", "error")
        self._reset_button()

    def _download_audio(self, url: str, filename: str, api_result: dict = None):
        save_dir = Path(self.save_dir_var.get())
        save_dir.mkdir(parents=True, exist_ok=True)
        manual_title = self.title_entry.get().strip()
        file_prefix = self._sanitize_filename(manual_title) if manual_title else "music"
        ext = ".wav" if "wav" in url.lower() else ".flac" if "flac" in url.lower() else ".mp3"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"{file_prefix}_{timestamp}{ext}"
        save_path = save_dir / audio_filename

        try:
            self.log_callback(f"📥 正在下载音频到: {save_path}", "info")
            urllib.request.urlretrieve(url, str(save_path))
            self.log_callback(f"✅ 音频已保存: {audio_filename}", "success")

            # 保存歌词
            lyrics_content = self.lyrics_text.get("1.0", tk.END).strip()
            if lyrics_content:
                lyrics_filename = f"{file_prefix}_{timestamp}.txt"
                (save_dir / lyrics_filename).write_text(lyrics_content, encoding="utf-8")
                self.log_callback(f"✅ 歌词已保存: {lyrics_filename}", "success")

            # 保存元数据
            meta_data = {
                "generated_at": datetime.datetime.now().isoformat(),
                "filename": audio_filename,
                "prompt": self.prompt_text.get("1.0", tk.END).strip(),
                "model": self.model_var.get(),
                "has_lyrics": bool(lyrics_content)
            }
            meta_filename = f"{file_prefix}_{timestamp}_meta.json"
            (save_dir / meta_filename).write_text(
                json.dumps(meta_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self.log_callback(f"✅ 元数据已保存: {meta_filename}", "accent")

        except Exception as e:
            self.log_callback(f"下载失败: {e}", "error")

    def _save_lyrics_to_file(self):
        lyrics_content = self.lyrics_text.get("1.0", tk.END).strip()
        if not lyrics_content:
            messagebox.showwarning("提示", "歌词内容为空！")
            return
        save_dir = Path(self.save_dir_var.get())
        save_dir.mkdir(parents=True, exist_ok=True)
        manual_title = self.title_entry.get().strip()
        title_clean = self._sanitize_filename(manual_title) if manual_title else ""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{title_clean}_{timestamp}.txt" if title_clean else f"lyrics_{timestamp}.txt"
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

    def _reset_button(self):
        self.generate_btn.configure(state="normal", text="🚀 生成音乐")

    def get_prompt(self) -> str:
        return self.prompt_text.get("1.0", tk.END).strip()

    def get_lyrics(self) -> str:
        return self.lyrics_text.get("1.0", tk.END).strip()

    def get_title(self) -> str:
        return self.title_entry.get().strip()