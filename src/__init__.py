"""
AI Music Studio - AI 音乐生成工具
基于 MiniMax API 的桌面应用程序
"""

__version__ = "1.0.0"
__author__ = "AI Creative Studio"

from src.config import COLORS
from src.api import MiniMaxAPI, SongAnalyzer

__all__ = ["COLORS", "MiniMaxAPI", "SongAnalyzer"]