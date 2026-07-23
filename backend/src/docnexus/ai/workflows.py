"""Stable application facade for the three DocNexus AI workflows."""

from docnexus.ai.document_operations import FormatAction, FormatPlan, handle_document_operation
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


def handle_module_1_format(input_data: DocumentOperationInput) -> DocumentOperationOutput:
    return handle_document_operation(input_data)


def handle_module_2_extract(input_data: InformationExtractionInput) -> InformationExtractionOutput:
    return handle_information_extraction(input_data)


def handle_module_3_fusion(input_data: TableFillingInput, progress_callback=None) -> TableFillingOutput:
    return handle_table_filling(input_data, progress_callback=progress_callback)


__all__ = [
    "FormatAction",
    "FormatPlan",
    "handle_document_operation",
    "handle_information_extraction",
    "handle_table_filling",
    "handle_module_1_format",
    "handle_module_2_extract",
    "handle_module_3_fusion",
    "_get_llm",
    "_chunk_text",
    "_merge_chunk_extractions",
]
