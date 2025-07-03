import sys
import argparse
from textwrap import wrap
import readline  # 用于改进命令行输入体验
from core import write, read_new

# 模拟数据存储
data_store = {
    "technology": {
        "new": [f"新科技动态{i}: 人工智能在医疗领域的突破性应用，详细分析请参考..." + "a"*(200+i) for i in range(1, 26)],
        "hot": [f"热门技术话题{i}: 量子计算最新进展与未来展望" + "b"*(250+i) for i in range(1, 21)]
    },
    "design": {
        "new": [f"设计趋势{i}: 极简主义在UI设计中的新表现" + "c"*(240+i) for i in range(1, 18)],
        "hot": [f"经典设计案例{i}: 苹果产品设计哲学深度解析" + "d"*(260+i) for i in range(1, 15)]
    }
}



def read_hot(channel=None, pageNo=1, pageSize=10):
    """获取热门内容"""
    return read_data('hot', channel, pageNo, pageSize)

def read_data(content_type, channel, page, page_size):
    """通用数据读取函数"""
    start = (page - 1) * page_size
    end = start + page_size
    
    if channel and channel in data_store:
        return data_store[channel][content_type][start:end]
    
    # 合并所有频道的数据
    all_items = []
    for ch in data_store.values():
        all_items.extend(ch[content_type])
    return all_items[start:end]

# CLI展示功能
class RNWReader:
    def __init__(self):
        self.channel = None
        self.content_type = 'new'
        self.page = 1
        self.page_size = 10
    
    def display_header(self):
        """显示当前阅读状态头部信息"""
        channel_display = self.channel or "所有频道"
        print(f"\n\033[1;36m=== {channel_display.upper()} - {self.content_type.upper()} 内容 (第{self.page}页) ===\033[0m")
        print("\033[90m" + "=" * 60 + "\033[0m")
    
    def display_item(self, idx, content):
        """格式化显示单个内容项"""
        wrapped = wrap(content, width=58)
        color = "\033[1;33m" if "热门" in content else "\033[0;32m"
        
        print(f"\033[1;35m{idx:>2}.\033[0m {color}{wrapped[0]}\033[0m")
        for line in wrapped[1:]:
            print(f"    {line}")
        print("\033[90m" + "-" * 60 + "\033[0m")
    
    def display_pagination(self, total_pages):
        """显示分页信息"""
        page_info = f"页码: {self.page}/{total_pages}"
        print(f"\033[1;34m{page_info:^60}\033[0m")
    
    def display_help(self):
        """显示帮助信息"""
        print("\n\033[1m命令选项:\033[0m")
        print("  [n] 下一页      [p] 上一页      [c] 切换频道")
        print("  [s] 切换排序    [q] 退出        [数字] 跳转页码")
        print("  [h] 帮助")
    
    def run(self):
        """主交互循环"""
        while True:
            # 获取当前页数据
            if self.content_type == 'new':
                items = read_new(self.channel, self.page, self.page_size)
            else:
                items = read_hot(self.channel, self.page, self.page_size)
            
            # 计算总页数
            total_items = sum(len(v[self.content_type]) for v in data_store.values())
            total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
            
            # 清屏并显示内容
            print("\033c", end="")  # 清屏
            self.display_header()
            
            if not items:
                print("\033[1;31m没有找到内容\033[0m")
            else:
                for i, item in enumerate(items, 1):
                    self.display_item(i, item)
            
            self.display_pagination(total_pages)
            self.display_help()
            
            # 获取用户输入
            try:
                cmd = input("\n> ").strip().lower()
            except EOFError:
                print("\n退出")
                break
            
            # 处理命令
            if cmd == 'q':
                print("退出阅读模式")
                break
            elif cmd == 'n':
                self.page = min(total_pages, self.page + 1)
            elif cmd == 'p':
                self.page = max(1, self.page - 1)
            elif cmd == 'c':
                self.select_channel()
            elif cmd == 's':
                self.toggle_sort()
            elif cmd.isdigit():
                page_num = int(cmd)
                if 1 <= page_num <= total_pages:
                    self.page = page_num
            elif cmd == 'h':
                continue  # 帮助信息已经显示

    def select_channel(self):
        """选择频道"""
        print("\n可用频道:")
        channels = ["所有频道"] + list(data_store.keys())
        for i, ch in enumerate(channels, 1):
            print(f"  {i}. {ch}")
        
        try:
            choice = int(input("选择频道编号: "))
            if 1 <= choice <= len(channels):
                self.channel = channels[choice-1] if choice > 1 else None
                self.page = 1  # 重置页码
        except ValueError:
            print("无效输入")

    def toggle_sort(self):
        """切换内容排序方式"""
        self.content_type = 'hot' if self.content_type == 'new' else 'new'
        self.page = 1  # 重置页码
        print(f"已切换到 {'热门' if self.content_type == 'hot' else '最新'} 内容")

# 主程序
def main():
    parser = argparse.ArgumentParser(description='RNW - 阅读与写作工具')
    parser.add_argument('content', nargs='*', help='要保存的内容')
    parser.add_argument('-c', '--channel', help='指定内容频道')
    
    args = parser.parse_args()
    
    if args.content:
        # 写模式
        content = " ".join(args.content)
        if len(content) > 280:
            print("错误: 内容超过280字符限制")
            return
        
        write(content)
        print(f"已保存内容: {content[:50]}...")
    else:
        # 读模式
        print("进入阅读模式...")
        reader = RNWReader()
        reader.run()

if __name__ == "__main__":
    main()