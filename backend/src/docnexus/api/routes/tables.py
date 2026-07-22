"""Table filling HTTP endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path
from typing import List
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
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from docnexus.ai.contracts import Mod3_FusionInput
from docnexus.ai.workflows import (
    handle_module_3_fusion,
)
from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.repositories.extractions import ExtractionRepository
from docnexus.services.document_parser import DocumentParser
from docnexus.services.llm_extractor import LLMExtractor
from docnexus.services.table_filler import TableFiller

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.post("/table-fill/simple")
async def fill_table_simple(
    document: UploadFile = File(..., description="源文档"),
    fields: str = Form(..., description="需要提取的字段，用逗号分隔"),
    db: Session = Depends(get_db),
):
    """
    【简化版】不上传模板，自动生成 Excel 并填写
    """
    try:
        # 1. 解析文档
        parse_result = await DocumentParser.parse_file(document)
        text_content = parse_result["content"]

        # 2. 处理字段（支持中英文逗号）
        # [OK] 关键修复：确保正确分割
        fields_list = [
            f.strip() for f in fields.replace("，", ",").split(",") if f.strip()
        ]

        logger.debug("Requested simple extraction fields: %s", fields_list)

        if not fields_list:
            raise HTTPException(400, "请至少指定一个填写字段")

        # 3. 提取数据
        extracted_data = LLMExtractor.extract_info(text_content, fields_list)

        if "error" in extracted_data:
            raise HTTPException(500, f"AI 提取失败：{extracted_data['error']}")

        logger.debug("Simple extraction completed with %s field(s)", len(extracted_data))

        # 4. 自动生成模板并填充
        logger.debug("Creating simple template with %s field(s)", len(fields_list))
        template_bytes = TableFiller.create_template_from_fields(fields_list)

        filled_file = TableFiller.fill_template(
            template_bytes=template_bytes.getvalue(), extracted_data=extracted_data
        )

        # 5. 保存提取记录到数据库
        ExtractionRepository.save_extraction(
            db=db,
            filename=parse_result["filename"],
            file_type=parse_result["file_type"],
            fields_requested=fields_list,
            extracted_data=extracted_data,
            content_preview=text_content,
            status="success",
        )

        # 6. 返回文件
        filename = f"auto_filled_{document.filename.split('.')[0]}.xlsx"
        encoded_filename = quote(filename)

        return StreamingResponse(
            filled_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        logger.exception("Simple table fill failed")
        raise HTTPException(500, f"填表失败：{str(e)}")


@router.post("/table-fill/upload")
async def table_fill_upload(
    background_tasks: BackgroundTasks,
    template: UploadFile = File(..., description="模板文件 (.xlsx 或 .docx)"),
    documents: List[UploadFile] = File(..., description="源文档 (.docx, .txt, .md 等)"),
    user_request: str = Form("", description="用户的附加自然语言要求（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    【模块三】表格自定义数据填写（多源融合填表）

    上传 Excel 模板和源文档，自动提取信息并填写到表格中
    使用多智能体系统进行跨文档特征提取与对齐
    """
    try:
        # 1. 校验模板文件类型
        ALLOWED_TEMPLATE_EXTS = {".xlsx", ".docx"}
        template_ext = Path(template.filename).suffix.lower()
        if template_ext not in ALLOWED_TEMPLATE_EXTS:
            raise HTTPException(400, f"模板文件必须是 .xlsx 或 .docx 格式，当前为 {template_ext}")

        # 2. 创建工作空间目录
        workspace_dir = Path(tempfile.gettempdir()) / f"table_fill_{uuid.uuid4().hex[:8]}"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # 3. 保存模板文件
        safe_template_name = Path(template.filename).name
        template_path = workspace_dir / f"模板_{safe_template_name}"
        with open(template_path, "wb") as f:
            content = await template.read()
            f.write(content)

        # 4. 保存源文档
        source_files = []
        for index, document in enumerate(documents):
            safe_document_name = Path(document.filename).name
            doc_path = workspace_dir / f"source_{index:03d}_{safe_document_name}"
            with open(doc_path, "wb") as f:
                content = await document.read()
                f.write(content)
            source_files.append(doc_path)

        # 5. 调用 ai_core engine 的模块三处理函数
        task_id = str(uuid.uuid4())[:8]
        input_data = Mod3_FusionInput(
            task_id=task_id,
            workspace_dir=str(workspace_dir),
            user_request=user_request if user_request else None
        )

        result = await run_in_threadpool(handle_module_3_fusion, input_data)

        # 6. 返回填充后的文件，并设置后台任务删除临时目录
        if result.status == "success":
            # 保存记录到数据库
            # 构建文件名列表
            doc_filenames = [Path(doc.filename).name for doc in documents]
            filename_str = f"{safe_template_name} + {', '.join(doc_filenames)}"

            output_path = result.output_excel_path
            output_ext = Path(output_path).suffix.lower()
            if output_ext == ".docx":
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                file_type = "docx"
            else:
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_type = "xlsx"

            ExtractionRepository.save_extraction(
                db=db,
                filename=filename_str,
                file_type=file_type,
                fields_requested=[],
                extracted_data={"output_path": output_path},
                content_preview=f"多源数据融合，生成文件：{output_path}",
                status="success",
            )

            def cleanup_temp():
                import shutil
                try:
                    shutil.rmtree(workspace_dir)
                    logger.debug("Cleaned temporary directory: %s", workspace_dir)
                except Exception as e:
                    logger.warning("Failed to clean temporary directory %s: %s", workspace_dir, e)

            background_tasks.add_task(cleanup_temp)

            filename = f"filled_{safe_template_name}"
            encoded_filename = quote(filename)
            logger.info("Generated output file: %s", output_path)
            return FileResponse(
                output_path,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
        else:
            raise HTTPException(500, f"表格填写失败：{result.error_msg}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"表格填写失败：{str(e)}")
