# the models for the project with helper functions
import datetime
import json
import os
import subprocess
from tkinter import E
from wsgiref import validate

from RVM.bases.base import (
    AnimalBase,
    BoxBase,
    ProjectSettingsBase,
    ProtocolBase,
    TrialBase,
)


class Protocol(ProtocolBase):
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

    def stop(self):
        self.state = "Stopped"
        self.end_time = datetime.datetime.now()

    @staticmethod
    def avalible_states():
        return [x for x in TrialBase.__fields__["state"].type_.__args__]
