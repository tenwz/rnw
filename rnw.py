#!/usr/bin/env python3
import os
import sys
import shutil
import textwrap
import threading
import time
from typing import List, Dict, Optional, Generator
from core import readlist_stream, write

class ChatTUI:
    def __init__(self):
        self.channel: Optional[str] = None
        self.page_size = 20
        self.current_page = 1
        self.posts: List[Dict] = []
        self.terminal_width = shutil.get_terminal_size().columns
        self.terminal_height = shutil.get_terminal_size().lines
        self.loading = False
        self.loading_dots = 0
        self.stream_complete = False
        
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
        
        # 添加加载指示器
        if self.loading:
            loading_indicator = "⚡ " + "." * (self.loading_dots % 4)
            channel_text += f" {loading_indicator}"
        
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
        if not self.posts and not self.loading:
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
            
        # 如果还在加载，显示加载提示
        if self.loading and len(self.posts) > 0:
            print(f"  📡 Loading more messages{'.' * (self.loading_dots % 4)}")
            print()
            
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
        
        # 状态信息
        status_info = ""
        if self.loading:
            status_info = f"  Loading...  "
        elif self.posts:
            status_info = f"  {len(self.posts)} messages  "
            
        # 右对齐状态信息
        spaces_needed = max(0, self.terminal_width - len(control_text) - len(status_info))
        footer_line = control_text + " " * spaces_needed + status_info
        
        print(footer_line[:self.terminal_width])
        
    def render(self):
        """渲染完整界面"""
        self.clear_screen()
        self.render_header()
        self.render_posts()
        self.render_footer()
        
    def load_posts_stream(self):
        """流式加载聊天数据"""
        self.loading = True
        self.posts = []
        self.stream_complete = False
        
        def stream_worker():
            try:
                for post in readlist_stream(self.channel, self.current_page, self.page_size):
                    self.posts.append(post)
                    # 实时更新界面
                    self.render()
                    time.sleep(0.1)  # 给用户一些视觉反馈
                    
                self.stream_complete = True
            except Exception as e:
                print(f"Error loading posts: {e}")
            finally:
                self.loading = False
                self.render()
                
        # 启动后台线程加载数据
        thread = threading.Thread(target=stream_worker)
        thread.daemon = True
        thread.start()
        
    def update_loading_animation(self):
        """更新加载动画"""
        if self.loading:
            self.loading_dots += 1
            
    def handle_input(self, key: str):
        """处理用户输入"""
        key = key.lower().strip()
        
        if key == 'q':
            return False
            
        elif key == 'r':
            self.load_posts_stream()
            
        elif key == 'w':
            self.write_message()
            
        elif key == 'c':
            if self.channel:
                self.channel = None
                self.current_page = 1
            else:
                self.set_channel()
            self.load_posts_stream()
            
        elif key == 'n' and self.stream_complete:
            self.current_page += 1
            self.load_posts_stream()
            
        elif key == 'p' and self.current_page > 1:
            self.current_page -= 1
            self.load_posts_stream()
            
        return True
        
    def write_message(self):
        """写入新消息"""
        self.clear_screen()
        print("✍️  Write a message")
        print("─" * self.terminal_width)
        print()
        print("💡 Tip: Press Enter twice to send, Ctrl+C to cancel")
        print()
        
        lines = []
        empty_lines = 0
        
        try:
            while True:
                line = input("📝 ")
                if line == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        if lines:  # 有内容才发送
                            print("\n✨ Sending message...")
                            break
                        else:
                            print("💭 Empty message, try again or press Ctrl+C to cancel")
                            empty_lines = 0
                else:
                    empty_lines = 0
                    if not lines:  # 第一行输入后给个鼓励
                        print("👍 Great! Continue typing, press Enter twice when done...")
                lines.append(line)
                
            content = '\n'.join(lines).strip()
            if content:
                write(content, self.channel)
                print(f"✅ Message sent to {f'#{self.channel}' if self.channel else 'global'}")
                print("\n🔄 Refreshing messages...")
                time.sleep(1)
                self.load_posts_stream()
                return
                
        except KeyboardInterrupt:
            print("\n❌ Message cancelled")
            
        input("\n👈 Press Enter to continue...")
            
    def set_channel(self):
        """设置频道"""
        self.clear_screen()
        print("🏷️  Set Channel")
        print("─" * self.terminal_width)
        print()
        
        try:
            channel = input("📺 Enter channel name (or press Enter for global): ").strip()
            if channel:
                self.channel = channel
                self.current_page = 1
                print(f"✅ Switched to #{channel}")
            else:
                self.channel = None
                self.current_page = 1
                print("✅ Switched to global")
                
            print("🔄 Loading messages...")
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            input("\n👈 Press Enter to continue...")
            
    def run(self):
        """主循环"""
        # 直接进入界面，不等待加载
        self.render()
        
        # 启动流式加载
        self.load_posts_stream()
        
        while True:
            # 更新加载动画
            self.update_loading_animation()
            
            # 如果正在加载，定期刷新界面
            if self.loading:
                self.render()
                
            try:
                # 非阻塞输入处理
                import select
                import sys
                
                # 检查是否有输入
                if select.select([sys.stdin], [], [], 0.5)[0]:
                    key = input("\n🎯 Command: ").strip()
                    if not self.handle_input(key):
                        break
                        
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except ImportError:
                # Windows系统不支持select，使用阻塞输入
                try:
                    key = input("\n🎯 Command: ").strip()
                    if not self.handle_input(key):
                        break
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                
        self.clear_screen()
        print("👋 Thanks for using the chat! Goodbye!")

def main():
    """启动TUI"""
    try:
        tui = ChatTUI()
        tui.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()