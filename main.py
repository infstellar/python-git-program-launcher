import os.path
import sys
from urllib.parse import urlparse

from utils import *

LAUNCHER_PYTHON_PATH = PYTHON_EXE_PATH
PROGRAM_PYTHON_PATH = LAUNCHER_PYTHON_PATH
REPO_PATH = ""


class GitManager(Command):

    def __init__(self, installer_config):
        self.git = os.path.join(ROOT_PATH, "toolkit\\Git\\mingw64\\bin\\git.exe")
        self.Repository = installer_config["Repository"]
        self.Branch = installer_config["Branch"]
        self.GitProxy = installer_config["GitProxy"]
        self.KeepLocalChanges = installer_config["KeepLocalChanges"]
        self.AutoUpdate = installer_config["AutoUpdate"]
        self.tag = installer_config["Tag"]
        self.folder_path = REPO_PATH

        verify_path(self.folder_path)

    @staticmethod
    def remove(file):
        try:
            os.remove(file)
            logger.info(f'Removed file: {file}')
        except FileNotFoundError:
            logger.info(f'File not found: {file}')

    def git_repository_init(self, repo, source='origin', branch='master', proxy=False, keep_changes=False):
        logger.hr('Git Init')
        if not self.execute(f'"{self.git}" init', allow_failure=True):
            self.remove('./.git/config')
            self.remove('./.git/index')
            self.remove('./.git/HEAD')
            self.execute(f'"{self.git}" init')

        logger.hr('Set Git Proxy', 1)
        if proxy:
            self.execute(f'"{self.git}" config --local http.proxy {proxy}')
            self.execute(f'"{self.git}" config --local https.proxy {proxy}')
        else:
            self.execute(f'"{self.git}" config --local --unset http.proxy', allow_failure=True)
            self.execute(f'"{self.git}" config --local --unset https.proxy', allow_failure=True)

        logger.hr('Set Git Repository', 1)
        if not self.execute(f'"{self.git}" remote set-url {source} {repo}', allow_failure=True):
            self.execute(f'"{self.git}" remote add {source} {repo}')

        logger.hr('Fetch Repository Branch', 1)
        # logger.hr('For cn user: 重要: 如果你正在使用Github地址，确保你已经启动Watt Toolkit或其他加速器')
        self.execute(f'"{self.git}" fetch {source} {branch}')

        logger.hr('Pull Repository Branch', 1)
        # Remove git lock
        lock_file = './.git/index.lock'
        if os.path.exists(lock_file):
            logger.info(f'Lock file {lock_file} exists, removing')
            os.remove(lock_file)
        if keep_changes:
            if self.execute(f'"{self.git}" stash', allow_failure=True):
                self.execute(f'"{self.git}" pull --ff-only {source} {branch}')
                if self.execute(f'"{self.git}" stash pop', allow_failure=True):
                    pass
                else:
                    # No local changes to existing files, untracked files not included
                    logger.info('Stash pop failed, there seems to be no local changes, skip instead')
            else:
                logger.info('Stash failed, this may be the first installation, drop changes instead')
                self.execute(f'"{self.git}" reset --hard {source}/{branch}')
                self.execute(f'"{self.git}" pull --ff-only {source} {branch}')
        else:
            self.execute(f'"{self.git}" reset --hard {source}/{branch}')
            self.execute(f'"{self.git}" pull --ff-only {source} {branch}')

        if self.tag != 'lastest' and self.tag != '':
            self.execute(f'"{self.git}" checkout {self.tag}')

        logger.hr('Show Version', 1)
        self.execute(f'"{self.git}" log --no-merges -1')

    def git_install(self):
        logger.hr(f'Update {PROGRAM_NAME}', 0)

        if not self.AutoUpdate:
            logger.info('AutoUpdate is disabled, skip')
            return

        os.environ['PATH'] += os.pathsep + self.git

        self.git_repository_init(
            repo=self.Repository,
            source='origin',
            branch=self.Branch,
            proxy=self.GitProxy,
            keep_changes=self.KeepLocalChanges,
        )


