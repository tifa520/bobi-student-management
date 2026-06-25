# backend/app/services/image_service.py
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image
from io import BytesIO
from loguru import logger

class ImageService:
    # 项目根目录（backend 所在目录）
    BASE_DIR = Path(__file__).parent.parent.parent
    MEDIA_ROOT = BASE_DIR / "media"   # /app/media
    
    CONFIG = {
        "avatar": {
            "subdir": "avatars",
            "max_width": 200,
            "max_height": 200,
            "quality": 85,
            "max_size_mb": 2
        },
        "card_bg": {
            "subdir": "card_bg",
            "max_width": 800,
            "max_height": 400,
            "quality": 80,
            "max_size_mb": 0.5
        },
        "user_avatar": {
            "subdir": "user_avatars",
            "max_width": 200,
            "max_height": 200,
            "quality": 85,
            "max_size_mb": 2
        },
        "item_image": {
            "subdir": "items",
            "max_width": 400,
            "max_height": 400,
            "quality": 85,
            "max_size_mb": 2
        },
        "login_bg": {
            "subdir": "login_bg",
            "max_width": 1920,
            "max_height": 1080,
            "quality": 85,
            "max_size_mb": 5
        },
        "activity_image": {
            "subdir": "activities",
            "max_width": 1920,
            "max_height": 1080,
            "quality": 85,
            "max_size_mb": 5
        },
    }
    
    @classmethod
    def _get_full_path(cls, subdir: str, filename: str) -> Path:
        return cls.MEDIA_ROOT / subdir / filename
    
    @classmethod
    async def save(cls, file: UploadFile, category: str) -> str:
        """保存图片，返回相对路径（如 'avatars/xxx.jpg'）"""
        config = cls.CONFIG.get(category)
        if not config:
            raise HTTPException(400, f"不支持的图片类型: {category}")
        
        # 1. 文件大小校验
        file.file.seek(0, 2)
        size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)
        if size_mb > config["max_size_mb"]:
            raise HTTPException(400, f"图片大小不能超过 {config['max_size_mb']}MB")
        
        # 2. 读取图片
        content = await file.read()
        try:
            image = Image.open(BytesIO(content))
        except Exception:
            raise HTTPException(400, "无效的图片文件")
        
        # 3. 转换为 RGB（处理透明通道）
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 4. 缩放
        max_w, max_h = config["max_width"], config["max_height"]
        ratio = min(max_w / image.width, max_h / image.height)
        if ratio < 1:
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 5. 生成唯一文件名
        ext = '.jpg'
        filename = f"{uuid.uuid4().hex}{ext}"
        subdir = config["subdir"]
        full_path = cls._get_full_path(subdir, filename)
        
        # 6. 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 7. 保存
        image.save(full_path, quality=config["quality"], optimize=True)
        
        # 8. 返回相对路径（如 "avatars/xxx.jpg"）
        return f"{subdir}/{filename}"
    
    @classmethod
    def delete(cls, relative_path: str) -> bool:
        """删除图片文件（相对路径）"""
        if not relative_path:
            return False
        # 防止路径遍历攻击：只允许子目录和文件名
        if '..' in relative_path or relative_path.startswith('/'):
            logger.warning(f"非法路径尝试删除: {relative_path}")
            return False
        full_path = cls.MEDIA_ROOT / relative_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    @classmethod
    def get_url(cls, relative_path: str) -> str:
        if not relative_path:
            return ""
        # 如果已经是 /media/ 开头的完整路径，直接返回
        if relative_path.startswith("/media/"):
            return relative_path
        # 如果以 http 开头，直接返回（外部链接）
        if relative_path.startswith("http"):
            return relative_path
        # 否则拼接 /media/
        return f"/media/{relative_path}"