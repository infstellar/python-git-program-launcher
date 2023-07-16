import os
import sys
import json
import time
from logger import logger
import locale
from i18n import t2t
import subprocess
import urllib.request
import ssl

PROGRAM_NAME = "Python-Git-Program-Launcher"
DEBUG_MODE = False
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE_PATH = os.path.join(ROOT_PATH, "toolkit\\python.exe")
LAUNCHER_PYTHON_PATH = PYTHON_EXE_PATH
PROGRAM_PYTHON_PATH = LAUNCHER_PYTHON_PATH
REPO_PATH = ""
os.chdir(ROOT_PATH)
CONFIG_TEMPLATE = {
    "RequirementsFile": "requirements.txt",
    "InstallDependencies": True,
    "PypiMirror": "AUTO",
    "PythonMirror": "AUTO",
    "Repository": "https://github.com/infstellar/python-git-program-launcher",
    "Main": "main.py",
    "Branch": "main",
    "GitProxy": False,
    "KeepLocalChanges": False,
    "AutoUpdate": True,
    "Tag": "",
    "PythonVersion": "3.10.10"
}



def get_local_lang():
    lang = locale.getdefaultlocale()[0]
    print(lang)
    if lang in ["zh_CN", "zh_SG", "zh_MO", "zh_HK", "zh_TW"]:
        return "zh_CN"
    else:
        return "en_US"


GLOBAL_LANG = get_local_lang()

if sys.path[0] != ROOT_PATH:
    sys.path.insert(0, ROOT_PATH)


def load_json(json_name) -> dict:
    if '.json' not in json_name:
        json_name += '.json'
    f = open(os.path.join(ROOT_PATH, 'configs', json_name), 'r')
    content = f.read()
    a = json.loads(content)
    f.close()
    return a

def download_url(url, dst):
        from tqdm import tqdm
        import requests
        first_byte = 0
        logger.info(t2t("downloading url:")+f"{url} -> {dst}")
        # tqdm 里可选 total= 参数，不传递这个参数则不显示文件总大小
        pbar = tqdm(initial=first_byte, unit='B', unit_scale=True, desc=dst)
        # 设置stream=True参数读取大文件
        req = requests.get(url, stream=True, verify=False)
        with open(dst, 'ab') as f:
            # 每次读取一个1024个字节
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
        pbar.close()

def save_json(x, json_name):
    """保存json.

    Args:
        x (_type_): dict/list对象
        json_name (str, optional): 同load_json. Defaults to 'General.json'.
        default_path (str, optional): 同load_json. Defaults to 'config\\settings'.
        sort_keys (bool, optional): 是否自动格式化. Defaults to True.
        auto_create (bool, optional): _description_. Defaults to False.
    """
    if '.json' not in json_name:
        json_name += '.json'
    json.dump(x, open(os.path.join(ROOT_PATH, 'configs', json_name), 'w', encoding='utf-8'), sort_keys=True, indent=2,
              ensure_ascii=False)


def load_json_from_folder(path, black_file: list = None):
    json_list = []
    if black_file is None:
        black_file = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f[f.index('.') + 1:] == "json":
                if f[:f.index('.')] not in black_file:
                    j = json.load(open(os.path.join(path, f), 'r', encoding='utf-8'))
                    json_list.append({"label": f, "json": j})
    return json_list

def verify_path(root):
    root = os.path.abspath(root)
    if not os.path.exists(root):
        verify_path(os.path.dirname(root))
        os.mkdir(root)
        logger.info(f"dir {root} has been created")

def read_file_flag(n:str) -> bool:
    p = os.path.join(ROOT_PATH, 'pgpl-cache')
    verify_path(p)
    with open(os.path.join(p, n), 'w+') as f:
        s = f.read()
        if s == '':
            f.write('False')
            return False
        else:
            return bool(s)
        
def write_file_flag(n:str, x:bool) -> None:
    p = os.path.join(ROOT_PATH, 'pgpl-cache')
    verify_path(p)
    with open(os.path.join(p, n), 'w') as f:
        f.write(str(x))

class ExecutionError(Exception):
    pass



def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    i = 0
    pt = time.time()
    while True:
        output = process.stdout.readline()
        if str(output, encoding='utf-8') == '' and (process.poll() is not None):
            break
        if output:
            orimess = output.strip()
            mess = str(orimess, encoding='utf-8')
            if 'Requirement already satisfied: ' not in mess:
                logger.trace(mess)
                print(mess)
            if 'Installing collected packages' in mess:
                logger.info('Please wait, pip is copying the file.')
            
        else:
            if time.time()-pt>5:
                list = ["\\", "|", "/", "—"]
                index = i % 4
                sys.stdout.write("\r {}".format(list[index]), end="")
                i+=1
    rc = process.poll()
    return rc

class Command():

    def show_error(self, command=None, error_code=None):
        logger.info("Update failed", 0)
        # self.show_config()
        logger.info("")
        logger.info(f"Last command: {command}\nerror_code: {error_code}")
        logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
        logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
        logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))

    def logger_hr_and_track(self, x, c=0, p=None):
        logger.hr(x, c)
        if p is None:
            self.progress_tracker.set_info(x)
        else:
            self.progress_tracker.inp(x,p)
    
    @logger.catch(reraise=True)
    def execute(self, command, allow_failure=False, output=True, is_format=True):
        """
        Args:
            command (str):
            allow_failure (bool):
            output(bool):

        Returns:
            bool: If success.
                Terminate installation if failed to execute and not allow_failure.
        """

        if is_format:
            command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        # command = command.replace(r"/", "\\")
        if not output:
            command = command + ' >nul 2>nul'
        logger.info(command)
        error_code = os.system(command) # run_command(command)
        if error_code:
            if allow_failure:
                logger.info(f"[ allowed failure ], error_code: {error_code}")
                return False
            else:
                logger.info(f"[ failure ], error_code: {error_code}")
                self.show_error(command, error_code)
                raise ExecutionError

        else:
            logger.info(f"[ success ]")
            return True

def url_file_exists(url):
    context = ssl._create_unverified_context()
    try:
        urllib.request.urlopen(url, context=context)
        return True
    except Exception as e:
        logger.error(e)
        return False


