from telegraph import TelegraphAPI, Page
import datetime
from urllib.parse import quote
import getpass
from typing import Optional, Generator, Dict
import json
import time

api = TelegraphAPI()

def create_account():
    return api.create_account(short_name=getpass.getuser(), author_name=getpass.getuser())

def generate_url(type_name: str, index: int) -> str:
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%m-%d")
    suffix = f"-{index}" if index > 1 else ""
    return f"rnw{quote(type_name)}-{date}{suffix}"

def write(content: str, channel: Optional[str] = None):
    create_account()
    metadata = f"rnwpost{channel or ''}"
    page = api.create_page(
        author_name=getpass.getuser(),
        title=metadata, 
        content=[{"tag": "p", "children": [content]}], 
        return_content=True
    )
    print(f"Page created: {page['url']}")

def read(channel: Optional[str], index: int) -> Page:
    return api.get_page(generate_url(f"post{channel or ''}", index), True)

def find_total_posts(channel: Optional[str]) -> int:
    def valid(i):
        try: 
            api.get_page(generate_url(f"post{channel or ''}", i), True)
            return True
        except: 
            return False
    
    if not valid(1): 
        return 0
    
    # 指数搜索 + 二分搜索
    guess = 16
    if valid(guess):
        low, high = guess, guess * 2
        while valid(high): 
            low, high = high, high * 2
        left, right = low + 1, high
    else:
        left, right = 2, guess
    
    while left < right:
        mid = (left + right) // 2
        if valid(mid): 
            left = mid + 1
        else: 
            right = mid
    return left - 1

def read_cache(channel: Optional[str], start: int, end: int):
    url = generate_url(f"list{channel or ''}-{start}-{end}", 1)
    page = api.get_page(url, True)
    
    # 尝试从content或description获取JSON数据
    for field in ["content", "description"]:
        if page.get(field):
            try:
                data = page[field][0]["children"][0] if field == "content" else page[field]
                return json.loads(data)
            except: 
                continue
    return []

def save_cache(channel: Optional[str], start: int, end: int, posts: list):
    create_account()
    metadata = f"rnwlist{channel or ''}-{start}-{end}"
    api.create_page(
        title=metadata, 
        content=[{"tag": "p", "children": [json.dumps(posts)]}], 
        return_content=True
    )

def readlist_stream(channel: Optional[str], pageNo: int = 1, pageSize: int = 10) -> Generator[Dict, None, None]:
    """流式读取消息列表，逐条返回消息"""
    total = find_total_posts(channel)
    end = total - (pageNo - 1) * pageSize
    start = max(1, end - pageSize + 1)
    
    if end <= 0:
        return
    
    # 首先尝试从缓存获取
    try:
        cached_posts = read_cache(channel, start, end)
        if cached_posts:
            # 如果有缓存，快速返回所有消息
            for post in cached_posts:
                yield post
            return
    except:
        pass
    
    # 缓存未命中，逐条读取并流式返回
    posts = []
    for i in range(end, start - 1, -1):
        try:
            post = read(channel, i)
            if post.get("description"):
                post_data = {
                    "name": post.get("author_name", "Anonymous"), 
                    "content": post["description"]
                }
                posts.append(post_data)
                
                # 立即返回这条消息
                yield post_data
                
                # 添加小延迟，让用户看到流式效果
                time.sleep(0.1)
                
        except Exception as e:
            # 读取失败时继续处理下一条
            continue
    
    # 所有消息读取完成后，异步保存缓存
    if posts:
        try:
            save_cache(channel, start, end, posts)
        except Exception as e:
            # 缓存保存失败不影响主流程
            pass

def readlist(channel: Optional[str], pageNo: int = 1, pageSize: int = 10):
    """兼容性函数，返回完整列表"""
    return list(readlist_stream(channel, pageNo, pageSize))

# 批量预加载函数，用于提升性能
def preload_posts(channel: Optional[str], start_page: int = 1, end_page: int = 3):
    """预加载多页数据到缓存"""
    import threading
    
    def preload_worker(page_no):
        try:
            list(readlist_stream(channel, page_no, 10))
        except:
            pass
    
    threads = []
    for page_no in range(start_page, end_page + 1):
        thread = threading.Thread(target=preload_worker, args=(page_no,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    return threads

# 使用示例
if __name__ == "__main__":
    write("HelloWord")
    
    print("Stream loading messages...")
    for post in readlist_stream(pageNo=1, pageSize=10):
        print(f"📨 {post['name']}: {post['content']}")
        print("─" * 50)