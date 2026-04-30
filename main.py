"""
AI Music Generator - Desktop Application
基于 MiniMax API 的 AI 音乐生成工具
设计风格: Deep Space Neon (深空霓虹)
"""

import os

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


from src.config import COLORS
from src.ui.app import AICreativeStudio


def main():
    app = AICreativeStudio()
    app.mainloop()


if __name__ == "__main__":
    main()