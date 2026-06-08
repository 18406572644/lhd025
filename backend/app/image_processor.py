from io import BytesIO
from typing import Tuple, Dict, Optional
from PIL import Image, ImageOps
from .config import get_settings

settings = get_settings()


class ImageProcessor:
    @staticmethod
    def validate_image(file_content: bytes, content_type: str) -> Tuple[bool, Optional[str]]:
        if content_type not in settings.IMAGE_ALLOWED_TYPES:
            return False, f"不支持的图片格式: {content_type}。支持的格式: {', '.join(settings.IMAGE_ALLOWED_TYPES)}"
        
        if len(file_content) > settings.IMAGE_MAX_SIZE:
            return False, f"图片大小超过限制: {len(file_content) / 1024 / 1024:.2f}MB。最大允许: {settings.IMAGE_MAX_SIZE / 1024 / 1024:.0f}MB"
        
        try:
            with Image.open(BytesIO(file_content)) as img:
                img.verify()
            return True, None
        except Exception as e:
            return False, f"图片验证失败: {str(e)}"

    @staticmethod
    def process_image(
        file_content: bytes,
        content_type: str,
        target_format: str = "WebP",
        quality: Optional[int] = None
    ) -> Dict[str, bytes]:
        quality = quality or settings.IMAGE_QUALITY
        results = {}
        
        try:
            img = Image.open(BytesIO(file_content))
            img = ImageOps.exif_transpose(img)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            for size_name, (max_width, max_height) in settings.IMAGE_THUMBNAIL_SIZES.items():
                resized_img = ImageProcessor._resize_image(img.copy(), max_width, max_height)
                
                output = BytesIO()
                resized_img.save(output, format=target_format, quality=quality, optimize=True)
                results[size_name] = output.getvalue()
            
            output = BytesIO()
            img.save(output, format=target_format, quality=quality, optimize=True)
            results["original"] = output.getvalue()
            
            return results
            
        except Exception as e:
            raise ValueError(f"图片处理失败: {str(e)}")

    @staticmethod
    def _resize_image(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        width, height = img.size
        ratio = min(max_width / width, max_height / height)
        
        if ratio < 1:
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img

    @staticmethod
    def get_image_info(file_content: bytes) -> Dict:
        try:
            with Image.open(BytesIO(file_content)) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
        except Exception as e:
            raise ValueError(f"获取图片信息失败: {str(e)}")


def get_image_processor() -> ImageProcessor:
    return ImageProcessor()
