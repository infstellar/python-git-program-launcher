import hashlib
import os.path
import threading
from pathlib import Path

from pywebio import *

from pgpl.advance_page import AdvancePage
from pgpl.console import *
from pgpl.webio_utils import *
from pgpl.managers import *
from pgpl.config_editer import ConfigPage


class ShowProcess():
    PROCESSBAR_PYTHON_MANAGER = AN()
    PROCESSBAR_STAGE = AN()

    SCOPE_PROGRESS_INFO = AN()
    SCOPE_PROGRESS_CMD = AN()
    SCOPE_PROGRESS_CMD_OUTPUT = AN()
    SCOPE_PROGRESS_CMD_STDERR = AN()
    SCOPE_EXIT = AN()

    def __init__(self, progress_tracker: ProgressTracker, title='') -> None:
        self.progress_tracker = progress_tracker
        self.title = title

    def create_popup(self):
        session.set_env(output_animation=False)
        # clean pt
        self.progress_tracker.err_info = ''
        self.progress_tracker.console_output = ''
        with output.popup(self.title, closable=False) as s:
            output.put_markdown(t2t("## Progress"))
            output.put_scope(self.SCOPE_PROGRESS_CMD_STDERR)
            output.clear(self.SCOPE_PROGRESS_CMD_STDERR)
            output.put_scope(self.SCOPE_PROGRESS_INFO)
            output.put_processbar(self.PROCESSBAR_STAGE)
            output.set_processbar(self.PROCESSBAR_STAGE, 0)
            output.put_processbar(self.PROCESSBAR_PYTHON_MANAGER)
            output.put_scope(self.SCOPE_PROGRESS_CMD)
            output.put_scope(self.SCOPE_PROGRESS_CMD_OUTPUT)
            output.put_scope(self.SCOPE_EXIT)

            # output.put_button(t2t("Stop start"), onclick = self._stop_start)

        def clear_and_put_text(_text, _scope):
            output.clear(_scope)
            output.put_markdown(_text, scope=_scope)

        def set_processbar(x: ProgressTracker, processbar_name: str, info_scope: str, cmd_scope, cmd_output_scope,
                           cmd_err_scope):
            last_info = ""
            last_progress = 0
            last_cmd = ''
            last_cmd_output = ''
            # last_cmd_err = ''
            while 1:
                if self.progress_tracker.end_flag: break
                time.sleep(0.1)
                if x.info != last_info:
                    last_info = x.info
                    clear_and_put_text(t2t("## Info: \n") + last_info, info_scope)
                if x.percentage != last_progress:
                    last_progress = x.percentage
                    output.set_processbar(processbar_name, last_progress)
                if x.cmd != last_cmd:
                    last_cmd = x.cmd
                    clear_and_put_text(t2t("#### Running Command: \n") + last_cmd, cmd_scope)
                if x.console_output != last_cmd_output:
                    last_cmd_output = x.console_output
                    clear_and_put_text(t2t("#### Command Output: \n") + last_cmd_output, cmd_output_scope)
                # if x.err_info != last_cmd_err:
                #     last_cmd_err = x.err_info
                #     clear_and_put_text(t2t("# ***ERR INFO*** \n")+last_cmd_err, cmd_err_scope)

        self.progress_tracker.end_flag = False
        self.t = threading.Thread(target=set_processbar, daemon=False,
                                  args=(self.progress_tracker, self.PROCESSBAR_PYTHON_MANAGER, self.SCOPE_PROGRESS_INFO,
                                        self.SCOPE_PROGRESS_CMD, self.SCOPE_PROGRESS_CMD_OUTPUT,
                                        self.SCOPE_PROGRESS_CMD_STDERR))
        session.register_thread(self.t)
        self.t.start()

    def show_exception(self, x=''):
        with output.use_scope(self.SCOPE_PROGRESS_INFO):
            output.put_markdown(t2t('***ERROR OCCURRED!***'))
            output.put_markdown(x)
            # output.put_markdown(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
            if self.progress_tracker.err_slu:
                output.put_markdown(t2t("## Possible reasons: "))
                output.put_markdown(self.progress_tracker.err_slu)
            output.put_markdown(t2t('***CHECK UP THE CONSOLE OR SEND THE ERROR LOG***'))
            # time.sleep(0.2)

            output.put_markdown(t2t("# ***ERR INFO*** \n") + self.progress_tracker.err_info,
                                scope=self.SCOPE_PROGRESS_CMD_STDERR).style('font: SimHei; color: red')

    def stop(self, is_success=True):
        session.set_env(output_animation=True)
        output.put_button("Exit", onclick=output.close_popup, color=('success' if is_success else 'fail'),
                          scope=self.SCOPE_EXIT)
        self.progress_tracker.end_flag = True
        output.set_processbar(self.PROCESSBAR_STAGE, 1)
        output.set_processbar(self.PROCESSBAR_PYTHON_MANAGER, 1)


