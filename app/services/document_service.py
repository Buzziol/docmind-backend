import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.models.workspace import Workspace

PDF_CONTENT_TYPE = "application/pdf"
PDF_EXTENSION = ".pdf"
CHUNK_SIZE = 1024 * 1024


class InvalidDocumentUploadError(ValueError):
    pass


def get_owned_workspace(
    db: Session,
    workspace_id: uuid.UUID,
    owner: User,
) -> Workspace | None:
    return (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.owner_id == owner.id)
        .first()
    )


def validate_pdf_upload(file: UploadFile) -> None:
    filename = file.filename or ""
    if file.content_type != PDF_CONTENT_TYPE:
        raise InvalidDocumentUploadError("Only PDF files are allowed")

    if Path(filename).suffix.lower() != PDF_EXTENSION:
        raise InvalidDocumentUploadError("Uploaded file must have a .pdf extension")


async def save_pdf_file(file: UploadFile) -> tuple[str, str, int]:
    validate_pdf_upload(file)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}{PDF_EXTENSION}"
    file_path = upload_dir / stored_filename
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_size = 0

    try:
        with file_path.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > max_size_bytes:
                    raise InvalidDocumentUploadError(
                        f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit"
                    )
                output.write(chunk)
    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    return stored_filename, str(file_path), file_size


async def create_document(
    db: Session,
    workspace: Workspace,
    file: UploadFile,
) -> Document:
    stored_filename, file_path, file_size = await save_pdf_file(file)
    document = Document(
        workspace_id=workspace.id,
        original_filename=Path(file.filename or "document.pdf").name,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=PDF_CONTENT_TYPE,
        file_size=file_size,
        status=DocumentStatus.UPLOADED,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception:
        saved_file = Path(file_path)
        if saved_file.exists():
            saved_file.unlink()
        raise

    return document


def list_workspace_documents(
    db: Session,
    workspace: Workspace,
) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.workspace_id == workspace.id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_user_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return (
        db.query(Document)
        .join(Workspace)
        .filter(Document.id == document_id, Workspace.owner_id == owner.id)
        .first()
    )


def delete_document(db: Session, document: Document) -> None:
    file_path = Path(document.file_path)
    db.delete(document)
    db.commit()

    if file_path.exists():
        file_path.unlink()
