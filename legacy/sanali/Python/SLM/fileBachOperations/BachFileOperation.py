# DEPRECATED: This module has been modernized and moved to BCor Common.
# Please use 'src.common.files.batch_pipeline' for Batch Action Pipelines.
# The new implementation is async-native and fully VFS-aware (PyFilesystem2).

from src.common.files.batch_pipeline import BatchPipeline, BatchItem, BatchAction 

__all__ = ["BatchPipeline", "BatchItem", "BatchAction"]
