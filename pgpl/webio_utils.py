import json
from pywebio import output
import traceback
import os
from pgpl.utils import *

def toast_succ(text="succ!", duration=2):
    output.toast(text, position='center', color='#2188ff', duration=duration)

def get_name(x):
    (filename, line_number, function_name, text) = x
    # = traceback.extract_stack()[-2]
    return text[:text.find('=')].strip()

def auto_name():
    return get_name(traceback.extract_stack()[-2])

AN = auto_name

def list2format_list_text(lst: list, inline = False) -> str:
    if lst is not None:  # 判断是否为空
        try:  # 尝试转换
            rt_str = json.dumps(lst, sort_keys=False, indent=4, separators=(',', ':'), ensure_ascii=False)
        except:
            rt_str = str(lst)

    else:
        rt_str = str(lst)
    # print(rt_str)
    if inline:
        rt_str = rt_str.replace('\n', ' ')
    return rt_str

def list_text2list(text: str) -> list:
    """str列表转列表.

    Args:
        text (str): _description_

    Returns:
        list: _description_
    """
    if text is not None:  # 判断是否为空
        try:  # 尝试转换
            rt_list = json.loads(text)
        except:
            rt_list = []

        if type(rt_list) != list:  # 判断类型(可能会为dict)
            rt_list = list(rt_list)

    else:
        rt_list = []

    return rt_list

def is_json_equal(j1: str, j2: str) -> bool:
    """_summary_

    Args:
        j1 (str): _description_
        j2 (str): _description_

    Returns:
        bool: _description_
    """
    try:
        return json.dumps(json.loads(j1), sort_keys=True) == json.dumps(json.loads(j2), sort_keys=True)
    except:
        return False

class StorageOptionsStatus():
    def __init__(self, pin_name) -> None:
        self.pin_name = pin_name
        self.fn=os.path.join(ROOT_PATH, "cache", f"{pin_name}.json")
        verify_path(os.path.join(ROOT_PATH, "cache"))
        if not os.path.exists(self.fn):
            save_json([],self.fn)
    
    def storage_options_status(self, pin_value:list):
        if isinstance(pin_value, list):
            save_json(pin_value, self.fn)

    def get_options_status(self, option_name):
        return option_name in load_json(self.fn)