#!/usr/bin/env python3
import os
import sys
import shutil
import textwrap
from typing import List, Dict, Optional
from core import readlist, write

class ChatTUI:
    def __init__(self):
        self.channel: Optional[str] = None
        self.page_size = 20
        self.current_page = 1
        self.posts: List[Dict] = []
        self.terminal_width = shutil.get_terminal_size().columns
        self.terminal_height = shutil.get_terminal_size().lines
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def get_terminal_size(self):
        """响应式获取终端尺寸"""
        size = shutil.get_terminal_size()
        self.terminal_width = size.columns
        self.terminal_height = size.lines
        
    def render_header(self):
        """渲染极简头部"""
        self.get_terminal_size()
        
        # 频道显示
        channel_text = f"#{self.channel}" if self.channel else "All Messages"
        
        # 居中显示
        header_line = f"  {channel_text}  "
        padding = (self.terminal_width - len(header_line)) // 2
        
        print(" " * padding + header_line)
        print("─" * self.terminal_width)
        print()
        
    def wrap_content(self, content: str, max_width: int) -> List[str]:
        """智能文本换行，保持阅读舒适度"""
        if not content:
            return [""]
            
        # 移除多余空白
        content = ' '.join(content.split())
        
        # 使用textwrap进行优雅换行
        wrapped = textwrap.fill(content, width=max_width, 
                              break_long_words=False, 
                              break_on_hyphens=False)
        return wrapped.split('\n')
        
    def render_post(self, post: Dict, index: int):
        """渲染单个聊天消息"""
        name = post.get('name', 'Anonymous')
        content = post.get('content', '')
        
        # 计算可用宽度 (留出边距)
        available_width = self.terminal_width - 4
        
        # 用户名最大宽度
        max_name_width = min(20, available_width // 3)
        if len(name) > max_name_width:
            name = name[:max_name_width-1] + "…"
            
        # 内容区域宽度
        content_width = available_width - len(name) - 3  # 3 for spacing
        
        # 换行处理
        content_lines = self.wrap_content(content, content_width)
        
        # 渲染第一行
        first_line = content_lines[0] if content_lines else ""
        print(f"  {name:<{len(name)}}   {first_line}")
        
        # 渲染剩余行
        for line in content_lines[1:]:
            print(f"  {' ' * len(name)}   {line}")
            
        # 添加微妙的分隔
        print()
        
    def render_posts(self):
        """渲染聊天列表"""
        if not self.posts:
            # 空状态
            empty_text = "No messages yet"
            padding = (self.terminal_width - len(empty_text)) // 2
            print("\n" * (self.terminal_height // 3))
            print(" " * padding + empty_text)
            print("\n" * (self.terminal_height // 3))
            return
            
        # 计算可显示的消息数量
        available_height = self.terminal_height - 6  # 头部、底部、缓冲区
        
        for i, post in enumerate(self.posts[:available_height]):
            self.render_post(post, i)
            
    def render_footer(self):
        """渲染底部控制区"""
        print("─" * self.terminal_width)
        
        # 控制提示
        controls = []
        controls.append("r: refresh")
        controls.append("w: write")
        if self.channel:
            controls.append("c: clear channel")
        else:
            controls.append("c: set channel")
        controls.append("q: quit")
        
        control_text = "  " + " • ".join(controls) + "  "
        
        # 分页信息
        if self.posts:
            page_info = f"  page {self.current_page}  "
            # 右对齐页码信息
            spaces_needed = max(0, self.terminal_width - len(control_text) - len(page_info))
            footer_line = control_text + " " * spaces_needed + page_info
        else:
            footer_line = control_text
            
        print(footer_line[:self.terminal_width])
        
    def render(self):
        """渲染完整界面"""
        self.clear_screen()
        self.render_header()
        self.render_posts()
        self.render_footer()
        
    def load_posts(self):
        """加载聊天数据"""
        try:
            self.posts = readlist(self.channel, self.current_page, self.page_size)
        except Exception as e:
            self.posts = []
            print(f"Error loading posts: {e}")
            
    def handle_input(self, key: str):
        """处理用户输入"""
        key = key.lower().strip()
        
        if key == 'q':
            return False
            
        elif key == 'r':
            self.load_posts()
            
        elif key == 'w':
            self.write_message()
            
        elif key == 'c':
            if self.channel:
                self.channel = None
                self.current_page = 1
            else:
                self.set_channel()
            self.load_posts()
            
        elif key == 'n' and self.posts:
            self.current_page += 1
            self.load_posts()
            
        elif key == 'p' and self.current_page > 1:
            self.current_page -= 1
            self.load_posts()
            
        return True
        
    def write_message(self):
        """写入新消息"""
        print("\n" + "─" * self.terminal_width)
        print("Write a message (press Enter twice to send, Ctrl+C to cancel):")
        print()
        
        lines = []
        empty_lines = 0
        
        try:
            while True:
                line = input()
                if line == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        break
                else:
                    empty_lines = 0
                lines.append(line)
                
            content = '\n'.join(lines).strip()
            if content:
                write(content, self.channel)
                print(f"\nMessage sent to {f'#{self.channel}' if self.channel else 'global'}")
                input("Press Enter to continue...")
                self.load_posts()
                
        except KeyboardInterrupt:
            print("\nCancelled")
            input("Press Enter to continue...")
            
    def set_channel(self):
        """设置频道"""
        print("\n" + "─" * self.terminal_width)
        try:
            channel = input("Enter channel name (or press Enter for global): ").strip()
            if channel:
                self.channel = channel
                self.current_page = 1
                print(f"Switched to #{channel}")
            else:
                self.channel = None
                self.current_page = 1
                print("Switched to global")
            input("Press Enter to continue...")
        except KeyboardInterrupt:
            pass
            
    def run(self):
        """主循环"""
        print("Loading...")
        self.load_posts()
        
        while True:
            self.render()
            try:
                key = input("\n> ").strip()
                if not self.handle_input(key):
                    break
            except KeyboardInterrupt:
                break
            except EOFError:
                break
                
        print("\nGoodbye!")

def main():
    """启动TUI"""
    try:
        tui = ChatTUI()
        tui.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()