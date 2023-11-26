import os.path
import sys
from urllib.parse import urlparse
import yaml

from pgpl.utils import *
from pgpl.pgpl_pth import generate_pgplpth




# class PGPLOut():
#     def __init__(self) -> None:
#         self.original = sys.stdout
#         self.flush = self.original.flush
        
#     def write(self,x):
#         if 'Requirement already satisfied: ' in x:
#             pass
#         else:
#             self.original.write(x)
    

    
class GitManager(Command):

    def __init__(self, installer_config, progress_tracker=None):
        super().__init__(progress_tracker=progress_tracker)
        self.git = os.path.join(ROOT_PATH, "toolkit/Git/mingw64/bin/git.exe")
        self.Repository = installer_config["Repository"]
        self.Branch = installer_config["Branch"]
        self.GitProxy = installer_config["GitProxy"]
        self.KeepLocalChanges = installer_config["KeepLocalChanges"]
        self.AutoUpdate = installer_config["AutoUpdate"]
        self.tag = installer_config["Tag"]
        self.folder_path = REPO_PATH

        os.environ['PATH'] += os.pathsep + self.git
        verify_path(self.folder_path)
        
        

    @staticmethod
    def remove(file):
        try:
            os.remove(file)
            logger.info(f'Removed file: {file}')
        except FileNotFoundError:
            logger.info(f'File not found: {file}')

    def git_repository_init(self, repo, source='origin', branch='master', proxy=False, keep_changes=False):
        self.logger_hr(t2t('Git Init'), progress=0.1)
        if not self.execute(f'"{self.git}" init', allow_failure=True):
            self.remove('./.git/config')
            self.remove('./.git/index')
            self.remove('./.git/HEAD')
            self.execute(f'"{self.git}" init')

        self.logger_hr(t2t('Set Git Proxy'), 1, progress=0.2)
        if proxy:
            self.execute(f'"{self.git}" config --local http.proxy {proxy}')
            self.execute(f'"{self.git}" config --local https.proxy {proxy}')
        else:
            self.execute(f'"{self.git}" config --local --unset http.proxy', allow_failure=True)
            self.execute(f'"{self.git}" config --local --unset https.proxy', allow_failure=True)

        self.logger_hr(t2t('Set Git Repository'), 1, progress=0.3)
        if not self.execute(f'"{self.git}" remote set-url {source} {repo}', allow_failure=True):
            self.execute(f'"{self.git}" remote add {source} {repo}')

        self.logger_hr(t2t('Fetch Repository Branch'), 1, progress=0.4)
        self.execute(f'"{self.git}" fetch {source} {branch}')

        self.logger_hr(t2t('Pull Repository Branch'), 1, progress=0.5)
        # Remove git lock
        lock_file = './.git/index.lock'
        if os.path.exists(lock_file):
            self.info(f'Lock file {lock_file} exists, removing')
            os.remove(lock_file)
        if keep_changes:
            if self.execute(f'"{self.git}" stash', allow_failure=True):
                run_command(f'"{self.git}" pull --ff-only {source} {branch}', progress_tracker=self.progress_tracker)
                if self.execute(f'"{self.git}" stash pop', allow_failure=True):
                    pass
                else:
                    # No local changes to existing files, untracked files not included
                    self.info(t2t('Stash pop failed, there seems to be no local changes, skip instead'))
            else:
                self.info(t2t('Stash failed, this may be the first installation, drop changes instead'))
                self.execute(f'"{self.git}" reset --hard {source}/{branch}')
                run_command(f'"{self.git}" pull --ff-only {source} {branch}', progress_tracker=self.progress_tracker)
        else:
            self.execute(f'"{self.git}" reset --hard {source}/{branch}')
            run_command(f'"{self.git}" pull --ff-only {source} {branch}', progress_tracker=self.progress_tracker)

        if self.tag != 'lastest' and self.tag != '':
            self.execute(f'"{self.git}" checkout {self.tag}')

        self.logger_hr(t2t('Show Version'), 1, progress=0.8)
        self.execute(f'"{self.git}" log --no-merges -1')

    def git_install(self, allow_failure = False):
        self.logger_hr(f'Update {PROGRAM_NAME}', 0, progress=0.9)
        
        if not self.AutoUpdate:
            self.info(t2t('AutoUpdate is disabled, skip'))
            return

        if False:
            r = self.execute(f'"{self.git}" config --local sendpack.sideband false', allow_failure=True)
            if r:
                r = self.execute(f'"{self.git}" diff', allow_failure=True)
                if r:
                    if self.progress_tracker.console_output == "":
                        self.info(t2t('no difference in git, skip'))
                        return

        try:
            self.git_repository_init(
                repo=self.Repository,
                source='origin',
                branch=self.Branch,
                proxy=self.GitProxy,
                keep_changes=self.KeepLocalChanges,
            )
        except Exception as e:
            if allow_failure:
                self.info(t2t("update git repo fail, skip"))
            else:
                raise e


