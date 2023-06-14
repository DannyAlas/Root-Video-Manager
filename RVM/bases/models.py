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

    def getAnimalFromId(self, uid):
        for animal in self.animals:
            if animal.uid == uid:
                return animal
        return None

    def getBoxFromId(self, uid):
        for box in self.boxes:
            if box.uid == uid:
                return box
        return None

    def getTrialFromId(self, uid):
        for trial in self.trials:
            if trial.uid == uid:
                return trial
        return None

    def updateTrial(self, trial: TrialBase):
        for i, t in enumerate(self.trials):
            if t.uid == trial.uid:
                self.trials[i] = trial
                return True
        return False

    def getProtocolFromId(self, uid):
        for protocol in self.protocols:
            if protocol.uid == uid:
                return protocol
        return None

    def getProlcolFromName(self, name):
        for protocol in self.protocols:
            if protocol.name == name:
                return protocol
        return None

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

class Trial(TrialBase):
    """A trial in the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self, **kwargs):
        # set our attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def avalible_states():
        return [x for x in TrialBase.__fields__['state'].type_.__args__]