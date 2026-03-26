from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from configobj import ConfigObj
from config import CONFIG_FILE, COPYRIGHT, TEL
from utils import hash_password


class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置管理员密码")
        self.setFixedSize(360, 250)
        self.setFont(QFont("Arial", 10))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        title = QLabel("首次运行，请设置管理员密码")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        self.new_pass_edit = QLineEdit()
        self.new_pass_edit.setEchoMode(QLineEdit.Password)
        self.new_pass_edit.setPlaceholderText("新密码")
        layout.addWidget(QLabel("新密码:"))
        layout.addWidget(self.new_pass_edit)

        self.confirm_pass_edit = QLineEdit()
        self.confirm_pass_edit.setEchoMode(QLineEdit.Password)
        self.confirm_pass_edit.setPlaceholderText("确认新密码")
        layout.addWidget(QLabel("确认密码:"))
        layout.addWidget(self.confirm_pass_edit)

        btn_box = QDialogButtonBox()
        ok_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        btn_box.addButton(ok_btn, QDialogButtonBox.AcceptRole)
        btn_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        ok_btn.clicked.connect(self.save_password)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(btn_box)

        copy = QLabel(f"{COPYRIGHT} | {TEL}")
        copy.setAlignment(Qt.AlignCenter)
        layout.addWidget(copy)

    def save_password(self):
        new_pass = self.new_pass_edit.text()
        confirm_pass = self.confirm_pass_edit.text()

        if not new_pass:
            QMessageBox.warning(self, "错误", "密码不能为空")
            return
        if new_pass != confirm_pass:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致")
            return
        if len(new_pass) < 6:
            QMessageBox.warning(self, "错误", "密码长度至少6位")
            return

        # 加密密码并保存到配置文件
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            cfg["Admin"] = {
                "password": hash_password(new_pass)
            }
            cfg.write()
            QMessageBox.information(self, "成功", "密码已保存")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存密码失败: {str(e)}")
