import hashlib

# 密码加密/解密函数
def hash_password(password):
    """使用SHA256哈希加密密码"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password, hashed):
    """验证密码"""
    return hash_password(password) == hashed
