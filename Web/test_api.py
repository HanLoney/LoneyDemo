#!/usr/bin/env python3
"""
九辞AI伴侣Web版API测试脚本
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_MESSAGE = "你好九辞，我是你的新朋友！"

def test_status():
    """测试服务状态"""
    print("🔍 测试服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务状态正常: {data}")
            return True
        else:
            print(f"❌ 服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        return False

def test_chat_text_only():
    """测试纯文字聊天"""
    print("\n💬 测试纯文字聊天...")
    try:
        payload = {
            "message": TEST_MESSAGE,
            "voice_enabled": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 文字聊天成功")
            print(f"📝 AI回复: {data.get('reply', '无回复')}")
            return True
        else:
            print(f"❌ 文字聊天失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 文字聊天异常: {e}")
        return False

def test_chat_with_voice():
    """测试语音聊天"""
    print("\n🎵 测试语音聊天...")
    try:
        payload = {
            "message": "请用可爱的声音说一句话",
            "voice_enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 语音聊天成功")
            print(f"📝 AI回复: {data.get('reply', '无回复')}")
            
            audio_id = data.get('audio_file')
            if audio_id:
                print(f"🎵 音频ID: {audio_id}")
                return test_audio_download(audio_id)
            else:
                print("⚠️ 未生成音频文件")
                return True
        else:
            print(f"❌ 语音聊天失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 语音聊天异常: {e}")
        return False

def test_audio_download(audio_id):
    """测试音频下载"""
    print(f"\n🔊 测试音频下载: {audio_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/audio/{audio_id}")
        
        if response.status_code == 200:
            print(f"✅ 音频下载成功")
            print(f"📊 音频大小: {len(response.content)} bytes")
            print(f"🎵 音频类型: {response.headers.get('Content-Type', '未知')}")
            return True
        else:
            print(f"❌ 音频下载失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 音频下载异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🌸 九辞AI伴侣Web版API测试 🌸\n")
    
    # 测试结果统计
    tests = []
    
    # 1. 测试服务状态
    tests.append(("服务状态", test_status()))
    
    # 2. 测试纯文字聊天
    tests.append(("纯文字聊天", test_chat_text_only()))
    
    # 3. 测试语音聊天
    tests.append(("语音聊天", test_chat_with_voice()))
    
    # 输出测试结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！九辞AI伴侣Web版运行正常！")
    else:
        print("⚠️ 部分测试失败，请检查服务配置")

if __name__ == "__main__":
    main()