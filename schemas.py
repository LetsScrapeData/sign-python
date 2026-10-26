# schemas.py
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, RootModel

class PostTokenInData(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    reset: bool = Field(False, description="如果为 true 且用户已存在，则强制重置并生成新 Token")

class DeleteTokenInData(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")

class TokenOutData(BaseModel):
    code: int = Field(200, description="状态码，200为成功")
    message: str = Field("success", description="提示信息")
    data: Optional[Dict[str, Any]] = Field(None, description="业务返回数据")
    ext_info: Optional[Dict[str, Any]] = Field(None, description="额外的扩展信息（可选）")


# ==========================================
# Variables Type Definition
# ==========================================
class Variables(RootModel[Dict[str, Any]]):
    root: Dict[str, Any]

    # Helper properties for easy access to the core structured fields
    @property
    def inParas(self) -> Dict[str, str]:
        return self.root.get("inParas", {})

    @property
    def userData(self) -> Dict[str, str]:
        return self.root.get("userData", {})

""" Excerpt from lsd_en.xsd:
  <xs:simpleType name="enumErrname">
    <xs:restriction base="xs:string">
      <!-- Execution terminates normally and the task is considered completed. -->
      <xs:enumeration value="normal" />
      <!-- Invalid task parameter(parasstr) and the task is considered completed. -->
      <xs:enumeration value="parasinvalid" />
      <!-- invalid automatic capability, such as wrong password or apiKey. -->
      <xs:enumeration value="capinvalid" />
      <!-- capability is temporarily locked and will be automatically unlocked later -->
      <xs:enumeration value="caplocked" />
      <!-- The state data of the logged-in capability has expired. If the capability is manually logged in, please log in again. -->
      <xs:enumeration value="capexpired" />
      <!-- The proxy(IP) is temporarily blocked from accessing this domain. -->
      <xs:enumeration value="proxylocked" />
      <!-- The proxy(IP) is permanently banned from accessing this domain. -->
      <xs:enumeration value="proxyforbidden" />
      <!-- The template is invalid and needs to be updated before it can be executed again. -->
      <xs:enumeration value="cfginvalid" />
      <!-- Unable to solve the captcha normally. -->
      <xs:enumeration value="captchafailed" />
      <xs:enumeration value="other" />
      <!-- The error is ignored and execution continues. -->
      <xs:enumeration value="ignore" />
    </xs:restriction>
  </xs:simpleType>
"""
ErrName = Literal[ "normal", "parasinvalid", "capinvalid", "capexpired", "proxylocked", "proxyforbidden", "cfginvalid", "captchafailed", "other", "ignored"]

# ==========================================
# API Script Interfaces
# ==========================================
class ApiScriptInData(BaseModel):
    method: Literal["DELETE", "GET", "POST", "PUT"]
    url: str
    safe: str
    headers: Optional[Dict[str, str]] = None  # valid if original headers is not undefined
    data: Optional[Any] = None  # valid if original request data is not undefined
    cookies: Optional[str] = None  # valid if script.external includes "cookies"
    localStorage: Optional[Dict[str, str]] = None  # valid if script.external includes "localStorage"
    vars: Variables
    errName: ErrName  # value of errname attribute in action_api

# {} will be treated as {errName: "cfginvalid"}
class ApiScriptOutData(BaseModel):
    headers: Optional[Dict[str, str]] = None  # headers to be used (original headers are ignored)
    newHeaders: Optional[Dict[str, str]] = Field(default=None, alias="newHeaders")  # new headers to be added/replaced; ignored if headers has a valid value
    data: Optional[Any] = None  # replace original request data if data is not undefined
    errName: Optional[ErrName] = Field(default=None, alias="errName")  # optional error, such as "cfginvalid" or "other". return errName (and message) if failed. invalid errName is treated as "cfginvalid"
    message: Optional[str] = None  # When cookies or localStorage are accessed, the message is ignored

