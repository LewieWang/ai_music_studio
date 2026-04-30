# AI Music Studio

基于 MiniMax API 的 AI 音乐生成桌面应用程序。

## 功能特性

- 🎵 **AI 音乐生成** - 使用 MiniMax API 生成原创音乐
- ✍️ **AI 歌词生成** - 自动生成歌曲歌词
- 🔍 **歌曲智能分析** - 输入歌曲名和作者，AI 自动分析歌曲特征并填充参数
- 🎨 **Deep Space Neon 风格** - 现代炫酷的深空霓虹 UI 设计
- 📁 **自动保存** - 生成的音频、歌词和元数据自动保存到本地

## 环境要求

- Python 3.8+
- Windows/macOS/Linux

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ai_music_studio.git
cd ai_music_studio
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：

创建 `.env` 文件，添加以下内容：
```
MINIMAX_API_KEY=your_api_key_here
```

或直接在应用程序设置中输入 API Key。

## 使用方法

1. 运行应用程序：
```bash
python main.py
```

2. 在设置中配置 MiniMax API Key

3. 使用方式：
   - **直接生成**：输入音乐风格提示词，点击"生成音乐"
   - **AI 分析**：输入歌曲名和作者，点击"AI 分析歌曲特征"，AI 会自动分析并填充参数
   - **歌词生成**：输入歌词主题，选择生成模式，点击"生成"

## 项目结构

```
ai_music_studio/
├── main.py              # 应用程序入口
├── src/
│   ├── config.py        # 配置和配色方案
│   ├── api/
│   │   └── minimax.py   # MiniMax API 封装
│   └── ui/
│       ├── app.py       # 主窗口
│       ├── components.py # UI 组件
│       └── tabs/
│           └── music_tab.py  # 音乐生成标签页
├── requirements.txt     # 依赖
└── README.md           # 说明文档
```

## 依赖

- customtkinter>=5.2.0
- requests>=2.31.0
- python-dotenv>=1.0.0
- langchain-openai>=0.3.0
- langchain-community>=0.3.0
- langchain-agents>=0.4.0
- duckduckgo-search>=7.0.0

## 许可证

MIT License

## 注意事项

- 需要有效的 MiniMax API Key 才能使用
- 生成的音频文件默认保存在 `D:/AIMusicData` 目录
- 歌曲智能分析功能需要联网