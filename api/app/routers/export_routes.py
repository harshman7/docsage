"""Export downloads."""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.deps import get_current_user
from app.models import User
from app.services.export_service import export_to_excel, export_summary_report

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/excel")
def export_excel(current_user: User = Depends(get_current_user)):
    buf = export_to_excel(user_id=current_user.id)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="docsage_export.xlsx"'},
    )


@router.get("/summary")
def export_summary(current_user: User = Depends(get_current_user)):
    text = export_summary_report(user_id=current_user.id)
    return StreamingResponse(
        iter([text.encode("utf-8")]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="summary_report.md"'},
    )
