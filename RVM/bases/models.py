# the models for the project with helper functions
import datetime
import json
import logging
import os
import subprocess

from RVM.bases.base import (AnimalBase, BoxBase, ProjectSettingsBase,
                            ProtocalBase, TrialBase)

log = logging.getLogger()


class ProjectSettings(ProjectSettingsBase):
    """The settings for the project"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def save(self, dir_path=None):
        """Save the settings to a json file

        Parameters
        ----------
        dir_path : str, optional
            The directory to save the file to, by default None. If None, the project location is used, THIS WILL OVERWRITE THE CURRENT PROJECT SETTINGS.
        """
        if dir_path is None:
            dir_path = self.project_location
        file_name = "settings.json"
        # check if the directory exists
        if not os.path.exists(dir_path):
            # make a project directory in the current directory
            try:
                os.mkdir(dir_path)
            except OSError:
                # make a directory in at the current directory
                dir_path = os.path.join(os.getcwd(), self.project_name)
                os.mkdir(dir_path)
                subprocess.Popen(["explorer", dir_path])
        with open(os.path.join(dir_path, file_name), "w") as file:
            file.write(self.json(indent=4))

    def load(self, dir_path=None, check=True):
        """
        Load the settings from a json file

        Parameters
        ----------
        dir_path : str, optional
            The directory to load the file from, by default None. If None, the project location is used. If the project location is not set, the current directory is used.
        check : bool, optional
            Whether to check the settings after loading, by default True
        """
        if dir_path is None:
            dir_path = self.project_location
        file_name = "settings.json"
        with open(os.path.join(dir_path, file_name), "r") as file:
            self.__init__(**json.load(file))

        self.project_location = dir_path
        if check:
            self.validateSettings()

    def validateSettings(self):
        """Validate the settings"""
        # check if the project location exists
        try:
            if not os.path.exists(self.project_location):
                raise FileNotFoundError(
                    f"The project location {self.project_location} does not exist"
                )
        except Exception as e:
            raise FileNotFoundError(
                f"The project location {self.project_location} is not valid"
            )
        # check if the project name is valid
        try:
            if not self.project_name.isidentifier():
                raise ValueError(f"The project name {self.project_name} is not valid")
        except Exception as e:
            raise ValueError(f"The project name {self.project_name} is not valid")
        # check if the project created date is valid
        try:
            datetime.datetime.strptime(str(self.created), "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            raise ValueError(f"The project created date {self.created} is not valid")
        # check that the window size is valid
        try:
            if self.window_size[0] < 0 or self.window_size[1] < 0:
                raise ValueError(f"The window size {self.window_size} is not valid")
        except Exception as e:
            raise ValueError(f"The window size {self.window_size} is not valid")

        for animal in self.animals:
            if isinstance(animal, AnimalBase) or isinstance(animal, Animal):
                animal.validateAnimal()
            else:
                raise TypeError(f"Animal {animal} is not an instance of AnimalBase")
        for box in self.boxes:
            if isinstance(box, BoxBase) or isinstance(box, Box):
                box.validateBox()
            else:
                raise TypeError(f"Box {box} is not an instance of BoxBase")
        for trial in self.trials:
            if isinstance(trial, TrialBase) or isinstance(trial, Trial):
                trial.validateTrial()
            else:
                raise TypeError(f"Trial {trial} is not an instance of TrialBase")

    def repairSettings(self):
        """A VERY CRUDE REPAIR FOR QUICK PATCH

        TODO: Make better...

        """
        for i, trial in enumerate(self.trials):
            try:
                trial.validateTrial()
            except:
                if trial.uid is None:
                    print(f"Trial {trial} has no uid and cannot be repaired")
                if trial.video_location is None:
                    print(f"Trial {trial} has NO video location and cannot be repaired")
                # get the file from the video location
                filename = str(os.path.basename(trial.video_location))
                if trial.uid != filename.split("_")[-1].split(".")[0]:
                    print(
                        f"Trial {trial} has an invalid video location and cannot be repaired"
                    )
                if isinstance(trial.animal, AnimalBase) or isinstance(
                    trial.animal, Animal
                ):
                    try:
                        animal = self.getAnimalFromId(trial.animal.uid)
                        trial.animal = animal
                        print(
                            f"{self.getAnimalFromId(trial.animal.uid)}, {trial.animal}"
                        )
                    except:
                        print(
                            f"Trial {trial} has no valid animal and cannot be repaired"
                        )
                else:
                    trial.animal = self.getAnimalFromId(filename.split("_")[0])
                    print(f"{filename.split('_')[0]}, {trial.animal}")

                if isinstance(trial.box, BoxBase) or isinstance(trial.box, Box):
                    try:
                        box = self.getBoxFromId(trial.box.uid)
                        trial.box = box
                    except:
                        print(f"Trial {trial} has no valid box and cannot be repaired")
                else:
                    trial.box = self.getBoxFromId(filename.split("_")[1])
            self.trials[i] = trial

        self.save()

    def getAnimalFromId(self, uid):
        for animal in self.animals:
            if animal.uid == uid:
                return animal
        return None

    def updateAnimal(self, animal: AnimalBase):
        for i, a in enumerate(self.animals):
            if a.uid == animal.uid:
                self.animals[i] = animal
                return True
        return False

    def getBoxFromId(self, uid):
        for box in self.boxes:
            if box.uid == uid:
                return box
        return None

    def getTrialFromId(self, uid) -> TrialBase:
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

    def stop(self):
        self.state = "Stopped"
        self.end_time = datetime.datetime.now()

    @staticmethod
    def avalible_states():
        return [x for x in TrialBase.__fields__["state"].type_.__args__]
