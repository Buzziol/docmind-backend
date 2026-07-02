import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate


def create_workspace(
    db: Session,
    workspace_data: WorkspaceCreate,
    owner: User,
) -> Workspace:
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=owner.id,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def list_user_workspaces(db: Session, owner: User) -> list[Workspace]:
    return (
        db.query(Workspace)
        .filter(Workspace.owner_id == owner.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )


def get_user_workspace(
    db: Session,
    workspace_id: uuid.UUID,
    owner: User,
) -> Workspace | None:
    return (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.owner_id == owner.id)
        .first()
    )


def update_workspace(
    db: Session,
    workspace: Workspace,
    workspace_data: WorkspaceUpdate,
) -> Workspace:
    update_data = workspace_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def delete_workspace(db: Session, workspace: Workspace) -> None:
    db.delete(workspace)
    db.commit()
