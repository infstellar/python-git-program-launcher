import os
os.path.abspath("translation\\pygettext")
pyfile = os.path.abspath('translation\\pygettext.py')
command_head_en = f"python translation\\pygettext.py -k t2t -d en_US -p translation\\locale\\en_US\\LC_MESSAGES"
command_head_zh = f'python translation\\pygettext.py -k t2t -d zh_CN -p translation\\locale\\zh_CN\\LC_MESSAGES'
command=r''

command+='main.py'
        
print(f'{command_head_en} {command}')
os.system(f'{command_head_en} {command}')
print(f'{command_head_zh} {command}')
os.system(f'{command_head_zh} {command}')