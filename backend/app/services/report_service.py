"""Report generation service."""

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.crud.topic import analysis_run_repository, topic_repository
from app.models.report import Report
from app.models.user import User
from app.reporting.base import ReportBuilder
from app.schemas.report import ReportCreate

logger = get_logger(__name__)

report_builder = ReportBuilder()


class ReportService:
    """Service for generating and managing reports."""

    async def create_report(
        self,
        db: AsyncSession,
        *,
        obj_in: ReportCreate,
        user: User,
    ) -> Report:
        """Create and generate a report for a topic."""
        topic = await topic_repository.get_or_404_for_organization(
            db, obj_in.topic_id, user.organization_id
        )
        report_repo = BaseRepository(Report)
        report = await report_repo.create(
            db,
            obj_in={
                **obj_in.model_dump(),
                "status": "generating",
                "organization_id": user.organization_id,
                "approved_by_user_id": None,
                "is_approved": False,
            },
        )
        await db.commit()
        await db.refresh(report)

        try:
            await self._generate_report(db, report=report, topic=topic, user=user)
            report.status = "completed"
        except Exception as exc:
            report.status = "failed"
            report.error_message = str(exc)
            logger.exception("report_generation_failed", report_id=report.id, error=str(exc))

        await db.commit()
        await db.refresh(report)
        return report

    async def _generate_report(
        self,
        db: AsyncSession,
        *,
        report: Report,
        topic: Any,
        user: User,
    ) -> None:
        """Generate report content and save to storage."""
        runs = await analysis_run_repository.get_by_topic(db, topic.id, limit=10)
        results: list[dict[str, Any]] = []
        for run in runs:
            for result in run.results:
                results.append(
                    {
                        "result_type": result.result_type,
                        "score": result.score,
                        "summary": result.summary,
                        "details": result.details,
                    }
                )

        summary = f"Report for {topic.name} based on {len(results)} analysis results."
        generated_at = datetime.now(timezone.utc).isoformat()
        markdown_content = await report_builder.build_markdown(
            title=report.title,
            topic_name=topic.name,
            organization_name=user.organization.name if user.organization else "",
            summary=summary,
            results=results,
            sources=topic.sources,
            generated_at=generated_at,
        )

        storage_path = settings.LOCAL_STORAGE_PATH
        os.makedirs(storage_path, exist_ok=True)
        base_name = f"report_{report.id}_{report.format}"

        if report.format == "markdown":
            file_path = os.path.join(storage_path, f"{base_name}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        elif report.format == "pdf":
            file_path = os.path.join(storage_path, f"{base_name}.pdf")
            html = await report_builder.build_html(markdown_content)
            try:
                from weasyprint import HTML

                HTML(string=html).write_pdf(file_path)
            except Exception as exc:
                logger.error("pdf_generation_failed", error=str(exc))
                file_path = os.path.join(storage_path, f"{base_name}.md")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
        elif report.format == "docx":
            file_path = os.path.join(storage_path, f"{base_name}.docx")
            await report_builder.build_docx(markdown_content, file_path)
        elif report.format == "pptx":
            file_path = os.path.join(storage_path, f"{base_name}.pptx")
            slides = [
                {"title": r["result_type"], "content": r.get("summary", "")}
                for r in results[:10]
            ]
            await report_builder.build_pptx(report.title, slides, file_path)
        else:
            raise AppException(f"Unsupported report format: {report.format}")

        report.file_path = file_path
        report.file_size = os.path.getsize(file_path)
        report.download_url = f"/storage/{os.path.basename(file_path)}"


report_service = ReportService()
