from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

T = TypeVar('T')

class DataSource(ABC, Generic[T]):
    """数据源抽象基类，用于封装不同类型的数据采集逻辑"""
    
    @abstractmethod
    async def fetch(self) -> T:
        """
        获取数据
        :return: 采集到的数据
        """
        pass
    
    @property
    @abstractmethod
    def refresh_interval(self) -> float:
        """
        刷新间隔（秒）
        :return: 采集间隔时间
        """
        pass