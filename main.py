import os
import time
import json
import sqlite3
import secrets
import importlib.util
from typing import Optional, Set
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.concurrency import run_in_threadpool
import inspect

from schemas import TokenOutData, PostTokenInData, ApiScriptInData, ApiScriptOutData

app = FastAPI()
HANDLERS_DIR = "./handlers"
DB_FILE = "app_data.db"
# DB_FILE = os.getenv("DB_FILE", "app_data.db") # if docker

# set ENABLE_TOKEN = "yes" to enable token
ENABLE_TOKEN = os.getenv("ENABLE_TOKEN", "no")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "MyGlobalSuperAdminPassword123")


# ==========================================
# 1. SQLite 数据库管理器 (支持覆盖/重置)
# ==========================================
class DatabaseManager:
    _tokens_cache: Set[str] = set()

    @classmethod
    def init_db(cls):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_tokens (
                    username TEXT PRIMARY KEY,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT,
                    client_ip TEXT,
                    method TEXT,
                    url_path TEXT,
                    status_code INTEGER,
                    process_time_ms REAL,
                    request_body TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        cls.refresh_tokens_cache()

    @classmethod
    def refresh_tokens_cache(cls):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token FROM active_tokens")
            # cls._tokens_cache = {row for row in cursor.fetchall()}
            cls._tokens_cache = {token for (token,) in cursor.fetchall()}
        print(f"🌟 已从 SQLite 加载 {len(cls._tokens_cache)} 个有效业务 Token 到内存")

    @classmethod
    def get_all_tokens(cls) -> Set[str]:
        return cls._tokens_cache

    @classmethod
    def add_or_reset_user_token(cls, username: str, reset: bool) -> str:
        """
        为新用户创建唯一 Token，或根据 reset 参数强制重置。
        """
        username = username.strip()
        generated_token = secrets.token_hex(32) # 固定 64 个字符长度
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # 1. 检查用户是否存在
            cursor.execute("SELECT 1 FROM active_tokens WHERE username = ?", (username,))
            user_exists = cursor.fetchone() is not None
            
            if user_exists:
                if not reset:
                    # 如果用户存在且没有传 reset=True，直接抛出 400 错误
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Username '{username}' already exists. Pass 'reset': true to overwrite."
                    )
                else:
                    # 如果用户存在且 reset=True，使用 REPLACE 覆盖
                    cursor.execute(
                        "INSERT OR REPLACE INTO active_tokens (username, token, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (username, generated_token)
                    )
            else:
                # 2. 用户不存在，正常插入
                cursor.execute(
                    "INSERT INTO active_tokens (username, token) VALUES (?, ?)", 
                    (username, generated_token)
                )
            conn.commit()
            
        cls.refresh_tokens_cache()
        return generated_token

    @classmethod
    def remove_user(cls, username: str):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_tokens WHERE username = ?", (username.strip(),))
            conn.commit()
        cls.refresh_tokens_cache()

    @classmethod
    def write_access_log(cls, trace_id: str, client_ip: str, method: str, url_path: str, status_code: int, process_time_ms: float, request_body: str):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO access_logs (trace_id, client_ip, method, url_path, status_code, process_time_ms, request_body)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (trace_id, client_ip, method, url_path, status_code, process_time_ms, request_body))
                conn.commit()
        except Exception as e:
            print(f"❌ 记录日志失败: {e}")

# 初始化数据库

if ENABLE_TOKEN == "yes":
    DatabaseManager.init_db()


# ==========================================
# 2. 全局拦截中间件 (现代高性能、绝不崩溃版)
# ==========================================
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    if ENABLE_TOKEN != "yes":
        return await call_next(request)
    
    start_time = time.time()
    req_body_str = ""
    trace_id = "N/A"
    
    # 【核心安全重构】：只在确有必要时读取纯字节流，利用现代属性缓存，绝不修改 _receive 管道
    if request.method == "POST":
        try:
            # 仅在非流式上传的大型表单情况下安全读取
            body_bytes = await request.body()
            if body_bytes:
                req_body_str = body_bytes.decode("utf-8", errors="ignore")
                try:
                    body_json = json.loads(req_body_str)
                    if isinstance(body_json, dict):
                        trace_id = str(body_json.get("trace_id", "N/A"))
                except Exception:
                    pass
        except Exception:
            pass

    # 执行后续路由：此时没有任何魔改流，FastAPI 就算抛出 400/422 也能完美走完管道
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        req_body_str = f"Exception occurred: {str(e)}"
        raise e  # 允许错误继续外抛
    finally:
        # 无论成功或出错，在最后阶段无安全风险地将日志推向 SQLite
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 截断长报文防撑爆
        safe_body = req_body_str if len(req_body_str) < 2000 else req_body_str[:2000] + "...(truncated)"
        
        try:
            DatabaseManager.write_access_log(
                trace_id=trace_id,
                client_ip=client_ip,
                method=request.method,
                url_path=request.url.path,
                status_code=status_code,
                process_time_ms=process_time_ms,
                request_body=safe_body
            )
        except Exception as db_err:
            print(f"❌ 写入访问日志到 SQLite 失败: {db_err}")

    return response


