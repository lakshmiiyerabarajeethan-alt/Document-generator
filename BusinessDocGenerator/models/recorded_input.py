from pydantic import BaseModel
from typing import List, Optional


class Metadata(BaseModel):
    recordedAt: Optional[str] = None
    totalSteps: Optional[int] = None
    totalScreenshots: Optional[int] = None
    browser: Optional[str] = None


class RecordedStep(BaseModel):
    action: str
    id: int
    timestamp: int

    selector: Optional[str] = None
    selectorBackup: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    value: Optional[str] = None
    placeholder: Optional[str] = None


class RecordedInput(BaseModel):
    metadata: Optional[Metadata] = None
    steps: List[RecordedStep]
