from pydantic import BaseModel
from zyndai_agent import AgentPayload


class RequestPayload(AgentPayload):
    pass


class ResponsePayload(BaseModel):
    model_config = {"extra": "allow"}
    response: str = ""


MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
