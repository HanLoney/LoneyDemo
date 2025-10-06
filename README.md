# 九辞AI伴侣 - Web版

一个现代化的、基于Web的AI伴侣系统，集成了智能对话、情感分析和语音合成功能，为您提供温暖、贴心、可交互的AI陪伴体验。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- `pip`

### 安装与启动

1. **克隆项目**
   ```bash
   git clone https://github.com/HanLoney/LoneyDemo.git
   cd LoneyDemo
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   - 复制 `.env.example` 并重命名为 `.env`
   - 在 `.env` 文件中填入您的API密钥等配置信息

4. **启动Web应用**
   ```bash
   python Web/start_web.py
   ```
   启动成功后，在浏览器中打开 `http://localhost:5000` 即可开始体验。

## 📁 项目结构

```
LoneyDemo/
├── Web/                 # 🌐 Web应用前端和后端API
├── core/                # 🧠 核心服务模块
│   ├── chat/           # 💬 对话服务
│   ├── emotion/        # 😊 情感分析
│   └── voice/          # 🎵 语音服务
├── shared/             # 🔧 共享组件
│   ├── models/         # 📊 数据模型
│   ├── utils/          # 🛠️ 工具函数
│   └── interfaces/     # 🔌 服务接口
├── config/             # ⚙️ 配置文件
├── data/               # 📁 数据存储（例如音频文件）
├── .gitignore          # 🚫 Git忽略配置
├── requirements.txt    # 📦 Python依赖
└── README.md           # 📖 项目说明
```

## ✨ 主要功能

- **智能对话**：基于大型语言模型，提供流畅、自然的对话体验。
- **情感分析**：实时分析用户输入的情感，并作出相应的回应。
- **语音合成 (TTS)**：将AI的回复转换成语音，提供更具沉浸感的交互。
- **Web界面**：简洁、现代化的Web界面，易于使用。

## 🤝 贡献

欢迎通过Pull Request或Issues为本项目做出贡献。

## 📄 许可证

本项目采用 MIT 许可证。
