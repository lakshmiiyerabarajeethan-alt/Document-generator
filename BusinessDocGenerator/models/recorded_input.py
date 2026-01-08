from pydantic import BaseModel
from typing import List, Any


class RecordedInput(BaseModel):
    application: str = "Mirrix"
    steps: List[Any]
