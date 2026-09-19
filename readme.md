本项目仅提供签名函数服务的基本框架，不提供任何网站的签名函数。本项目开源免费，使用者需遵守相关法律和网站的要求，包括但不限于用于学习目的、严格限制访问频率等；本项目不能确保本项目和第三方的签名函数的正确性和潜在的安全风险，不承担任何不良后果。

## 风险提示

> [!WARNING] 风险提示
>
> 1. 使用签名函数服务很可能造成访问账号异常，包括但不限于临时禁制访问或封号，请谨慎使用。
> 2. 签名函数经常需要访问headers、cookies、localStorage等敏感信息，为了减少敏感信息泄露风险，建议在本地不能访问外网的环境中学习使用。如发现第三方签名函数尝试窃取敏感信息等恶意行为，欢迎告知。
> 3. 鉴于潜在的安全风险，本项目根据具体情况，可能随时终止本开源项目。

## 安装与运行

1.  一键同步环境（创建虚拟环境并安装所有依赖）

```bash
uv sync
# uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple # 使用清华镜像安装
```

2. 本地快速启动网关（无需激活虚拟环境）

```bash
# Linux / macOS
uv run main.py

# Windows PowerShell
uv run main.py
```

3. 动态添加新依赖（例如未来需要用到 xxx）

```bash
uv add xxx
```

## 如何添加一个新网站的签名计算

在 `handlers/` 目录下的每个python文件提供一个网站的签名计算，文件名为网站昵称。

假设网站昵称为`newsite`，如果为同步，则拷贝`sync.py`为`newsite.py`；如果为异步，则拷贝`async.py`为`newsite.py`，然后修改新文件即可。

第一行，说明该签名函数需要访问的新包。

第二行，请如实填写签名函数需要访问ApiScriptInData的哪些属性数据，该配置可能影响输入数据内容和签名函数风险评估。

第三行，签名函数地址，可能用于定期同步；建议先fork本项目，可能便于同步。

## 如何启用token管理

缺省用户访问服务不需要token，如果需要启用token管理：

```bash
# Linux / macOS 终端
export ENABLE_TOKEN="yes"
export ADMIN_TOKEN="MyGlobalSuperAdminPassword123"

# Windows PowerShell 终端
\$env:ENABLE_TOKEN="yes"
\$env:ADMIN_TOKEN="MyGlobalSuperAdminPassword123"
```

你可以通过访问 `http://localhost:8000/docs` 直接进入 **Swagger 交互式文档页面** 查看如何管理token。
