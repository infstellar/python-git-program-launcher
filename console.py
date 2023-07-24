import os.path
import sys
from urllib.parse import urlparse
import yaml

from utils import *
from pgpl_pth import generate_pgplpth
from inputimeout import inputimeout, TimeoutOccurred
from managers import *


class ConfigEditor():
    def __init__(self):
        pass

    def _input(self, info=t2t('Input'), possible_answer: list = None, ignore_case: bool = False, input_type: object = str,
               allow_empty=True):
        note = info
        if possible_answer is not None:
            x = t2t('Options')
            note += f" {x}: " + str(possible_answer)
        logger.info(f"{note}")
        r = input()
        if ignore_case:
            r = r.lower()
        if possible_answer is not None:
            if r not in possible_answer:
                logger.error(t2t("Illegal parameters"))
                return self._input(info, possible_answer, ignore_case, input_type, allow_empty)

        if allow_empty:
            if r == '':
                return ''
        else:
            if r == '':
                logger.error(t2t("Illegal parameters: Empty"))
                return self._input(info, possible_answer, ignore_case, input_type, allow_empty)

        try:
            r = input_type(r)
        except Exception as e:
            logger.error(t2t("Illegal parameter type"))
            return self._input(info, possible_answer, ignore_case, input_type, allow_empty)
        return r

    def _input_bool(self, info=t2t('Input')):
        r = self._input(info, possible_answer=['y', 'n', ''], ignore_case=True)
        if r != '':
            r = {'y': True, 'n': False}[r]
        return r

    def _download_config_from_repo(self, url:str):
        url = url.replace('https', 'http')
        url = url.replace("http://github.com/", "")
        url = f"https://raw.githubusercontent.com/{url}/main/pgpl.yaml"
        # url += "/blob/main/pgpl.yaml"
        if url_file_exists(url):
            verify_path(os.path.join(ROOT_PATH, 'cache'))
            fp = os.path.join(ROOT_PATH, 'cache', 'cac.yaml')
            download_url(url, fp)
            with open(fp,encoding='utf-8') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
            for key in data:
                with open(os.path.join(ROOT_PATH, 'configs', f"{key}.json"), "w") as f:
                    json.dump(data[key], f)
            logger.info(t2t('download config from repo succ'))
            return
        else:
            logger.error(t2t("Invalid address"))
            inp_conf_name = self._input(allow_empty=False)
            self._download_config_from_repo(inp_conf_name)
    
    def _run_edit(self):
        possible_configs = load_json_from_folder(os.path.join(ROOT_PATH, 'configs'))
        possible_configs = [ii['label'][:ii['label'].index('.')] for ii in possible_configs]
        
        def print_possible_configs():
            logger.hr(t2t("possible configs:"), level=1)
            for i in possible_configs:
                logger.info(i)
            logger.hr(t2t("end"), level=1)
        print_possible_configs() 
        logger.info(t2t('Do you want to edit or add config? If you do not need to edit or add config, just select other config, please enter `n` or enter directly.'))
        
        r = self._input_bool()
        if r:
            # print_possible_configs() 
            logger.info(t2t("Please enter the config name."))
            logger.info(t2t("Config will be created automatically if the file does not exist."))
            # logger.info(t2t('Tips: You can enter the repository url to get the pgpl configuration from the remote repository (if the remote repository is already configured with pgpl.yaml)'))
            logger.info(t2t("If the repository has pre-configured files, you can also download the configuration file by entering the repository address directly. (if the remote repository is already configured with pgpl.yaml)"))

            inp_conf_name = self._input(allow_empty=False)
            if 'http' in inp_conf_name:
                self._download_config_from_repo(inp_conf_name)
            else:
                logger.info(t2t('If you do not want to change the settings, press enter directly on the option.'))
                self.edit_config(inp_conf_name)
            
        logger.info(t2t('Please enter the launching config name.'))
        possible_configs = load_json_from_folder(os.path.join(ROOT_PATH, 'configs'))
        possible_configs = [ii['label'][:ii['label'].index('.')] for ii in possible_configs]
        print_possible_configs()
        launching_config = self._input(allow_empty=False, possible_answer=possible_configs)
        possible_configs = load_json_from_folder(os.path.join(ROOT_PATH, 'configs'))
        possible_configs = [ii['label'][:ii['label'].index('.')] for ii in possible_configs]

        

        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w', encoding='utf-8') as f:
            f.write(launching_config)
            f.close()
    

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
        logger.hr(t2t("Successfully edit config."))
        
    def run(self):

        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'r') as f:
            launching_config = str(f.read())
            f.close()
        logger.info(t2t('Current Config')+f": {launching_config}")
        logger.info(t2t('Do you want to edit settings or select other settings?'))
        
        try:
            c = inputimeout(prompt="\033[1;37m"+t2t("After $t$ seconds without input, PGPL will automatically start.") + "\033[0m "+ t2t("Options") + ": " + f"{['y', 'n', '']}", timeout=5)
        except TimeoutOccurred:
            c = ''

        if c != '': c = {'y': True, 'n': False}[c]
        is_edit = bool(c)

        if launching_config == '':
            logger.info(t2t('No config selected. A config must be selected.'))
            is_edit = True
        if is_edit:
            self._run_edit()

        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'r') as f:
            launching_config = str(f.read())
            f.close()
        
        return load_json(launching_config)


def run():
    logger.hr(f"Welcome to {PROGRAM_NAME}", 0)
    logger.hr(t2t("The program is free and open source on github"))
    logger.hr(t2t("Please see the help file at https://github.com/infstellar/python-git-program-launcher"))
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
    
    logger.hr(t2t("Launching..."))
    GitManager(launching_config).git_install()
    PipManager(launching_config).pip_install()
    
    # add program path to sys.path
    with open(os.path.join(os.path.dirname(PROGRAM_PYTHON_PATH), 'pgpl.pth'), 'w') as f:
        f.write(REPO_PATH)
    
    logger.hr(f"Successfully install. Activating {PROGRAM_NAME}", 0)
    print(f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')

    # os.system("color 07")
    os.system(f"title {PROGRAM_NAME} Console")
    os.system(f'"{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')

if __name__ == "__main__":
    run()    
