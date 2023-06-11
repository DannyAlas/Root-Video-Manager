from re import U
import pandas
import pydantic
import json
import os
import datetime
from typing import Union


class Animal(pydantic.BaseSettings):
    animalId: str = "AnimalID"
    genotype: str = "Genotype"
    alive: bool = True
    excluded: bool = False
    notes: str = ""
    trials: list = []

    def dict(self):
        return {
            "animalId": self.animalId,
            "genotype": self.genotype,
            "alive": self.alive,
            "excluded": self.excluded,
            "notes": self.notes,
        }

    def json(self):
        return json.dumps(self.dict(), indent=4)

    def fromJson(json_string):
        data = json.loads(json_string)
        return Animal(**data)


class Trial(pydantic.BaseSettings):
    trialId: str = "trialId"
    subject: Animal = Animal()
    box: str = "BoxID"
    # custom date time format
    start_time: str
    end_time: str
    protocal_name: str = "Protocal"
    original_data_location: str
    video_location: str = None
    data: pandas.DataFrame = pandas.DataFrame()

    def dict(self):
        return {
            "trialId": self.trialId,
            "subject": self.subject.dict(),
            "box": self.box,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "protocal_name": self.protocal_name,
            "original_data_location": self.original_data_location,
            "video_location": self.video_location,
            "data": self.data.to_dict(),
        }

    # define serialisation methods
    def json(self):
        return json.dumps(self.dict(), indent=4)

    def fromJson(json_string):
        # convert json data dict to a data frame
        data = json.loads(json_string)
        data["data"] = pandas.DataFrame.from_dict(data["data"])
        return Trial(**data)


class Box(pydantic.BaseSettings):
    """Represents a box in the lab"""

    boxId: str = "BoxID"
    camera: str = "CameraAltID"
    trials: list[Trial] = []
    notes: str = ""

    def dict(self):
        return {
            "boxId": self.boxId,
            "camera": self.camera,
            "trials": [trial.dict() for trial in self.trials],
            "notes": self.notes,
        }

    def json(self):
        return json.dumps(self.dict(), indent=4)

    def fromJson(json_string):
        data = json.loads(json_string)
        data["trials"] = [Trial.fromJson(trial) for trial in data["trials"]]
        return Box(**data)


class ProjectSettings(pydantic.BaseSettings):
    project_name: str = "ProjectName"
    start_date: datetime.date = datetime.datetime.now()
    project_location: str = os.getcwd()
    window_size: tuple[int, int] = (1280, 720)
    window_position: tuple[int, int] = (0, 0)
    video_devices: dict[str, str] = {}
    animals: list[Animal] = []
    trials: list[Trial] = []
    boxes: list[Box] = []

    def dict(self):
        return {
            "project_name": self.project_name,
            "start_date": str(self.start_date),
            "project_location": self.project_location,
            "window_size": self.window_size,
            "window_position": self.window_position,
            "video_devices": self.video_devices,
            "animals": [animal.dict() for animal in self.animals],
            "trials": [trial.dict() for trial in self.trials],
            "boxes": [box.dict() for box in self.boxes],
        }

    def json(self):
        return json.dumps(self.dict(), indent=4)

    def save(self, dir_path=None):
        if dir_path is None:
            dir_path = self.project_location
        file_name = "settings.json"
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, "w") as f:
            f.write(self.json())

    def fromJson(json_string):
        data = json.loads(json_string)
        data["start_date"] = datetime.datetime.strptime(
            data["start_date"], "%Y-%m-%d"
        ).date()
        return ProjectSettings(**data)
