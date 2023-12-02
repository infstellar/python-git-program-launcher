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
                pass
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
        self.python_folder = os.path.join(ROOT_PATH, f'installed_python', f"{self.python_version}_{n}")
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
        # site_packages_path = os.path.join(ROOT_PATH, "toolkit", "python_site_packages")
        # sys.path.insert(0, site_packages_path)
        # logger.error(os.environ['PATH'])
        # DEBUG
        # self.execute('set path')
        # self.execute(f'"{self.python_path}" -m pip install --no-cache-dir -r {os.path.join(ROOT_PATH, "toolkit", "basic_requirements.txt")}')

    

    def clean_py(self, py_folder):
        import shutil
        shutil.rmtree(py_folder)
    
    def download_python_zip(self):
        # import zipfile
        self.progress_tracker.inp(t2t('download python'), 0.1)
        if PROXY_LANG == 'zh_CN':
            CONDARC_FILE_PATH = rf'{os.environ["USERPROFILE"]}/.condarc'
            CONDARC_MARK_PATH = rf'{os.environ["USERPROFILE"]}/.condarc_flag'
            if not os.path.exists(CONDARC_FILE_PATH):
                CONDARC_NOT_FOUND_flag = True
                import shutil
                self.info(t2t('The .condarc not found, create one'), mode='a')
                shutil.copyfile(rf'{ROOT_PATH}/toolkit/.condarc', CONDARC_FILE_PATH)
                shutil.copyfile(rf'{ROOT_PATH}/toolkit/.condarc', CONDARC_MARK_PATH)
            else:
                self.info(t2t('The .condarc already exists, you may have install anaconda/miniconda, the original configuration file will be used'), mode='a')
        
        self.execute(fr'"{ROOT_PATH}/toolkit/Scripts/activate.bat" && conda create -p "{self.python_folder}" python={self.python_version} -y')
        
        if os.path.exists(CONDARC_MARK_PATH):
            if DEBUG_MODE: self.info('remove .condarc file')
            os.remove(CONDARC_FILE_PATH)
            os.remove(CONDARC_MARK_PATH)

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
        
# if __name__ == '__main__':
    #MiniCondaManager(CONFIG_TEMPLATE).create_python()