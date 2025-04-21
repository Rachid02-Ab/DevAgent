from pydantic import BaseModel

class CodeRequest(BaseModel):
    instruction: str

class CodeResponse(BaseModel):
    code: str
    output: str
    full_result: str