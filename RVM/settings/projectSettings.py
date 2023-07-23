# A project settings class that handles all manipulations to the project with getters and setters, handles saving and loading of the project, repairing of the project, and undo and redo functionality.
# This project currently has the gui code manipulating the project directly, which is not good practice. and has led to bugs and data loss. Going forward, the gui should only manipulate the project through this class.

import inspect
import json
import os
from turtle import st
from zipfile import ZipFile

from RVM.bases.models import (AnimalBase, BoxBase, ProjectSettingsBase,
                              ProtocolBase, TrialBase)

from .utils import singleton


@singleton
class ProjectSettings:
    def __init__(self) -> None:
        # explicitly set the class name to ProjectSettings
        self.__class__.__name__ = "ProjectSettings"
        self.modified = False
        self.default_save_file = os.path.join(
            os.path.expanduser("~"), "Documents", "Root Video Manager", "temp.rvmx"
        )
        self.project_settings = ProjectSettingsBase(
            project_location=self.default_save_file
        )

    def _get_settings_from_file(self, file_path: str):
        """Get the settings from a file

        Parameters
        ----------
        file_path : str
            The path to the settings file

        Returns
        -------
        settings : dict
            The settings
        """
        if str(file_path).endswith(".rvmx"):
            # load the settings from the rvmx file
            with ZipFile(file_path, "r") as zip_file:
                with zip_file.open("settings.json", "r") as file:
                    settings = json.loads(file.read())

        elif file_path.endswith(".json"):
            # load the settings from the json file
            with open(file_path, "r") as file:
                settings = json.loads(file.read())
        else:
            raise ValueError("Invalid file type")
        settings = dict(settings)

        return settings

    def _string_sanitizer(self, string: str):
        """Sanitize a string for use in a file path

        Parameters
        ----------
        string : str
            The string to sanitize

        Returns
        -------
        string : str
            The sanitized string
        """
        if string.endswith(".rvmx"):
            string = string[:-5]
            string = (
                string.replace(".", "_")
                .replace(",", "_")
                .replace(":", "_")
                .replace(";", "_")
                .replace("?", "_")
                .replace("!", "_")
                .replace("'", "_")
                .replace('"', "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace("|", "_")
                .replace("<", "_")
                .replace(">", "_")
                .replace("*", "_")
            )
            string = string + ".rvmx"
        else:
            string = (
                string.replace(" ", "_")
                .replace(".", "_")
                .replace(",", "_")
                .replace(":", "_")
                .replace(";", "_")
                .replace("?", "_")
                .replace("!", "_")
                .replace("'", "_")
                .replace('"', "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace("|", "_")
                .replace("<", "_")
                .replace(">", "_")
                .replace("*", "_")
            )
        string = string.encode("ascii", "ignore").decode("ascii")

        return string

    def createNewProject(self, project_name: str, project_location: str):
        """Create a new project

        Parameters
        ----------
        project_name : str
            The name of the project
        project_location : str
            The location of the project
        """
        self.save(self.project_settings.project_location)

        project_location = os.path.abspath(project_location)
        if not os.path.exists(os.path.dirname(project_location)):
            raise ValueError("The project location does not exist")

        if self.project_settings:
            del self.project_settings

        self.project_settings = ProjectSettingsBase(
            project_name=project_name, project_location=project_location
        )

    def load(self, file_path: str):
        """Load the settings from a file. The file can be a .rvmx file or a settings.json file

        Parameters
        ----------
        file_path : str
            The path to the settings file
        """
        settings = self._get_settings_from_file(file_path)

        self.project_settings = self.validate_settings(settings)
        self.modified = False

        return self

    def load_default(self):
        """Load the default settings"""
        if not os.path.exists(self.default_save_file):
            # create the default save file
            self.createNewProject("Default", self.default_save_file)

        self.load(self.default_save_file)

    def validate_settings(self, settings: dict):
        """Validate the settings

        Parameters
        ----------
        settings : dict
            The settings to validate

        Returns
        -------
        class : ProjectSettingsBase
            The validated settings
        """
        # the settings MUST contain a uid, project_name, and created
        if "uid" not in settings.keys():
            raise ValueError("The settings must contain a uid")
        if "project_name" not in settings.keys():
            raise ValueError("The settings must contain a project_name")
        if "created" not in settings.keys():
            raise ValueError("The settings must contain a created")
        settings["animals"] = [AnimalBase(**animal) for animal in settings["animals"]]
        settings["boxes"] = [BoxBase(**box) for box in settings["boxes"]]
        settings["trials"] = [TrialBase(**trial) for trial in settings["trials"]]
        settings["protocols"] = [
            ProtocolBase(**protocol) for protocol in settings["protocols"]
        ]
        return ProjectSettingsBase(**settings)

    def save(self, file_path: str):
        """Save the settings to a .rvmx file"""

        # if we're saving to the default save location, then then ensure that the location exists
        if os.path.abspath(file_path) == os.path.abspath(self.default_save_file):
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))

        if self.modified == False:
            return True

        file_path = os.path.abspath(file_path)
        # if the file path is the default save location, then ensure that the location exists
        if file_path == self.default_save_file:
            return True

        if not file_path.endswith(".rvmx"):
            raise ValueError("The file path must end with .rvmx")

        with ZipFile(file_path, "w") as zip_file:
            zip_file.writestr("settings.json", self.project_settings.json())
            self.modified = False

    def repair(self):
        pass

    def __setattr__(self, name, value):
        """
        Prevents any class other than ProjectSettings from setting attributes directly. Any attribute that needs to be set will need to have a custom setter, otherwise it will be read only!
        """
        stack = inspect.stack()
        the_class = stack[1][0].f_locals["self"].__class__.__name__
        if not the_class == "ProjectSettings":
            raise AttributeError(
                f"CALLER: {the_class}\nSETTING: {name} = {value}\nCannot set attributes directly, use the getters and setters"
            )

        super().__setattr__(name, value)

    def __delattr__(self, name):
        stack = inspect.stack()
        the_class = stack[1][0].f_locals["self"].__class__.__name__
        if not the_class == "ProjectSettings":
            raise AttributeError(
                f"CALLER: {the_class}\nDELETING: {name}\nCannot delete attributes directly, use the getters and setters"
            )

    @property
    def project_name(self):
        return self.project_settings.project_name

    def set_project_name(self, value):
        self.modified = True
        self.project_settings.project_name = value

    @property
    def project_location(self):
        return self.project_settings.project_location

    def set_project_location(self, value):
        self.modified = True
        if not os.path.exists(os.path.dirname(value)):
            raise ValueError("The project location does not exist")
        self.project_settings.project_location = value

    @property
    def window_size(self):
        return self.project_settings.window_size

    def set_window_size(self, value):
        self.modified = True
        self.project_settings.window_size = value

    @property
    def window_position(self):
        return self.project_settings.window_position

    def set_window_position(self, value):
        self.modified = True
        self.project_settings.window_position = value

    @property
    def video_devices(self):
        return self.project_settings.video_devices

    @property
    def protocols(self):
        return [
            protocol
            for protocol in self.project_settings.protocols
            if protocol.deleted == False
        ]

    @property
    def animals(self):
        return [
            animal
            for animal in self.project_settings.animals
            if animal.deleted == False
        ]

    @property
    def boxes(self):
        return [box for box in self.project_settings.boxes if box.deleted == False]

    @property
    def trials(self):
        return [
            trial for trial in self.project_settings.trials if trial.deleted == False
        ]

    def add_box(self, box: BoxBase):
        self.modified = True
        print(box)
        if not isinstance(box, BoxBase):
            raise ValueError("The box must be of type BoxBase")
        if box not in self.project_settings.boxes:
            self.project_settings.boxes.append(box)

    def get_box(self, uid: str):
        self.modified = True
        for box in self.project_settings.boxes:
            if box.uid == uid:
                return box
        return None

    def update_box(self, box: BoxBase):
        self.modified = True
        if not isinstance(box, BoxBase):
            raise ValueError("The box must be of type BoxBase")
        for i, b in enumerate(self.project_settings.boxes):
            if b.uid == box.uid:
                self.project_settings.boxes[i] = box
                break

    def delete_box(self, uid: str):
        """Does not delete box, just marks it as deleted"""
        self.modified = True
        for i, box in enumerate(self.project_settings.boxes):
            if box.uid == uid:
                self.project_settings.boxes[i].deleted = True
                break

    def add_animal(self, animal: AnimalBase):
        self.modified = True
        if not isinstance(animal, AnimalBase):
            raise ValueError("The animal must be of type AnimalBase")
        if animal not in self.project_settings.animals:
            self.project_settings.animals.append(animal)

    def get_animal(self, uid: str):
        self.modified = True
        for animal in self.project_settings.animals:
            if animal.uid == uid:
                return animal
        return None

    def update_animal(self, animal: AnimalBase):
        self.modified = True
        if not isinstance(animal, AnimalBase):
            raise ValueError("The animal must be of type AnimalBase")
        for i, a in enumerate(self.project_settings.animals):
            if a.uid == animal.uid:
                self.project_settings.animals[i] = animal
                break

    def delete_animal(self, uid: str):
        """Does not delete animal, just marks it as deleted"""
        self.modified = True
        for i, animal in enumerate(self.project_settings.animals):
            if animal.uid == uid:
                self.project_settings.animals[i].deleted = True
                break

    def add_video_device(self, name: str, uid: str):
        self.modified = True
        self.project_settings.video_devices[name] = uid


"""
TODO: TRIAL MANAGEMENT class to handle creation, deletion, and modification of trials. Trial class to handle the trial data, validation, running protocols, and data management, saving and loading.

example procedural trial creation structure:
    def animal filter
        - all
        - Animals with genotype that matches :x:

    def box filter
        - select boxes

    def way to limit length
        - Run each animal :X: times per day
        - For :Y: days

    OUT comes a set of trials with dayNum (the day it runs on) and SetNum (the set of that day it runs in)
"""
