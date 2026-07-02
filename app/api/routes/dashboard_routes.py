import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard_schema import (
    DashboardOverviewResponse,
    WorkspaceDashboardResponse,
)
from app.services.dashboard_service import (
    get_dashboard_overview,
    get_workspace_dashboard,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOverviewResponse)
def dashboard_overview(
    recent_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverviewResponse:
    return get_dashboard_overview(db, current_user, recent_limit)


@router.get(
    "/workspaces/{workspace_id}/dashboard",
    response_model=WorkspaceDashboardResponse,
)
def workspace_dashboard(
    workspace_id: uuid.UUID,
    recent_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceDashboardResponse:
    dashboard = get_workspace_dashboard(db, workspace_id, current_user, recent_limit)
    if dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return dashboard
