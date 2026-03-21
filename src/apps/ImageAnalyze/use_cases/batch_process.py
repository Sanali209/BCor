from __future__ import annotations

from ..domain.models import ImageAnalysisRecord, ProcessingResult, Rule
from ..infrastructure.sqlite_repo import SqliteImageRepo
from ..domain.interfaces.image_processor import IImageProcessor


class ExecuteBatchRulesUseCase:
    """Юзкейс для пакетной обработки изображений.
    Применяет правила к каждому изображению, используя процессор.
    """

    def __init__(self, repo: SqliteImageRepo, processor: IImageProcessor) -> None:
        self.repo = repo
        self.processor = processor

    async def execute(self, rules: list[Rule], dry_run: bool = False) -> list[ProcessingResult]:
        # 1. Fetch images from repo
        images = self.repo.get_all()

        results = []
        for record in images:
            for rule in rules:
                if rule.condition.evaluate(record):
                    # We use the processor to execute the action intent
                    res = self.processor.execute(record, rule.action, dry_run=dry_run)
                    results.append(res)

                    # If action was successful and not a dry run, we might need to update DB
                    # (e.g. if file was deleted)
                    if not dry_run and res.success:
                        if res.action_taken == "DELETE":
                            self.repo.clear() # For simplicity, force fresh scan after deletes 
                        elif res.action_taken == "CONVERT":
                            # In a real app we'd update specifically, but for now we follow the pattern
                            pass

                    if res.action_taken == "DELETE" and res.success and not dry_run:
                        break  # Stop processing deleted file
        return results
