import hashlib

import yaml
from utils import *
from pywebio import *
from webio_utils import *
import socket
import threading
import time
from advance_page import AdvancePage
from main import *



class MainPage(AdvancePage):
    SCOPE_START = AN()
    SCOPE_LOG = AN()
    SCOPE_CONFIG = AN()
    SCOPE_CONFIG_NAME = AN()
    BUTTON_START = AN()
    SELECT_CONFIG = AN()
    SCOPE_ADD_CONFIG = AN()
    SCOPE_LOG_AREA = AN()
    
    PROCESSBAR_PYTHON_MANAGER = AN()
    PROCESSBAR_STAGE = AN()
    PROCESSBAR_PIP_MANAGER = AN()
    PROCESSBAR_START = AN()
    SCOPE_PROGRESS_INFO = AN()
    SCOPE_PROGRESS_STAGE = AN()
    
    
    def __init__(self):
        super().__init__()
        self.log_list = []
        self.log_history = []
        self.log_list_lock = threading.Lock()
        self.config_files = []
        self.last_config = ""
        
        self._load_config_files()
        
        if not os.path.exists(os.path.join(ROOT_PATH, 'launcher_config_name.txt')):
            with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w') as f:
                f.close()

    def _event_thread(self):
        while self.loaded:  # 当界面被加载时循环运行
            time.sleep(0.1)
            # try:
            #     pin.pin['isSessionExist']
            # except SessionNotFoundException:
            #     logger.info(t2t("未找到会话，可能由于窗口关闭。请刷新页面重试。"))
            #     return
            # except SessionClosedException:
            #     logger.info(t2t("未找到会话，可能由于窗口关闭。请刷新页面重试。"))
            #     return
            
            # self.log_list_lock.acquire()
            # for text, color in self.log_list:
            #     if text == "$$end$$":
            #         output.put_text("", scope=self.SCOPE_LOG_AREA)
            #     else:
            #         output.put_text(text, scope=self.SCOPE_LOG_AREA, inline=True).style(f'color: {color}; font_size: 20px') # ; background: aqua
            # self.log_list.clear()
            # self.log_list_lock.release()
            
            if pin.pin[self.SELECT_CONFIG] != self.last_config:
                if pin.pin[self.SELECT_CONFIG] is None: continue
                self.last_config = pin.pin[self.SELECT_CONFIG]
                output.clear(self.SCOPE_CONFIG_NAME)
                output.put_text(load_json(pin.pin[self.SELECT_CONFIG])['Repository'], scope=self.SCOPE_CONFIG_NAME)
                with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'w', encoding='utf-8') as f:
                    f.write(self.last_config)
                    f.close()
    
    def _start(self):
        with output.popup(t2t("Program Starting"), implicit_close=False) as s:
            output.put_markdown(t2t("## Progress"))
            output.put_scope(self.SCOPE_PROGRESS_STAGE)
            output.put_scope(self.SCOPE_PROGRESS_INFO)
            output.put_processbar(self.PROCESSBAR_STAGE)
            output.set_processbar(self.PROCESSBAR_STAGE, 0/3)
            output.put_processbar(self.PROCESSBAR_PYTHON_MANAGER)
            # output.put_button(t2t("Stop start"), onclick = self._stop_start)
        def set_processbar(x:ProgressTracker, processbar_name:str, info_scope:str):
            last_info = ""
            last_progress = 0
            while 1:
                if pt.end_flag: break
                time.sleep(0.1)
                if x.info != last_info:
                    last_info = x.info
                    output.clear(info_scope)
                    output.put_text(last_info, scope=info_scope)
                if x.percentage != last_progress:
                    last_progress = x.percentage
                    output.set_processbar(processbar_name, last_progress)
                
        logger.hr(f"Welcome to {PROGRAM_NAME}", 0)
        logger.hr(t2t("The program is free and open source on github"))
        logger.hr(t2t("Please see the help file at https://github.com/infstellar/python-git-program-launcher"))
        launching_config = load_json(pin.pin[self.SELECT_CONFIG])
        
        pt = ProgressTracker()
        t = threading.Thread(target=set_processbar, daemon=False, args=(pt, self.PROCESSBAR_PYTHON_MANAGER, self.SCOPE_PROGRESS_INFO))
        session.register_thread(t)
        t.start()
        try:
            global PROGRAM_PYTHON_PATH
            PROGRAM_PYTHON_PATH = PythonManager(launching_config, pt).run()
            output.set_processbar(self.PROCESSBAR_STAGE, 1/3)
            logger.info(launching_config)
            REPO_PATH = os.path.join(ROOT_PATH, 'repositories', launching_config['Repository'].split('/')[-1])
            verify_path(REPO_PATH)
            os.chdir(REPO_PATH)
            logger.hr(t2t("Launching..."))

            GitManager(launching_config, pt).git_install()
            output.set_processbar(self.PROCESSBAR_STAGE, 2/3)
            PipManager(launching_config, pt).pip_install()
            output.set_processbar(self.PROCESSBAR_STAGE, 3/3)
            pt.end_flag = True
            
            # add program path to sys.path
            with open(os.path.join(os.path.dirname(PROGRAM_PYTHON_PATH), 'pgpl.pth'), 'w') as f:
                f.write(REPO_PATH)
            
            logger.hr(f"Successfully install. Activating {PROGRAM_NAME}", 0)
            logger.info(f'execute: "{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')
            output.clear(self.SCOPE_PROGRESS_INFO)
            output.put_markdown(f'execute: "{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}', scope=self.SCOPE_PROGRESS_INFO)
            
            # os.system("color 07")
            os.system(f"title {PROGRAM_NAME} Console")
            os.system(f'start cmd /k "{PROGRAM_PYTHON_PATH}" {launching_config["Main"]}')
            os.chdir(ROOT_PATH)
            
        except Exception as e:
            pt.end_flag = True
            # output.clear(self.SCOPE_PROGRESS_INFO)
            output.put_markdown(t2t('***ERROR OCCURRED!***'),scope=self.SCOPE_PROGRESS_INFO)
            output.put_markdown('***' + t2t("Please check your NETWORK ENVIROUMENT and re-open Launcher.exe") + '***',scope=self.SCOPE_PROGRESS_INFO)
            output.put_markdown(t2t('***CHECK UP THE CONSOLE OR SEND THE ERROR LOG***'),scope=self.SCOPE_PROGRESS_INFO)
            logger.exception(e)
            raise e

    def _load_config_files(self):
        self.config_files = []
        for root, dirs, files in os.walk(os.path.join(ROOT_PATH, 'configs')):
            for f in files:
                if f[f.index('.') + 1:] == "json":
                    self.config_files.append({"label": f, "value": os.path.join(root, f)})
    
    def _load(self):
        # output.put_html('<style>@font-face {font-family: "SmileySans-Oblique"; src: url("M:\\ProgramData\\PGPL\\python-git-program-launcher\\toolkit\\SmileySans-Oblique.ttf");}</style>')
        # output.put_html('<style>body {font-family: "Arial", sans-serif;}</style>')
        self.last_config = ""
        self._load_config_files()
        show_config = self.config_files
        with open(os.path.join(ROOT_PATH, 'launcher_config_name.txt'), 'r') as f:
            launching_config = str(f.read())
            f.close()
        for i in show_config:
            if i['value'] == launching_config:
                i['selected'] = True
        with output.use_scope(self.main_scope):
            output.put_row([
                output.put_column([
                    # 选择配置
                    
                    pin.put_select(name=self.SELECT_CONFIG, options=self.config_files),
                    # 当前配置
                    output.put_scope(self.SCOPE_CONFIG_NAME),
                    # 启动按钮
                    output.put_button(label=t2t("Start Program"), onclick=self._start)
                ], size='auto'),
                # None,
                # output.put_scope(self.SCOPE_LOG)
            ], size=r'auto')
        
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
            