class PipManager(Command):

    def __init__(self, installer_config):
        self.RequirementsFile = installer_config["RequirementsFile"]
        self.python = PROGRAM_PYTHON_PATH  # os.path.join(os.path.dirname(os.path.abspath(__file__)), "toolkit\\python.exe")

        self.InstallDependencies = installer_config["InstallDependencies"]
        self.PypiMirror = installer_config["PypiMirror"]
        if self.PypiMirror == "AUTO":
            self.PypiMirror = {
                "zh_CN": "http://mirrors.aliyun.com/pypi/simple",
                "en_US": "https://pypi.org/simple"
            }[GLOBAL_LANG]

        # self.execute("set _pyBin=%_root%\\toolkit")
        # self.execute("set _GitBin=%_root%\\toolkit\Git\mingw64\\bin")
        # self.execute("set PATH=%_root%\\toolkit\\alias;%_root%\\toolkit\command;%_pyBin%;%_pyBin%\Scripts;%_GitBin%")

    def requirements_file(self):
        return 'requirements.txt'

    def pip(self):
        return f'"{self.python}" -m pip'
        # return 'pip'

    def pip_install(self):
        logger.info('Update Dependencies')

        if not self.InstallDependencies:
            logger.info('InstallDependencies is disabled, skip')
            return

        logger.info('Check Python')
        self.execute(f'"{self.python}" --version')

        arg = []
        if self.PypiMirror:
            mirror = self.PypiMirror
            arg += ['-i', mirror]
            # Trust http mirror
            # if 'http:' in mirror:
            arg += ['--trusted-host', urlparse(mirror).hostname]
        # arg += ['--disable-pip-version-check']
        arg = ' ' + ' '.join(arg) if arg else ''
        # Don't update pip, just leave it.
        logger.hr('Update pip', 1)
        self.execute(f'{self.pip()} install --upgrade pip{arg}')
        self.execute(f'{self.pip()} install --upgrade setuptools{arg}')
        # self.execute(f'pip install progressbar2{arg}')

        logger.hr('Update Dependencies', 1)

        # self.execute((f'{self.pip()} install pycocotools-windows{arg}'))
        self.execute(f'{self.pip()} install -r {self.requirements_file()}{arg}')


