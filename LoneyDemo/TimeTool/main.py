"""
TimeTool - 主程序
处理用户交互，调用时间分析器进行内容总结
"""

from time_analyzer import TimeAnalyzer

def main():
    """主函数，处理用户交互循环"""
    print("欢迎使用TimeTool - 您的智能时间分析与总结助手！")
    print("输入 'quit' 退出程序。")
    print("-" * 50)

    analyzer = TimeAnalyzer()

    while True:
        # 获取用户输入
        user_input = input("请输入您想分析和总结的内容: ")

        if user_input.lower() == 'quit':
            print("感谢使用TimeTool，再见！")
            break

        if not user_input.strip():
            print("输入内容不能为空，请重新输入。")
            continue

        # 调用分析器进行处理
        print("\n正在分析和总结，请稍候...")
        summary = analyzer.analyze_and_summarize(user_input)

        # 显示结果
        print("\n--- 总结结果 ---")
        print(summary)
        print("-" * 50)

if __name__ == "__main__":
    main()