import json
from pywebio import output
import traceback

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