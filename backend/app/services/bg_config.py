import json
import os
from app.models import SystemConfig

CONFIG_FILE = "data/login_bg.json"
CONFIG_KEY = "login_bg_url"

def save_bg_url(url: str, db=None):
    """保存背景图片URL，同时写入文件和数据库"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"url": url}, f)
    if db:
        config = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
        if not config:
            config = SystemConfig(key=CONFIG_KEY, value=url, description="登录页背景图片URL")
            db.add(config)
        else:
            config.value = url
        db.commit()

def get_bg_url(db=None) -> str:
    if db:
        config = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
        if config and config.value:
            return config.value
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("url", "")
    except:
        return ""