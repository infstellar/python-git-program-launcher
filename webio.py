from utils import *
from pywebio import *
import subprocess
import pywebio
from logger import add_logger_to_GUI
import log_handler
from page_manager import manager
from pages import MainPage, ConfigPage
status = True
global first_run
first_run = False
def get_branch_commit_id():
    res = subprocess.Popen('git rev-parse --short HEAD', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    res.wait()
    commit_id = res.stdout.read().decode('utf8').replace('\n', '')

    res = subprocess.Popen('git symbolic-ref --short -q HEAD', shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    res.wait()
    branch = res.stdout.read().decode('utf8').replace('\n', '')
    return branch,commit_id

def main():
    global first_run
    pywebio.session.set_env(output_max_width='80%', title=f"PGPL {1.0} {get_branch_commit_id()[1]}")
    session.run_js(f'document.querySelector("body > footer").innerHTML+="| PGPL: {"-".join(get_branch_commit_id())}"')
    manager.reg_page('MainPage', MainPage())
    manager.reg_page('ConfigPage', ConfigPage())
    manager.load_page('MainPage')
    if not first_run:
        add_logger_to_GUI(log_handler.webio_poster)
        first_run = True
    logger.info(t2t("webio启动完成"))

if __name__ == '__main__':
    platform.tornado.start_server(main, auto_open_webbrowser=True, debug=True)
