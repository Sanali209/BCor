"""
DuckDuckGo Image Search - SLM Framework Reimplementation

A modern, async-first image search application built on the SLM Core Framework
with advanced features including settings persistence, thumbnail caching, and
unified progress reporting.
"""

__version__ = "1.0.0"
__author__ = "SLM Framework"

from .app import ImageSearchSLMApp

__all__ = ["ImageSearchSLMApp"]
