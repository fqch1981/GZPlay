import hmac
import hashlib
import base64
import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EosClient:
    def __init__(self, ak, sk, endpoint):
        self.ak = ak
        self.sk = sk
        self.endpoint = endpoint.strip("https://").strip("http://")
        print(f"[EOS] 初始化客户端: endpoint={self.endpoint}, ak={ak[:8]}...")

    def _generate_signature(self, method, resource, date):
        """生成EOS签名（S3 V2签名算法）"""
        # S3 V2签名字符串格式: HTTP-VERB\n\n\nDate\nCanonicalizedResource
        string_to_sign = f"{method}\n\n\n{date}\n{resource}"
        print(f"[EOS] 签名字符串: {repr(string_to_sign)}")

        # 使用HMAC-SHA1进行签名
        h = hmac.new(self.sk.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
        signature = base64.b64encode(h.digest()).decode()
        return signature

    def list_all_buckets(self):
        """列出所有桶"""
        try:
            print("[EOS] 正在列出所有桶...")
            date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            resource = "/"
            signature = self._generate_signature("GET", resource, date)

            headers = {
                "Date": date,
                "Authorization": f"AWS {self.ak}:{signature}"
            }

            url = f"http://{self.endpoint}/"
            print(f"[EOS] 请求URL: {url}")
            print(f"[EOS] Authorization: {headers['Authorization']}")

            r = requests.get(url, headers=headers, timeout=10)
            print(f"[EOS] 响应状态码: {r.status_code}")
            print(f"[EOS] 响应内容: {r.text[:500]}...")

            r.raise_for_status()
            root = ET.fromstring(r.text)
            ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
            buckets = []
            for b in root.findall(ns + "Buckets/" + ns + "Bucket"):
                name = b.find(ns + "Name").text
                buckets.append(name)
                print(f"[EOS] 找到桶: {name}")

            print(f"[EOS] 共找到 {len(buckets)} 个桶")
            return buckets

        except Exception as e:
            print(f"[EOS] 列出桶失败: {str(e)}")
            raise

    def list_objects(self, bucket, prefix="", delimiter="/", max_keys=1000):
        """列出桶内对象"""
        try:
            print(f"[EOS] 正在列出桶 '{bucket}' 的对象，前缀: '{prefix}'")

            # 构建查询参数（需要按字母顺序排序）
            params = []
            if delimiter:
                params.append(f"delimiter={quote(delimiter)}")
            if max_keys:
                params.append(f"max-keys={max_keys}")
            if prefix:
                params.append(f"prefix={quote(prefix)}")
            query_string = "&".join(params)

            # S3 V2签名：资源字符串不包含查询参数
            # 注意：移动云可能需要 /bucket 而不是 /bucket/
            resource = f"/{bucket}"
            date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            signature = self._generate_signature("GET", resource, date)

            headers = {
                "Date": date,
                "Authorization": f"AWS {self.ak}:{signature}"
            }

            url = f"http://{self.endpoint}/{bucket}?{query_string}"
            print(f"[EOS] 请求URL: {url}")
            print(f"[EOS] 签名资源: {resource}")

            r = requests.get(url, headers=headers, timeout=15)
            print(f"[EOS] 响应状态码: {r.status_code}")
            r.raise_for_status()

            print(f"[EOS] 成功获取对象列表")
            return r.text

        except Exception as e:
            print(f"[EOS] 列出对象失败: {str(e)}")
            raise

    def generate_presigned_url(self, bucket, key, expires_in=3600):
        """生成预签名URL - 使用GET参数方式"""
        try:
            # 计算过期时间（Unix时间戳）
            expiration = int((datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).timestamp())

            # 构建预签名URL，使用AWS Signature V2 Query String Authentication
            # 资源路径
            resource = f"/{bucket}/{quote(key, safe='/')}"

            # 按S3 V2 Query String Authentication格式构建签名字符串
            # 格式: GET\n\n\n{Expires}\n{CanonicalizedResource}
            string_to_sign = f"GET\n\n\n{expiration}\n{resource}"
            print(f"[EOS] 预签名签名字符串: {repr(string_to_sign)}")

            # 使用HMAC-SHA1进行签名
            h = hmac.new(self.sk.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
            signature = base64.b64encode(h.digest()).decode()

            # 构建预签名URL（AWS V2格式）
            url = f"http://{self.endpoint}{resource}?AWSAccessKeyId={self.ak}&Expires={expiration}&Signature={quote(signature)}"
            print(f"[EOS] 预签名URL: {url}")
            return url

        except Exception as e:
            print(f"[EOS] 生成预签名URL失败: {str(e)}")
            raise

    def generate_direct_url(self, bucket, key):
        """生成直接访问URL（带签名header，用于内部使用）"""
        try:
            resource = f"/{bucket}/{quote(key, safe='/')}"
            date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            signature = self._generate_signature("GET", resource, date)

            return {
                'url': f"http://{self.endpoint}{resource}",
                'headers': {
                    "Date": date,
                    "Authorization": f"AWS {self.ak}:{signature}"
                }
            }
        except Exception as e:
            print(f"[EOS] 生成直接访问URL失败: {str(e)}")
            raise
