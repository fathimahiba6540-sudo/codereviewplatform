"""
pdf_tools.py — API Router for PDF Processing & Exam-Oriented Summarization
"""

import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, status, HTTPException
from fastapi.responses import FileResponse
from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.models.schemas import APIResponse, PDFSummaryResponse
from backend.app.routers.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.services.pdf_summary_service import pdf_summary_service

router = APIRouter(prefix="/pdf", tags=["PDF Processing & Exam Summarizer"])


@router.post(
    "/summarize-bundle",
    response_model=APIResponse[PDFSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload single or multiple PDF documents, combine text, and generate exam-oriented high-yield summary"
)
async def summarize_pdf_bundle(
    files: List[UploadFile] = FastAPIFile(...),
    current_user: User = Depends(get_current_active_user)
):
    """Combine text from uploaded PDF bundle and generate exam-oriented summary."""
    if not files:
        raise AppException(message="No PDF files provided", code="NO_FILES")

    pdf_data = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise AppException(message=f"File {file.filename} is not a valid PDF document", code="INVALID_FILE_TYPE")
        content = await file.read()
        pdf_data.append((file.filename, content))

    res = pdf_summary_service.process_pdf_bundle(pdf_data)

    return APIResponse(
        message=f"Successfully processed {len(files)} PDF documents and generated exam-oriented summary",
        data=res
    )


@router.get(
    "/download-merged/{bundle_id}",
    summary="Download merged PDF document bundle"
)
def download_merged_pdf(
    bundle_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download the combined/merged PDF document for a bundle."""
    file_path = os.path.join(settings.UPLOAD_DIR, "pdf_bundles", f"bundle_{bundle_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Merged PDF bundle not found")

    return FileResponse(
        path=file_path,
        filename=f"merged_study_bundle_{bundle_id[:8]}.pdf",
        media_type="application/pdf"
    )