class MainPage(AdvancePage, Command, ConfigPage):
    SCOPE_START = AN()
    SCOPE_LOG = AN()
    SCOPE_CONFIG = AN()
    SCOPE_CONFIG_NAME = AN()
    BUTTON_START = AN()


    SCOPE_ADD_CONFIG = AN()
    SCOPE_LOG_AREA = AN()


    PROCESSBAR_PIP_MANAGER = AN()
    PROCESSBAR_START = AN()

    CHECKBOX_PIP = AN()

    # CHECKBOX_DISABLE_REQUIREMENTS_CHECK = AN()
    # CHECKBOX_DISABLE_PULL = AN()

    def __init__(self):
        self.pt = ProgressTracker()
        AdvancePage.__init__(self)
        Command.__init__(self, progress_tracker=self.pt)
        ConfigPage.__init__(self)
        self.log_list = []
        self.log_history = []
        self.log_list_lock = threading.Lock()
        self.config_files = []
        self.last_config = ""
        self.sos = StorageOptionsStatus(self.CHECKBOX_PIP)

        self._load_config_files()

        if not os.path.exists(os.path.join(ROOT_PATH, 'launcher_config_name.txt')):
            output.toast(t2t('Please click \'Check for launcher updates\' for your first use'), duration=30)
            with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w') as f:
                f.close()

    def _event_thread(self):
        while self.loaded:  # 当界面被加载时循环运行
            time.sleep(0.1)

            if pin.pin[self.SELECT_CONFIG] != self.last_config:
                if pin.pin[self.SELECT_CONFIG] is None: continue
                self.last_config = pin.pin[self.SELECT_CONFIG]
                output.clear(self.SCOPE_CONFIG_NAME)
                output.put_text(
                    t2t("Repository address") + ": " + load_config_json(pin.pin[self.SELECT_CONFIG])['Repository'],
                    scope=self.SCOPE_CONFIG_NAME)
                with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w', encoding='utf-8') as f:
                    f.write(self.last_config)
                    f.close()
                self.last_file = pin.pin[self.SELECT_CONFIG]

                output.clear(self.SCOPE_STARTUP_CONFIG)

                self.put_setting(pin.pin[self.SELECT_CONFIG])  # 配置配置页

    def _direct_start(self):
        output.toast(t2t("you are using direct startup. if fail, please click Install and Start Program."), duration=10)
        self._start(skip_install=True)

    def _start(self, skip_install=False, delay=0):
        while not self.loaded:
            print('waiting for loading')
            time.sleep(0.1)
        is_proxy, proxy_server = proxy_info()
        # 检测代理
        while is_proxy:
            is_proxy, proxy_server = proxy_info()
            tip = t2t("Please disable proxy servers to prevent download failures.")
            output.toast(tip, color='red', duration=5)
            if '7890' in proxy_server:
                output.toast("请关闭Clash代理软件", color='red', duration=5)

            time.sleep(1)

        sp = ShowProcess(self.pt)

        logger.hr(f"Welcome to {PROGRAM_NAME}", 0)
        logger.hr(t2t("The program is free and open source on github"))
        logger.hr(t2t("Please see the help file at https://github.com/infstellar/python-git-program-launcher"))
        launching_config = load_config_json(pin.pin[self.SELECT_CONFIG])

        sp.create_popup()

        try:
            # 开启fastgithub
            # if "FastGithub" in pin.pin[self.CHECKBOX_PIP]:
            #     run_command(f'{ROOT_PATH}\\..\\toolkit\\fastgithub_win-x64\\fastgithub.exe start')
            global PROGRAM_PYTHON_PATH
            logger.hr(t2t("Launching..."))
            logger.info(launching_config)


            if 'PGPLLOCALREPO' not in launching_config['Repository']:
                global REPO_PATH
                REPO_PATH = os.path.join(ROOT_PATH, 'repositories', launching_config['Repository'].split('/')[-1])
                verify_path(REPO_PATH)
                os.chdir(REPO_PATH)
                GitManager(launching_config,REPO_PATH, self.pt).git_install(allow_failure=("APR" in pin.pin[self.CHECKBOX_PIP]))


            else:
                REPO_PATH = os.path.abspath(os.path.join(ROOT_PATH, '../', 'repositories', launching_config['Repository'].split('/')[-1]))
            os.chdir(REPO_PATH)
            logger.trace(f"REPO_PATH: {REPO_PATH}")

            output.set_processbar(sp.PROCESSBAR_STAGE, 1 / 3)

            # Download Python
            # Set Python Version From Repository
            if os.path.exists(os.path.join(REPO_PATH, 'pgpl.yaml')):
                with open(os.path.join(REPO_PATH, 'pgpl.yaml'), 'r', encoding='utf-8') as f:
                    pgpl_yaml: dict = yaml.load(f, Loader=yaml.FullLoader)
                    try:
                        ver = list(pgpl_yaml.values())[0]["PythonVersion"]
                        launching_config["PythonVersion"] = ver
                        logger.info(f"Python version set to {ver}")
                    except:
                        logger.error(f"No Python version set in pgpl.yaml")

            # Download Python


            PROGRAM_PYTHON_PATH = PythonManager(launching_config, self.pt).run(check_install=not skip_install)
            output.set_processbar(sp.PROCESSBAR_STAGE, 2 / 3)
            if not skip_install:
                cp = pin.pin[self.CHECKBOX_PIP]
                check_pip = 'DCPU' not in cp
                check_reqs = 'DCRU' not in cp
                # print(cp, check_pip, check_reqs)
                PipManager(launching_config, self.pt).pip_install(check_pip=check_pip, check_reqs=check_reqs)
            output.set_processbar(sp.PROCESSBAR_STAGE, 3 / 3)
            self.pt.end_flag = True

            # add program path to sys.path
            with open(os.path.join(os.path.dirname(PROGRAM_PYTHON_PATH), 'pgpl.pth'), 'w') as f:
                f.write(REPO_PATH)

            # os.system("color 07")
            # self.execute(f"title {PROGRAM_NAME} Console")
            # self.execute("")

            # set start cmd


            start_cmd_1 = f'@echo off\nset "PATH={os.environ["PATH"]};%PATH%"\ncd /d "{REPO_PATH}"'
            if ("DEBUG" in pin.pin[self.CHECKBOX_PIP]):
                start_cmd_2 = f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}\npause'
            else:
                start_cmd_2 = (f'%1(start /min cmd.exe /c %0 :& exit )\n'
                               f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}>bat_run_log.txt')

            start_cmd = f'{start_cmd_1}\n{start_cmd_2}'
            if launching_config['UAC']:
                start_cmd = requesting_administrative_privileges + '\n' + start_cmd  # f'{requesting_administrative_privileges}\nset "PATH={os.environ["PATH"]};%PATH%"\ncd /d "{REPO_PATH}"\n"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}'
            run_path = os.path.join(ROOT_PATH, 'cache', 'run.bat')
            with open(run_path, 'w') as f:
                f.write(start_cmd)
            execute_cmd = f'C:\\Windows\\explorer.exe "{run_path}"'
            self.progress_tracker.cmd = execute_cmd
            self.progress_tracker.console_output = ""
            os.system(execute_cmd)
            # t = threading.Thread(target=lambda : os.system(f'C:\\Windows\\explorer.exe "{run_path}"'), daemon=True)
            # t.start()
            os.chdir(ROOT_PATH)

            if os.path.exists(f"{ROOT_PATH}\\..\\scripts.bat"):
                target_script_path = f"{ROOT_PATH}\\..\\scripts.bat"
                os.chdir(REPO_PATH)
                logger.info(f"executing {target_script_path}")
                os.system(target_script_path)
                os.chdir(ROOT_PATH)

            logger.hr(f"Successfully install. Activating {PROGRAM_NAME}", 0)
            logger.info(f'execute: "{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')
            output.clear(sp.SCOPE_PROGRESS_INFO)
            output.put_markdown(t2t("## Info: \n") + t2t("#### Successfully install. Activating"),
                                scope=sp.SCOPE_PROGRESS_INFO)  # +f" {PROGRAM_NAME}"
            output.put_markdown(
                t2t("#### You can close this popup window and start another programme or restart this programme."),
                scope=sp.SCOPE_PROGRESS_INFO)

        except Exception as e:
            # output.clear(self.SCOPE_PROGRESS_INFO)
            sp.show_exception(t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe"))
            logger.exception(e)
            self.pt.end_flag = True
            sp.stop(False)
            raise e
        self.pt.end_flag = True
        sp.stop()
        if ("SSASC" in pin.pin[self.CHECKBOX_PIP]):
            self.info(t2t("Preparing to shut down the starter"))
            output.toast(t2t("Preparing to shut down the starter"))
            time.sleep(2)
            os._exit(0)


    def _load(self):
        # output.put_html('<style>@font-face {font-family: "SmileySans-Oblique"; src: url("M:\\ProgramData\\PGPL\\python-git-program-launcher\\toolkit\\SmileySans-Oblique.ttf");}</style>')
        # output.put_html('<style>body {font-family: "Arial", sans-serif;}</style>')
        self.last_config = ""
        self._load_config_files()
        show_config = self.config_files
        self.last_file = None
        default_path = f'{ROOT_PATH}\\..\\default_config.json'
        if os.path.exists(default_path):
            with open(f'{ROOT_PATH}\\launcher_config_name.txt', 'w', encoding='utf-8') as f:
                f.write(default_path)
            output.toast(t2t('The default startup configuration has been detected'),duration=30)
            output.toast(t2t('If you want to manually startup, please delete default_config.json file.'), duration=5)
            autostart_thread = threading.Thread(target=lambda: self._start(skip_install=False), daemon=True)
            session.register_thread(autostart_thread)
            autostart_thread.start()
        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'r') as f:
            launching_config = str(f.read())
        for i in show_config:
            if i['value'] == launching_config:
                i['selected'] = True
        with output.use_scope(self.main_scope):
            output.put_row([
                output.put_button(label=t2t("Open logs folder"), onclick=self._onclick_open_log_folder,
                                  scope=self.main_scope),
                output.put_button(label=t2t("Check for launcher updates"), onclick=self._onclick_upd,
                                  scope=self.main_scope),
                output.put_button(label=t2t("Test fastest download links(use it when download stuck)"), onclick=self._onclick_speedtest,
                                  scope=self.main_scope),
            ]
                , size='auto'),

            output.put_row([
                output.put_column([
                    # 选择配置
                    output.put_markdown(t2t("## Select startup configuration")),
                    pin.put_select(name=self.SELECT_CONFIG, options=self.config_files),
                    # 当前配置
                    output.put_scope(self.SCOPE_CONFIG_NAME),
                    # 启动按钮
                    output.put_row([
                        output.put_button(label=t2t("Install and Start Program"), onclick=self._start),
                        output.put_button(label=t2t("Direct Start"), onclick=self._direct_start),
                    ]
                        , size='auto'),

                    # 其他配置
                    output.put_column([
                        output.put_markdown(t2t('## Startup Options')),
                        output.put_markdown(
                            t2t("Setting the startup options, which may speed up the startup of the programme, but may cause the programme to fail to start. Make sure you use them when you understand what they do.")),
                        pin.put_checkbox(name=self.CHECKBOX_PIP, options=[
                            # {
                            #     "label": t2t("Use FastGithub to accelerate access"),
                            #     "value": "FastGithub",
                            #     "selected": self.sos.get_options_status('FastGithub'),
                            # },
                            {
                                "label": t2t("DEBUG MODE"),
                                "value": "DEBUG",
                                "selected": self.sos.get_options_status('DEBUG'),
                            },
                            {
                                "label": t2t("Disable checking pip update"),
                                "value": "DCPU",
                                "selected": self.sos.get_options_status('DCPU'),
                            },
                            {
                                "label": t2t("Disable checking requirements update"),
                                "value": "DCRU",
                                "selected": self.sos.get_options_status('DCRU'),
                            },
                            {
                                "label": t2t("Allow git to abort pulling repositories if the connection fails"),
                                "value": "APR",
                                "selected": self.sos.get_options_status('APR'),
                            },
                            {
                                "label": t2t("Automatic shutdown of the starter after startup completion"),
                                "value": "SSASC",
                                "selected": self.sos.get_options_status('SSASC'),
                            },

                        ]),

                    ], size='auto'),
                    pin.pin_on_change(self.CHECKBOX_PIP, onchange=self.sos.storage_options_status)
                ], size='auto'),
                # None,
                # output.put_scope(self.SCOPE_LOG)
            ], size=r'auto')
            # Edit Config

            output.put_markdown(t2t('## Edit Configuration')),
            # output.put_row([
            #     output.put_button(label=t2t("New Configuration"), onclick=self._onclick_new_config),
            output.put_button(t2t('Add config'), onclick=self._onclick_add_config)
            output.put_scope(self.SCOPE_STARTUP_CONFIG)





        #     output.popup(t2t("Error:PGPL path must contain only ASCII characters\nThe current path is ")+ROOT_PATH, closable=False)

        # with output.use_scope(self.SCOPE_LOG):
        #     output.put_markdown(t2t('## Log'))
        #     output.put_scrollable(output.put_scope(self.SCOPE_LOG_AREA), keep_bottom=True)

    def _stop_start(self):
        output.close_popup()

    def logout(self, text: str, color='black'):
        if self.loaded:
            self.log_list_lock.acquire()
            self.log_list.append((text, color))
            self.log_list_lock.release()

    def _onclick_open_log_folder(self):
        os.startfile(os.path.join(ROOT_PATH, "Logs"))

    branch = "cpp_launcher"  # ("main" if not os.path.exists(fr'{ROOT_PATH}/../resource/.condarc') else "miniconda")
    CONFIG_PGPL = {
        "RequirementsFile": "requirements.txt",
        "InstallDependencies": True,
        "PypiMirror": "AUTO",
        "PythonMirror": "AUTO",
        "Repository": select_fastest_url(["https://github.com/infstellar/python-git-program-launcher",
                                          "https://gitee.com/infstellar/python-git-program-launcher"]),
        "Main": "main.py",
        "Branch": branch,
        "GitProxy": False,
        "KeepLocalChanges": True,
        "AutoUpdate": True,
        "Tag": "",
        "PythonVersion": "3.10.10",
        "UAC": False
    }

    def _onclick_upd(self):

        os.chdir(ROOT_PATH)
        if self.branch == 'main':
            output.toast(
                t2t('PGPL-2.3 will soon be unsupported, please visit https://github.com/infstellar/python-git-program-launcher for the latest version.'),
                duration=10)
        sp = ShowProcess(self.pt)
        self.pt.reset()
        self.pt.add_monitor('Already up to date.')
        sp.create_popup()
        gm = GitManager(self.CONFIG_PGPL,REPO_PATH, self.pt)
        try:
            gm.git_install()
            sp.stop(True)
            time.sleep(0.2)
            if self.pt.get_counts('Already up to date.') > 0:
                output.clear(sp.SCOPE_PROGRESS_INFO)
                output.put_markdown(t2t('### Already up to date.'), scope=sp.SCOPE_PROGRESS_INFO)
            else:
                output.clear(sp.SCOPE_PROGRESS_INFO)
                output.put_markdown(t2t('### Update complete, please restart the launcher.'),
                                    scope=sp.SCOPE_PROGRESS_INFO)

        except:
            sp.stop(False)
            time.sleep(0.2)
            output.put_markdown(t2t('### Update Fail, please check whether your network is able to access github.com.'),
                                scope=sp.SCOPE_PROGRESS_INFO)

        self.pt.reset()
        # rc, inf, erc = run_command('git pull')
        # output.popup(t2t("Update"), f"{rc}, {inf}, {erc}")

    def _onclick_speedtest(self):
        is_proxy, proxy_server = proxy_info()
        # 检测代理
        if is_proxy:
            tip = t2t("Please disable proxy servers to prevent download failures.")
            output.toast(tip, color='red', duration=5)
            return
        output.toast(t2t('Testing speed...'), duration=20)
        r1 = select_fastest_url(["https://pypi.org/simple", "http://pypi.tuna.tsinghua.edu.cn/simple",
                             "https://mirrors.bfsu.edu.cn/pypi/web"],use_cache=False,
                           is_pypi=True)
        output.toast(t2t('Pypi fastest url: ') + r1)
        r2 = select_fastest_url(["https://github.com/infstellar/python-git-program-launcher",
                            "https://gitee.com/infstellar/python-git-program-launcher"], use_cache=False)
        output.toast(t2t('git fastest url: ') + r2)
        output.toast(t2t('Test Complete'), duration=20, color='success')




