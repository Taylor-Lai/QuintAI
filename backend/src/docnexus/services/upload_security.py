"""统一的上传文件校验与安全落盘。"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile

from docnexus.core.settings import get_settings

CHUNK_SIZE = 1024 * 1024
SAFE_FILENAME_PATTERN = re.compile(r"[^\w.()\-\u4e00-\u9fff]+", re.UNICODE)


def safe_filename(filename: str | None) -> str:
    name = Path(filename or "").name.strip().replace("\x00", "")
    name = SAFE_FILENAME_PATTERN.sub("_", name)
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="文件名无效")
    return name[:180]


def validate_file_count(count: int) -> None:
    maximum = get_settings().max_upload_files
    if count < 1:
        raise HTTPException(status_code=400, detail="至少需要上传一个文件")
    if count > maximum:
        raise HTTPException(status_code=413, detail=f"一次最多上传 {maximum} 个文件")


async def read_upload_limited(upload: UploadFile) -> bytes:
    maximum = get_settings().max_upload_bytes
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(CHUNK_SIZE):
        total += len(chunk)
        if total > maximum:
            raise HTTPException(status_code=413, detail=f"单个文件不能超过 {maximum // 1024 // 1024} MB")
        chunks.append(chunk)
    return b"".join(chunks)


def _validate_office_archive(content: bytes, suffix: str) -> None:
    settings = get_settings()
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > settings.max_archive_entries:
                raise HTTPException(status_code=400, detail="Office 文件包含过多内部条目")
            total_size = 0
            names: set[str] = set()
            for entry in entries:
                normalized = entry.filename.replace("\\", "/")
                if normalized.startswith("/") or "../" in f"/{normalized}":
                    raise HTTPException(status_code=400, detail="Office 文件包含不安全路径")
                if entry.flag_bits & 0x1:
                    raise HTTPException(status_code=400, detail="不支持加密的 Office 文件")
                total_size += entry.file_size
                if total_size > settings.max_archive_uncompressed_bytes:
                    raise HTTPException(status_code=413, detail="Office 文件解压后体积过大")
                names.add(normalized)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Office 文件结构无效") from exc

    required = "word/document.xml" if suffix == ".docx" else "xl/workbook.xml"
    if required not in names or "[Content_Types].xml" not in names:
        raise HTTPException(status_code=400, detail=f"文件内容不是有效的 {suffix} 文档")


def validate_upload_content(filename: str, content: bytes, allowed_extensions: set[str]) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions:
        supported = "、".join(sorted(allowed_extensions))
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，允许：{supported}")
    if not content:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if suffix in {".docx", ".xlsx"}:
        _validate_office_archive(content, suffix)
    elif b"\x00" in content[:4096]:
        raise HTTPException(status_code=400, detail="文本文件包含非法二进制内容")
    return suffix


async def save_upload_safely(
    upload: UploadFile,
    destination: Path,
    allowed_extensions: set[str],
) -> tuple[Path, int]:
    name = safe_filename(upload.filename)
    content = await read_upload_limited(upload)
    validate_upload_content(name, content, allowed_extensions)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / name
    path.write_bytes(content)
    return path, len(content)