class PythonManager(Command):

    @logger.catch()
    def __init__(self, installer_config):
        self.python_version = installer_config['PythonVersion']
        self.python_folder = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version))
        self.python_path = os.path.join(self.python_folder, "python.exe")
        self.python_mirror = installer_config['PythonMirror']
        if self.python_mirror == "AUTO":
            self.python_mirror = {
                "zh_CN": "https://mirrors.huaweicloud.com/python",
                "en_US": "https://www.python.org/ftp/python"
            }[GLOBAL_LANG]
        # https://registry.npmmirror.com/-/binary/python/3.10.1/python-3.10.1-amd64.exe
        paths = ''
        for i in os.environ['PATH'].split(';'):
            if "Scripts" not in i and "Anaconda" not in i:
                paths += os.pathsep + i
        
        paths = paths[1:]
        
        os.environ['PATH'] = paths

        os.environ['PATH'] += os.pathsep + os.path.join(self.python_folder)
        os.environ['PATH'] += os.pathsep + os.path.join(self.python_folder, "Scripts")
        os.environ['PATH'] += os.pathsep + os.path.join(self.python_folder, "Lib")
        os.environ['PATH'] += os.pathsep + os.path.join(self.python_folder, "Lib", "site-packages")
        progress_path = os.path.join(ROOT_PATH, "toolkit", "python_site_packages")
        sys.path.insert(0, progress_path)

    def download_url(self, url, dst):
        from tqdm import tqdm
        import requests
        first_byte = 0
        # tqdm 里可选 total= 参数，不传递这个参数则不显示文件总大小
        pbar = tqdm(initial=first_byte, unit='B', unit_scale=True, desc=dst)
        # 设置stream=True参数读取大文件
        req = requests.get(url, stream=True)
        with open(dst, 'ab') as f:
            # 每次读取一个1024个字节
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
        pbar.close()

    def download_python_zip(self):
        import zipfile
        ver = self.python_version
        url = fr"{self.python_mirror}/{ver}/python-{ver}-embed-amd64.zip"
        logger.info(f'url: {url}')
        file_name = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version), f'python-{ver}-amd64.zip')
        self.download_url(url, file_name)
        logger.hr("Successful Download")
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(self.python_folder)
        # install pip
        self.execute(f'"{self.python_path}" {os.path.join(ROOT_PATH, "toolkit", "get-pip.py")}')
        
        ver2 = ver.split(".")[0]+ver.split(".")[1]
        # https://blog.csdn.net/liangma/article/details/120022530
        with open(os.path.join(self.python_folder, fr"python{ver2}._pth"), 'r+') as f:
            f.seek(0)
            file_str = f.read()
            file_str = file_str.replace('# import site', 'import site')
            file_str = file_str.replace('#import site', 'import site')
            f.seek(0)
            f.write(file_str)
        
        # self.execute(f'pip')
    
    def download_python_installer(self):
        # 3.7 only
        logger.warning("确认python版本：")
        logger.warning("你的电脑每种大版本的python只能安装过一种。如果你已预先安装了，必须先手动卸载。")
        logger.warning("例1：目标版本3.7.6，而你的电脑安装了3.7.8，则必须先卸载3.7.8版本的python再使用。")
        logger.warning("例2：目标版本3.10.10，而你的电脑安装了3.10.10，则必须先卸载3.10.10版本的python再使用。")
        logger.warning("Anaconda等独立包管理器不受此影响。")
        logger.warning("python-git-program-launcher不会添加python到环境变量；不会添加到所有用户；不会添加python launcher程序。但放弃使用时，仍需到控制面板卸载python。")
        input("按下回车以确认。")
        # self.download_python_installer()
        ver = self.python_version
        url = fr"{self.python_mirror}/{ver}/python-{ver}-amd64.exe"
        # url = fr"https://www.python.org/ftp/python/{ver}/python-{ver}-amd64.exe"
        # url = fr"https://www.python.org/ftp/python/{ver}/python-{ver}-embed-amd64.zip"
        logger.info(f'url: {url}')
        file_name = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version), f'python-{ver}-amd64.exe')
        file_name2 = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version), f'python_{ver}.exe')

        if not os.path.exists(file_name2):
            if os.path.exists(file_name):
                os.remove(file_name)
            self.download_url(url, file_name)
            os.rename(file_name, file_name2)

        logger.hr("Download Successfully")

        # with zipfile.ZipFile(file_name, 'r') as zip_ref:
        #     zip_ref.extractall(self.python_folder)


        file_name = file_name2

        os.chdir(self.python_folder)
        self.execute(
            f'python_{ver}.exe Include_launcher=0 InstallAllUsers=0 Include_test=0 SimpleInstall=1 /passive TargetDir={self.python_folder}',
            is_format=False)
        os.chdir(ROOT_PATH)
        logger.hr("Please waiting, python is installing. It may cost a few minutes.")

        while 1:
            time.sleep(1)
            if os.path.exists(self.python_path):
                break
        logger.hr("Python installed successfully. Cleaning.")
        time.sleep(1)
        logger.hr("Python is installed.")

    def install_pip(self):
        # self.execute(f'curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
        # self.execute(f'"set PATH=%path%;{os.path.join(self.python_folder, "Scripts")}"')
        self.execute(f'"{self.python_path}" {os.path.join(ROOT_PATH, "toolkit", "get-pip.py")}')
        # self.execute(f'"{self.python_path}" {os.path.join(ROOT_PATH, "toolkit", "get-pip.py --force-reinstall")}')

    def run(self):
        verify_path(self.python_folder)
        
        if not os.path.exists(self.python_path):
            logger.hr(f"Downloading Python Version: {self.python_version} into {self.python_folder}")
            
            self.download_python_zip()

        # if not os.path.exists(os.path.join(self.python_folder, "Lib")):
        #     logger.hr(f"Installing pip")
        #     self.install_pip()

        global PROGRAM_PYTHON_PATH
        PROGRAM_PYTHON_PATH = self.python_path
        # self.execute(f'{self.python_path} -m pip')


