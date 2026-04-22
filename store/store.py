from typing import Callable, List, Dict, Any
from models.types import AppState
import time


class ModuleState:
    """模块级状态"""
    def __init__(self, data: Any):
        self.data = data
        self.version = 0
        self.last_updated = time.time()


class Store:
    def __init__(self):
        self._modules: Dict[str, ModuleState] = {}
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, module: str, callback: Callable):
        """订阅特定模块的状态变化"""
        if module not in self._subscribers:
            self._subscribers[module] = []
        self._subscribers[module].append(callback)

    def set_state(self, new_state: AppState):
        """保留原有 set_state 方法以兼容现有 API"""
        self._modules['app'] = ModuleState(new_state)
        for cb in self._subscribers.get('app', []):
            cb(new_state)

    @property
    def state(self) -> AppState:
        """保留原有 state 属性以兼容现有 API"""
        app_state = self._modules.get('app')
        return app_state.data if app_state else AppState()

    def update_module(self, module: str, data: Any):
        """更新单个模块状态，仅通知该模块的订阅者"""
        state = self._modules.get(module, ModuleState(data))
        state.data = data
        state.version += 1
        state.last_updated = time.time()
        self._modules[module] = state

        # 仅通知该模块的订阅者
        for cb in self._subscribers.get(module, []):
            cb(data)

    def get_module_data(self, module: str):
        """获取模块数据"""
        module_state = self._modules.get(module)
        return module_state.data if module_state else None