class PipManager(Command):

    def __init__(self, installer_config, progress_tracker=None):
        super().__init__(progress_tracker=progress_tracker)
        self.RequirementsFile = installer_config["RequirementsFile"]
        self.python = PROGRAM_PYTHON_PATH  # os.path.join(os.path.dirname(os.path.abspath(__file__)), "toolkit\\python.exe")

        self.InstallDependencies = installer_config["InstallDependencies"]
        self.PypiMirror = installer_config["PypiMirror"]
        if self.PypiMirror == "AUTO" or self.PypiMirror == "":
            self.PypiMirror = {
                "zh_CN": "https://pypi.tuna.tsinghua.edu.cn/simple",
                "en_US": "https://pypi.org/simple"
            }[PROXY_LANG]
        
        self.pip_arg = []
        if self.PypiMirror:
            mirror = self.PypiMirror
            self.pip_arg += ['-i', mirror]
            # Trust http mirror
            # if 'http:' in mirror:
            self.pip_arg += ['--trusted-host', urlparse(mirror).hostname]
        # self.pip_arg += ['--disable-pip-version-check']
        self.pip_arg = ' ' + ' '.join(self.pip_arg) if self.pip_arg else ''
        
        # self.execute("set _pyBin=%_root%\\toolkit")
        # self.execute("set _GitBin=%_root%\\toolkit\Git\mingw64\\bin")
        # self.execute("set PATH=%_root%\\toolkit\\alias;%_root%\\toolkit\command;%_pyBin%;%_pyBin%\Scripts;%_GitBin%")

    def requirements_file(self):
        return 'requirements.txt'

    def pip(self):
        return f'"{self.python}" -m pip'
        # return 'pip'

    def update_pip(self):
        self.execute(f'{self.pip()} install --upgrade pip{self.pip_arg}')
        self.execute(f'{self.pip()} install setuptools{self.pip_arg}')
        self.execute(f'{self.pip()} install wheel{self.pip_arg}')
        self.execute(f'{self.pip()} install -r "{os.path.join(ROOT_PATH, "toolkit", "basic_requirements.txt")}"{self.pip_arg}')
    
    def pip_install(self, check_pip = True, check_reqs = True):
        self.info(t2t('Update Dependencies'))

        if not self.InstallDependencies:
            self.info(t2t('InstallDependencies is disabled, skip'))
            return

        self.info(t2t('Check Python'))
        self.execute(f'"{self.python}" --version')
        
        # self.execute(f'pip install progressbar2{arg}')

        try:
            self.logger_hr(t2t('Update Dependencies'), 1, progress=0.3)
            if check_pip:
                self.execute(f'{self.pip()} install -r "{os.path.join(ROOT_PATH, "toolkit", "lowest_requirements.txt")}"{self.pip_arg}')
                self.execute(f'{self.pip()} install -r "{os.path.join(ROOT_PATH, "toolkit", "basic_requirements.txt")}"{self.pip_arg}')
            if check_reqs:
                self.execute(f'{self.pip()} install -r {self.requirements_file()}{self.pip_arg}')
        except ExecutionError as e:
            self.logger_hr(t2t('Update Dependencies Fail, Update pip'), 1, progress=0.1)
            self.update_pip()

        # self.execute((f'{self.pip()} install pycocotools-windows{arg}'))
        
        self.progress_tracker.set_percentage(1)


