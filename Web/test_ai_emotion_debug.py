#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI情感分析调试脚本
用于测试AI情感分析功能是否正常工作
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.emotion.emotion_service import EmotionService

async def test_ai_emotion_analysis():
    """测试AI情感分析功能"""
    print("=== AI情感分析调试测试 ===")
    
    try:
        # 初始化情感服务
        emotion_service = EmotionService()
        
        # 测试文本
        test_texts = [
            "呜呜，你这样我心跳都乱了呢，别吓我啦~",
            "我今天很开心！",
            "这让我感到很难过",
            "我对此感到愤怒",
            "这真是太令人惊讶了！"
        ]
        
        print(f"开始测试 {len(test_texts)} 个文本的AI情感分析...")
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n--- 测试 {i}: {text} ---")
            
            try:
                # 分析情感
                result = await emotion_service.analyze_emotion(text)
                
                if result:
                    print(f"✓ 分析成功")
                    print(f"  主要情感: {result.primary_emotion.value}")
                    print(f"  置信度: {result.confidence:.3f}")
                    print(f"  情感分数: {result.sentiment_score:.3f}")
                    print(f"  检测到的情感: {[(k.value, f'{v:.3f}') for k, v in result.detected_emotions.items()]}")
                    print(f"  分析耗时: {result.analysis_time:.3f}ms")
                else:
                    print("✗ 分析失败 - 返回None")
                    
            except Exception as e:
                print(f"✗ 分析异常: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_emotion_analysis())