from config_hide import HIDE_LIST
import sys
import os

# 处理隐藏配置的函数
def hide_config(config_content):
    lines = config_content.split('\n')
    for i, line in enumerate(lines):
        for hide_key in HIDE_LIST:
            if line.startswith(hide_key):
                lines[i] = f"{hide_key} = ''"
    return '\n'.join(lines)

def config_to_example():
    # 读取原始config.py内容
    with open('config.py', 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 隐藏指定配置
    hidden_content = hide_config(original_content)

    # 将处理后的内容写入config.py.example
    with open('config.py.example', 'w', encoding='utf-8') as f:
        f.write(hidden_content)
    print("Sensitive information hidden and saved to config.py.example")

def copy_example():
    if os.path.exists('config.py'):
        print("config.py already exists. Please backup it before running this script.")
        return
    # 复制config.py.example到config.py
    with open('config.py.example', 'r', encoding='utf-8') as f:
        example_content = f.read()
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(example_content)
    print("config.py.example copied to config.py")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <action>")
        print(
            "Actions: 'hide' to hide sensitive info and save to config.py.example, 'copy' to copy config.py.example to config.py")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == '--hide':
        config_to_example()

    elif action == '--copy':
        copy_example()

    else:
        print("Invalid action. Use 'hide' or 'copy'.")
        sys.exit(1)