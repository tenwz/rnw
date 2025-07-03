from telegraph import TelegraphAPI, Page
import datetime
from urllib.parse import quote
import getpass
from typing import Optional
import json

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
    page = api.create_page(author_name=getpass.getuser(),title=metadata, content=[{"tag": "p", "children": [content]}], return_content=True)
    print(f"Page created: {page['url']}")

def read(channel: Optional[str], index: int) -> Page:
    return api.get_page(generate_url(f"post{channel or ''}", index), True)

def find_total_posts(channel: Optional[str]) -> int:
    def valid(i): 
        try: api.get_page(generate_url(f"post{channel or ''}", i), True); return True
        except: return False
    
    if not valid(1): return 0
    
    # 指数搜索 + 二分搜索
    guess = 16
    if valid(guess):
        low, high = guess, guess * 2
        while valid(high): low, high = high, high * 2
        left, right = low + 1, high
    else:
        left, right = 2, guess
    
    while left < right:
        mid = (left + right) // 2
        if valid(mid): left = mid + 1
        else: right = mid
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
            except: continue
    return []

def save_cache(channel: Optional[str], start: int, end: int, posts: list):
    create_account()
    metadata = f"rnwlist{channel or ''}-{start}-{end}"
    api.create_page(title=metadata, content=[{"tag": "p", "children": [json.dumps(posts)]}], return_content=True)

def readlist(channel: Optional[str], pageNo: int = 1, pageSize: int = 10):
    total = find_total_posts(channel)
    end = total - (pageNo - 1) * pageSize
    start = max(1, end - pageSize + 1)
    
    if end <= 0: return []
    
    try:
        return read_cache(channel, start, end)
    except:
        posts = []
        for i in range(end, start - 1, -1):
            try:
                post = read(channel, i)
                if post.get("description"):
                    posts.append({"name": post.get("author_name", "Anonymous"), "content": post["description"]})
            except: continue
        save_cache(channel, start, end, posts)
        return posts

# 使用示例
if __name__ == "__main__":
    write("HelloWord")
    news = readlist(pageNo=1,pageSize=10)
    for item in news:
        print(f"{item['name']}: {item['content']}")
        print("-" * 50)