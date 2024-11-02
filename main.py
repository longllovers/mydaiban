import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QDateTime, QPoint
from PyQt5.QtGui import QFont, QIcon
import pystray
from PIL import Image

class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks_file = "tasks.json"  # 定义保存任务的文件
        self.initUI()  # 初始化用户界面
        self.oldPos = self.pos()  # 用于记录窗口的旧位置，以便拖动
        self.load_tasks()  # 启动时加载任务

        # 创建系统托盘图标
        self.create_tray_icon()  # 使用 pystray 创建托盘图标

    def create_tray_icon(self):
        """
        使用 pystray 创建系统托盘图标并定义菜单项
        """
        icon_image = Image.open("代办.png")  # 替换为实际图标路径
        # 设置托盘图标和菜单项，包括显示、显示任务和退出选项
        self.tray_icon = pystray.Icon("To-Do List", icon_image, menu=pystray.Menu(
            pystray.MenuItem("显示", self.show_app),
            pystray.MenuItem("显示任务", self.show_tasks_in_tray),
            pystray.MenuItem("退出", self.quit_app)
        ))
        # 启动托盘图标并在后台运行
        self.tray_icon.run_detached()

    def show_app(self):
        """
        显示主窗口
        """
        self.showNormal()

    def show_tasks_in_tray(self, icon, item):
        """
        在托盘通知中显示当前任务列表
        """
        # 获取所有任务文本
        tasks = [self.task_list.itemWidget(self.task_list.item(i)).layout().itemAt(1).widget().text()
                 for i in range(self.task_list.count())]
        # 将任务组合成一条通知消息
        tasks_message = "\n".join(tasks) if tasks else "没有任务"
        self.tray_icon.notify("当前任务列表", tasks_message)

    def quit_app(self, icon, item):
        """
        退出应用程序并关闭托盘图标
        """
        self.tray_icon.stop()  # 停止托盘图标
        QApplication.instance().quit()  # 退出应用程序

    def closeEvent(self, event):
        """
        在关闭窗口事件中隐藏窗口，而不是退出程序
        """
        event.ignore()  # 忽略关闭事件
        self.hide()  # 隐藏窗口
        # 在托盘中显示通知，告知用户应用已最小化到托盘
        self.tray_icon.notify("To-Do List", "应用已最小化到系统托盘")

    def initUI(self):
        """
        初始化用户界面
        """
        # 设置窗口标题和尺寸
        self.setWindowTitle("To-Do List")
        self.setGeometry(100, 100, 400, 300)
        # 设置无边框窗口，并将其设为工具窗口，以隐藏任务栏图标
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        # 设置窗口背景为半透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(249, 247, 232, 180);")

        # 创建主布局
        main_layout = QVBoxLayout()

        # 添加标题
        header = QLabel("代办事项")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # 创建任务输入区域
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()  # 创建任务输入框
        self.task_input.setPlaceholderText("添加新任务...")
        add_task_btn = QPushButton("+")  # 创建添加任务按钮
        add_task_btn.clicked.connect(self.add_task)  # 将按钮点击事件连接到add_task方法

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(add_task_btn)
        main_layout.addLayout(input_layout)

        # 创建任务列表
        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)

        # 设置主布局
        self.setLayout(main_layout)

    def add_task(self):
        """
        添加新任务到任务列表
        """
        task_text = self.task_input.text()  # 获取输入框中的任务文本
        if task_text:
            # 获取当前时间并格式化
            current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
            # 创建任务项并添加到任务列表
            self.create_task_item(task_text, current_time)
            self.save_tasks()  # 保存任务到文件
            self.task_input.clear()  # 清空输入框

    def create_task_item(self, task_text, timestamp):
        """
        创建带有删除按钮和复选框的任务项
        """
        item = QListWidgetItem()  # 创建任务列表项
        item_widget = QWidget()  # 创建容器部件
        layout = QHBoxLayout()  # 创建水平布局

        # 复选框用于标记任务完成
        checkbox = QCheckBox()
        checkbox.setStyleSheet("QCheckBox::indicator { width: 16px; height: 16px;}")
        layout.addWidget(checkbox)

        # 任务标签显示任务文本
        task_label = QLabel(task_text)
        task_label.setFont(QFont("Arial", 12))
        layout.addWidget(task_label)

        # 时间戳标签显示任务添加时间
        time_label = QLabel(timestamp)
        time_label.setFont(QFont("Arial", 10))
        layout.addWidget(time_label)

        # 删除按钮用于删除任务
        delete_button = QPushButton("🗑")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("border: none; color: #FF6347;")
        delete_button.clicked.connect(lambda: self.delete_task(item))  # 连接到删除任务的方法
        layout.addWidget(delete_button)

        layout.setAlignment(Qt.AlignLeft)  # 左对齐布局
        item_widget.setLayout(layout)  # 将布局设置到容器部件
        item.setSizeHint(item_widget.sizeHint())  # 设置任务项的大小
        self.task_list.addItem(item)  # 将任务项添加到列表
        self.task_list.setItemWidget(item, item_widget)  # 在列表项中设置自定义小部件

    def delete_task(self, item):
        """
        删除任务项并保存更改
        """
        row = self.task_list.row(item)  # 获取任务项的行号
        self.task_list.takeItem(row)  # 删除该行任务
        self.save_tasks()  # 保存更改

    def save_tasks(self):
        """
        保存当前任务列表到JSON文件
        """
        tasks = []
        # 遍历所有任务项并保存其内容
        for i in range(self.task_list.count()):
            item_widget = self.task_list.itemWidget(self.task_list.item(i))
            task_text = item_widget.layout().itemAt(1).widget().text()
            timestamp = item_widget.layout().itemAt(2).widget().text()
            tasks.append({"task": task_text, "time": timestamp})
        # 将任务保存到文件
        with open(self.tasks_file, "w", encoding="utf-8") as file:
            json.dump(tasks, file, ensure_ascii=False, indent=4)

    def load_tasks(self):
        """
        从JSON文件加载任务列表
        """
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as file:
                tasks = json.load(file)
                for task in tasks:
                    self.create_task_item(task["task"], task["time"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # 若文件不存在或JSON解码错误则忽略

    def mousePressEvent(self, event):
        """
        捕捉鼠标按下事件，用于实现窗口拖动
        """
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()  # 记录鼠标的初始位置

    def mouseMoveEvent(self, event):
        """
        捕捉鼠标移动事件，用于实现窗口拖动
        """
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)  # 计算移动偏移量
            self.move(self.x() + delta.x(), self.y() + delta.y())  # 移动窗口
            self.oldPos = event.globalPos()  # 更新鼠标的位置


if __name__ == '__main__':
    app = QApplication(sys.argv)
    todo_app = TodoApp()  # 创建主窗口
    todo_app.show()  # 显示主窗口
    sys.exit(app.exec_())  # 运行应用程序主循环