# ==========================================
# 3. 鉴权依赖项
# ==========================================
async def get_smart_business_token(authorization: Optional[str] = Header(None, description="业务接口凭证")):
    valid_tokens = DatabaseManager.get_all_tokens()
    if not valid_tokens:
        return None

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired business token")
    return token

async def verify_admin_master_key(authorization: Optional[str] = Header(None, description="最高权限主密码")):
    if not authorization:
        raise HTTPException(status_code=401, detail="Admin Authorization header is required")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Permission denied: Invalid Admin Master Key")
    return token


# ==========================================
# 4. Token管理API
# ==========================================
@app.post("/api/token", response_model=TokenOutData, tags=["Token 管理"])
async def create_or_reset_user_token(payload: PostTokenInData, _admin: str = Depends(verify_admin_master_key)):
    """
    输入用户名生成业务 Token。
    1. 如果用户名不存在：直接创建。
    2. 如果用户名已存在 且 reset=false：触发 400 错误。
    3. 如果用户名已存在 且 reset=true：强制用新 Token 覆盖旧 Token。
    """
    if ENABLE_TOKEN != "yes":
        return {
            "code": 200,
            "message": f"Not supported because ENABLE_TOKEN is not 'yes'"
        }

    new_token = DatabaseManager.add_or_reset_user_token(payload.username, payload.reset)
    
    action_msg = "重置" if payload.reset else "生成"
    return {
        "code": 200,
        "message": f"成功为用户 '{payload.username}' {action_msg} Token",
        "data": {
            "username": payload.username,
            "token": new_token,
            "token_type": "Bearer"
        }
    }

@app.delete("/api/token/{username}", response_model=TokenOutData, tags=["Token 管理"])
async def delete_user_token(username: str, _admin: str = Depends(verify_admin_master_key)):
    if ENABLE_TOKEN != "yes":
        return {
            "code": 200,
            "message": f"Not supported because ENABLE_TOKEN is not 'yes'"
        }

    DatabaseManager.remove_user(username)
    return {
        "code": 200,
        "message": f"用户 '{username}' 的 Token 已成功注销"
    }


# ==========================================
# 4. 动态注册业务路由 
# ==========================================
def register_dynamic_routes():
    if not os.path.exists(HANDLERS_DIR):
        print(f"目录 {HANDLERS_DIR} 不存在！")
        return

    for filename in os.listdir(HANDLERS_DIR):
        if filename.endswith(".py") and not filename.startswith("__"):
            service_name = filename[:-3]
            file_path = os.path.join(HANDLERS_DIR, filename)

            try:
                spec = importlib.util.spec_from_file_location(service_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                handler_func = getattr(module, "handle_request", None)
                if not handler_func:
                    continue  # 跳过没有处理函数的文件

                def create_route_handler(func=handler_func):
                    async def route_handler(
                        payload: ApiScriptInData, 
                        _token: Optional[str] = Depends(get_smart_business_token)
                    ) -> ApiScriptOutData:
                        try:
                            # 兼容异步与同步，直接将整个 payload 传给子模块
                            if inspect.iscoroutinefunction(func):
                                return await func(payload)
                            else:
                                return await run_in_threadpool(func, payload)
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
                    return route_handler
                
                # 动态注册路由，并显式指定 response_model
                app.add_api_route(
                    path=f"/api/sign/{service_name}",
                    endpoint=create_route_handler(),
                    methods=["POST"],
                    response_model=ApiScriptOutData,  # 强制生成 Swagger 响应文档并自动过滤/校验输出
                    response_model_exclude_none=True,  # 全自动剔除所有值为 None 的字段
                    summary=f"Dynamic handler for {service_name}"
                )
                print(f"成功注册路由: POST /api/sign/{service_name}")

            except Exception as e:
                print(f"加载模块 {filename} 失败: {e}")
                

# ==========================================
# 5. 动态路由注册
# ==========================================
register_dynamic_routes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=6699)
