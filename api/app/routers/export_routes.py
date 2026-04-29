"""Export downloads."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.export_service import export_to_excel, export_summary_report

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/excel")
def export_excel():
    buf = export_to_excel()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="docsage_export.xlsx"'},
    )


@router.get("/summary")
def export_summary():
    text = export_summary_report()
    return StreamingResponse(
        iter([text.encode("utf-8")]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="summary_report.md"'},
    )
