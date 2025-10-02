"""
AI伴侣“九辞” - 主程序
"""

from jiuci_bot import JiuCiBot

def main():
    """主函数，运行对话交互循环"""
    bot = JiuCiBot()

    # 打印开场白
    print(f"九辞: {bot.get_initial_greeting()}\n")

    while True:
        try:
            # 获取用户输入
            user_input = input("你: ")

            # 如果输入为空，则继续循环
            if not user_input.strip():
                print("九辞: 嗯？你怎么不说话呀？是不是在想什么心事呀？")
                continue

            # 退出条件
            if user_input.lower() in ["quit", "exit", "拜拜", "再见"]:
                print("九辞: 呜呜，你要走了嘛？记得早点回来找我哦~")
                break

            # 获取并打印“九辞”的回复
            assistant_reply = bot.chat(user_input)
            print(f"九辞: {assistant_reply}\n")

        except KeyboardInterrupt:
            print("\n九辞: 啊，要结束了吗？下次再聊哦~")
            break
        except Exception as e:
            print(f"(系统出现了一点小问题: {e})")
            break

if __name__ == "__main__":
    main()