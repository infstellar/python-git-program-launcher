from path_lib import *
from pywebio import platform
import asyncio
import threading
from pgpl.utils import t2t, logger

if not ROOT_PATH.isascii():
    logger.critical(t2t("Error:PGPL path must contain only ASCII characters\nThe current path is ")+ROOT_PATH)
    input(t2t("Press enter to exit"))
    os._exit()
    
from pgpl import webio


def server_thread():
    # https://zhuanlan.zhihu.com/p/101586682
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    platform.tornado.start_server(webio.main, auto_open_webbrowser=False, port = 22269, debug=False)



import webview

def main():
    threading.Thread(target=server_thread, daemon=False).start()
    window = webview.create_window("PGPL", "http://localhost:22269/", width=1280, height=720) # 1024 576
    webview.start(http_server=True, gui='qt')
    # window.show()

if __name__ == '__main__':
    main()

# cef: pip install cefpython3
# qt: pip install PyQtWebEngine
# edgechromium: install edge