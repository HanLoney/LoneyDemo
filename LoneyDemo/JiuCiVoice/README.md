# 🎵 JiuCiVoice - 九辞语音伴侣

九辞语音伴侣是一个集成了AI对话和语音合成功能的智能伴侣系统。它将九辞AI伴侣的文字回复转换为甜美的语音，为用户提供更加生动和温暖的交互体验。

## ✨ 功能特色

### 🤖 智能AI对话
- 基于九辞AI伴侣的深度人格设定
- 支持情感分析和智能回复
- 具备记忆功能，能够维持连贯的对话

### 🎵 高质量语音合成
- 基于Volcengine TTS技术
- 支持多种音色选择（甜美/温柔/活泼/成熟）
- 高质量24kHz音频输出
- 自动保存语音文件

### 💝 贴心功能设计
- 交互式命令行界面
- 自动文件管理和命名
- 灵活的配置系统
- 批量对话处理

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置设置
复制 `config_template.json` 为 `config.json` 并填入你的API密钥：
```json
{
  "authentication": {
    "app_id": "YOUR_APP_ID",
    "access_token": "YOUR_ACCESS_TOKEN"
  }
}
```

### 3. 运行程序
```bash
python main.py
```

## 📖 使用指南

### 基本对话
直接输入文字与九辞对话：
```
👤 你: 你好九辞，今天天气真不错呢
💬 九辞: 嘿嘿，是呀！阳光暖暖的，就像你给我的感觉一样温暖~
🎵 语音: 已生成并保存
```

### 系统命令

#### 🎵 语音设置
```bash
/voice sweet    # 甜美音色 (默认)
/voice gentle   # 温柔音色  
/voice lively   # 活泼音色
/voice mature   # 成熟音色
```

#### 📁 文件管理
```bash
/save on/off    # 开启/关闭自动保存
/output         # 查看输出目录
/list           # 列出已保存的音频文件
```

#### 🔧 系统命令
```bash
/help           # 显示帮助信息
/status         # 显示当前状态
/clear          # 清空对话历史
/quit           # 退出程序
```

### 命令行参数
```bash
python main.py --help                    # 查看帮助
python main.py --voice gentle            # 指定默认音色
python main.py --config custom.json      # 使用自定义配置
python main.py --no-greeting             # 跳过初始问候
python main.py --test                    # 运行测试模式
```

## 🔧 高级用法

### 编程接口使用

#### 快速对话
```python
import asyncio
from jiuci_voice_bot import quick_jiuci_chat

async def example():
    result = await quick_jiuci_chat("你好九辞！", voice_profile="sweet")
    print(f"回复: {result['text_reply']}")
    print(f"音频大小: {result['audio_size']} 字节")

asyncio.run(example())
```

#### 完整功能使用
```python
import asyncio
from jiuci_voice_bot import JiuCiVoiceBot

async def advanced_example():
    bot = JiuCiVoiceBot()
    await bot.initialize()
    
    # 获取问候语音
    greeting = await bot.get_initial_greeting_with_voice("gentle")
    
    # 进行对话
    result = await bot.chat_with_voice("今天心情怎么样？", "sweet")
    
    # 批量处理
    conversations = ["你好", "今天天气如何", "再见"]
    results = await bot.batch_synthesize_replies(conversations, "lively")

asyncio.run(advanced_example())
```

### 纯语音合成
```python
import asyncio
from tts_synthesizer import quick_tts

async def tts_example():
    audio_data = await quick_tts(
        "这是一段测试文本",
        output_file="test.wav"
    )
    print(f"生成了 {len(audio_data)} 字节的音频")

asyncio.run(tts_example())
```

## ⚙️ 配置说明

### 配置文件结构
```json
{
  "authentication": {
    "app_id": "你的应用ID",
    "access_token": "你的访问令牌"
  },
  "service": {
    "endpoint": "TTS服务端点",
    "max_message_size": 10485760
  },
  "tts": {
    "speaker": "默认音色",
    "audio_params": {
      "voice_type": "BV700_streaming",
      "encoding": "wav",
      "rate": 24000
    }
  },
  "jiuci_voice": {
    "default_output_dir": "./output",
    "auto_save": true,
    "filename_template": "jiuci_reply_{timestamp}.wav",
    "voice_profiles": {
      "sweet": "S_female_01",
      "gentle": "S_female_02", 
      "lively": "S_female_03",
      "mature": "S_female_04"
    }
  }
}
```

### 音色配置
- `sweet` (S_female_01): 甜美可爱的声音
- `gentle` (S_female_02): 温柔轻柔的声音
- `lively` (S_female_03): 活泼开朗的声音
- `mature` (S_female_04): 成熟稳重的声音

## 📁 项目结构

```
JiuCiVoice/
├── main.py                 # 主程序入口
├── jiuci_voice_bot.py      # 九辞语音伴侣核心逻辑
├── tts_synthesizer.py      # 语音合成模块
├── config.json             # 配置文件
├── config_template.json    # 配置模板
├── requirements.txt        # 依赖包列表
├── README.md              # 说明文档
└── output/                # 音频输出目录
    ├── jiuci_greeting_*.wav
    └── jiuci_reply_*.wav
```

## 🔗 依赖项目

JiuCiVoice 依赖于以下LoneyDemo子项目：
- **JiuCi**: AI伴侣核心逻辑
- **AIEmoTool**: AI情感系统
- **EmoTool**: 情感分析工具
- **TimeTool**: 时间分析工具
- **Voice**: Volcengine TTS SDK

## 🐛 故障排除

### 常见问题

1. **配置文件错误**
   - 确保 `config.json` 存在且格式正确
   - 检查API密钥是否有效

2. **网络连接问题**
   - 确保网络连接正常
   - 检查防火墙设置

3. **音频文件无法保存**
   - 检查输出目录权限
   - 确保磁盘空间充足

4. **依赖模块导入失败**
   - 确保所有依赖项目都在正确位置
   - 检查Python路径设置

### 调试模式
```bash
python main.py --test  # 运行测试模式
```

## 📄 许可证

本项目遵循MIT许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

💝 **享受与九辞的语音对话时光！**