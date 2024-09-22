import os, sys, subprocess
import shutil
import requests, zipfile
from tqdm import tqdm
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
print(ROOT_PATH)
sys.path.append(ROOT_PATH)
from packageinit import *

import argparse
DEV = True
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
if not DEV:
    args = parser.parse_args()


    if args.repository == "":
        args.repository = f"PGPLLOCALREPO/{args.name}"

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
verify_path(f"{ROOT_PATH}\\cache")

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
    PGPLC_VERSION = "0.6.0"
    PGPLCPP_PATH = f"{ROOT_PATH}\\cache\\PGPLC-{PGPLC_VERSION}.zip"
    if not os.path.exists(PGPLCPP_PATH):
        download_file(f"https://github.com/infstellar/python-git-program-launcher-cpp/releases/download/v{PGPLC_VERSION}/PGPLC-{PGPLC_VERSION}.zip", filename=PGPLCPP_PATH)
    unzip_file(PGPLCPP_PATH, f"{output_path}")
    os.rename(f"{output_path}\\PGPLC-{PGPLC_VERSION}", f"{output_path}\\{name}")



def build_package(name:str, target_dir:str, startup_config:dict, output_path:str):
    verify_path(target_dir)
    verify_path(output_path)
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

    def load_gitignore_patterns(gitignore_path):
        with open(gitignore_path, 'r') as file:
            patterns = [line.strip() for line in file if line.strip() and not line.startswith('#')]
        return patterns

    if os.path.exists(f"{target_dir}\\pyproject.toml"):
        pass
    else:
        DEFAULT_TOML = """
        [build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pgplautobuild"
version = "0.0.1"

[tool.hatch.build]
include = [
  "*"
]
        """
        with open(f"{target_dir}\\pyproject.toml", 'w', encoding='utf-8') as f:
            f.write(DEFAULT_TOML)

    logger.info(f"build python package")

    import build
    import uuid
    k = uuid.uuid4().__str__()[:10]
    build.ProjectBuilder(target_dir).build('sdist', output_directory=f"{ROOT_PATH}\\cache\\{k}")
    import tarfile
    import glob
    logger.info(f"unzip package")
    tarfilename = glob.glob(f"{ROOT_PATH}\\cache\\{k}\\*.gz")[0]
    tar = tarfile.open(tarfilename)
    # verify_path(f"{package_path}\\python-git-program-launcher\\repositories\\{name}")
    tar.extractall(path=f"{ROOT_PATH}\\cache\\{k}")
    shutil.copytree(f"{tarfilename.replace('.tar.gz', '')}", f"{package_path}\\python-git-program-launcher\\repositories\\{name}")
    tar.close()
        # ignore_patterns = shutil.ignore_patterns("*.pyc")
        # shutil.copytree(target_dir, f"{package_path}\\python-git-program-launcher\\repositories\\{name}",
        #                 ignore=ignore_patterns)
    # def ignore_gitignore(rel_path, names):
    #     gitignore_files = GITIGNORE_FILE.split('\n')
    #
    #     for i in gitignore_files:
    #         if rel_path in os.path.join(target_dir, i):
    #             return set(names)
    #         if '*' in i:





    json.dump(startup_config, open(f"{package_path}\\default_config.json", 'w', encoding='utf-8'), sort_keys=True, indent=2, ensure_ascii=False)

    # copy license

    logger.info(f"generate license")

    repo_license = f"{target_dir}\\LICENSE"
    pgpl_license = f"{ROOT_PATH}\\LICENSE"
    with open(f"{package_path}\\LICENSE", "w", encoding='utf-8') as f1:
        strs = ""
        if os.path.exists(repo_license):
            with open(repo_license, "r", encoding='utf-8') as f2:
                strs+=f"{name} LICENSE\n"
                strs+=f2.read()
                strs+="\n"
        if os.path.exists(pgpl_license):
            with open(pgpl_license, "r", encoding='utf-8') as f2:
                strs += f"Python Git Program Launcher LICENSE\n"
                strs+=f2.read()
                strs+="\n"
        f1.write(strs)

    # rename
    logger.info(f"rename exe")
    os.rename(f"{package_path}\\Launcher.exe", f"{package_path}\\{name}.exe")

    logger.info(f"package complete. output in {package_path}")

    # repositories
    pass

if len(sys.argv)>1:
    if sys.argv[1] == 'build':
        build_package(args.name,
                      args.target_dir,
                      INP_CONFIG,
                      args.output_path)

if DEV:
    build_package('123', f'{ROOT_PATH}/repositories/GIA_Launcher_Download_Lib', CONFIG_TEMPLATE, f'{ROOT_PATH}/cache')
