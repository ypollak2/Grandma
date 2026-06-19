from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Impact(BaseModel):
    positive: Optional[str] = None
    negative: Optional[str] = None
    neutral: Optional[str] = None


class Verdict(BaseModel):
    what_happened: str = Field(default="")
    what_changed: str = Field(default="")
    impact: Impact = Field(default_factory=Impact)
    net_gain: str = Field(default="")
    action_items: List[str] = Field(default_factory=list)
    story_so_far: Optional[str] = Field(default=None)


class Mode(str, Enum):
    DEFAULT = "default"
    DEEP = "deep"
    OFF = "off"
