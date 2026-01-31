# Terminal Input (tinput)

一个基于 prompt_toolkit 的终端多行文本输入工具，支持类似现代文本编辑器的快捷键操作。

## 功能特性

- 多行文本输入
- 鼠标支持（点击移动光标、选择文本）
- 完整的剪贴板操作
- 撤销/重做支持
- 类似现代编辑器的选区操作

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+D | 提交/完成输入 |
| Ctrl+A | 全选 |
| Ctrl+C | 复制选中内容 |
| Ctrl+V | 粘贴 |
| Ctrl+X | 剪切选中内容 |
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| ←/→/↑/↓ | 移动光标（有选区时取消选区） |
| Shift+← | 向左扩展选区 |
| Shift+→ | 向右扩展选区 |
| Shift+↑ | 选择到行首 |
| Shift+↓ | 选择到行尾 |
| Backspace | 删除前一个字符（有选区时删除选区） |
| Delete | 删除后一个字符（有选区时删除选区） |

## 安装依赖

```bash
pip install prompt_toolkit pyperclip
```

或使用 uv:

```bash
uv sync
```

## 使用方法

直接运行 Python 脚本:

```bash
python terminal-input.py
```

或运行打包后的可执行文件:

```bash
tinput
```

### 单行模式

使用 `-s` 或 `--single-line` 参数启用单行模式：

```bash
tinput -s
```

单行模式下：
- **Enter** 直接提交
- **Alt+Enter** 换行

> 注意：由于 VT100 终端限制，Shift+Enter 和 Ctrl+Enter 无法在终端中识别。

默认多行模式下：
- **Enter** 换行
- **Ctrl+D** 提交

## 打包

使用 PyInstaller 打包:

```bash
pyinstaller terminal-input.spec
```

打包后的可执行文件将生成在 `dist/tinput.exe`。

## 注意事项

- Ctrl+S 已禁用（不会触发 I-search）
- Ctrl+Shift+Z 在终端中不支持，使用 Ctrl+Y 代替重做
- 在有选区的情况下输入任意字符会替换选中内容
