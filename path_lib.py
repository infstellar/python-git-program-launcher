import os, sys

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_PATH)
if sys.path[0] != ROOT_PATH:
    sys.path.insert(0, ROOT_PATH)
