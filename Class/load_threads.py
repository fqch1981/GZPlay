import xml.etree.ElementTree as ET
from PySide6.QtCore import QThread, Signal


class LoadBucketThread(QThread):
    result = Signal(list)
    error = Signal(str)
    def __init__(self, client):
        super().__init__()
        self.client = client
    def run(self):
        try:
            buckets = self.client.list_all_buckets()
            self.result.emit(buckets)
        except Exception as e:
            self.error.emit(str(e))


class LoadObjectsThread(QThread):
    result = Signal(str, dict)
    error = Signal(str)
    progress = Signal(str)  # 添加进度信号
    def __init__(self, client, bucket):
        super().__init__()
        self.client = client
        self.bucket = bucket
        self.visited = set()  # 记录已访问的路径
    def run(self):
        try:
            tree = {}
            def walk(prefix=""):
                # 避免重复访问
                if prefix in self.visited:
                    return
                self.visited.add(prefix)

                self.progress.emit(f"正在扫描: {prefix or '根目录'}")
                print(f"[LoadObjects] 扫描路径: '{prefix}'")

                xml = self.client.list_objects(self.bucket, prefix)
                ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
                root = ET.fromstring(xml)

                # 获取所有子文件夹（CommonPrefixes）
                for cp in root.findall(ns + "CommonPrefixes"):
                    pre = cp.find(ns + "Prefix").text
                    name = pre.rstrip("/").split("/")[-1]
                    tree[pre] = {"t":"d","n":name}
                    print(f"[LoadObjects] 找到目录: {name} (路径: {pre})")
                    walk(pre)

                # 获取所有文件（Contents）
                for c in root.findall(ns + "Contents"):
                    k = c.find(ns + "Key").text
                    # 只添加视频文件
                    if k.lower().endswith((".mp4",".mov",".avi",".mkv",".flv",".wmv",".mpg",".mpeg")):
                        tree[k] = {"t":"f","n":k.split("/")[-1]}
                        print(f"[LoadObjects] 找到视频: {k.split('/')[-1]}")

            walk("")
            print(f"[LoadObjects] 扫描完成，共 {len([v for v in tree.values() if v['t']=='d'])} 个目录, {len([v for v in tree.values() if v['t']=='f'])} 个视频")
            self.result.emit(self.bucket, tree)
        except Exception as e:
            print(f"[LoadObjects] 错误: {str(e)}")
            self.error.emit(str(e))
