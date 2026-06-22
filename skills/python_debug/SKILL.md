# Python Debug 技能

当用户遇到 Python 报错、依赖安装、虚拟环境、路径、运行命令问题时，使用本技能。

## 处理步骤

1. 先让用户看到错误的关键位置，优先看报错最后 3 行。
2. 判断错误类型：
   - ModuleNotFoundError：通常是缺少依赖，或装到了错误的虚拟环境。
   - FileNotFoundError：通常是路径不对，或当前运行目录不对。
   - SyntaxError：通常是代码语法错误。
   - ImportError：通常是包版本、导入路径或文件名冲突。
   - PermissionError：通常是权限或脚本执行策略问题。
3. 如果涉及虚拟环境，先确认终端前面是否有 `(.venv)`。
4. 如果涉及缺包，优先建议：
   ```powershell
   pip install 包名