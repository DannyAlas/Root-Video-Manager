# pydantic base models for the data structures used in the RVM
from asyncio import protocols
from pydantic import BaseModel, Field, validator
from uuid import uuid4
from typing import Literal, List, Optional, TypeVar
from datetime import datetime
from pathlib import Path
from pandas import DataFrame

DataFrameType = TypeVar("DataFrameType", DataFrame, dict)

def uid_gen():
    return str(uuid4())

class AnimalBase(BaseModel):
    uid: str = ""
    genotype: str = ""
    alive: bool = True
    excluded: bool = False
    notes: str = ""

class BoxBase(BaseModel):
    uid: str = ""
    camera: str = ""
    notes: str = ""

class TrialBase(BaseModel):
    uid: str = Field(default_factory=uid_gen)
    animal: Optional[AnimalBase]
    box: Optional[BoxBase]
    protocol: Optional[str] = None
    state: Literal["Waiting", "Running", "Finished", "Stopped", "Failed"] = "Waiting"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    original_data_location: Optional[Path] = None
    video_location: Optional[Path] = None
    data: Optional[DataFrameType] = None
    notes: str = ""

    class Config:
        arbitrary_types_allowed = True

class ProtocalBase(BaseModel):
    uid: str = ""
    description: Optional[str] = None
    animals: List[AnimalBase] = []
    boxes: List[BoxBase] = []
    trials: List[TrialBase] = []

class ProjectSettingsBase(BaseModel):
    uid: str = Field(default_factory=uid_gen)
    project_name: str = ""
    created: datetime = Field(default_factory=datetime.now)
    project_location: Path = Path.cwd()
    window_size: tuple[int, int] = (1280, 720)
    window_position: tuple[int, int] = (0, 0)
    video_devices: dict[str, str] = {}
    protocols: list[ProtocalBase] = []
    animals: list[AnimalBase] = []
    trials: list[TrialBase] = []
    boxes: list[BoxBase] = []
