"""DocNexus AI modules with lazy public exports."""

__all__ = [
    "FormatAction",
    "FormatPlan",
    "handle_document_operation",
    "handle_information_extraction",
    "handle_table_filling",
]


def __getattr__(name: str):
    if name in {"FormatAction", "FormatPlan", "handle_document_operation"}:
        from .document_operations import FormatAction, FormatPlan, handle_document_operation

        exports = {
            "FormatAction": FormatAction,
            "FormatPlan": FormatPlan,
            "handle_document_operation": handle_document_operation,
        }
        return exports[name]
    if name == "handle_information_extraction":
        from .information_extraction import handle_information_extraction

        return handle_information_extraction
    if name == "handle_table_filling":
        from .table_filling import handle_table_filling

        return handle_table_filling
    raise AttributeError(name)
