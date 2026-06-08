from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import Optional
import uuid
import os
from datetime import datetime

from ..database import get_db
from ..models import Image, User
from ..schemas import ImageResponse, ImageUploadResponse, ImageListResponse
from ..auth import get_current_user, oauth2_scheme
from ..config import get_settings
from ..storage import get_storage_backend
from ..image_processor import get_image_processor

settings = get_settings()
storage = get_storage_backend()
image_processor = get_image_processor()

router = APIRouter(prefix="/uploads", tags=["Uploads"])


async def save_image_to_storage(
    processed_images: dict,
    file_path_base: str,
    user_id: int
) -> dict:
    urls = {}
    
    for size_name, image_data in processed_images.items():
        file_path = f"{file_path_base}_{size_name}.webp"
        url = await storage.save(file_path, image_data)
        urls[size_name] = url
    
    return urls


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    is_public: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传图片文件"
        )
    
    file_content = await file.read()
    
    is_valid, error_msg = image_processor.validate_image(file_content, file.content_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        image_info = image_processor.get_image_info(file_content)
        processed_images = image_processor.process_image(file_content, file.content_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    date_str = datetime.now().strftime("%Y/%m/%d")
    file_id = str(uuid.uuid4())[:8]
    original_ext = os.path.splitext(file.filename or "image")[1]
    file_path_base = f"images/{date_str}/{file_id}"
    
    urls = await save_image_to_storage(processed_images, file_path_base, current_user.id)
    
    db_image = Image(
        user_id=current_user.id,
        filename=f"{file_id}.webp",
        original_filename=file.filename or "image",
        file_path=f"{file_path_base}_original.webp",
        file_size=len(processed_images["original"]),
        width=image_info.get("width"),
        height=image_info.get("height"),
        format="WebP",
        thumb_small_url=urls.get("small"),
        thumb_medium_url=urls.get("medium"),
        thumb_large_url=urls.get("large"),
        original_url=urls.get("original"),
        content_type="image/webp",
        is_public=is_public
    )
    
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    
    return ImageUploadResponse(
        success=True,
        message="图片上传成功",
        image=db_image,
        urls=urls
    )


@router.get("/images", response_model=ImageListResponse)
async def get_my_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * page_size
    
    count_result = await db.execute(
        select(func.count(Image.id)).where(Image.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(Image)
        .where(Image.user_id == current_user.id)
        .order_by(desc(Image.created_at))
        .offset(offset)
        .limit(page_size)
    )
    images = result.scalars().all()
    
    return ImageListResponse(
        items=images,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme) if settings.IMAGE_REQUIRE_AUTH else None
):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    if settings.IMAGE_REQUIRE_AUTH and not image.is_public:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证才能访问此图片"
            )
        try:
            from ..auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            if current_user.id != image.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此图片"
                )
        except HTTPException:
            raise
    
    return image


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此图片"
        )
    
    for size_name in ["small", "medium", "large", "original"]:
        file_path = f"{os.path.splitext(image.file_path)[0].rsplit('_', 1)[0]}_{size_name}.webp"
        await storage.delete(file_path)
    
    await db.delete(image)
    await db.commit()
    
    return {"success": True, "message": "图片删除成功"}
