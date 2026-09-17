from pydantic import BaseModel


class Credentials(BaseModel):
    email: str
    password: str
    display_name: str = ""


class ConversationCreate(BaseModel):
    title: str = "Cuộc trò chuyện mới"


class ConversationRename(BaseModel):
    title: str


class ChatRequest(BaseModel):
    text: str
    direct_search: bool = False


class FeedbackRequest(BaseModel):
    message_id: int
    verdict: str          # "phu_hop" | "khong_phu_hop"
    note: str = ""


class ResetRequest(BaseModel):
    scope: str = "my_conversations"   # my_conversations | all_conversations | everything
    confirm: str = ""                 # phải gõ đúng "XOA" mới chạy


class DevToggle(BaseModel):
    enabled: bool | None = None       # None = đảo trạng thái


class WebSearchTest(BaseModel):
    query: str = ""
