from packaging import version
import urllib.request
import urllib.parse
import logging
import ctypes
import json
import sys
import re

logger = logging.getLogger(__name__)

class UpdateChecker:
    pass


class VS_FIXEDFILEINFO(ctypes.Structure):
    _fields_ = [
        ("dwSignature", ctypes.c_uint32),
        ("dwStrucVersion", ctypes.c_uint32),
        ("dwFileVersionMS", ctypes.c_uint32),
        ("dwFileVersionLS", ctypes.c_uint32),
        ("dwProductVersionMS", ctypes.c_uint32),
        ("dwProductVersionLS", ctypes.c_uint32),
        ("dwFileFlagsMask", ctypes.c_uint32),
        ("dwFileFlags", ctypes.c_uint32),
        ("dwFileOS", ctypes.c_uint32),
        ("dwFileType", ctypes.c_uint32),
        ("dwFileSubtype", ctypes.c_uint32),
        ("dwFileDateMS", ctypes.c_uint32),
        ("dwFileDateLS", ctypes.c_uint32),
    ]


def check_app_update_status(app_manual_version=None):
    file_version, _ = get_file_and_product_version()
    latest_online_version  = get_latest_app_version()
    if not file_version:
        file_version = app_manual_version

    try:
        if latest_online_version:
            latest_online_version  = version.parse(latest_online_version )
        file_version = version.parse(file_version)
    except Exception as e:
        logging.exception(e)
        return None

    if latest_online_version is None:
        logging.debug("Offline")
        return "Offline"
    elif latest_online_version == file_version:
        logging.debug("The installed version is the same as the version available online.")
        return False  # Installed version is up to date.
    elif latest_online_version > file_version:
        logging.debug("The installed version is outdated.")
        return True  # Installed version is outdated.
    elif latest_online_version < file_version:
        logging.debug("The installed version is up to date.")
        return False  # Installed version is up to date.
    else:
        logging.debug("Error: app version check")
        return None  # Error


def get_file_and_product_version(exe_path=sys.executable):
    size = ctypes.windll.version.GetFileVersionInfoSizeW(exe_path, None)
    if size == 0:
        return None, None

    res = ctypes.create_string_buffer(size)
    ctypes.windll.version.GetFileVersionInfoW(exe_path, None, size, res)

    r = ctypes.c_void_p()
    l = ctypes.c_uint()

    # Query the root block for the VS_FIXEDFILEINFO structure
    ctypes.windll.version.VerQueryValueW(res, '\\', ctypes.byref(r), ctypes.byref(l))

    info = ctypes.cast(r, ctypes.POINTER(VS_FIXEDFILEINFO)).contents

    def print_vs_fixedfileinfo(info):
        print("VS_FIXEDFILEINFO:")
        print(f"  dwFileVersionMS: {info.dwFileVersionMS:#010x}")
        print(f"  dwFileVersionLS: {info.dwFileVersionLS:#010x}")
        print(f"  dwProductVersionMS: {info.dwProductVersionMS:#010x}")
        print(f"  dwProductVersionLS: {info.dwProductVersionLS:#010x}")
    #print_vs_fixedfileinfo(info)

    # Extract file version numbers
    file_version_ms = info.dwFileVersionMS
    file_version_ls = info.dwFileVersionLS
    file_version = (file_version_ms >> 16, file_version_ms & 0xffff, file_version_ls >> 16, file_version_ls & 0xffff)
    file_version = ".".join(map(str, file_version)) if file_version else "Unknown file version"

    # Extract product version numbers
    product_version_ms = info.dwProductVersionMS
    product_version_ls = info.dwProductVersionLS
    product_version = (product_version_ms >> 16, product_version_ms & 0xffff, product_version_ls >> 16, product_version_ls & 0xffff)
    product_version = ".".join(map(str, product_version)) if product_version else "Unknown file version"

    return file_version, product_version

def get_latest_app_version():
    # Base URL and repository path
    base_url = "https://api.github.com/repos/"
    repo_path = "RybarskiDominik/GML-2021/releases/latest"
    # Construct the full URL
    #api_url_str = urllib.parse.urljoin(base_url, repo_path)

    api_url_str = r"https://api.github.com/repos/RybarskiDominik/GML-2021/releases/latest"

    # Prepare the request
    headers = {
        "Accept": "application/json"
        #"Accept": "application/vnd.github.v3+json"
    }

    # Create a request object with headers
    request = urllib.request.Request(api_url_str, headers=headers)

    # Send the GET request and handle the response
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                # Odczyt danych w formacie JSON i zwrócenie wartości klucza "tag_name"
                data = json.loads(response.read().decode())
                return data["tag_name"]
            else:
                print(f"Request failed with status code: {response.status}")
                return False
    except urllib.error.URLError as e:
        logging.exception(e)
        print(f"Failed to reach the server. Reason: {e.reason}")
        return None

if __name__ == "__main__":
    print(check_app_update_status())