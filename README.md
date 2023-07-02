# python-git-program-launcher
自动安装并启动基于git管理的python程序。

# 特点
- 一键启动python程序
- 允许使用不同的配置，管理不同python版本的不同仓库。
- 自动下载并安装python和pip包。
- 使用git自动更新
- 丰富的的自定义配置
- 使用命令行选择/修改配置
# 使用

下载[toolkit](https://github.com/infstellar/python-git-program-launcher/releases/download/v1.0.0/toolkit.7z)放在Launcher.exe同级目录下。

运行Launcher.bat或Launcher.exe。

你可能需要使用管理员权限运行。

# 设置配置

|配置项|内容|默认值|
|----|----|----|
|RequirementsFile|requirement文件位置|requirements.txt|
|InstallDependencies|是否安装pip依赖|true|
|PypiMirror|pypi镜像|AUTO|
|PythonMirror|python镜像|AUTO|
|Repository|仓库地址|https://github.com/infstellar/python-git-program-launcher|
|Main|python执行文件|main.py|
|Branch|分支|main|
|GitProxy|是否开启Git验证|false|
|KeepLocalChanges|是否保持本地更改|false|
|AutoUpdate|是否自动更新|true|
|Tag|tag，有tag时优先使用tag，否则使用branch。||
|PythonVersion|python版本，必须为有效版本|3.10.10|

# 文件位置

## 仓库位置
./repositories

## python位置
./toolkit/python  
你可能需要通过控制面板卸载。

# 为你的项目添加默认配置

Fork本仓库，在configs文件夹中添加配置，然后再分发。

# 范例配置

[SRC](docs/SRC.json)   
[GIA](docs/GIA.json)  

# 鸣谢
ALAS-EasyInstaller

GIA
