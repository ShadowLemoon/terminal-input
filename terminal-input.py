import sys
import argparse
import locale
import pyperclip
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.selection import SelectionType

# 检测系统语言
def is_chinese_locale():
    try:
        lang = locale.getlocale()[0]
        if lang:
            return lang.startswith('zh') or lang.startswith('Chinese')
        # 备用方案：检查环境变量
        import os
        for env in ('LANG', 'LC_ALL', 'LC_MESSAGES'):
            val = os.environ.get(env, '')
            if val.startswith('zh'):
                return True
        return False
    except Exception:
        return False

# 多语言帮助信息
HELP_EN = {
    'description': 'Terminal multi-line input tool',
    'single_line': 'Single-line mode: Enter submits, Alt+Enter for new line',
    'help': 'show this help message and exit',
    'epilog': '''
Keyboard Shortcuts:
  Ctrl+D          Submit (in default mode)
  Enter           Submit (in single-line mode)
  Alt+Enter       New line (in single-line mode)
  Ctrl+A          Select all
  Ctrl+C          Copy selection
  Ctrl+V          Paste
  Ctrl+X          Cut selection
  Ctrl+Z          Undo
  Ctrl+Y          Redo
  Arrow keys      Move cursor (cancel selection if any)
  Shift+Arrows    Extend selection
  Backspace/Del   Delete character or selection
'''
}

HELP_ZH = {
    'description': '终端多行文本输入工具',
    'single_line': '单行模式：Enter 提交，Alt+Enter 换行',
    'help': '显示帮助信息并退出',
    'epilog': '''
快捷键说明：
  Ctrl+D          提交（默认多行模式）
  Enter           提交（单行模式）
  Alt+Enter       换行（单行模式）
  Ctrl+A          全选
  Ctrl+C          复制选中内容
  Ctrl+V          粘贴
  Ctrl+X          剪切选中内容
  Ctrl+Z          撤销
  Ctrl+Y          重做
  方向键          移动光标（有选区时取消选区）
  Shift+方向键    扩展选区
  Backspace/Del   删除字符或选中内容
'''
}

# 选择语言
HELP = HELP_ZH if is_chinese_locale() else HELP_EN

# 解析命令行参数
parser = argparse.ArgumentParser(
    description=HELP['description'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=HELP['epilog'],
    add_help=False)  # 禁用自动添加的 -h

parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                    help=HELP['help'])
parser.add_argument('-s', '--single-line', action='store_true',
                    help=HELP['single_line'])
args = parser.parse_args()

# 定义快捷键
kb = KeyBindings()

# 本地剪贴板缓存（用于处理 Windows 剪贴板同步延迟）
_local_clipboard = ""

# 绑定 Ctrl+D 为提交 (Submit)
@kb.add('c-d')
def _(event):
    event.current_buffer.validate_and_handle()

# 单行模式：Enter 提交，Alt+Enter/Shift+Enter/Ctrl+Enter 换行
if args.single_line:
    @kb.add('enter')
    def _(event):
        event.current_buffer.validate_and_handle()

    @kb.add('escape', 'enter')
    def _(event):
        event.current_buffer.insert_text('\n')

# Ctrl+Z 为 撤销
@kb.add('c-z', save_before=lambda e: False)
def _(event):
    event.current_buffer.undo()

# Ctrl+Y 为 Redo (Ctrl+Shift+Z 在终端中无法直接识别)
@kb.add('c-y', save_before=lambda e: False)
def _(event):
    event.current_buffer.redo()

# 禁用 Ctrl+S 的 I-search（什么都不做）
@kb.add('c-s')
def _(event):
    pass

# 绑定 Ctrl+A 为全选
@kb.add('c-a')
def _(event):
    buffer = event.current_buffer
    buffer.cursor_position = 0
    buffer.start_selection()
    buffer.cursor_position = len(buffer.text)

