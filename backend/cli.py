from backend.agent import DajiAgent


def main():
    print("====================================")
    print("  Daji Agent Studio - Backend CLI")
    print("  妲己智能体工作台：工程化结构版")
    print("====================================")
    print("输入 exit / quit / q / 退出 可以结束程序。")
    print("输入 clear 可以清空当前聊天记忆。")
    print("试试输入：帮我查看当前 Python 版本")
    print("试试输入：请读取 backend/agent.py，并解释它的核心流程")
    print()

    agent = DajiAgent()

    while True:
        user_input = input("你：").strip()

        if user_input.lower() in ["exit", "quit", "q", "退出"]:
            print("妲己：妾身退下了，主人下次再唤妲己便是。")
            break

        if user_input.lower() in ["clear", "清空"]:
            agent.clear()
            print("妲己：妾身已清空当前记忆，主人可以重新吩咐。")
            continue

        if not user_input:
            print("妲己：主人还未吩咐妾身呢。")
            continue

        result = agent.chat(user_input)

        steps = result["steps"]

        if steps:
            print()
            print("妲己：妾身需要动用工具查验一番。")

            for step in steps:
                print(f"[工具调用] {step['tool']}({step['args']})")
                print("[工具结果]")
                print(step["result"])

        print()
        print("妲己：")
        print(result["reply"])
        print()


if __name__ == "__main__":
    main()