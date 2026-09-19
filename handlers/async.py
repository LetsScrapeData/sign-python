# new packages: 
# dependent ApiScriptInData attributes: method, url, data, headers, cookies[(c1,c2)], localStorage[(l1,l2)], vars, errName
# source: https://github.com/username/projectname/blob/main/handlers/website.py 

from schemas import ApiScriptInData, ApiScriptOutData 
import asyncio

async def handle_request(in_data: ApiScriptInData) -> ApiScriptOutData:
    """
    异步处理：接收完整的 ApiScriptInData 对象，返回 ApiScriptOutData 实例
    """
    # 根据输入数据in_data计算输出数据
    newHeaders = {"aa-bb": "AAA_BBB", "x-y": "XXX_YYY", "url": in_data.url};

    # 模拟异步业务逻辑（例如查库或外部请求）
    await asyncio.sleep(0.05) 

    # 构造并返回标准的 ApiScriptOutData 实例
    return ApiScriptOutData(newHeaders=newHeaders)
