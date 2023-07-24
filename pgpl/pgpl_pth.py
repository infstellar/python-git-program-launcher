from utils import *

PGPLPTH = "Lib/site-packages\n../../python_site_packages\n../../python_site_packages/future\n# DEBUG\n# import sys; print(sys.path)"

def generate_pgplpth(path):
    with open(os.path.join(path, 'pgpl.pth'), 'w') as f:
        f.write(PGPLPTH)

# 一些包因为某些原因无法正常安装。
# pgpl_pth提供了一种摆烂的解决方案。

# pip失败：

#   Collecting future
#   Using cached future-0.18.3.tar.gz (840 kB)
#   Preparing metadata (setup.py) ... error
#   error: subprocess-exited-with-error

#   python setup.py egg_info did not run successfully.
#   │ exit code: 1
#   ╰─> [7 lines of output]
#       Traceback (most recent call last):
#         File "<string>", line 36, in <module>
#         File "<pip-setuptools-caller>", line 34, in <module>
#         File "C:\Users\\admin\AppData\Local\Temp\pip-install-78567xgc\\future_7b8221b33d6345a6bd9a370172ba4baa\setup.py", line 86, in <module>
#           import src.future
#       ModuleNotFoundError: No module named 'src'

# 解决方案：
# 手动下载无法下载的包，解压放入toolkit/python_site_packages，在PGPLPTH中写入导入失败的包位置
# TODO: 使用anaconda的python安装流程可能解决此问题



# PGPLPTH_PATHS = ['../../python_site_packages', '../../python_site_packages/future']






