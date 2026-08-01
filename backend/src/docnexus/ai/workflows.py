"""Stable application facade for the three DocNexus AI workflows."""

from docnexus.ai.document_operations import (
    DocumentAction,
    DocumentOperationPlan,
    FormatAction,
    FormatPlan,
    handle_document_operation,
)
from docnexus.ai.information_extraction import (
    chunk_text as _chunk_text,
)
from docnexus.ai.information_extraction import (
    handle_information_extraction,
)
from docnexus.ai.information_extraction import (
    merge_chunk_extractions as _merge_chunk_extractions,
)
from docnexus.ai.llm import get_chat_llm as _get_llm
from docnexus.ai.table_filling import handle_table_filling

from .contracts import (
    DocumentOperationInput,
    DocumentOperationOutput,
    InformationExtractionInput,
    InformationExtractionOutput,
    TableFillingInput,
    TableFillingOutput,
)


def run_document_workflow(input_data: DocumentOperationInput) -> DocumentOperationOutput:
    return handle_document_operation(input_data)


def run_information_extraction_workflow(
    input_data: InformationExtractionInput,
) -> InformationExtractionOutput:
    return handle_information_extraction(input_data)


def run_table_filling_workflow(
    input_data: TableFillingInput,
    progress_callback=None,
) -> TableFillingOutput:
    return handle_table_filling(input_data, progress_callback=progress_callback)


# Compatibility aliases for callers that still use the original UI-oriented
# module numbering. Runtime code uses the domain names above.
handle_module_1_format = run_document_workflow
handle_module_2_extract = run_information_extraction_workflow
handle_module_3_fusion = run_table_filling_workflow


__all__ = [
    "DocumentAction",
    "DocumentOperationPlan",
    "FormatAction",
    "FormatPlan",
    "handle_document_operation",
    "handle_information_extraction",
    "handle_table_filling",
    "run_document_workflow",
    "run_information_extraction_workflow",
    "run_table_filling_workflow",
    "handle_module_1_format",
    "handle_module_2_extract",
    "handle_module_3_fusion",
    "_get_llm",
    "_chunk_text",
    "_merge_chunk_extractions",
]
