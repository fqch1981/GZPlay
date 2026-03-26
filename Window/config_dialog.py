import sys
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
from configobj import ConfigObj
from config import CONFIG_FILE, COPYRIGHT, TEL


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EOS配置")
        self.setFixedSize(480, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint)
        layout = QFormLayout(self)

        self.endpoint = QLineEdit("eos-jinan-1.cmecloud.cn")
        self.ak = QLineEdit()
        self.sk = QLineEdit()
        self.ffmpeg = QLineEdit("ffmpeg.exe")

        layout.addRow("端点地址", self.endpoint)
        layout.addRow("访问密钥", self.ak)
        layout.addRow("秘密密钥", self.sk)
        layout.addRow("FFmpeg路径", self.ffmpeg)

        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
        # 设置按钮文字
        btn_box.button(QDialogButtonBox.Save).setText("保存")
        btn_box.button(QDialogButtonBox.Cancel).setText("取消")

        copy = QLabel(f"{COPYRIGHT} | {TEL}")
        copy.setAlignment(Qt.AlignCenter)
        layout.addRow(copy)

    def save(self):
        cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
        cfg["EOS"] = {
            "endpoint": self.endpoint.text().strip(),
            "ak": self.ak.text().strip(),
            "sk": self.sk.text().strip(),
            "ffmpeg": self.ffmpeg.text().strip(),
        }
        cfg.write()
        QMessageBox.information(self, "成功", "已保存！重启后生效")
        self.accept()
        sys.exit(0)
