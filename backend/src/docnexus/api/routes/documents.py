"""Document editing HTTP endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from docnexus.ai.contracts import Mod1_FormatInput
from docnexus.ai.workflows import (
    handle_module_1_format,
)
from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import User

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.post("/doc-chat/upload")
async def doc_chat_upload(
    background_tasks: BackgroundTasks,
    command: str = Form(..., description="自然语言指令，例如：'把第一段变成红色字体，并且加粗'"),
    document: UploadFile = File(..., description="Word 文档文件 (.docx)"),
    current_user: User = Depends(get_current_user),
):
    """
    【模块一】文档智能操作交互

    通过自然语言指令对文档进行编辑、排版、格式调整等操作
    """
    try:
        # 0. 校验文件类型
        if not document.filename.lower().endswith(".docx"):
            raise HTTPException(400, "仅支持 .docx 文件进行格式调整")

        # 1. 保存上传的文件到临时目录
        temp_dir = Path(tempfile.gettempdir()) / f"doc_chat_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(document.filename).name
        file_path = temp_dir / safe_filename
        with open(file_path, "wb") as f:
            content = await document.read()
            f.write(content)

        # 2. 调用 ai_core engine 的模块一处理函数
        input_data = Mod1_FormatInput(
            file_path=str(file_path),
            natural_language_cmd=command
        )

        result = await run_in_threadpool(handle_module_1_format, input_data)

        # 3. 返回处理后的文件，并设置后台任务删除临时目录
        if result.status == "success":
            def cleanup_temp():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug("Cleaned temporary directory: %s", temp_dir)
                except Exception as e:
                    logger.warning("Failed to clean temporary directory %s: %s", temp_dir, e)

            background_tasks.add_task(cleanup_temp)

            # 处理中文文件名编码
            filename = f"formatted_{safe_filename}"
            encoded_filename = quote(filename)

            return FileResponse(
                result.processed_file_path,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
        else:
            raise HTTPException(500, f"文档操作失败：{result.message}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"文档操作失败：{str(e)}")
