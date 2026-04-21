# Textual Dashboard

基于Textual的终端仪表板，实现了状态驱动架构。

## 快速开始

```bash
pip install -r requirements.txt
python app.py
```

## 功能
- 系统监控（CPU、内存、磁盘）
- Agent状态显示
- Todo任务管理
- 笔记功能
- 键盘交互（t: 切换todo, q: 退出）

## 架构
- Store: 全局状态管理
- Widgets: UI组件
- Services: 数据服务（后续扩展）