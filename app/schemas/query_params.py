from pydantic import BaseModel
from typing import Optional


class QueryParams(BaseModel):
    skip: int = 0
    limit: int = 20
    sort: Optional[str] = None