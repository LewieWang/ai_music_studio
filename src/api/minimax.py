"""
API 模块 - MiniMax API 调用封装
"""

import requests
import json
import os
import urllib.request
import datetime
from pathlib import Path


class MiniMaxAPI:
    """MiniMax API 封装类"""

    BASE_URL = "https://api.minimaxi.com/v1"

    # 翻唱风格推荐内置提示词
    COVER_STYLE_SYSTEM_PROMPT = """你是一位精通全球流行音乐趋势的资深音乐制作人，熟悉当下各大音乐平台（Spotify、Billboard、抖音、网易云等）的热门风格。

## 任务
根据当前主流市场流行的音乐风格，随机推荐 6 种翻唱风格，涵盖不同语种、情绪和曲风。

## 输出格式（严格 JSON，不要多余文字）
```json
{
  "styles": [
    {
      "name": "风格名称（4字以内）",
      "emoji": "1个代表emoji",
      "prompt": "直接可用的翻唱风格提示词，10-300字，逗号分隔关键词",
      "desc": "一句话描述这个风格的特点和适合场景"
    }
  ]
}
```

## 要求
- styles 数组固定 6 项
- prompt 字段必须是中文+英文混合、逗号分隔的风格关键词，可直接用于翻唱API
- 每种风格差异要大（不同语种/乐器/情绪/年代）
- 至少包含：1个华语流行向、1个欧美向、1个日韩向、1个独立/另类向、1个复古/怀旧向、1个实验/混搭向
- 每次调用都要随机组合，不要固定输出
- 不要输出思考过程，直接输出JSON"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def generate_lyrics(self, prompt: str, mode: str = "write_full_song") -> dict:
        """
        调用歌词生成 API

        Args:
            prompt: 歌词提示词
            mode: 生成模式 (write_full_song/write_verse/write_chorus)

        Returns:
            API 响应结果
        """
        url = f"{self.BASE_URL}/lyrics_generation"
        payload = {"mode": mode, "prompt": prompt}

        response = requests.post(url, json=payload, headers=self.headers, timeout=60)
        return response.json()

    def recommend_cover_styles(self) -> dict:
        """
        调用 LLM 推荐翻唱风格

        Returns:
            包含 styles 数组的推荐结果，每项含 name/emoji/prompt/desc
        """
        url = f"{self.BASE_URL}/chat/completions"
        payload = {
            "model": "MiniMax-M2.5",
            "messages": [
                {"role": "system", "content": self.COVER_STYLE_SYSTEM_PROMPT},
                {"role": "user", "content": "请推荐 6 种当前流行的翻唱风格，要求随机、多样、有创意"}
            ],
            "temperature": 0.9,
            "max_tokens": 1200
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            data = response.json()

            # 提取文本内容
            content = ""
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")

            if not content:
                return {"error": "LLM 未返回内容"}

            # 解析 JSON（兼容 markdown 代码块包裹）
            json_str = content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            if "styles" in result and isinstance(result["styles"], list):
                return result
            return {"error": "返回格式不正确"}

        except json.JSONDecodeError:
            return {"error": "LLM 返回内容无法解析为 JSON"}
        except Exception as e:
            return {"error": f"推荐风格失败: {e}"}

    def cover_preprocess(self, audio_url: str = None, audio_base64: str = None) -> dict:
        """
        翻唱前处理 - 提取参考音频特征

        Args:
            audio_url: 参考音频 URL（与 audio_base64 二选一）
            audio_base64: Base64 编码的参考音频（与 audio_url 二选一）

        Returns:
            包含 cover_feature_id, formatted_lyrics, structure_result 等的响应
        """
        if not audio_url and not audio_base64:
            return {"error": "请提供 audio_url 或 audio_base64"}
        if audio_url and audio_base64:
            return {"error": "audio_url 和 audio_base64 只能提供一个"}

        url = f"{self.BASE_URL}/music_cover_preprocess"
        payload = {"model": "music-cover"}
        if audio_url:
            payload["audio_url"] = audio_url
        else:
            payload["audio_base64"] = audio_base64

        response = requests.post(url, json=payload, headers=self.headers, timeout=300)
        return response.json()


    def generate_cover(self, prompt: str, model: str = "music-cover",
                       audio_url: str = None, audio_base64: str = None,
                       cover_feature_id: str = None, lyrics: str = "",
                       sample_rate: int = 44100, bitrate: int = 256000,
                       output_format: str = "mp3") -> dict:
        """
        翻唱音乐生成

        Args:
            prompt: 翻唱风格描述（必填，10-300字）
            model: 模型版本 (music-cover / music-cover-free)
            audio_url: 参考音频 URL（与 audio_base64/cover_feature_id 互斥）
            audio_base64: Base64 编码的参考音频
            cover_feature_id: 翻唱前处理返回的特征 ID（传入时 lyrics 必填）
            lyrics: 歌词内容
            sample_rate: 采样率
            bitrate: 比特率
            output_format: 输出格式

        Returns:
            API 响应结果
        """
        url = f"{self.BASE_URL}/music_generation"
        payload = {
            "model": model,
            "prompt": prompt,
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": output_format
            },
            "output_format": "url"
        }

        # 翻唱音频来源（三选一）
        if cover_feature_id:
            payload["cover_feature_id"] = cover_feature_id
            if lyrics:
                payload["lyrics"] = lyrics
        elif audio_url:
            payload["audio_url"] = audio_url
            if lyrics:
                payload["lyrics"] = lyrics
        elif audio_base64:
            payload["audio_base64"] = audio_base64
            if lyrics:
                payload["lyrics"] = lyrics

        response = requests.post(url, headers=self.headers, json=payload, timeout=300)
        return response.json()

    def generate_music(self, model: str, prompt: str, lyrics: str = "",
                       sample_rate: int = 44100, bitrate: int = 256000,
                       output_format: str = "mp3") -> dict:
        """
        调用音乐生成 API

        Args:
            model: 模型版本 (music-2.5/music-2.6/music-01-preview)
            prompt: 音乐风格提示词
            lyrics: 歌词内容
            sample_rate: 采样率
            bitrate: 比特率
            output_format: 输出格式 (mp3/wav/flac)

        Returns:
            API 响应结果
        """
        url = f"{self.BASE_URL}/music_generation"
        payload = {
            "model": model,
            "prompt": prompt,
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": output_format
            },
            "output_format": "url"
        }

        if lyrics:
            payload["lyrics"] = lyrics

        response = requests.post(url, headers=self.headers, json=payload, timeout=300)
        return response.json()

    def download_audio(self, url: str, save_dir: Path, filename: str,
                       lyrics: str = "", metadata: dict = None) -> Path:
        """
        下载音频文件

        Args:
            url: 音频下载链接
            save_dir: 保存目录
            filename: 文件名
            lyrics: 歌词内容（可选，保存为 txt）
            metadata: 元数据（可选，保存为 json）

        Returns:
            保存的文件路径
        """
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / filename

        # 下载音频
        urllib.request.urlretrieve(url, str(save_path))

        # 保存歌词
        if lyrics:
            lyrics_filename = filename.rsplit('.', 1)[0] + ".txt"
            (save_dir / lyrics_filename).write_text(lyrics, encoding="utf-8")

        # 保存元数据
        if metadata:
            meta_filename = filename.rsplit('.', 1)[0] + "_meta.json"
            (save_dir / meta_filename).write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        return save_path


class SongAnalyzer:
    """歌曲分析器 - 使用 LangChain Agent"""

    SYSTEM_PROMPT = """你是一位专业音乐分析师，精通音乐理论和编曲。

