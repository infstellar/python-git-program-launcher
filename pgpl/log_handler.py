from page_manager import manager

def ansl_code2col(ansl_code):
    if ansl_code == "0":
        return 'black'
    elif ansl_code == "31":
        return "red"
    elif ansl_code == "32":
        return "green"
    elif ansl_code == "33":
        return "olive"
    elif ansl_code == "34":
        return "blue"
    elif ansl_code == "35":
        return "green"
    elif ansl_code == "36": # cyan
        return "#0099CC"
    elif ansl_code == "37": # white
        return "black"
    
    return "NO_COL"

def webio_poster(record:str):
    record_list = record.split("\x1b")
    color = "black"
    for text in record_list:
        if text == '':
            continue
        ansl_code = text[text.index("[")+1:text.index("m")]
        c = ansl_code2col(ansl_code)
        if c != "NO_COL":
            color = ansl_code2col(ansl_code)
        text = text[text.index("m")+1:]
        manager.get_page('MainPage').logout(text, color=color)
    
    manager.get_page('MainPage').logout("$$end$$")

