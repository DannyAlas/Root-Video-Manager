# the models for the project with helper functions
from RVM.bases.base import AnimalBase, BoxBase, ProtocalBase, ProjectSettingsBase, TrialBase
import os
import json

class ProjectSettings(ProjectSettingsBase):
    """The settings for the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def save(self, dir_path=None):
        if dir_path is None:
            dir_path = self.project_location
        file_name = "settings.json"
        with open(os.path.join(dir_path, file_name), "w") as file:
            file.write(self.json(indent=4))

    def load(self, dir_path=None):
        if dir_path is None:
            dir_path = self.project_location
        file_name = "settings.json"
        with open(os.path.join(dir_path, file_name), "r") as file:
            self.__init__(**json.load(file))

class Protocol(ProtocalBase):
    """The protocol in the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Animal(AnimalBase):
    """An animal in the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Box(BoxBase):
    """A box in the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self, **kwargs):
        # set our attributes
        for key, value in kwargs.items():
            setattr(self, key, value)