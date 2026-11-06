from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


def prepare_image(data: bytes, filename: str, *, max_bytes: int, max_dimension: int) -> tuple[bytes, str]:
    """Validate, orient, resize, and re-encode an image without its EXIF metadata."""
    if not data or len(data) > max_bytes:
        raise ValueError("이미지 크기는 1바이트 이상, 설정된 업로드 한도 이하여야 합니다.")
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        raise ValueError("JPG, PNG, WebP 파일만 사용할 수 있습니다.")
    try:
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("파일 내용을 이미지로 읽을 수 없습니다.") from exc
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, format="JPEG", quality=86, optimize=True)
    return output.getvalue(), "image/jpeg"
