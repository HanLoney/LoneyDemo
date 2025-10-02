# LoneyDemo - AI工具集合

一个集成了多种AI功能的工具集合，包含语音合成、情感分析、时间管理等多个实用工具。

## 📁 项目结构

```
LoneyDemo/
├── JiuCiVoice/          # 🎵 九辞语音伴侣 - 带语音合成的AI对话
├── JiuCi/               # 🤖 九辞AI伴侣 - 纯文本AI对话
├── AIEmoTool/           # 😊 AI情感系统 - 高级情感分析与表达
├── EmoTool/             # 📊 情感分析工具 - 基础情感识别
├── TimeTool/            # ⏰ 时间分析工具 - 智能内容总结
└── README.md            # 📖 项目总览 (本文件)
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 各项目的具体依赖请查看对应的 `requirements.txt`

### 安装依赖
```bash
# 进入具体项目目录安装依赖
cd JiuCiVoice
pip install -r requirements.txt

# 或者安装所有项目的依赖
for dir in JiuCiVoice JiuCi AIEmoTool EmoTool TimeTool; do
    cd $dir && pip install -r requirements.txt && cd ..
done
```

## 🎯 项目介绍

### 🎵 JiuCiVoice - 九辞语音伴侣
**最完整的AI语音对话体验**

- **功能**: 集成语音合成的AI对话系统
- **特色**: 
  - 🤖 智能AI对话 - 九辞的温暖陪伴
  - 🎵 语音合成 - 将文字转换为甜美声音
  - 💝 多种音色 - sweet/gentle/lively/mature
  - 📁 自动保存 - 珍藏每一次对话的声音
- **启动**: `cd JiuCiVoice && python main.py`
- **测试**: `python main.py --test`

### 🤖 JiuCi - 九辞AI伴侣
**纯文本的AI对话体验**

- **功能**: 基础的AI对话系统
- **特色**: 
  - 💬 智能对话 - 自然流畅的交流
  - 🎭 情感表达 - 丰富的情感回应
  - 🧠 记忆能力 - 上下文理解
- **启动**: `cd JiuCi && python main.py`

### 😊 AIEmoTool - AI情感系统
**高级情感分析与表达系统**

- **功能**: 完整的AI情感管理系统
- **特色**:
  - 🔍 情感分析 - 深度理解文本情感
  - 🎭 情感表达 - 自然的情感回应
  - 📈 情感平滑 - 情感状态的自然过渡
  - 💾 状态持久化 - 情感状态的保存与恢复
- **启动**: `cd AIEmoTool && python ai_emotion_system.py`

### 📊 EmoTool - 情感分析工具
**基础情感识别工具**

- **功能**: 简单的情感分析功能
- **特色**:
  - 📝 文本情感识别
  - 📊 情感强度评估
  - 🎯 快速分析
- **启动**: `cd EmoTool && python emotion_analyzer.py`

### ⏰ TimeTool - 时间分析工具
**智能内容总结助手**

- **功能**: 内容分析与智能总结
- **特色**:
  - 📖 内容理解与分析
  - ✨ 智能总结生成
  - ⚡ 快速处理
- **启动**: `cd TimeTool && python main.py`

## 🔧 使用指南

### 选择合适的工具

| 需求 | 推荐工具 | 说明 |
|------|----------|------|
| 语音对话 | JiuCiVoice | 完整的语音合成功能 |
| 文本对话 | JiuCi | 轻量级AI对话 |
| 情感分析 | AIEmoTool | 高级情感系统 |
| 简单情感识别 | EmoTool | 基础情感分析 |
| 内容总结 | TimeTool | 智能文本总结 |

### 配置说明

大部分工具都支持配置文件自定义：
- `config.json` - 主要配置文件
- `ai_emotion_state.json` - 情感状态文件
- 具体配置请参考各项目的README

## 📋 功能对比

| 功能 | JiuCiVoice | JiuCi | AIEmoTool | EmoTool | TimeTool |
|------|------------|-------|-----------|---------|----------|
| AI对话 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 语音合成 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 情感分析 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 情感表达 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 内容总结 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 状态持久化 | ✅ | ✅ | ✅ | ❌ | ❌ |

## 🎨 特色功能

### 🎵 语音合成 (JiuCiVoice)
- 支持多种音色选择
- 高质量语音输出
- 自动保存音频文件

### 😊 情感系统 (AIEmoTool)
- 多维度情感分析
- 情感状态平滑过渡
- 自然的情感表达

### 🤖 AI对话 (JiuCi/JiuCiVoice)
- 上下文理解
- 个性化回应
- 情感化交流

## 🛠️ 开发说明

### 项目依赖
- 各项目相对独立，可单独运行
- JiuCiVoice包含完整的协议实现
- 情感系统可被其他项目调用

### 扩展开发
- 每个工具都有清晰的模块化设计
- 支持配置文件自定义
- 易于集成和扩展

## 📝 更新日志

### v1.0.0 (2024-10-02)
- ✅ 完成JiuCiVoice语音合成功能
- ✅ 实现AI情感系统
- ✅ 集成多个实用工具
- ✅ 项目模块化重构

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**🌟 如果这个项目对你有帮助，请给个Star支持一下！**