from textual.widgets import Static
from models.types import SystemData


class SystemPanel(Static):
    def __init__(self, **kwargs):
        """初始化系统面板，增加对数据源的支持"""
        super().__init__(**kwargs)
        
    def update_data(self, data: SystemData):
        cpu_bar = "█" * int(data.cpu // 10) + "░" * int((100 - data.cpu) // 10)
        mem_bar = "█" * int(data.memory // 10) + "░" * int((100 - data.memory) // 10)
        
        # 生成 TOP 进程显示内容
        top_processes_lines = ["TOP PROCESSES:"]
        for proc in data.top_processes:
            name_part = f"{proc['name'][:12]:<12}"  # 截取前12个字符并左对齐
            pid_part = f"PID:{str(proc['pid'])[:8]:<8}"  # PID部分左对齐
            cpu_part = f"CPU:{proc['cpu_percent']:>5.1f}%"  # CPU使用率右对齐
            mem_part = f"MEM:{proc['memory_percent']:>5.1f}%"  # 内存使用率右对齐
            top_processes_lines.append(f"{name_part} {pid_part} {cpu_part} {mem_part}")
        
        top_processes_str = "\n".join(top_processes_lines)
        
        content = (
            f"CPU: {cpu_bar} {data.cpu:.1f}% ({data.cpu_count} cores)\n"
            f"MEM: {mem_bar} {data.memory:.1f}% ({data.memory_used_gb:.1f}G/{data.memory_total_gb:.1f}G)\n"
            f"DISK: {data.disk:.1f}% ({data.disk_used_gb:.1f}G/{data.disk_total_gb:.1f}G)\n"
            f"NET: ↑{data.network_upload_kb:.1f}KB/s ↓{data.network_download_kb:.1f}KB/s\n"
            f"PROC: {data.process_count} processes\n\n"
            f"{top_processes_str}"
        )
        self.update(content)
    
    def format_text(self, data: SystemData):
        cpu_bar = "█" * int(data.cpu // 10) + "░" * int((100 - data.cpu) // 10)
        mem_bar = "█" * int(data.memory // 10) + "░" * int((100 - data.memory) // 10)
        
        # 生成 TOP 进程显示内容
        top_processes_lines = ["TOP PROCESSES:"]
        for proc in data.top_processes:
            name_part = f"{proc['name'][:12]:<12}"  # 截取前12个字符并左对齐
            pid_part = f"PID:{str(proc['pid'])[:8]:<8}"  # PID部分左对齐
            cpu_part = f"CPU:{proc['cpu_percent']:>5.1f}%"  # CPU使用率右对齐
            mem_part = f"MEM:{proc['memory_percent']:>5.1f}%"  # 内存使用率右对齐
            top_processes_lines.append(f"{name_part} {pid_part} {cpu_part} {mem_part}")
        
        top_processes_str = "\n".join(top_processes_lines)
        
        return (
            f"CPU: {cpu_bar} {data.cpu:.1f}% ({data.cpu_count} cores)\n"
            f"MEM: {mem_bar} {data.memory:.1f}% ({data.memory_used_gb:.1f}G/{data.memory_total_gb:.1f}G)\n"
            f"DISK: {data.disk:.1f}% ({data.disk_used_gb:.1f}G/{data.disk_total_gb:.1f}G)\n"
            f"NET: ↑{data.network_upload_kb:.1f}KB/s ↓{data.network_download_kb:.1f}KB/s\n"
            f"PROC: {data.process_count} processes\n\n"
            f"{top_processes_str}"
        )