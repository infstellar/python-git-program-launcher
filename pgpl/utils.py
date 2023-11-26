import os
import sys
import json
import time
from pgpl.logger import logger
import locale
from i18n import t2t
import subprocess
import urllib.request
import ssl

PROGRAM_NAME = "Python-Git-Program-Launcher"
DEBUG_MODE = False
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE_PATH = os.path.join(ROOT_PATH, "toolkit/python.exe")
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
    "PythonVersion": "3.10.10",
    "UAC": True
}



def get_local_lang():
    lang = locale.getdefaultlocale()[0]
    print(lang)
    if lang in ["zh_CN", "zh_SG", "zh_MO", "zh_HK", "zh_TW"]:
        return "zh_CN"
    else:
        return "en_US"


GLOBAL_LANG = get_local_lang()
if locale.getdefaultlocale()[0] == 'zh_CN':
    PROXY_LANG = 'zh_CN' 
else:
    PROXY_LANG = "en_US"

if sys.path[0] != ROOT_PATH:
    sys.path.insert(0, ROOT_PATH)


def load_config_json(json_name) -> dict:
    if '.json' not in json_name:
        json_name += '.json'
    f = open(os.path.join(ROOT_PATH, 'configs', json_name), 'r')
    content = f.read()
    a = json.loads(content)
    f.close()
    return a

def load_json(json_name) -> dict:
    if '.json' not in json_name:
        json_name += '.json'
    f = open(json_name, 'r')
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

