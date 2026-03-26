from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from configobj import ConfigObj
from config import CONFIG_FILE, SOFTWARE_NAME, DEFAULT_ADMIN_PASSWORD, COPYRIGHT, TEL
from utils import verify_password


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.setFixedSize(360, 220)
        self.setFont(QFont("Arial", 10))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        title = QLabel(f"{SOFTWARE_NAME}")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setPlaceholderText("管理员密码")
        layout.addWidget(QLabel("管理员密码:"))
        layout.addWidget(self.pass_edit)

        btn_box = QDialogButtonBox()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_box.addButton(ok_btn, QDialogButtonBox.AcceptRole)
        btn_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        ok_btn.clicked.connect(self.check)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(btn_box)

        copy = QLabel(f"{COPYRIGHT} | {TEL}")
        copy.setAlignment(Qt.AlignCenter)
        layout.addWidget(copy)

    def check(self):
        # 从配置文件读取加密后的密码
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            if "Admin" in cfg and "password" in cfg["Admin"]:
                hashed_password = cfg["Admin"]["password"]
                if verify_password(self.pass_edit.text(), hashed_password):
                    self.accept()
                else:
                    QMessageBox.warning(self, "错误", "密码错误")
            else:
                # 配置文件中没有密码，使用默认密码
                if self.pass_edit.text() == DEFAULT_ADMIN_PASSWORD:
                    self.accept()
                else:
                    QMessageBox.warning(self, "错误", "密码错误")
        except Exception as e:
            # 配置文件读取失败，使用默认密码
            if self.pass_edit.text() == DEFAULT_ADMIN_PASSWORD:
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "密码错误")
