import argparse
import json
import os
import re
import subprocess
import urllib.request
import zipfile

GLOBAL_FFMPEG_LOCATION = os.path.expanduser("~")


def get_ffmpeg(location):
    """
    download ffmpeg from github and extract it to the given location

    Parameters
    ----------
    location : str
        the location to extract ffmpeg to, should be the user directory
    """
    with urllib.request.urlopen(
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
    ) as response:
        data = response.read()
    with open(os.path.join(location, "ffmpeg.zip"), "wb") as f:
        f.write(data)
    with zipfile.ZipFile(os.path.join(location, "ffmpeg.zip"), "r") as zip:
        zip.extractall(location)
        print(zip.namelist())
    if os.path.exists(os.path.join(location, "ffmpeg.zip")):
        os.remove(os.path.join(location, "ffmpeg.zip"))


def check_ffmpeg():
    """
    check if ffmpeg is installed, if not, download it
    """
    if not os.path.exists(
        os.path.join(
            GLOBAL_FFMPEG_LOCATION,
            "ffmpeg-master-latest-win64-gpl-shared",
            "bin",
            "ffmpeg.exe",
        )
    ):
        get_ffmpeg(GLOBAL_FFMPEG_LOCATION)


def get_ffmpeg_list():
    """
    get a list of all the devices that ffmpeg can use

    Returns
    -------
    dict
        a dict of all the devices that ffmpeg can use
    """
    proc = subprocess.Popen(
        [
            f'{os.path.join(GLOBAL_FFMPEG_LOCATION, "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")}',
            "-stats",
            "-hide_banner",
            "-list_devices",
            "true",
            "-f",
            "dshow",
            "-i",
            "dummy",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return json.loads(json.dumps(stderr.decode("UTF-8")))


def format_device_output(text):
    """

    Formats the ffmpeg output into a dict


    """
    lines = text.split("\n")
    devices = {}
    current_device_type = None
    current_device_name = None

    for i, line in enumerate(lines):
        try:
            if re.findall(r'"([^"]*)"', line)[0].__contains__("@device") == False:
                if re.findall(r"\(([^()]*)\)[^()]*$", line)[0] == "video":
                    current_device_type = "video"
                elif re.findall(r"\(([^()]*)\)[^()]*$", line)[0] == "audio":
                    current_device_type = "audio"
                current_device_name = re.findall(r'"([^"]*)"', line)[0]
                cont = True

            if cont == True:
                if (
                    re.findall(r'"([^"]*)"', lines[i + 1])[0].__contains__("@device")
                    == True
                ):
                    if current_device_type not in devices:
                        devices[current_device_type] = {}
                    devices[current_device_type][
                        re.findall(r'"([^"]*)"', lines[i + 1])[0]
                    ] = current_device_name
                cont = False
        except:
            continue

    return devices


def get_devices():
    """
    get a dict of all the devices that ffmpeg can use

    Returns
    -------
    dict
        a dict of all the devices that ffmpeg can use
    """
    return format_device_output(get_ffmpeg_list())
