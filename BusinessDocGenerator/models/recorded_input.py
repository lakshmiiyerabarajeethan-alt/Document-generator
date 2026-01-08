from pydantic import BaseModel
from typing import List, Any


class RecordedInput(BaseModel):
    application: str = "Stockmann STEP / OPIL UI"
    steps: List[Any]