## 工作流程
1. 尝试使用 search_song_info 搜索（仅尝试一次，失败直接跳过）
2. 基于搜索结果和你自身的音乐知识进行分析
3. 直接输出结果，不要输出思考过程（think/推理内容）

## 输出格式（严格遵循，不要多余解释）

### 核心特征
节奏：BPM [数值]，[拍号]，[速度描述]
曲风：[主风格]，融合[子风格]
调性：[调性]
听感：[2-3句描述]

### 编曲特点
主要乐器：[列出主要乐器及音色特点]
人声：[唱腔风格]
节奏：[鼓点/节拍特点]

### AI 音乐生成提示词
"[风格] [语言] [性别] [乐器] BPM:[数值], [英文关键词], [情感氛围]"

**重要**：不确定的参数给出专业估算值。全程中文，精简输出，不输出思考过程。
"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "").strip()
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")

    def _ddg_search(self, query: str) -> str:
        """DuckDuckGo 搜索"""
        try:
            from duckduckgo_search import DDGS
            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    items = [{"title": r["title"], "snippet": r["body"], "url": r["href"]}
                             for r in results]
                    return json.dumps(items, ensure_ascii=False)
        except Exception:
            pass
        return ""

    def analyze(self, song_name: str, artist: str) -> str:
        """
        分析歌曲特征

        Args:
            song_name: 歌曲名
            artist: 歌手名

        Returns:
            分析结果文本
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.tools import StructuredTool
        from langchain.agents import create_agent

        if not self.api_key:
            raise ValueError("缺少 MINIMAX_API_KEY")

        llm = ChatOpenAI(
            model="MiniMax-M2.5",
            api_key=self.api_key,
            base_url=f"{self.base_url}",
            temperature=0.3,
            max_tokens=1200
        )

        search_tool = StructuredTool.from_function(
            func=self._ddg_search,
            name="search_song_info",
            description="搜索歌曲详细信息。如果搜索失败返回空即可。",
        )

        agent = create_agent(
            model=llm,
            tools=[search_tool],
            system_prompt=self.SYSTEM_PROMPT
        )

        user_message = f'请分析歌曲《{song_name}》，歌手是 {artist}'
        final_result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

        return self._extract_response(final_result)

    @staticmethod
    def _extract_response(agent_result) -> str:
        """从 Agent 结果中提取响应"""
        if isinstance(agent_result, dict):
            messages = agent_result.get("messages", [])
            for msg in reversed(messages):
                role = getattr(msg, "type", None) or (msg.get("type") if isinstance(msg, dict) else None)
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
                if content and role == "ai":
                    return str(content).strip()
            for msg in reversed(messages):
                content = getattr(msg, "content", None) or ""
                if isinstance(content, str) and len(content.strip()) > 20:
                    return content.strip()
        if hasattr(agent_result, "content"):
            return str(agent_result.content).strip()
        if isinstance(agent_result, str):
            return agent_result.strip()
        return ""