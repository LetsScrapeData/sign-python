# new packages: 
# dependent ApiScriptInData attributes: method, url, data, headers, cookies[(c1,c2)], localStorage[(l1,l2)], vars, errName
# source: https://github.com/username/projectname/blob/main/handlers/website.py 

from schemas import ApiScriptInData, ApiScriptOutData 

def handle_request(in_data: ApiScriptInData) -> ApiScriptOutData:
    """
    同步处理：接收完整的 ApiScriptInData 对象，返回 ApiScriptOutData 实例
    """
    # 根据输入数据in_data计算输出数据
    newHeaders = {"aa-bb": "aaa_bbb", "x-y": "xxx_yyy", "url": in_data.url};

    # 构造并返回标准的 ApiScriptOutData 实例
    return ApiScriptOutData(newHeaders=newHeaders)
