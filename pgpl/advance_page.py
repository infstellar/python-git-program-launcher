from pgpl.utils import *
from pgpl.page import Page
from pgpl.page_manager import manager
from pgpl.webio_utils import *

class AdvancePage(Page):
    """Page的加强版，多了一个显示页面切换的功能

    Args:
        Page (_type_): _description_
    """
    def __init__(self, page_name=""):
        super().__init__(page_name)
    
    def _on_load(self):
        with output.use_scope(self.main_scope):
            # 标题
            if DEBUG_MODE:
                output.put_markdown(t2t('# PGPL DEBUG') + f" 2.3.0"),
            else:
                output.put_markdown(t2t('# PGPL GUI') + f" 2.3.0"),
            
            # 页面切换按钮
            output.put_buttons(self._value_list2buttons_type(list(manager.page_dict)), onclick=manager.load_page, scope=self.main_scope)
            super()._on_load()
            
    def _reload_self(self):
        self.unload()
        self.load()