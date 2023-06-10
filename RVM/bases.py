from re import U
import pandas
import pydantic
import json
import os
import datetime
from typing import Union

class Trial(pydantic.BaseSettings):
    subject: str = "MouseID"
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
            "subject": self.subject,
            "box": self.box,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "protocal_name": self.protocal_name,
            "original_data_location": self.original_data_location,
            "video_location": self.video_location,
            "data": self.data.to_dict()
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
    box: str = "BoxID"
    subject: str = "MouseID"
    genotype: str = "Genotype"
    camera: str = "CameraAltID"
    trials: list[Trial] = []

    def dict(self):
        return {
            "box": self.box,
            "subject": self.subject,
            "genotype": self.genotype,
            "camera": self.camera,
            "trials": [trial.dict() for trial in self.trials]
        }

    def json(self):
        return json.dumps(self.dict(), indent=4)

class ProjectSettings(pydantic.BaseSettings):
    project_name: str = "ProjectName"
    start_date: datetime.date = datetime.datetime.now()
    project_location: str = os.getcwd()
    window_size: tuple[int, int] = (1280, 720)
    window_position: tuple[int, int] = (0, 0)
    boxes: list[Box] = []

    def dict(self):
        return {
            "project_name": self.project_name,
            "start_date": str(self.start_date),
            "project_location": self.project_location,
            "window_size": self.window_size,
            "window_position": self.window_position,
            "boxes": [box.dict() for box in self.boxes]
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
        data["start_date"] = datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        return ProjectSettings(**data)