from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
from configobj import ConfigObj
from config import CONFIG_FILE, COPYRIGHT, TEL


class BucketConfigDialog(QDialog):
    def __init__(self, bucket_name, parent=None):
        super().__init__(parent)
        self.bucket_name = bucket_name
        self.setWindowTitle(f"存储桶配置 - {bucket_name}")
        self.setFixedSize(400, 280)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint & ~Qt.WindowMaximizeButtonHint)

        layout = QFormLayout(self)

        self.ak = QLineEdit()
        self.ak.setPlaceholderText("访问密钥ID (AK)")

        self.sk = QLineEdit()
        self.sk.setPlaceholderText("访问密钥 (SK)")
        self.sk.setEchoMode(QLineEdit.Password)

        self.endpoint = QLineEdit()
        self.endpoint.setPlaceholderText("例如: eos-jinan-1.cmecloud.cn")

        layout.addRow("存储桶名称:", QLabel(bucket_name))
        layout.addRow("访问密钥ID (AK):", self.ak)
        layout.addRow("访问密钥 (SK):", self.sk)
        layout.addRow("端点地址:", self.endpoint)

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

        # 尝试加载已有配置
        self.load_config()

    def load_config(self):
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            bucket_section = f"Bucket_{self.bucket_name}"
            if bucket_section in cfg:
                # 加载AK
                if 'ak' in cfg[bucket_section]:
                    self.ak.setText(cfg[bucket_section]['ak'])
                elif 'EOS' in cfg and 'ak' in cfg['EOS']:
                    self.ak.setText(cfg['EOS']['ak'])  # 使用默认AK
                
                # 加载SK
                if 'sk' in cfg[bucket_section]:
                    self.sk.setText(cfg[bucket_section]['sk'])
                elif 'EOS' in cfg and 'sk' in cfg['EOS']:
                    self.sk.setText(cfg['EOS']['sk'])  # 使用默认SK
                
                # 加载Endpoint
                if 'endpoint' in cfg[bucket_section]:
                    self.endpoint.setText(cfg[bucket_section]['endpoint'])
        except Exception as e:
            print(f"[LoadConfig] 加载配置失败: {e}")

    def save(self):
        try:
            cfg = ConfigObj(CONFIG_FILE, encoding="utf-8")
            bucket_section = f"Bucket_{self.bucket_name}"
            if bucket_section not in cfg:
                cfg[bucket_section] = {}

            # 保存AK/SK/Endpoint
            if self.ak.text().strip():
                cfg[bucket_section]["ak"] = self.ak.text().strip()
            if self.sk.text().strip():
                cfg[bucket_section]["sk"] = self.sk.text().strip()
            cfg[bucket_section]["endpoint"] = self.endpoint.text().strip()
            cfg.write()
            QMessageBox.information(self, "成功", f"已保存存储桶 '{self.bucket_name}' 的配置")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Save failed: {str(e)}")
