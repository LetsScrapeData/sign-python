from schemas import ApiScriptInData
import re
from urllib.parse import urlparse, parse_qs


def get_cookie(name: str, in_data: ApiScriptInData) -> str:
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


def get_storage(name: str, in_data: ApiScriptInData) -> str:
    """从 in_data.localStorage 字典中安全获取指定键的值。"""
    # 如果 localStorage 为 None，直接返回空
    if not in_data.localStorage:
        return ""
        
    # 直接作为标准的 Python 字典利用 .get() 进行安全查找
    val = in_data.localStorage.get(name)
    return str(val) if val is not None else ""


def get_header(header_name: str, in_data: ApiScriptInData) -> str:
    """Safely retrieves a header from the Pydantic 'headers' RootModel."""
    # Ensure headers and its underlying root dictionary exist
    if in_data.headers and in_data.headers.root:
        val = in_data.headers.root.get(header_name)
        return str(val) if val is not None else ""
    return ""


def get_variable(var_name: str, in_data: ApiScriptInData) -> str:
    """Safely retrieves a variable from the Pydantic 'vars' RootModel."""
    if in_data.vars and in_data.vars.root:
        val = in_data.vars.root.get(var_name)
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


def get_url_param(param_name: str, in_data: ApiScriptInData) -> str:
    """Extracts a specific query parameter from the URL."""
    if not in_data.url:
        return ""
    try:
        query_str = urlparse(in_data.url).query
        params = parse_qs(query_str)
        
        val = params.get(param_name)
        return val[0] if val else ""
    except Exception:
        return ""
