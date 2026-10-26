from schemas import ApiScriptInData
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict;


def get_cookie(in_data: ApiScriptInData, name: str) -> str:
    """从 in_data.cookies 字符串中解析并获取指定名称的 cookie 值。"""
    # 如果 cookies 为 None 或空字符串，直接返回空
    if not in_data.cookies:
        return ""
    
    cookie_obj = {}
    # 使用正则切分字符串，完美模拟 JS 的 .split(/;\s*/)
    items = re.split(r";\s*", in_data.cookies.strip())
    
    for item in items:
        if "=" in item:
            # 限制只切分第一个 '='，防止 cookie 属性值本身包含 '=' 导致报错
            key, val = item.split("=", 1)
            cookie_obj[key] = val
            
    val = cookie_obj.get(name)
    return val if val is not None else ""


def get_cookies(in_data: ApiScriptInData) -> dict[str, str]:
    """从 in_data.cookies 字符串中解析并获取指定名称的 cookie 值。"""
    cookie_obj = {}

    # 如果 cookies 为 None 或空字符串，直接返回{}
    if not in_data.cookies:
        return cookie_obj 
    
    # 使用正则切分字符串，完美模拟 JS 的 .split(/;\s*/)
    items = re.split(r";\s*", in_data.cookies.strip())
    
    for item in items:
        if "=" in item:
            # 限制只切分第一个 '='，防止 cookie 属性值本身包含 '=' 导致报错
            key, val = item.split("=", 1)
            cookie_obj[key] = val
            
    return cookie_obj


def get_storage(in_data: ApiScriptInData, name: str) -> str:
    """从 in_data.localStorage 字典中安全获取指定键的值。"""
    # 如果 localStorage 为 None，直接返回空
    if not in_data.localStorage:
        return ""
        
    # 直接作为标准的 Python 字典利用 .get() 进行安全查找
    val = in_data.localStorage.get(name)
    return str(val) if val is not None else ""


def get_header(in_data: ApiScriptInData, header_name: str) -> str:
    """Safely retrieves a header from the Pydantic 'headers' RootModel."""
    if in_data.headers:
        val = in_data.headers.get(header_name)
        return str(val) if val is not None else ""
    return ""


def get_variable(in_data: ApiScriptInData, var_name: str) -> str:
    """Safely retrieves a variable from the Pydantic 'vars' RootModel."""
    if in_data.vars and in_data.vars.root:
        root = in_data.vars.root
        var_names = var_name.split(".")
        cnt = len(var_names)
        if cnt > 2:
            return ""
        elif cnt == 2:
            val = root.get(var_names[0])
            if isinstance(val, Dict):
                val = val.get(var_names[1])
            else:
                return ""
        else:
            val = root.get(var_name)
        return str(val) if val is not None else ""
    return ""


def get_url_path(in_data: ApiScriptInData) -> str:
    """Extracts the pathname from the URL."""
    if not in_data.url:
        return ""
    try:
        return urlparse(in_data.url).path
    except Exception:
        return ""

def get_url_query(in_data: ApiScriptInData) -> str:
    """Extracts the pathname from the URL."""
    if not in_data.url:
        return ""

    try:
        parsed = urlparse(in_data.url)
        if in_data.method != "GET":
            return parsed.query

        query_dict = parse_qs(parsed.query)
        if isinstance(in_data.data, Dict):
            for key, value in in_data.data.items():
                query_dict[key] = value if isinstance(value, list) else [value]

        return urlencode(query_dict, doseq=True, safe=in_data.safe)
    except Exception:
        return ""

def get_url_complete(in_data: ApiScriptInData) -> str:
    """Extracts the pathname from the URL."""
    if not in_data.url:
        return ""
    elif in_data.method != "GET":
        return in_data.url

    try:
        parsed = urlparse(in_data.url)

        query_dict = parse_qs(parsed.query)
        if isinstance(in_data.data, Dict):
            for key, value in in_data.data.items():
                query_dict[key] = value if isinstance(value, list) else [value]

        new_query = urlencode(query_dict, doseq=True, safe=in_data.safe)
        new_components = parsed._replace(query = new_query)
        return urlunparse(new_components)
    except Exception:
        return ""

def get_url_path_query(in_data: ApiScriptInData) -> str:
    """Extracts the pathname from the URL."""
    if not in_data.url:
        return ""
    try:
        parsed = urlparse(in_data.url)
        query = get_url_query(in_data)
        
        if not query:
            return parsed.path
        else:
            return f"{parsed.path}?{query}"
    except Exception:
        return ""


def get_url_param(in_data: ApiScriptInData, param_name: str) -> str:
    """Extracts the pathname from the URL."""
    if not in_data.url:
        return ""
    try:
        parsed = urlparse(in_data.url)
        query_dict = parse_qs(parsed.query)
        if isinstance(in_data.data, Dict):
            for key, value in in_data.data.items():
                query_dict[key] = value

        val = query_dict.get(param_name)
        return val if val else ""
    except Exception:
        return ""