class PythonManager(Command):

    @logger.catch()
    def __init__(self, installer_config, progress_tracker:ProgressTracker=None):
        super().__init__(progress_tracker=progress_tracker)
        self.python_version = installer_config['PythonVersion']
        n = installer_config['Repository'].split('/')[-1]
        self.python_folder = os.path.join(ROOT_PATH, 'toolkit', f'python', f"{self.python_version}_{n}")
        self.python_path = os.path.join(self.python_folder, "python.exe")
        self.python_mirror = installer_config['PythonMirror']
        if self.python_mirror == "AUTO" or self.python_mirror == "":
            self.python_mirror = {
                "zh_CN": "https://mirrors.huaweicloud.com/python",
                "en_US": "https://www.python.org/ftp/python"
            }[PROXY_LANG]
        self.PypiMirror = installer_config["PypiMirror"]
        if self.PypiMirror == "AUTO" or self.PypiMirror == "":
            self.PypiMirror = {
                "zh_CN": "https://pypi.tuna.tsinghua.edu.cn/simple",
                "en_US": "https://pypi.org/simple"
            }[PROXY_LANG]
        
        # https://registry.npmmirror.com/-/binary/python/3.10.1/python-3.10.1-amd64.exe
        # paths = ''
        # for i in os.environ['PATH'].split(';'):
        #     if "Scripts" not in i and "Anaconda" not in i:
        #         paths += os.pathsep + i
        
        # paths = paths[1:]
        
        # os.environ['PATH'] = paths

        def add_environ(x):
            os.environ['PATH'] = x + os.pathsep + os.environ['PATH']
        self.progress_tracker.inp(t2t('set environ'), 0)
        # add_environ(os.path.join(ROOT_PATH, "toolkit", "Scripts"))
        add_environ(os.path.join(self.python_folder, "Lib", "site-packages"))
        add_environ(os.path.join(self.python_folder, "Lib"))
        add_environ(os.path.join(self.python_folder, "Scripts"))
        add_environ(self.python_folder)
        site_packages_path = os.path.join(ROOT_PATH, "toolkit", "python_site_packages")
        sys.path.insert(0, site_packages_path)
        # logger.error(os.environ['PATH'])
        # DEBUG
        # self.execute('set path')
        # self.execute(f'"{self.python_path}" -m pip install --no-cache-dir -r {os.path.join(ROOT_PATH, "toolkit", "basic_requirements.txt")}')

    

    def clean_py(self, py_folder):
        import shutil
        shutil.rmtree(py_folder)
    
    def download_python_zip(self):
        import zipfile
        self.progress_tracker.inp(t2t('download python'), 0.1)
        ver = self.python_version
        ver2 = ver.split(".")[0]+ver.split(".")[1]
        url = fr"{self.python_mirror}/{ver}/python-{ver}-embed-amd64.zip"
        self.info(f'url: {url}')
        file_name = os.path.join(self.python_folder, f'python-{ver}-amd64.zip')
        download_url(url, file_name)
        self.logger_hr(t2t("Download python successfully, extract zip"), progress=0.5)
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(self.python_folder)
        # with zipfile.ZipFile(file_name.replace(f'python-{ver}-amd64.zip', f'python{ver2}.zip'), 'r') as zip_ref:
        #     zip_ref.extractall(self.python_folder)
        # install pip
        self.logger_hr("Installing pip", progress=0.8)
        pip_path = os.path.join(ROOT_PATH, "toolkit", "Lib\\site-packages\\pip", "__main__.py")
        self.execute(f'"{LAUNCHER_PYTHON_PATH}" "{pip_path}" config set global.index-url {self.PypiMirror}')
        self.execute(f'"{self.python_path}" "{os.path.join(ROOT_PATH, "toolkit", "get-pip.py")}" --no-setuptools --no-wheel')
        # self.execute(f'"{self.python_path}" -m pip install setuptools ')
        
        # https://blog.csdn.net/liangma/article/details/120022530
        with open(os.path.join(self.python_folder, fr"python{ver2}._pth"), 'r+') as f:
            f.seek(0)
            file_str = f.read()
            file_str = file_str.replace('# import site', 'import site')
            file_str = file_str.replace('#import site', 'import site')
            f.seek(0)
            f.write(file_str)
        
        generate_pgplpth(self.python_folder)
        
        
        
        # self.execute(f'pip')
    
    def download_python_installer(self):
        # 这个没bug，但是要安装，因此暂时弃用
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
        self.info(f'url: {url}')
        file_name = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version), f'python-{ver}-amd64.exe')
        file_name2 = os.path.join(ROOT_PATH, 'toolkit', 'python', str(self.python_version), f'python_{ver}.exe')

        if not os.path.exists(file_name2):
            if os.path.exists(file_name):
                os.remove(file_name)
            download_url(url, file_name)
            os.rename(file_name, file_name2)

        self.logger_hr(t2t("Download Successfully"))

        # with zipfile.ZipFile(file_name, 'r') as zip_ref:
        #     zip_ref.extractall(self.python_folder)


        file_name = file_name2

        os.chdir(self.python_folder)
        self.execute(
            f'python_{ver}.exe Include_launcher=0 InstallAllUsers=0 Include_test=0 SimpleInstall=1 /passive TargetDir={self.python_folder}',
            is_format=False)
        os.chdir(ROOT_PATH)
        self.logger_hr(t2t("Please waiting, python is installing. It may cost a few minutes."))

        while 1:
            time.sleep(1)
            if os.path.exists(self.python_path):
                break
        self.logger_hr(t2t("Python installed successfully. Cleaning."))
        time.sleep(1)
        self.logger_hr(t2t("Python is installed."))

    def install_pip(self):
        pass
        # self.execute(f'curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
        # self.execute(f'"set PATH=%path%;{os.path.join(self.python_folder, "Scripts")}"')
        # self.execute(f'"{self.python_path}" "{os.path.join(ROOT_PATH, "toolkit", "get-pip.py")}"')
        # self.execute(f'"{self.python_path}" {os.path.join(ROOT_PATH, "toolkit", "get-pip.py --force-reinstall")}')

    def run(self):
        verify_path(self.python_folder)
        
        if not os.path.exists(self.python_path):
            self.logger_hr(f"Downloading Python Version: {self.python_version} into {self.python_folder}", progress=0.05)
            # logger.warning(t2t("Please do not exit the program while python is being downloaded. If you accidentally quit or the installation fails, empty the . /toolkit/python folder in the corresponding folder and try again."))
            self.download_python_zip()
        else:
            try:
                self.progress_tracker.inp(t2t('Verify pip installation'), 0.05)
                self.execute(f'"{self.python_path}" "{self.python_folder}/Lib/site-packages/pip/__main__.py" --version')
            except ExecutionError as e:
                logger.warning(t2t("pip fail, reinstall python"))
                self.clean_py(self.python_folder)
                verify_path(self.python_folder)
                self.download_python_zip()
        
        
        # if not os.path.exists(os.path.join(self.python_folder, "Lib")):
        #     logger.hr(f"Installing pip")
        #     self.install_pip()
        global PROGRAM_PYTHON_PATH
        PROGRAM_PYTHON_PATH = self.python_path
        self.logger_hr(t2t('python installed'), progress=1)
        return self.python_path
        # self.execute(f'{self.python_path} -m pip')