# 这是我写代码的副产品，一个简单的推特服务
# 底层采用了telegra.ph 

import requests
import json
from typing import Dict, List, Optional, Union, Any, TypedDict



# 类型定义
class Account(TypedDict, total=False):
    short_name: str
    author_name: str
    author_url: str
    access_token: str
    auth_url: str
    page_count: int

class Page(TypedDict, total=False):
    path: str
    url: str
    title: str
    description: str
    author_name: str
    author_url: str
    image_url: str
    content: List[Any]
    views: int
    can_edit: bool

class PageList(TypedDict):
    total_count: int
    pages: List[Page]

class PageViews(TypedDict):
    views: int

class NodeElement(TypedDict, total=False):
    tag: str
    attrs: Dict[str, str]
    children: List[Union[str, 'NodeElement']]

Node = Union[str, NodeElement]

class TelegraphAPI:
    BASE_URL = "https://api.telegra.ph/"
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
    
    def _request(
        self, 
        method: str, 
        params: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
        use_post: bool = False
    ) -> Dict[str, Any]:
        """内部请求方法"""
        url = f"{self.BASE_URL}{method}"
        if path:
            url = f"{url}/{path}"
        
        try:
            if use_post:
                response = requests.post(url, data=params)
            else:
                response = requests.get(url, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise TelegraphException(f"API error: {error}")
                
            return data.get("result", {})
        
        except requests.exceptions.RequestException as e:
            raise TelegraphException(f"Network error: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise TelegraphException("Invalid JSON response") from e
    
    def create_account(
        self,
        short_name: str,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None
    ) -> Account:
        """
        创建新的Telegraph账户
        
        :param short_name: 账户短名称 (1-32字符)
        :param author_name: 默认作者名称 (0-128字符)
        :param author_url: 默认作者链接 (0-512字符)
        :return: 账户信息 (包含access_token)
        """
        params = {"short_name": short_name}
        if author_name:
            params["author_name"] = author_name
        if author_url:
            params["author_url"] = author_url
            
        result = self._request("createAccount", params)
        self.access_token = result.get("access_token", self.access_token)
        return result
    
    def edit_account_info(
        self,
        short_name: Optional[str] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,   
        access_token: Optional[str] = None
    ) -> Account:
        """
        编辑账户信息
        
        :param short_name: 新账户名称 (1-32字符)
        :param author_name: 新作者名称 (0-128字符)
        :param author_url: 新作者链接 (0-512字符)
        :param access_token: 访问令牌 (默认使用实例令牌)
        :return: 更新后的账户信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        params = {"access_token": token}
        if short_name:
            params["short_name"] = short_name
        if author_name:
            params["author_name"] = author_name
        if author_url:
            params["author_url"] = author_url
            
        return self._request("editAccountInfo", params)
    
    def get_account_info(
        self,
        fields: Optional[List[str]] = None,
        access_token: Optional[str] = None
    ) -> Account:
        """
        获取账户信息
        
        :param fields: 要返回的字段列表
        :param access_token: 访问令牌 (默认使用实例令牌)
        :return: 账户信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        params = {"access_token": token}
        if fields:
            params["fields"] = json.dumps(fields)
            
        return self._request("getAccountInfo", params)
    
    def revoke_access_token(
        self, 
        access_token: Optional[str] = None
    ) -> Account:
        """
        撤销并重新生成访问令牌
        
        :param access_token: 当前访问令牌 (默认使用实例令牌)
        :return: 包含新令牌的账户信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        result = self._request("revokeAccessToken", {"access_token": token})
        self.access_token = result.get("access_token", self.access_token)
        return result
    
    def create_page(
        self,
        title: str,
        content: List[Node],
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
        return_content: bool = False,
        access_token: Optional[str] = None
    ) -> Page:
        """
        创建新页面
        
        :param title: 页面标题 (1-256字符)
        :param content: 页面内容 (Node数组)
        :param author_name: 作者名称 (0-128字符)
        :param author_url: 作者链接 (0-512字符)
        :param return_content: 是否返回内容
        :param access_token: 访问令牌 (默认使用实例令牌)
        :return: 创建的页面信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        params = {
            "access_token": token,
            "title": title,
            "content": json.dumps(content),
            "return_content": str(return_content).lower()
        }
        if author_name:
            params["author_name"] = author_name
        if author_url:
            params["author_url"] = author_url
            
        return self._request("createPage", params, use_post=True)
    
    def edit_page(
        self,
        path: str,
        title: str,
        content: List[Node],
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
        return_content: bool = False,
        access_token: Optional[str] = None
    ) -> Page:
        """
        编辑现有页面
        
        :param path: 页面路径
        :param title: 新标题 (1-256字符)
        :param content: 新内容 (Node数组)
        :param author_name: 新作者名称 (0-128字符)
        :param author_url: 新作者链接 (0-512字符)
        :param return_content: 是否返回内容
        :param access_token: 访问令牌 (默认使用实例令牌)
        :return: 更新后的页面信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        params = {
            "access_token": token,
            "title": title,
            "content": json.dumps(content),
            "return_content": str(return_content).lower()
        }
        if author_name:
            params["author_name"] = author_name
        if author_url:
            params["author_url"] = author_url
            
        return self._request("editPage", params, path=path, use_post=True)
    
    def get_page(
        self, 
        path: str, 
        return_content: bool = False
    ) -> Page:
        """
        获取页面信息
        
        :param path: 页面路径
        :param return_content: 是否返回内容
        :return: 页面信息
        """
        params = {"return_content": str(return_content).lower()}
        return self._request("getPage", params, path=path)
    
    def get_page_list(
        self,
        offset: int = 0,
        limit: int = 50,
        access_token: Optional[str] = None
    ) -> PageList:
        """
        获取账户下的页面列表
        
        :param offset: 起始偏移量
        :param limit: 返回数量限制 (0-200)
        :param access_token: 访问令牌 (默认使用实例令牌)
        :return: 页面列表信息
        """
        token = access_token or self.access_token
        if not token:
            raise TelegraphException("access_token is required")
        
        params = {
            "access_token": token,
            "offset": offset,
            "limit": limit
        }
        return self._request("getPageList", params)
    
    def get_views(
        self,
        path: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None
    ) -> PageViews:
        """
        获取页面浏览数据
        
        :param path: 页面路径
        :param year: 年份 (2000-2100)
        :param month: 月份 (1-12)
        :param day: 日期 (1-31)
        :param hour: 小时 (0-24)
        :return: 浏览数据
        """
        params = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        if day is not None:
            params["day"] = day
        if hour is not None:
            params["hour"] = hour
            
        return self._request("getViews", params, path=path)

class TelegraphException(Exception):
    """Telegraph API异常基类"""
    pass

# ===================== 使用示例 =====================
if __name__ == "__main__":
    # 初始化API客户端
    api = TelegraphAPI()
    import getpass


    
    try:
        # 创建账户
        account = api.create_account(
            short_name=getpass.getuser(),
            author_name=getpass.getuser()
        )
        print(f"Account created: {account['short_name']}")
        print(f"Access token: {account['access_token']}")
        
        # 创建页面
        page_content = [
            {"tag": "h3", "children": ["Hi"]},
            {"tag": "p", "children": ["This is a sample paragraph created by the Telegraph API"]},
            {"tag": "p", "children": [
                "Check out ",
                {"tag": "a", "attrs": {"href": "https://example.com"}, "children": ["this link"]}
            ]}
        ]
        
        new_page = api.create_page(
            title="rnwpost",
            content=page_content,
            return_content=True
        )
        print(f"Page created: {new_page['url']}")
        print(f"Page views: {new_page['views']}")
        
        # 获取页面信息
        page_path = new_page['path']
        print(page_path)
        page_info = api.get_page(page_path, return_content=True)    
        print(page_info)
        print(f"Page title: {page_info['title']}")
        
        # 获取账户信息
        account_info = api.get_account_info(fields=["short_name", "page_count"])
        print(f"Total pages: {account_info.get('page_count', 0)}")
        
        # 获取页面浏览数据
        views_data = api.get_views(page_path, year=2023, month=10)
        print(f"October 2023 views: {views_data['views']}")
        
    except TelegraphException as e:
        print(f"Error: {str(e)}")