class ConfigEditor():
    def __init__(self):
        pass

    def _input(self, info={'zh_CN':'输入','en_US':'Input'}[GLOBAL_LANG], possible_answer: list = None, ignore_case: bool = False, input_type: object = str,
               allow_empty=True):
        note = info
        if possible_answer is not None:
            x = {'zh_CN':'选项','en_US':'Options'}[GLOBAL_LANG]
            note += f" {x}: " + str(possible_answer)
        logger.info(f"{note}")
        r = input()
        if ignore_case:
            r = r.lower()
        if possible_answer is not None:
            if r not in possible_answer:
                logger.error("Illegal parameters")
                return self._input(info, possible_answer, ignore_case, input_type, allow_empty)

        if allow_empty:
            if r == '':
                return ''
        else:
            if r == '':
                logger.error("Illegal parameters: Empty")
                return self._input(info, possible_answer, ignore_case, input_type, allow_empty)

        try:
            r = input_type(r)
        except Exception as e:
            logger.error("Illegal parameter type")
            return self._input(info, possible_answer, ignore_case, input_type, allow_empty)
        return r

    def _input_bool(self, info):
        r = self._input(info, possible_answer=['y', 'n', ''], ignore_case=True)
        if r != '':
            r = {'y': True, 'n': False}[r]
        return r

    def _download_config_from_repo(self):
        pass

    def run(self):

        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'r') as f:
            launching_config = str(f.read())
            f.close()
        logger.info({'zh_CN':'当前配置','en_US':'Config'}[GLOBAL_LANG]+f": {launching_config}")
        is_edit = self._input_bool({'zh_CN':'你想要改变配置吗','en_US':'Do you want to edit Settings?'}[GLOBAL_LANG])

        if launching_config == '':
            logger.info({'zh_CN':'未选择配置文件。必须选择配置文件。','en_US':'No config selected. A config must be selected.'}[GLOBAL_LANG])
            is_edit = True
        if is_edit:
            possible_configs = load_json_from_folder(os.path.join(ROOT_PATH, 'configs'))
            possible_configs = [ii['label'][:ii['label'].index('.')] for ii in possible_configs]
            if GLOBAL_LANG == 'en_US':
                logger.hr(f"possible configs")
            elif GLOBAL_LANG == 'zh_CN':
                logger.hr(f"可能的config名")

            for i in possible_configs:
                logger.info(i)
            if GLOBAL_LANG == 'en_US':
                logger.info("Please enter the config name.")
                logger.info("Config will be created automatically if the file does not exist.")
            elif GLOBAL_LANG == 'zh_CN':
                logger.info("请输入Config名。")
                logger.info("如果该文件不存在，将自动创建配置。")
            # logger.info("If the repository has pre-configured files, you can also download the configuration file by entering the repository address directly.")

            r = self._input(allow_empty=False)
            # if 'http' in r:
            #     pass
            logger.info({'zh_CN': '如果你不想改变设置，直接在选项上按回车键。',
                         'en_US': 'If you do not want to change the settings, press enter directly on the option.'}[GLOBAL_LANG])
            self.edit_config(r)

            possible_configs = load_json_from_folder(os.path.join(ROOT_PATH, 'configs'))
            possible_configs = [ii['label'][:ii['label'].index('.')] for ii in possible_configs]

            logger.info({'zh_CN': '请输入启动配置文件名。',
                         'en_US': 'Please enter the launching config name.'}[GLOBAL_LANG])
            launching_config = self._input(allow_empty=False, possible_answer=possible_configs)

            with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w', encoding='utf-8') as f:
                f.write(launching_config)
                f.close()

        return load_json(launching_config)

    def edit_config(self, config_name: str):
        if not os.path.exists(os.path.join(ROOT_PATH, 'configs', config_name + '.json')):
            save_json(CONFIG_TEMPLATE, config_name)
        config = load_json(config_name)

        var_type = str

        for k in config.keys():
            info = f"Editing: {k} ({config[k]})"
            if isinstance(config[k], bool):
                var_type = bool
                r = self._input(info, possible_answer=['y', 'n', ''], ignore_case=True)
                if r != '':
                    r = {'y': True, 'n': False}[r]
            elif isinstance(config[k], int):
                var_type = int
                r = self._input(info, input_type=var_type)
            elif isinstance(config[k], float):
                var_type = float
                r = self._input(info, input_type=var_type)
            else:
                var_type = str
                r = self._input(info, input_type=var_type)

            if r != '':
                logger.info(f"config {k}: {config[k]} -> {r}")
                config[k] = r

        save_json(config, config_name)
        logger.hr(f"Successfully edit config.")


if __name__ == "__main__":
    logger.hr(f"Welcome to {PROGRAM_NAME}", 0)
    logger.hr("The program is free and open source on github")
    # logger.hr("Make sure you have read README.md and configured installer_config.json")
    if not os.path.exists(os.path.join(ROOT_PATH, 'launcher_config_name.txt')):
        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w') as f:
            f.close()
    launching_config = ConfigEditor().run()
    PythonManager(launching_config).run()
    logger.info(launching_config)
    REPO_PATH = os.path.join(ROOT_PATH, 'repositories', launching_config['Repository'].split('/')[-1])
    verify_path(REPO_PATH)
    os.chdir(REPO_PATH)
    
    logger.hr("Launching...")
    GitManager(launching_config).git_install()
    PipManager(launching_config).pip_install()
    
    sys.path[0] = REPO_PATH
    os.environ['PATH'] = REPO_PATH + os.environ['PATH'] + os.pathsep
    
    logger.hr("successfully install. Activating GIA", 0)
    print(f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')

    # os.system("color 07")
    os.system(f"title {PROGRAM_NAME} Console")
    os.system(f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')
