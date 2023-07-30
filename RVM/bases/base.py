# pydantic base models for the data structures used in the RVM
import os
from datetime import datetime
from pathlib import Path
from socket import gethostname
from subprocess import check_output
from typing import List, Literal, Optional, TypeVar
from uuid import UUID, getnode, uuid4

from pandas import DataFrame

from pydantic import BaseModel, Field

DataFrameType = TypeVar("DataFrameType", DataFrame, dict)


def uid_gen():
    return str(uuid4())


def get_machine_name_uid():
    """
    Get the machine name and id

    Returns
    -------
    dict
        The machine name and id
    """
    try:
        host_name = gethostname()
    except Exception:
        host_name = "Unknown"
    try:
        if os.name != "nt":
            machine_id = UUID(int=getnode())
        else:
            machine_id = (
                check_output("wmic csproduct get uuid").decode().split("\n")[1].strip()
            )
    except Exception:
        machine_id = "Unknown"
    return {"host_name": host_name, "machine_id": machine_id}


class AnimalBase(BaseModel):
    uid: str
    genotype: str = ""
    alive: bool = True
    excluded: bool = False
    notes: str = ""
    deleted: bool = False

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
    uid: str
    camera: str = ""
    notes: str = ""
    deleted: bool = False

    # @validator('uid')
    # def passwords_match(cls, v):
    #     if len(v) == 0:
    #         raise ValueError("The box uid is invalid")
    #     if not v.isalnum():
    #         raise ValueError("The box uid is invalid")


class TrialBase(BaseModel):
    uid: str = Field(default_factory=uid_gen)
    animal: AnimalBase
    box: BoxBase
    protocol: Optional[str] = None
    state: Literal["Waiting", "Running", "Finished", "Stopped", "Failed"] = "Waiting"
    created: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    original_data_location: Optional[Path] = None
    video_location: Optional[Path] = None
    data: Optional[DataFrameType] = None  # type: ignore
    notes: str = ""
    deleted: bool = False

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

    class Config:
        arbitrary_types_allowed = True


class ProtocolBase(BaseModel):
    uid: str = ""
    description: Optional[str] = None
    animals: List[AnimalBase] = []
    boxes: List[BoxBase] = []
    trials: List[TrialBase] = []
    deleted: bool = False


class ProjectSettingsBase(BaseModel):
    uid: str = Field(default_factory=uid_gen)
    host: dict = Field(default_factory=get_machine_name_uid, alias="host")
    created: datetime = Field(default_factory=datetime.now)
    project_name: str = ""
    project_location: Path
    video_location: Optional[Path] = None
    window_size: tuple[int, int] = (1280, 720)
    window_position: tuple[int, int] = (0, 0)
    video_devices: dict[str, str] = {}
    protocols: list[ProtocolBase] = []
    animals: list[AnimalBase] = []
    trials: list[TrialBase] = []
    boxes: list[BoxBase] = []
