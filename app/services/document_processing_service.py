import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.document_page import DocumentPage
from app.models.user import User
from app.services.document_service import get_user_document
from app.services.pdf_processing_service import PdfProcessingError, extract_pdf_pages


class DocumentProcessingError(RuntimeError):
    pass


def get_processable_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return get_user_document(db, document_id, owner)


def list_document_pages(
    db: Session,
    document: Document,
) -> list[DocumentPage]:
    return (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number.asc())
        .all()
    )


def process_document(
    db: Session,
    document: Document,
) -> Document:
    if not Path(document.file_path).exists():
        _mark_document_failed(db, document)
        raise DocumentProcessingError("Document file was not found")

    try:
        document.status = DocumentStatus.PROCESSING
        db.add(document)
        db.commit()
        db.refresh(document)

        db.query(DocumentPage).filter(DocumentPage.document_id == document.id).delete(
            synchronize_session=False
        )
        db.flush()

        extracted_pages = extract_pdf_pages(document.file_path)

        for page in extracted_pages:
            db.add(
                DocumentPage(
                    document_id=document.id,
                    page_number=page["page_number"],
                    text=page["text"],
                )
            )

        document.total_pages = len(extracted_pages)
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.now(timezone.utc)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except (PdfProcessingError, OSError, ValueError) as exc:
        db.rollback()
        _mark_document_failed(db, document)
        raise DocumentProcessingError(str(exc)) from exc
    except Exception:
        db.rollback()
        _mark_document_failed(db, document)
        raise


def _mark_document_failed(db: Session, document: Document) -> None:
    document.status = DocumentStatus.FAILED
    db.add(document)
    db.commit()
    db.refresh(document)
