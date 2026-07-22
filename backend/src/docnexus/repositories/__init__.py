"""Persistence repositories isolated from HTTP and domain services."""

from .extractions import ExtractionRepository

__all__ = ["ExtractionRepository"]
