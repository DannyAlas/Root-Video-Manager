# pydantic base models for the data structures used in the RVM
from asyncio import protocols
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, TypeVar
from uuid import uuid4

from pandas import DataFrame
from pydantic import BaseModel, Field, validator

DataFrameType = TypeVar("DataFrameType", DataFrame, dict)


def uid_gen():
    return str(uuid4())


class AnimalBase(BaseModel):
    uid: str = ""
    genotype: str = ""
    alive: bool = True
    excluded: bool = False
    notes: str = ""

    def validateAnimal(self):
        if type(self.uid) != str or len(self.uid) == 0:
            raise ValueError("The animal uid is invalid")
        if type(self.genotype) != str:
            raise ValueError("The animal genotype is invalid")
        if type(self.alive) != bool:
            raise ValueError("The animal alive is invalid")
        if type(self.excluded) != bool:
            raise ValueError("The animal excluded is invalid")
        if type(self.notes) != str:
            raise ValueError("The animal notes is invalid")


class BoxBase(BaseModel):
    uid: str = ""
    camera: str = ""
    notes: str = ""

    def validateBox(self):
        if type(self.uid) != str or len(self.uid) == 0:
            raise ValueError("The box uid is invalid")
        if type(self.camera) != str:
            raise ValueError("The box camera is invalid")
        if type(self.notes) != str:
            raise ValueError("The box notes is invalid")


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

    def validateTrial(self):
        if type(self.uid) != str or len(self.uid) == 0:
            raise ValueError("The trial uid is invalid")
        try:
            if self.animal is not None:
                self.animal.validateAnimal()
            else:
                raise ValueError("The trial animal is None")
        except Exception as e:
            raise ValueError(f"The trial animal for trial {self.uid} is invalid: {e}")
        try:
            self.box.validateBox()
        except ValueError as e:
            raise ValueError(f"The trial box for trial {self.uid} is invalid: {e}")

    def load(self, **kwargs):
        # set our attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def stop(self):
        self.state = "Stopped"
        self.end_time = datetime.now()

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