# 方向键处理：有选区时取消选区并移到边界
@kb.add('left')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        # 移动到选区开始位置
        start = min(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        buffer.exit_selection()
        buffer.cursor_position = start
    else:
        buffer.cursor_left()

@kb.add('right')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        # 移动到选区结束位置
        end = max(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        buffer.exit_selection()
        buffer.cursor_position = end
    else:
        buffer.cursor_right()

@kb.add('up')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        start = min(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        buffer.exit_selection()
        buffer.cursor_position = start
    buffer.auto_up()

@kb.add('down')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        end = max(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        buffer.exit_selection()
        buffer.cursor_position = end
    buffer.auto_down()

# Shift+方向键：扩展/调整选区
@kb.add('s-left')
def _(event):
    buffer = event.current_buffer
    if not buffer.selection_state:
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
    buffer.cursor_left()

@kb.add('s-right')
def _(event):
    buffer = event.current_buffer
    if not buffer.selection_state:
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
    buffer.cursor_right()

@kb.add('s-up')
def _(event):
    buffer = event.current_buffer
    if not buffer.selection_state:
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
    # 移到行首
    buffer.cursor_position = buffer.document.get_start_of_line_position(after_whitespace=False) + buffer.cursor_position

@kb.add('s-down')
def _(event):
    buffer = event.current_buffer
    if not buffer.selection_state:
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
    # 移到行尾
    buffer.cursor_position = buffer.document.get_end_of_line_position() + buffer.cursor_position

# 辅助函数：删除选区但不影响剪贴板
def delete_selection(buffer):
    start, end = buffer.document.selection_range()
    buffer.exit_selection()
    buffer.cursor_position = start
    buffer.delete(end - start)

# 退格键：有选区时删除选中内容
@kb.add('backspace')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        delete_selection(buffer)
    else:
        buffer.delete_before_cursor(1)

# Delete键：有选区时删除选中内容
@kb.add('delete')
def _(event):
    buffer = event.current_buffer
    if buffer.selection_state:
        delete_selection(buffer)
    else:
        buffer.delete(1)

# Ctrl+C 复制选中内容（而不是退出）
@kb.add('c-c')
def _(event):
    global _local_clipboard
    buffer = event.current_buffer
    if buffer.selection_state:
        # 手动获取选区文本
        start, end = buffer.document.selection_range()
        text = buffer.text[start:end]
        _local_clipboard = text  # 保存本地副本
        pyperclip.copy(text)

# Ctrl+V 粘贴
@kb.add('c-v')
def _(event):
    buffer = event.current_buffer
    # 获取剪贴板内容
    try:
        text_to_paste = pyperclip.paste()
    except Exception:
        text_to_paste = ""
    # 如果有选区，先删除
    if buffer.selection_state:
        delete_selection(buffer)
    if text_to_paste:
        buffer.insert_text(text_to_paste)

# 处理括号粘贴模式（终端 Ctrl+V 触发）
@kb.add(Keys.BracketedPaste)
def _(event):
    global _local_clipboard
    buffer = event.current_buffer
    data = event.data  # 粘贴的文本

    # 如果粘贴的内容不是本地剪贴板的内容（可能是旧的缓存），使用本地副本
    if _local_clipboard and data != _local_clipboard:
        # 检查系统剪贴板是否已同步
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard == _local_clipboard:
                data = _local_clipboard
        except Exception:
            pass

    # 如果有选区，先删除
    if buffer.selection_state:
        delete_selection(buffer)
    if data:
        buffer.insert_text(data)

# Ctrl+X 剪切
@kb.add('c-x')
def _(event):
    global _local_clipboard
    buffer = event.current_buffer
    if buffer.selection_state:
        # 先获取选区文本
        start, end = buffer.document.selection_range()
        text = buffer.text[start:end]
        _local_clipboard = text  # 保存本地副本
        # 复制到剪贴板
        pyperclip.copy(text)
        # 删除选区
        delete_selection(buffer)

# 处理任意字符输入：有选区时先删除再输入
@kb.add(Keys.Any, save_before=lambda e: not e.is_repeat)
def _(event):
    buffer = event.current_buffer
    data = event.data
    # 只处理有数据的情况
    if not data:
        return
    # 如果有选区，先删除
    if buffer.selection_state:
        delete_selection(buffer)
    # 插入字符
    buffer.insert_text(data)

def get_input():
    # mouse_support=True: 允许鼠标点击移动光标、选择文本
    # 提示符前加空行，避免 VS Code 终端命令覆盖第一行
    user_text = prompt(
        '\n> ',
        multiline=True,
        key_bindings=kb,
        mouse_support=True
    )
    return user_text

if __name__ == "__main__":
    try:
        get_input()
    except EOFError:
        # 如果用户按 Ctrl+D 在空缓冲区，退出
        sys.exit(1)