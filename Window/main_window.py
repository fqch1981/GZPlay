import sys
from pathlib import Path
from configobj import ConfigObj
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFont

from config import CONFIG_FILE, SOFTWARE_NAME, VERSION, COPYRIGHT, TEL
from Class.eos_client import EosClient
from Class.load_threads import LoadBucketThread, LoadObjectsThread
from Window.login_dialog import LoginDialog
from Window.change_password_dialog import ChangePasswordDialog
from Window.config_dialog import ConfigDialog
from Window.bucket_config_dialog import BucketConfigDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{SOFTWARE_NAME} {VERSION}")
        self.setGeometry(100,100,1400,800)
        self.setFont(QFont("Arial", 10))

        # 检查是否需要设置密码
        if not self.has_admin_password():
            # 首次运行，弹出设置密码窗口
            if ChangePasswordDialog().exec() != QDialog.Accepted:
                sys.exit()

        # 登录验证
        if LoginDialog().exec() != QDialog.Accepted:
            sys.exit()

        self.config = self.load_config()
        if not self.config: return

        self.client = EosClient(
            self.config["EOS"]["ak"],
            self.config["EOS"]["sk"],
            self.config["EOS"]["endpoint"]
        )
        self.bucket_client = None  # 当前选中的桶的客户端
        self.current_bucket = None
        self.current_key = None
        self.init_ui()
        self.load_buckets()

    def has_admin_password(self):
        """检查是否已设置管理员密码"""
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            return "Admin" in cfg and "password" in cfg["Admin"]
        except:
            return False

    def load_config(self):
        if not Path(CONFIG_FILE).exists():
            ConfigDialog().exec()
            return None
        try:
            return ConfigObj(CONFIG_FILE, encoding="utf-8")
        except:
            ConfigDialog().exec()
            return None

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10,10,10,10)

        # 左侧树状列表容器
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0,0,0,0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("所有存储桶")
        self.tree.setMinimumWidth(200)
        self.tree.itemClicked.connect(self.on_tree_click)

        # 启用水平滚动和自动调整列宽
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setColumnWidth(0, 400)  # 设置初始列宽
        self.tree.setWordWrap(False)  # 不自动换行

        # 设置行高
        self.tree.setIconSize(QSize(20, 20))

        # 设置Header样式为透明
        header = self.tree.header()
        header.setStyleSheet("""
            QHeaderView {
                background: transparent;
                border: none;
            }
            QHeaderView::section {
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)

        # 获取标准样式
        from PySide6.QtWidgets import QStyle

        # 设置选中样式 - 深色背景，文字反色
        self.tree.setStyleSheet("""
            QTreeWidget {
                outline: none;
                border: none;
            }
            QTreeWidget::header {
                background: transparent;
                border: none;
            }
            QTreeWidget::item {
                height: 30px;
                padding: 5px;
                border: none;
            }
            QTreeWidget::item:selected {
                background: #005a9e;
                color: white;
                border: none;
                outline: none;
            }
            QTreeWidget::item:hover {
                background: #0078d4;
                color: white;
                border: none;
            }
        """)

        left_layout.addWidget(self.tree)

        # 添加刷新按钮
        refresh_container = QWidget()
        refresh_layout = QHBoxLayout(refresh_container)
        refresh_layout.setContentsMargins(0, 5, 0, 0)
        self.refresh_btn = QPushButton("刷新选中存储桶")
        self.refresh_btn.clicked.connect(self.refresh_selected_bucket)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_container.setStyleSheet("background: transparent;")

        left_layout.addWidget(refresh_container)

        # 右侧播放器容器
        right = QWidget()
        layout = QVBoxLayout(right)

        # 播放器占满剩余空间
        self.video = QVideoWidget()
        self.video.setStyleSheet("background:#000; border-radius: 5px;")
        layout.addWidget(self.video, stretch=1)

        # 播放控制栏
        bar = QWidget()
        bar.setStyleSheet("""
            QWidget {
                background: transparent;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(10, 5, 10, 5)

        # 播放/暂停按钮（合并）
        self.play_pause_btn = QPushButton()
        self.stop_btn = QPushButton()
        self.progress = QSlider(Qt.Horizontal)
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setFixedWidth(120)
        self.volume.setValue(70)
        self.label = QLabel("就绪")

        # 设置按钮图标
        self.play_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.pause_icon = self.style().standardIcon(QStyle.SP_MediaPause)
        self.stop_icon = self.style().standardIcon(QStyle.SP_MediaStop)

        self.play_pause_btn.setIcon(self.play_icon)
        self.stop_btn.setIcon(self.stop_icon)

        # 设置按钮大小
        icon_size = QSize(24, 24)
        self.play_pause_btn.setIconSize(icon_size)
        self.stop_btn.setIconSize(icon_size)

        self.play_pause_btn.setFixedSize(40, 40)
        self.stop_btn.setFixedSize(40, 40)

        # 美化按钮样式
        btn_style = """
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #106ebe;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
        """
        for btn in [self.play_pause_btn, self.stop_btn]:
            btn.setStyleSheet(btn_style)

        # 美化滑块
        slider_style = """
            QSlider::groove:horizontal {
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                background: #0078d4;
                border-radius: 8px;
                margin: -4px 0;
            }
        """
        self.progress.setStyleSheet(slider_style)
        self.volume.setStyleSheet(slider_style)

        bar_layout.addWidget(self.play_pause_btn)
        bar_layout.addWidget(self.stop_btn)
        bar_layout.addWidget(self.progress)
        bar_layout.addWidget(QLabel("音量:"))
        bar_layout.addWidget(self.volume)
        bar_layout.addStretch()
        layout.addWidget(bar)

        # 使用分割器实现左右布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)

        # 状态栏 - 左侧显示播放状态，右侧显示版权信息
        self.statusBar().addWidget(self.label)
        self.copyright = QLabel(f"{COPYRIGHT} | {TEL}")
        self.statusBar().addPermanentWidget(self.copyright)
        # 美化状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #f8f9fa;
                border-top: 1px solid #d0d0d0;
            }
        """)

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)

        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.stop_btn.clicked.connect(self.player.stop)
        self.volume.valueChanged.connect(self.audio.setVolume)
        self.progress.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.progress.setValue)
        self.player.durationChanged.connect(self.progress.setMaximum)
        self.player.playbackStateChanged.connect(self.on_state_change)

    def load_buckets(self):
        self.th = LoadBucketThread(self.client)
        self.th.result.connect(self.show_buckets)
        self.th.error.connect(lambda e:QMessageBox.warning(self,"错误",str(e)))
        self.th.start()

    def show_buckets(self, buckets):
        self.tree.clear()
        for b in buckets:
            # 创建桶项，包含桶名和刷新按钮
            item = QTreeWidgetItem(self.tree)
            item.setText(0, b)
            # 设置存储桶图标
            item.setIcon(0, self.tree.style().standardIcon(QStyle.SP_DriveNetIcon))

            # 设置桶项的数据
            item.setData(0, Qt.UserRole, {"scanned": False, "endpoint": None})

    def on_tree_click(self, item, column):
        name = item.text(0)
        parent = item.parent()

        if parent is None:
            # 点击的是桶
            self.current_bucket = name

            # 检查是否已扫描
            bucket_data = item.data(0, Qt.UserRole)
            if bucket_data and bucket_data.get("scanned"):
                # 已扫描，切换展开/收缩
                item.setExpanded(not item.isExpanded())
                return

            # 获取桶的专属配置
            bucket_config = self.get_bucket_config(name)
            self.bucket_client = EosClient(
                bucket_config['ak'],
                bucket_config['sk'],
                bucket_config['endpoint']
            )

            # 检查是否需要保存桶的配置
            bucket_section = f"Bucket_{name}"
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            if bucket_section not in cfg:
                # 没有桶专属配置，弹出配置对话框
                dlg = BucketConfigDialog(name, self)
                if dlg.exec() != QDialog.Accepted:
                    return
                
                # 保存桶专属配置（包含AK/SK/Endpoint）
                cfg[bucket_section] = {}
                cfg[bucket_section]['ak'] = dlg.ak.text().strip() if hasattr(dlg, 'ak') else self.config["EOS"]["ak"]
                cfg[bucket_section]['sk'] = dlg.sk.text().strip() if hasattr(dlg, 'sk') else self.config["EOS"]["sk"]
                cfg[bucket_section]['endpoint'] = dlg.endpoint.text().strip()
                cfg.write()
                
                # 重新加载配置并创建客户端
                bucket_config = self.get_bucket_config(name)
                self.bucket_client = EosClient(
                    bucket_config['ak'],
                    bucket_config['sk'],
                    bucket_config['endpoint']
                )

            self.load_objects(name, item, self.bucket_client)
            return

        # 点击的是目录或文件
        bucket = item.data(0, Qt.UserRole + 1)
        key = item.data(0, Qt.UserRole)

        # 只有文件才播放
        if key:
            print(f"[TreeClick] 播放文件: {name}, Bucket: {bucket}, Key: {key}")
            self.play_file(bucket, key)

    def refresh_bucket(self, item):
        """刷新桶内容"""
        name = item.text(0)

        # 检查桶的地域设置
        bucket_endpoint = self.get_bucket_endpoint(name)
        if bucket_endpoint is None:
            # 没有设置，弹出配置对话框
            dlg = BucketConfigDialog(name, self)
            if dlg.exec() != QDialog.Accepted:
                return
            bucket_endpoint = dlg.endpoint.text().strip()

        # 使用桶的地域endpoint创建客户端
        self.bucket_client = EosClient(
            self.config["EOS"]["ak"],
            self.config["EOS"]["sk"],
            bucket_endpoint
        )

        self.load_objects(name, item, self.bucket_client)

    def refresh_selected_bucket(self):
        """刷新当前选中的桶"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择一个存储桶")
            return

        item = selected_items[0]
        name = item.text(0)

        # 检查是否是桶（没有父节点）
        if item.parent() is not None:
            QMessageBox.warning(self, "提示", "请选择存储桶，而不是文件或文件夹")
            return

        self.refresh_bucket(item)

    def get_bucket_endpoint(self, bucket_name):
        """获取桶的endpoint配置，返回None表示未配置"""
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            bucket_section = f"Bucket_{bucket_name}"
            if bucket_section in cfg and "endpoint" in cfg[bucket_section]:
                return cfg[bucket_section]["endpoint"]
        except:
            pass
        return None

    def get_bucket_config(self, bucket_name):
        """获取桶的专属配置，如果桶没有专属配置则使用默认配置"""
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            
            # 检查是否有桶专属配置
            bucket_section = f"Bucket_{bucket_name}"
            if bucket_section in cfg:
                config = {}
                # 优先使用桶专属配置
                if 'ak' in cfg[bucket_section]:
                    config['ak'] = cfg[bucket_section]['ak']
                else:
                    config['ak'] = cfg["EOS"]["ak"]
                
                if 'sk' in cfg[bucket_section]:
                    config['sk'] = cfg[bucket_section]['sk']
                else:
                    config['sk'] = cfg["EOS"]["sk"]
                
                if 'endpoint' in cfg[bucket_section]:
                    config['endpoint'] = cfg[bucket_section]['endpoint']
                else:
                    config['endpoint'] = cfg["EOS"]["endpoint"]
                
                print(f"[GetConfig] 使用桶专属配置: {bucket_name}")
                return config
            
            # 使用默认配置
            print(f"[GetConfig] 使用默认配置: {bucket_name}")
            return {
                'ak': cfg["EOS"]["ak"],
                'sk': cfg["EOS"]["sk"],
                'endpoint': cfg["EOS"]["endpoint"]
            }
        except Exception as e:
            print(f"[GetConfig] 获取配置失败: {str(e)}")
            return {
                'ak': self.config["EOS"]["ak"],
                'sk': self.config["EOS"]["sk"],
                'endpoint': self.config["EOS"]["endpoint"]
            }

    def load_objects(self, bucket, parent_item, client=None):
        parent_item.takeChildren()
        # 使用传入的客户端，如果没有则使用默认客户端
        eos_client = client if client else self.client
        self.th = LoadObjectsThread(eos_client, bucket)
        self.th.result.connect(lambda b, t: self.build_tree(parent_item, t, bucket))
        self.th.progress.connect(self.label.setText)  # 显示扫描进度
        self.th.error.connect(lambda e:QMessageBox.warning(self,"错误",str(e)))
        self.th.start()

    def build_tree(self, parent_item, data, bucket):
        print(f"[BuildTree] 开始构建树，父项: {parent_item.text(0)}, Bucket: {bucket}, 数据项数: {len(data)}")
        items = {}

        # 标记桶为已扫描
        if parent_item.parent() is None:  # 父项是根节点，说明parent_item是桶
            bucket_data = parent_item.data(0, Qt.UserRole)
            if bucket_data:
                bucket_data["scanned"] = True
                parent_item.setData(0, Qt.UserRole, bucket_data)

        # 先添加所有目录
        for k,v in data.items():
            if v["t"]=="d":
                # 计算父路径
                path_parts = k.rstrip("/").split("/")
                if len(path_parts) == 1:
                    # 根级目录，直接添加到桶下
                    it = QTreeWidgetItem(parent_item, [v["n"]])
                    # 设置文件夹图标
                    it.setIcon(0, self.tree.style().standardIcon(QStyle.SP_DirIcon))
                    # 保存bucket信息
                    it.setData(0, Qt.UserRole + 1, bucket)
                    items[k] = it
                    print(f"[BuildTree] 添加根级目录: {v['n']}")
                else:
                    # 子目录，找到父目录
                    parent_path = "/".join(path_parts[:-1]) + "/"
                    pi = items.get(parent_path)
                    if pi:
                        it = QTreeWidgetItem(pi, [v["n"]])
                        # 设置文件夹图标
                        it.setIcon(0, self.tree.style().standardIcon(QStyle.SP_DirIcon))
                        # 保存bucket信息（从父目录继承）
                        it.setData(0, Qt.UserRole + 1, pi.data(0, Qt.UserRole + 1))
                        items[k] = it
                        print(f"[BuildTree] 添加子目录: {v['n']} (父: {parent_path})")

        # 再添加所有文件
        for k,v in data.items():
            if v["t"]=="f":
                # 计算文件所在目录
                path_parts = k.split("/")
                if len(path_parts) == 1:
                    # 根级文件，直接添加到桶下
                    it = QTreeWidgetItem(parent_item, [v["n"]])
                    # 设置文件图标
                    it.setIcon(0, self.tree.style().standardIcon(QStyle.SP_FileIcon))
                    it.setData(0, Qt.UserRole, k)
                    it.setData(0, Qt.UserRole + 1, bucket)
                    print(f"[BuildTree] 添加根级文件: {v['n']}")
                else:
                    # 子文件，找到所在目录
                    file_path = "/".join(path_parts[:-1]) + "/"
                    pi = items.get(file_path)
                    if pi:
                        it = QTreeWidgetItem(pi, [v["n"]])
                        # 设置文件图标
                        it.setIcon(0, self.tree.style().standardIcon(QStyle.SP_FileIcon))
                        it.setData(0, Qt.UserRole, k)
                        # 保存bucket信息（从所在目录继承）
                        it.setData(0, Qt.UserRole + 1, pi.data(0, Qt.UserRole + 1))
                        print(f"[BuildTree] 添加子文件: {v['n']} (目录: {file_path})")

        # 展开第一层
        parent_item.setExpanded(True)
        print(f"[BuildTree] 树构建完成")

    def play_file(self, bucket, key):
        # 获取桶的专属配置
        bucket_config = self.get_bucket_config(bucket)
        
        # 使用桶专属配置创建临时客户端
        client = EosClient(
            bucket_config['ak'],
            bucket_config['sk'],
            bucket_config['endpoint']
        )

        # 生成带签名的请求信息
        request_info = client.generate_direct_url(bucket, key)
        print(f"[Play] 使用桶专属配置: {bucket}")
        print(f"[Play] 下载URL: {request_info['url']}")

        # 下载文件到临时目录
        import requests
        import tempfile
        import os

        try:
            self.label.setText(f"正在下载: {key.split('/')[-1]}")

            # 创建临时文件
            filename = key.split('/')[-1]
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"gplay_{filename}")

            # 下载文件
            response = requests.get(
                request_info['url'],
                headers=request_info['headers'],
                timeout=30,
                stream=True
            )
            response.raise_for_status()

            # 保存到临时文件
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"[Play] 文件已下载到: {temp_file}")

            # 停止当前播放
            self.player.stop()

            # 设置新源（播放本地文件）
            media_url = QUrl.fromLocalFile(temp_file)
            self.player.setSource(media_url)

            # 更新状态标签
            self.label.setText(f"正在播放: {filename}")

            # 开始播放
            self.player.play()

            # 清理之前的临时文件（可以在这里添加清理逻辑）
            if hasattr(self, 'last_temp_file') and os.path.exists(self.last_temp_file):
                try:
                    os.remove(self.last_temp_file)
                except:
                    pass
            self.last_temp_file = temp_file

        except Exception as e:
            print(f"[Play] 播放失败: {str(e)}")
            self.label.setText(f"播放失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"无法播放文件:\n{str(e)}")

    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def update_play_pause_button(self, state):
        """根据播放状态更新按钮图标"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setIcon(self.pause_icon)
        else:
            self.play_pause_btn.setIcon(self.play_icon)

    def on_state_change(self, s):
        if s == QMediaPlayer.PlayingState:
            self.label.setText("正在播放")
        elif s == QMediaPlayer.PausedState:
            self.label.setText("已暂停")
        elif s == QMediaPlayer.StoppedState:
            self.label.setText("已停止")
        self.update_play_pause_button(s)

