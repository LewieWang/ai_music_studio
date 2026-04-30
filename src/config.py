"""
配置模块 - 包含配色方案和常量定义
"""

import customtkinter as ctk

# 设置 CustomTkinter 主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ==================== 配色方案: Deep Space Neon ====================
COLORS = {
    "bg_dark": "#0a0e17",
    "bg_card": "#111827",
    "bg_input": "#1a2332",
    "bg_hover": "#1e2d3d",
    "accent_primary": "#00d4ff",
    "accent_secondary": "#7c3aed",
    "accent_success": "#10b981",
    "accent_warning": "#f59e0b",
    "accent_error": "#ef4444",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#1e293b",
}