from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArticleModel(BaseModel):
    title:        str
    url:          str
    content:      str
    source_name:  str
    category_id:  Optional[str] = None
    is_posted:    bool = False
    published_at: Optional[datetime] = None


class LogModel(BaseModel):
    event_type: str                   # SCRAPE | POST | ERROR | CLASSIFY | AI
    message:    str
    article_id: Optional[str] = None