class ConfigPage(AdvancePage):
    def __init__(self):
        super().__init__()

        # self.main_scope = "SettingPage"

        self.exit_popup = None
        self.last_file = None
        self.file_name = ''
        self.config_file_name = 'common_config'

        self.config_files = []
        self.config_files_name = []
        self._load_config_files()
        self.can_check_select = True
        self.can_remove_last_scope = False
        # 注释显示模式在这改
        self.mode = True
        self.read_only = False

        self.input_verify={
            "test":lambda x:x
        }

    def _load_config_files(self):
        self.config_files = []
        for root, dirs, files in os.walk('configs'):
            for f in files:
                if f[f.index('.') + 1:] == "json":
                    self.config_files.append({"label": f, "value": os.path.join(root, f)})
        return self.config_files

    def _create_new_config(self):
        pass
    
    def _prepro_url(self,url):
        url = url.replace('https', 'http')
        url = url.replace("http://github.com/", "")
        url = f"https://raw.githubusercontent.com/{url}/main/pgpl.yaml"
        return url
    
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
    
    def _address_verify(self,x):
        if 'http' in x:
            x = self._prepro_url(x)
            if url_file_exists(x):
                return None
            else:
                return t2t("Invalid address")
        else:
            return None
    
    def _onclick_add_config(self):
        n = input.input(t2t('config name')+t2t("(You can enter the github repository address which already have existing config)"), validate=self._address_verify)
        if 'http' not in n:
            save_json(CONFIG_TEMPLATE, os.path.join(ROOT_PATH, 'configs', n + '.json'))
        else:
            self._download_config_from_repo(n)
        self._load_config_files()
        self._reload_self()
    
    def _load(self):
        self._load_config_files()
        self.last_file = None

        # 配置页
        with output.use_scope(self.main_scope):
            output.put_markdown(t2t('## config:'))

            output.put_button(t2t('Add config'), onclick=self._onclick_add_config)
            
            output.put_scope("select_scope")
        
        pin.put_select('file', self.config_files, scope="select_scope")

    # 重新加载选项
    def _reload_select(self):
        self.can_check_select = False
        self._load_config_files()
        output.clear("select_scope")
        pin.put_select('file', self.config_files, scope="select_scope")
        self.can_check_select = True
    
    # 循环线程
    def _event_thread(self):
        while self.loaded:
            if not self.can_check_select:
                time.sleep(1)
                continue
            try:
                pin.pin['isSessionExist']
            except SessionNotFoundException:
                logger.info(t2t("Cannot Find Session")) # 未找到会话，可能由于窗口关闭。请刷新页面重试。
                return
                
            if pin.pin['file'] != self.last_file:  # 当下拉框被更改时
                self.last_file = pin.pin['file']

                if self.can_remove_last_scope:  # 判断是否可以移除
                    output.remove('now')
                else:
                    self.can_remove_last_scope = True

                output.put_scope('now', scope=self.main_scope)  # 创建配置页scope
                
                
                self.put_setting(pin.pin['file'])  # 配置配置页

            time.sleep(1)

    def _str_verify(self, x, verify_list, scope_name):
        if x in verify_list:
            output.clear_scope(scope_name)
            output.put_text(t2t("Verified!"), scope=scope_name).style(f'color: green; font_size: 20px')
            return
        else:
            f1 = False
            sl = []
            for i in verify_list:
                if x in i:
                    f1 = True
                    output.clear_scope(scope_name)
                    output.put_text(t2t("Waiting..."), scope=scope_name).style(f'color: black; font_size: 20px')
                    if len(sl)<=15:
                        sl.append(i)
            
        if f1:
            output.put_text(t2t("You may want to enter: "), scope=scope_name).style(f'color: black; font_size: 20px')
            for i in sl:
                output.put_text(i, scope=scope_name).style(f'color: black; font_size: 12px; font-style:italic')
        else:
            output.clear_scope(scope_name)
            output.put_text(t2t("Not a valid name"), scope=scope_name).style(f'color: red; font_size: 20px')

    def _before_load_json(self):
        pass
     
    def put_setting(self, name='', j=None):
        self.file_name = name
        self._before_load_json()
        output.put_markdown('## {}'.format(name), scope='now')  # 标题
        if j is None:
            with open(name, 'r', encoding='utf8') as f:
                j = json.load(f)

        # with open(os.path.join(root_path, "config", "settings", "config.json"), 'r', encoding='utf8') as f:
        #     lang = json.load(f)["lang"]
        doc_name = f'configs\\json_doc\\{self.config_file_name}.yaml'
        lang_doc_name = f'configs\\json_doc\\{self.config_file_name}.{GLOBAL_LANG}.yaml'

        if os.path.exists(doc_name):
            with open(doc_name, 'r', encoding='utf8') as f:
                doc = yaml.load(f, Loader=yaml.FullLoader)
            if os.path.exists(lang_doc_name):
                with open(lang_doc_name, 'r', encoding='utf8') as f:
                    doc_addi = yaml.load(f, Loader=yaml.FullLoader)
                for k1 in doc_addi:
                    for k2 in doc_addi[k1]:
                        if k1 not in doc:
                            doc[k1] = doc_addi[k1]
                        doc[k1][k2] = doc_addi[k1][k2]
        else:
            doc = {}
        self.put_json(j, doc, 'now', level=3)  # 载入json
        
        if not self.read_only:
            output.put_button('save', scope='now', onclick=self.save)

    # 保存json文件
    def save(self):

        j = json.load(open(self.file_name, 'r', encoding='utf8'))

        json.dump(self.get_json(j), open(self.file_name, 'w', encoding='utf8'), ensure_ascii=False, indent=4)
        # output.put_text('saved!', scope='now')
        output.toast(t2t('saved!'), color='success', duration=4)

    # 
    def get_json(self, j: dict, add_name=''):
        rt_json = {}
        for k in j:
            k_sha1 = hashlib.sha1(k.encode('utf8')).hexdigest()
            v = j[k]
            if type(v) == dict:
                rt_json[k] = self.get_json(v, add_name='{}-{}'.format(add_name, k_sha1))

            elif type(v) == list:

                # 判断是否为dict列表
                is_dict_list = True
                for i in v:
                    is_dict_list = is_dict_list and (type(i) == dict)

                if is_dict_list:
                    # 这个是dict的id,是在列表的位置,从1开始,当然也可以改成从0开始,都一样
                    dict_id = 0
                    # 在当前dict列表里循环,取出每一个dict
                    rt_list = []
                    for i in v:
                        # 计次+1
                        dict_id += 1
                        rt_list.append(
                            self.get_json(v[dict_id - 1], add_name='{}-{}-{}'.format(add_name, k_sha1, str(dict_id))))
                    rt_json[k] = rt_list
                else:
                    rt_json[k] = list_text2list(pin.pin['{}-{}'.format(add_name, k_sha1)])
            else:
                rt_json[k] = pin.pin['{}-{}'.format(add_name, k_sha1)]

        return rt_json

    def _on_unload(self):
        if not self.read_only:
            j = json.load(open(self.file_name, 'r', encoding='utf8'))
            self.exit_popup = True
            if not is_json_equal(json.dumps(self.get_json(j)), json.dumps(j)):
                self.exit_popup = False
                output.popup(t2t('Do you need to save changes?'), [
                    output.put_buttons([(t2t('No'), 'No'), (t2t('Yes'), 'Yes')], onclick=self.popup_button)
                ])
            while not self.exit_popup:
                time.sleep(0.1)

    def popup_button(self, val):
        if val == 'No':
            self.close_popup()
        elif val == 'Yes':
            self.save_and_exit_popup()

    def save_and_exit_popup(self):
        self.save()
        output.close_popup()
        self.exit_popup = True

    def close_popup(self):
        output.close_popup()
        self.exit_popup = True
    
    # 展示str型项
    def _show_str(self, doc_items, component_name, display_name, scope_name, v, doc_special):
        if doc_items:
            pin.put_select(component_name,
                            [{"label": i, "value": i} for i in doc_items], value=v,
                            label=display_name,
                            scope=scope_name)
        elif doc_special:
            doc_special = doc_special.split('#')
            if doc_special[0] == "$FILE_IN_FOLDER$":
                
                json_dict = load_json_from_folder(os.path.join(ROOT_PATH, doc_special[1]), black_file=["character","character_dist",""])
                sl = []
                for i in json_dict:
                    sl.append({"label": i["label"], "value": i["label"]})
                pin.put_select(component_name,
                    sl, value=v,
                    label=display_name,
                    scope=scope_name)
            elif doc_special[0] == "$INPUT_VERIFY$":
                pin.put_input(component_name, label=display_name, value=v, scope=scope_name)
                output.put_scope(name=component_name, content=[
                    output.put_text("")
                ], scope=scope_name)
                def onchange(x):
                    self._str_verify(x, verify_list=self.input_verify[doc_special[1]], scope_name=component_name)
                pin.pin_on_change(component_name, onchange=onchange, clear=False, init_run=True)
        else:
            pin.put_input(component_name, label=display_name, value=v, scope=scope_name)
    
    # 展示inf型项
    def _show_int(self, doc_items, component_name, display_name, scope_name, v, doc_special):
        if doc_items:
            pin.put_select(component_name,
                            [{"label": i, "value": i} for i in doc_items], value=v,
                            label=display_name,
                            scope=scope_name)
        else:
            pin.put_input(component_name, label=display_name, value=v, scope=scope_name, type='number')
    
    # 展示float型项
    def _show_float(self, doc_items, component_name, display_name, scope_name, v, doc_special):
        if doc_items:
            pin.put_select(component_name,
                            [{"label": i, "value": i} for i in doc_items], value=v,
                            label=display_name,
                            scope=scope_name)
        else:
            pin.put_input(component_name, label=display_name, value=v, scope=scope_name, type='float')
    
    # 展示bool型项
    def _show_bool(self, component_name, display_name, scope_name, v, doc_special):
        pin.put_select(component_name,
            [{"label": 'True', "value": True}, {"label": 'False', "value": False}], value=v,
            label=display_name,
            scope=scope_name)
    
    # 展示dict型项
    def _show_dict(self, level, component_name, display_name, scope_name, doc, v, doc_special):
        output.put_scope(component_name, scope=scope_name)
        output.put_markdown('#' * level + ' ' + display_name, scope=component_name)
        self.put_json(v, doc, component_name, add_name=component_name,
                        level=level + 1)
    
    # 展示list/list&dict型项
    def _show_list(self, level, display_name, scope_name, component_name, doc, v, doc_special):
        # 判断是否为dict列表
        is_dict_list = True
        for i in v:
            is_dict_list = is_dict_list and (type(i) == dict)

        if is_dict_list:
            output.put_markdown('#' * level + ' ' + display_name,
                                scope=scope_name)
            # 差点把我绕晕....
            # 这个是dict的id,是在列表的位置,从1开始,当然也可以改成从0开始,都一样
            dict_id = 0
            # 在当前dict列表里循环,取出每一个dict
            for i in v:
                # 计次+1
                dict_id += 1

                # 创建一个容器以容纳接下来的dict,第一个是控件名称,为了防止重复,加上了dict id,后面那个是当前容器id
                output.put_scope(component_name + '-' + str(dict_id), scope=scope_name)
                # 写标题,第一项是标题文本,遵守markdown语法,第二项是当前容器名称
                output.put_markdown('#' * (level + 1) + ' ' + str(dict_id),
                                    scope=component_name + '-' + str(dict_id))
                # 写dict,第一项为输入的dict,第二项为doc,第三项为当前容器名称,第四项为控件名称前缀,最后是缩进等级
                self.put_json(i, doc, component_name + '-' + str(dict_id),
                                component_name + '-' + str(dict_id),
                                level=level + 2)
        else:
            pin.put_textarea(component_name, label=display_name, value=list2format_list_text(v),
                                scope=scope_name)
    
    # 显示json
    def put_json(self, j: dict, doc: dict, scope_name, add_name='', level=1):
        for k in j:
            v = j[k]
            # 获取注释
            doc_now = ''
            doc_now_data = {}
            doc_items = None
            doc_special = None
            doc_annotation = None
            doc_type = None
            if k in doc:
                # 判断doc的类型
                if type(doc[k]) == dict:
                    if 'doc' in doc[k]:
                        doc_now = doc[k]['doc']
                    if 'data' in doc[k]:
                        doc_now_data = doc[k]['data']
                    if 'select_items' in doc[k]:
                        doc_items = doc[k]['select_items']
                    if 'special_index' in doc[k]:
                        doc_special = doc[k]['special_index']
                    if "annotation" in doc[k]:
                        doc_annotation = doc[k]['annotation']
                    if 'type' in doc[k]:
                        doc_type = doc[k]['type']
                if type(doc[k]) == str:
                    doc_now = doc[k]
            # 取显示名称
            display_name = doc_now if doc_now else k if self.mode else '{} {}'.format(k, doc_now)

            k_sha1 = hashlib.sha1(k.encode('utf8')).hexdigest()
            component_name = '{}-{}'.format(add_name, k_sha1)
            
            if doc_type != None:
                if doc_type == 'int':
                    self._show_int(doc_items, component_name, display_name, scope_name, v, doc_special)
                elif doc_type == 'float':
                    self._show_float(doc_items, component_name, display_name, scope_name, v, doc_special)
                elif doc_type == 'bool':
                    self._show_bool(component_name, display_name, scope_name, v, doc_special)
                elif doc_type == 'dict':
                    self._show_dict(level, component_name, display_name, scope_name, doc, v, doc_special)
                elif doc_type == 'list':
                    self._show_list(level, display_name, scope_name, component_name, doc, v, doc_special)
                elif doc_type == 'str':
                    self._show_str(doc_items, component_name, display_name, scope_name, v, doc_special)
            else:    
                if type(v) == str or v is None:
                    self._show_str(doc_items, component_name, display_name, scope_name, v, doc_special)
                elif type(v) == int:
                    self._show_int(doc_items, component_name, display_name, scope_name, v, doc_special)
                elif type(v) == float:
                    self._show_float(doc_items, component_name, display_name, scope_name, v, doc_special)
                elif type(v) == bool:
                    self._show_bool(component_name, display_name, scope_name, v, doc_special)
                elif type(v) == dict:
                    self._show_dict(level, component_name, display_name, scope_name, doc, v, doc_special)
                elif type(v) == list:
                    self._show_list(level, display_name, scope_name, component_name, doc, v, doc_special)
            if doc_annotation != None:
                    output.put_text(doc_annotation, scope=scope_name)
                    output.put_text("\n", scope=scope_name).style("font-size: 1px")