def save_config_json(x, json_name):
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
    json.dump(x, open(json_name, 'w', encoding='utf-8'), sort_keys=True, indent=2,
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

class ProgressTracker():
    """
    给GUI用的进度追踪器
    """
    def __init__(self) -> None:
        self.percentage = 0
        self.info = ''
        self.end_flag = False
        self.cmd = ""
        self.console_output = ""
        self.err_info = ""
        self.err_code = 0
        self.err_slu = ""
        self.monitor_list = []
    
    def set_percentage(self, x):
        self.percentage = x
    
    def set_info(self, x):
        self.info = x

    def inp(self, info, percentage):
        self.info = info
        self.percentage = percentage

    def add_monitor(self, text:str):
        self.monitor_list.append({'text':text,'count':0})
    
    def monitor(self, t):
        for i in self.monitor_list:
            if t in i['text'] and t != '':
                i['count'] += 1
    
    def get_counts(self, t):
        for i in self.monitor_list:
            if t == i['text']:
                return i['count']
    
    def reset(self):
        self.monitor_list = []
    
def find_right_encoding(str):
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
    for encoding in encodings:
        try:
            if DEBUG_MODE: logger.trace(f"encoding: {encoding}, decode: {str.decode(encoding)}")
            str.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            pass

def run_command(command, progress_tracker:ProgressTracker = None):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    i = 0
    pt = time.time()
    while True:
        output = process.stdout.readline()
        logger.info(f"output: {output}")
        right_encoding = find_right_encoding(output)
        if str(output, encoding=right_encoding) == '' and (process.poll() is not None):
            break
        if output:
            orimess = output.strip()
            mess = str(orimess, encoding=right_encoding)
            if progress_tracker is not None: progress_tracker.monitor(mess)
            if 'Requirement already satisfied: ' not in mess:
                logger.trace(mess)
                if progress_tracker is not None: progress_tracker.console_output = mess
                # print(mess)
            if 'Installing collected packages' in mess:
                logger.info(t2t('Please wait, pip is copying the file.'))
                # progress_tracker.set_info(t2t('Please wait, pip is copying the file.'))
                if progress_tracker is not None: progress_tracker.console_output = t2t('Please wait, pip is copying the file.')
            
        else:
            pass
            # if time.time()-pt>5:
            #     list = ["\\", "|", "/", "—"]
            #     index = i % 4
            #     sys.stdout.write("\r {}".format(list[index]))
            #     i+=1
    stdout, stderr = process.communicate()
    stdout_encoding = find_right_encoding(stdout)
    stderr_encoding = find_right_encoding(stderr)
    rc = process.poll()
    return rc, stdout.decode(stdout_encoding), stderr.decode(stderr_encoding)


class Command():

    def __init__(self, progress_tracker=None) -> None:
        if progress_tracker is None:
            logger.warning("progress_tracker is None")
            progress_tracker = ProgressTracker()
        self.progress_tracker = progress_tracker
    
    def error_checking(self, err_msg, err_code):
        def add_slu(msg:str):
            self.progress_tracker.err_slu+=f"- {msg}\n"
        logger.info("Running automatic error checking...")
        if 'get-pip.py' in err_msg and "No such file or directory" in err_msg:
            add_slu(t2t("toolkit is not installed. Please check if you downloaded the correct file or if you cloned the submodule."))
    
    def show_error(self, command=None, error_code=None):
        logger.info("Update failed", 0)
        # self.show_config()
        logger.info("")
        logger.info(f"Last command: {command}\nerror_code: {error_code}")
        # logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
        # logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
        # logger.warning(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))

    def logger_hr(self, message, hr_mode=0, progress=None):
        logger.hr(message, hr_mode)
        if progress is None:
            self.progress_tracker.set_info(message)
        else:
            self.progress_tracker.inp(message, progress)
    
    def info(self, x:str):
        """output info to console and UI.

        Args:
            x (str): message.
        """
        logger.info(x)
        self.progress_tracker.set_info(x)
    
    def execute(self, command, allow_failure=False, output=True, is_format=True): #, systematic_retry=False, systematic_execute=False):
        """
        
        execute command in subprocess and synchronize command output to GUI and console.
        
        Args:
            command (str): command
            allow_failure (bool): whether to raise an exception on failure
            output(bool):
            
            # systematic_retry, systematic_execute: when subprocess fail but os.system succ, use it.

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
        self.progress_tracker.cmd = command
        self.progress_tracker.console_output = ""
        if False: #systematic_execute:
            error_code = os.system(command)
            stdout = ""
            stderr = ""
        else:
            error_code, stdout, stderr = run_command(command, self.progress_tracker)
            # error_code = run_command(command, progress_tracker=self.progress_tracker) # os.system(command)
        if error_code:
            if allow_failure:
                logger.info(f"[ allowed failure ], error_code: {error_code} stdout: {stdout} stderr: {stderr}")
                return False
            elif False: #systematic_retry:
                logger.info(f"[ failure - USE SYSTEM INSTEAD ], error_code: {error_code}")
                return self.execute(command, allow_failure, output, is_format, systematic_retry=False, systematic_execute=True)
            else:
                logger.info(f"[ failure ], error_code: {error_code} stdout: {stdout} stderr: {stderr}")
                self.show_error(command, error_code)
                self.progress_tracker.err_code = error_code
                self.progress_tracker.err_info = stderr
                self.progress_tracker.console_output = stdout
                self.error_checking(stderr, error_code)
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


requesting_administrative_privileges = "@echo off\n"+\
"\n"+\
":: BatchGotAdmin\n"+\
":-------------------------------------\n"+\
"REM  --> Check for permissions\n"+\
"    IF \"%PROCESSOR_ARCHITECTURE%\" EQU \"amd64\" (\n"+\
">nul 2>&1 \"%SYSTEMROOT%\SysWOW64\cacls.exe\" \"%SYSTEMROOT%\SysWOW64\config\system\"\n"+\
") ELSE (\n"+\
">nul 2>&1 \"%SYSTEMROOT%\system32\cacls.exe\" \"%SYSTEMROOT%\system32\config\system\"\n"+\
")\n"+\
"\n"+\
"REM --> If error flag set, we do not have admin.\n"+\
"if '%errorlevel%' NEQ '0' (\n"+\
"    echo Requesting administrative privileges...\n"+\
"    goto UACPrompt\n"+\
") else ( goto gotAdmin )\n"+\
"\n"+\
":UACPrompt\n"+\
"    echo Set UAC = CreateObject^(\"Shell.Application\"^) > \"%temp%\getadmin.vbs\"\n"+\
"    set params= %*\n"+\
"    echo UAC.ShellExecute \"cmd.exe\", \"/c \"\"%~s0\"\" %params:\"=\"\"%\", \"\", \"runas\", 1 >> \"%temp%\getadmin.vbs\"\n"+\
"\n"+\
"    \"%temp%\getadmin.vbs\"\n"+\
"    del \"%temp%\getadmin.vbs\"\n"+\
"    exit /B\n"+\
"\n"+\
":gotAdmin\n"+\
"    pushd \"%CD%\"\n"+\
"    CD /D \"%~dp0\"\n"+\
":--------------------------------------    \n"