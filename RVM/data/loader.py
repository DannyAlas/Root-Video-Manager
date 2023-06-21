import os
from datetime import datetime
from json import load

import pandas as pd

from RVM.bases import Trial


class Loader:
    def __init__(self, data_txt=None):
        self.data_savable = False

    def loadShockTxt(self, txt_file_path):
        """Load the shock data from the text file"""
        self.original_data_location = txt_file_path
        with open(self.original_data_location, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.__contains__("Start Date"):
                self.start_date = datetime.strptime(
                    line.split(":")[1].strip(), "%m/%d/%y"
                )
            if line.__contains__("End Date"):
                self.end_date = datetime.strptime(
                    line.split(":")[1].strip(), "%m/%d/%y"
                )
            if line.__contains__("Subject"):
                self.subject = line.split(":")[1].strip()
            if line.__contains__("Box"):
                self.box = line.split(":")[1].strip()
            if line.__contains__("Start Time"):
                # time will be in hours:minutes:seconds
                # convert to datetime object with the start date
                self.start_time = datetime.strptime(
                    line.strip("Start Time: ").strip("\n"), "%H:%M:%S"
                )
                # set the date of the start time to the start date
                self.start_time = self.start_time.replace(
                    year=self.start_date.year,
                    month=self.start_date.month,
                    day=self.start_date.day,
                ).strftime("%Y-%m-%d_%Hh%Mm%Ss")
            if line.__contains__("End Time"):
                # time will be in hours:minutes:seconds
                # convert to datetime object with the start date
                self.end_time = datetime.strptime(
                    line.strip("End Time: ").strip("\n"), "%H:%M:%S"
                )
                # set the date of the start time to the start date
                self.end_time = self.end_time.replace(
                    year=self.start_date.year,
                    month=self.start_date.month,
                    day=self.start_date.day,
                ).strftime("%Y-%m-%d_%Hh%Mm%Ss")
            if line.__contains__("MSN"):
                self.protocal_name = line.split(":")[1].strip()
            if line.__contains__("C:\n"):
                # the next lines till the end of the file are the data
                data = lines[i + 1 :]
                # save the data to a temp csv file
                with open("temp.txt", "w") as f:
                    f.writelines(data)
                # load the data into a pandas dataframe
                df = pd.read_csv("temp.txt", delim_whitespace=True, header=None)
                # drop the first column
                df = df.drop(df.columns[0], axis=1)
                self.outdf = pd.DataFrame()
                csp = []
                csm = []
                shock = []
                # iterate through each row and then column in the row and print the data
                for row in df.iterrows():
                    for col in row[1]:
                        # convert to a string
                        col = str(col)
                        ts = col.split(".")[0]
                        ts_type = col.split(".")[1]
                        if ts_type == "6":
                            # CS+
                            csp.append(ts)
                        elif ts_type == "19":
                            # Shock
                            shock.append(ts)
                        elif ts_type == "13":
                            # CS-
                            csm.append(ts)
                # save the data to a csv file
                # get the longest list and make all lists that length with Null values
                max_len = max(len(csp), len(csm), len(shock))
                csp = csp + [None] * (max_len - len(csp))
                csm = csm + [None] * (max_len - len(csm))
                shock = shock + [None] * (max_len - len(shock))
                self.outdf["CS+ TS's"] = csp
                self.outdf["CS- TS's"] = csm
                self.outdf["Shock TS's"] = shock
                self.data_savable = True
                break

    def save(self, dir_path):
        if self.data_savable:
            trial = Trial(
                start_time=self.start_time,
                end_time=self.end_time,
                subject=self.subject,
                box=self.box,
                protocal_name=self.protocal_name,
                data=self.outdf,
                original_data_location=self.original_data_location,
            )

            file_name = (
                self.start_time
                + "_"
                + self.subject
                + "_"
                + self.box
                + "_"
                + self.protocal_name
                + ".json"
            )
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "w") as f:
                f.write(trial.json())

    def loadJson(self, file_path):
        with open(file_path, "r") as f:
            data = f.read()
        trial = Trial.fromJson(data)
        return trial
