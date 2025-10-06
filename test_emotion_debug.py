#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析调试测试脚本
用于验证情感分析功能是否正常工作
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_emotion_analysis_api():
    """测试情感分析API"""
    print("=" * 50)
    print("🧪 开始测试情感分析API")
    print("=" * 50)
    
    # 测试用例：不同情感的消息
    test_cases = [
        {"message": "我今天非常开心！", "expected_emotion": "joy"},
        {"message": "我感到很难过和沮丧", "expected_emotion": "sadness"},
        {"message": "这让我非常愤怒！", "expected_emotion": "anger"},
        {"message": "我对此感到很担心", "expected_emotion": "fear"},
        {"message": "这真是太令人惊讶了！", "expected_emotion": "surprise"},
        {"message": "我觉得很恶心", "expected_emotion": "disgust"}
    ]
    
    base_url = "http://localhost:5000"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test_case['message']}")
        print(f"🎯 期望情感: {test_case['expected_emotion']}")
        
        try:
            # 发送请求
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "message": test_case["message"],
                    "user_id": "test_user"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 请求成功")
                
                # 检查响应结构
                if "debug_info" in data:
                    debug_info = data["debug_info"]
                    print(f"📊 调试信息存在: {bool(debug_info)}")
                    
                    if "emotion_info" in debug_info:
                        emotion_info = debug_info["emotion_info"]
                        print(f"💭 情感信息: {json.dumps(emotion_info, ensure_ascii=False, indent=2)}")
                        
                        # 检查用户情感分析
                        if "user_emotion" in emotion_info:
                            user_emotion = emotion_info["user_emotion"]
                            print(f"👤 用户情感分析: {user_emotion}")
                        
                        # 检查AI情感状态
                        if "ai_emotion" in emotion_info:
                            ai_emotion = emotion_info["ai_emotion"]
                            print(f"🤖 AI情感状态: {ai_emotion}")
                    else:
                        print("❌ 缺少emotion_info")
                else:
                    print("❌ 缺少debug_info")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
        
        print("-" * 30)
        time.sleep(1)  # 避免请求过快

def check_emotion_state_file():
    """检查情感状态文件"""
    print("\n" + "=" * 50)
    print("📁 检查情感状态文件")
    print("=" * 50)
    
    emotion_file_paths = [
        "d:/Work/X0001/Git/LoneyDemo/Web/data/emotion_state_default.json",
        "d:/Work/X0001/Git/LoneyDemo/data/emotion_state_default.json"
    ]
    
    for file_path in emotion_file_paths:
        if os.path.exists(file_path):
            print(f"📄 找到文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    emotion_data = json.load(f)
                print(f"📊 情感状态数据:")
                print(json.dumps(emotion_data, ensure_ascii=False, indent=2))
                
                # 检查最后更新时间
                if "last_update" in emotion_data:
                    last_update = emotion_data["last_update"]
                    print(f"⏰ 最后更新时间: {last_update}")
                
            except Exception as e:
                print(f"❌ 读取文件失败: {str(e)}")
        else:
            print(f"❌ 文件不存在: {file_path}")

def test_direct_emotion_service():
    """直接测试情感服务"""
    print("\n" + "=" * 50)
    print("🔧 直接测试情感服务")
    print("=" * 50)
    
    try:
        # 导入情感服务
        from core.emotion.emotion_service import EmotionService
        from shared.utils.config import Config
        
        # 初始化配置和服务
        config = Config()
        emotion_service = EmotionService(config)
        
        print("✅ 情感服务初始化成功")
        
        # 测试情感分析
        test_message = "我今天非常开心！"
        print(f"📝 测试消息: {test_message}")
        
        result = emotion_service.analyze_emotion(test_message)
        print(f"📊 分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 测试情感状态更新
        if result and "emotions" in result:
            emotions = result["emotions"]
            intensity = result.get("intensity", 0.5)
            
            print(f"🔄 更新情感状态...")
            emotion_service.update_emotion(emotions, intensity)
            
            # 获取当前状态
            current_state = emotion_service.get_current_state()
            print(f"📈 当前情感状态: {json.dumps(current_state, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 直接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始情感分析调试测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试API
    test_emotion_analysis_api()
    
    # 2. 检查情感状态文件
    check_emotion_state_file()
    
    # 3. 直接测试情感服务
    test_direct_emotion_service()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")
    print("=" * 50)