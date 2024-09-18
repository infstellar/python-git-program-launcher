import os, sys, subprocess
import shutil
import requests, zipfile
from tqdm import tqdm
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
print(ROOT_PATH)
sys.path.append(ROOT_PATH)
from pgpl.utils import *
from pgpl.logger import STDOUT_HANDEL_ID

import argparse

parser = argparse.ArgumentParser(description='pgpl pack config')
parser.add_argument("build")
parser.add_argument("--name", type=str, default="python-project")
parser.add_argument("--target-dir", type=str)
parser.add_argument("--output-path", type=str)
parser.add_argument("--main", type=str)
parser.add_argument("--requirements-file", type=str, default="requirements.txt")
parser.add_argument("--repository", type=str, default="")
parser.add_argument("--branch", type=str, default="main")
parser.add_argument("--use-UAC", type=bool, default=False)
parser.add_argument("--python-version", type=str, default="3.10.10")

args = parser.parse_args()

if args.repository == "":
    args.repository = f"https://123/{args.name}"

INP_CONFIG = {
    "RequirementsFile": args.requirements_file,
    "InstallDependencies": True,
    "PypiMirror": "AUTO",
    "PythonMirror": "AUTO",
    "Repository": args.repository,
    "Main": args.main,
    "Branch": args.branch,
    "GitProxy": False,
    "KeepLocalChanges": False,
    "AutoUpdate": True,
    "Tag": "",
    "PythonVersion": args.python_version,
    "UAC": not (args.use_UAC)
}




# sys.argv.pop(0)
logger.remove(STDOUT_HANDEL_ID)
STDOUT_HANDEL_ID = logger.add(sys.stdout, level="TRACE", backtrace=True)

def download_file(url, filename):
    # 发起请求并设置stream为True，这样可以逐块下载文件
    with requests.get(url, stream=True, verify=False) as r:
        r.raise_for_status()
        # 尝试从响应头中获取文件总大小
        total = int(r.headers.get('content-length', 0))
        # 初始化tqdm进度条
        with tqdm(total=total, unit='B', unit_scale=True, desc=filename) as bar:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # 写入文件并更新进度条
                    f.write(chunk)
                    bar.update(len(chunk))


def unzip_file(zip_path, extract_to):
    # 确保解压目录存在
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    # 打开ZIP文件
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 解压所有文件到指定目录
        zip_ref.extractall(extract_to)
        print(f"Unzip to：{extract_to}")

def copy_self(output_path):
    verify_path(output_path)
    os.chdir(output_path)
    run_command(f"git clone https://github.com/infstellar/python-git-program-launcher")

def install_pgplcpp(name, output_path) -> str:
    """

    Args:
        name:
        output_path:

    Returns: final dir

    """
    PGPLC_VERSION = "0.5.1"
    PGPLCPP_PATH = f"{ROOT_PATH}\\cache\\PGPLC-{PGPLC_VERSION}.zip"
    if not os.path.exists(PGPLCPP_PATH):
        download_file(f"https://github.com/infstellar/python-git-program-launcher-cpp/releases/download/v{PGPLC_VERSION}/PGPLC-{PGPLC_VERSION}.zip", filename=PGPLCPP_PATH)
    unzip_file(PGPLCPP_PATH, f"{output_path}")
    os.rename(f"{output_path}\\PGPLC-{PGPLC_VERSION}", f"{output_path}\\{name}")


def build_package(name:str, target_dir:str, startup_config:dict, output_path:str):
    package_path = f"{output_path}\\{name}"
    if os.path.exists(package_path):
        r = input(f"folder \'{package_path}\' exist. [Y]remove or [n]exit program.")
        if r in ['n', 'N']:
            sys.exit(0)
        else:
            try:
                os.remove(package_path)
                shutil.rmtree(package_path)
            except PermissionError as e:
                logger.exception(e)
                logger.error(f"CANNOT DELETE FOLDER. PLEASE REMOVE IT MANUALLY.")
                sys.exit(0)
    install_pgplcpp(name, output_path)
    copy_self(package_path)
    shutil.copytree(target_dir, f"{package_path}\\python-git-program-launcher\\repositories\\{name}")
    json.dump(startup_config, open(f"{package_path}\\default_config.json", 'w', encoding='utf-8'), sort_keys=True, indent=2, ensure_ascii=False)
    logger.info(f"package complete. output in {package_path}")

    # repositories
    pass

if len(sys.argv)>1:
    if sys.argv[1] == 'build':
        build_package(args.name,
                      args.target_dir,
                      INP_CONFIG,
                      args.output_path)

