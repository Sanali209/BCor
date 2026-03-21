import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...domain.models import AreaCondition, ConvertAction, DeleteAction, FormatCondition, Rule, SizeCondition
from ...use_cases import ExecuteBatchRulesUseCase


class BatchOperationsWidget(QWidget):
    def __init__(self, batch_use_case: ExecuteBatchRulesUseCase) -> None:
        super().__init__()
        self.batch_use_case = batch_use_case
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. Configuration Area
        config_group = QGroupBox("Batch Operation Configuration")
        config_layout = QFormLayout(config_group)

        self.condition_type = QComboBox()
        self.condition_type.addItems(["Size (Bytes)", "Area (Pixels)", "Format"])
        config_layout.addRow("Filter By:", self.condition_type)

        self.min_val = QSpinBox()
        self.min_val.setRange(0, 10**9)
        config_layout.addRow("Minimum:", self.min_val)

        self.action_type = QComboBox()
        self.action_type.addItems(["Convert to JPG", "Delete File"])
        config_layout.addRow("Action:", self.action_type)

        self.dry_run_cb = QCheckBox("Dry Run (Safe)")
        self.dry_run_cb.setChecked(True)
        config_layout.addRow(self.dry_run_cb)

        self.run_btn = QPushButton("Execute Batch Job")
        self.run_btn.setStyleSheet("background-color: #e94560; color: white;")
        self.run_btn.clicked.connect(self.run_batch)
        config_layout.addRow(self.run_btn)

        layout.addWidget(config_group)

        # 2. Results Area
        results_group = QGroupBox("Execution Results")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(["Path", "Action", "Status", "Savings"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)

        layout.addWidget(results_group)

    def run_batch(self) -> None:
        asyncio.create_task(self._execute_batch())

    async def _execute_batch(self) -> None:
        # Build Rule based on UI
        cond_type = self.condition_type.currentText()
        condition: AreaCondition | SizeCondition | FormatCondition | Any
        if "Size" in cond_type:
            condition = SizeCondition(min_bytes=self.min_val.value())
        elif "Area" in cond_type:
            condition = AreaCondition(min_area=self.min_val.value())
        else:
            condition = FormatCondition([".png"]) # Example

        act_type = self.action_type.currentText()
        action: DeleteAction | ConvertAction | Any
        if "Convert" in act_type:
            action = ConvertAction(target_format=".jpg", delete_original=True)
        else:
            action = DeleteAction()

        rule = Rule(condition=condition, action=action)
        
        # Execute
        try:
            logger.info(f"Executing batch job with rule: {rule}, dry_run: {self.dry_run_cb.isChecked()}")
            results = await self.batch_use_case.execute([rule], dry_run=self.dry_run_cb.isChecked())
            logger.info(f"Batch job completed. {len(results)} results received.")
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            return

        # Update Table
        self.results_table.setRowCount(0)
        for res in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(res.original_path))
            self.results_table.setItem(row, 1, QTableWidgetItem(res.action_taken))
            self.results_table.setItem(row, 2, QTableWidgetItem("Success" if res.success else f"Error: {res.error_message}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{res.saved_bytes / 1024:.2f} KB"))
