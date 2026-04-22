import psutil
from typing import Dict, Any
from store.sources.base import DataSource


class SystemDataSource(DataSource[Dict[str, Any]]):
    """系统资源数据源，使用 psutil 采集真实系统信息"""
    
    def __init__(self, refresh_interval: float = 2.0, top_processes_limit: int = 5):
        """
        初始化系统数据源
        :param refresh_interval: 刷新间隔（秒），默认2秒
        :param top_processes_limit: 显示的顶级进程数量，默认5个
        """
        self._refresh_interval = refresh_interval
        self._top_processes_limit = top_processes_limit
        # 用于计算网络速度
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = psutil.time.time()

    async def fetch(self) -> Dict[str, Any]:
        """采集系统资源数据"""
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # CPU 核心数
        cpu_count = psutil.cpu_count(logical=True)
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        memory_percent = memory.percent
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        disk_percent = disk.percent
        
        # 网络IO - 计算传输速率
        current_net_io = psutil.net_io_counters()
        current_time = psutil.time.time()
        
        # 计算时间差
        time_diff = current_time - self._last_net_time if self._last_net_time else 1
        time_diff = max(time_diff, 1)  # 防止除零错误
        
        # 计算上传下载速度
        upload_speed = (current_net_io.bytes_sent - self._last_net_io.bytes_sent) / time_diff
        download_speed = (current_net_io.bytes_recv - self._last_net_io.bytes_recv) / time_diff
        
        # 转换为 KB/s
        upload_speed_kb = upload_speed / 1024
        download_speed_kb = download_speed / 1024
        
        # 更新上次数据用于下次计算
        self._last_net_io = current_net_io
        self._last_net_time = current_time
        
        # 系统启动时间
        boot_time = psutil.boot_time()
        
        # 当前进程数
        process_count = len(psutil.pids())
        
        # 获取顶级进程
        top_processes = self._get_top_processes(self._top_processes_limit)
        
        return {
            'cpu': cpu_percent,
            'cpu_count': cpu_count,
            'memory': memory_percent,
            'memory_used_gb': memory_used_gb,
            'memory_total_gb': memory_total_gb,
            'disk': disk_percent,
            'disk_used_gb': disk_used_gb,
            'disk_total_gb': disk_total_gb,
            'network_upload_kb': upload_speed_kb,
            'network_download_kb': download_speed_kb,
            'process_count': process_count,
            'boot_time': boot_time,
            'top_processes': top_processes
        }

    def _get_top_processes(self, limit: int = 5):
        """获取 CPU 使用率最高的 N 个进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'] or 0.0,
                    'memory_percent': proc.info['memory_percent'] or 0.0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 有些进程可能在遍历时已被终止，跳过即可
                continue
        
        # 按 CPU 使用率排序，取前 N 个
        top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
        return top_processes[:limit]

    @property
    def refresh_interval(self) -> float:
        """获取刷新间隔"""
        return self._refresh_interval