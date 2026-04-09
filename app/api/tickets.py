from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.graph import run_redraft_workflow, run_ticket_workflow
from app.db.session import get_db
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import (
    TicketActionResponse,
    TicketCreate,
    TicketDetailResponse,
    TicketResponse,
    TicketReviewRequest,
)
from app.schemas.workflow import ReviewDecision, WorkflowState


router = APIRouter(prefix="/tickets", tags=["tickets"])


def build_ticket_detail_response(state: WorkflowState) -> TicketDetailResponse:
    """
    WorkflowState를 TicketDetailResponse 형식으로 변환한다.

    Args:
        state (WorkflowState): 변환할 상태 객체

    Returns:
        TicketDetailResponse: 상세 조회 응답 객체

    Raises:
        ValueError: raw_ticket 또는 ticket_id가 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("상세 응답을 만들려면 raw_ticket이 필요합니다.")

    if state.ticket_id is None:
        raise ValueError("상세 응답을 만들려면 ticket_id가 필요합니다.")

    return TicketDetailResponse(
        ticket_id=state.ticket_id,
        title=state.raw_ticket.title,
        content=state.raw_ticket.content,
        customer_type=state.raw_ticket.customer_type,
        channel=state.raw_ticket.channel,
        status=state.status,
        category=state.category,
        priority=state.priority,
        draft_reply=state.draft_reply,
        final_reply=state.final_reply,
        review_required=state.review_required,
        reviewer=state.review_decision.reviewer if state.review_decision else None,
        review_decision=state.review_decision.decision if state.review_decision else None,
        review_comment=state.review_decision.comment if state.review_decision else None,
        logs=state.logs,
        errors=state.errors
    )


@router.post("", response_model=TicketResponse)
def create_ticket(ticket_data: TicketCreate, db: Session = Depends(get_db)) -> TicketResponse:
    """
    신규 티켓을 생성한다.

    Args:
        ticket_data (TicketCreate): 사용자가 입력한 티켓 생성 데이터
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketResponse: 생성된 티켓 기본 응답 데이터
    """
    repository = TicketRepository(db)
    state = repository.create_ticket(ticket_data)
    return repository.to_ticket_response(state)


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
) -> List[TicketResponse]:
    """
    전체 티켓 목록을 조회하거나 조건에 따라 필터링한다.

    Args:
        status (Optional[str]): 조회할 상태 값
        category (Optional[str]): 조회할 카테고리 값
        priority (Optional[str]): 조회할 우선순위 값
        db (Session): SQLAlchemy 세션 객체

    Returns:
        List[TicketResponse]: 조건에 맞는 티켓 목록
    """
    repository = TicketRepository(db)

    if status or category or priority:
        states = repository.filter_tickets(
            status=status,
            category=category,
            priority=priority
        )
    else:
        states = repository.list_tickets()

    return [repository.to_ticket_response(state) for state in states]


@router.get("/review-queue", response_model=List[TicketResponse])
def get_review_queue(db: Session = Depends(get_db)) -> List[TicketResponse]:
    """
    사람 검토가 필요한 티켓 목록을 조회한다.

    Args:
        db (Session): SQLAlchemy 세션 객체

    Returns:
        List[TicketResponse]: waiting_human_review 상태의 티켓 목록
    """
    repository = TicketRepository(db)
    states = repository.get_review_queue()
    return [repository.to_ticket_response(state) for state in states]


@router.get("/failed", response_model=List[TicketResponse])
def get_failed_tickets(db: Session = Depends(get_db)) -> List[TicketResponse]:
    """
    실패 상태의 티켓 목록을 조회한다.

    Args:
        db (Session): SQLAlchemy 세션 객체

    Returns:
        List[TicketResponse]: failed 또는 failed_redraft 상태의 티켓 목록
    """
    repository = TicketRepository(db)
    states = repository.get_failed_tickets()
    return [repository.to_ticket_response(state) for state in states]


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketDetailResponse:
    """
    티켓 상세 정보를 조회한다.

    Args:
        ticket_id (int): 조회할 티켓 ID
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketDetailResponse: 티켓 상세 응답 데이터

    Raises:
        HTTPException: 티켓이 없을 때 발생
    """
    repository = TicketRepository(db)
    state = repository.get_ticket(ticket_id)

    if state is None:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    return build_ticket_detail_response(state)


@router.post("/{ticket_id}/run", response_model=TicketDetailResponse)
def run_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketDetailResponse:
    """
    지정한 티켓의 워크플로우를 실행한다.

    Args:
        ticket_id (int): 실행할 티켓 ID
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketDetailResponse: 실행 결과가 반영된 상세 응답 데이터

    Raises:
        HTTPException: 티켓이 없을 때 발생
        HTTPException: 워크플로우 실행 중 오류가 발생할 때 발생
    """
    repository = TicketRepository(db)
    state = repository.get_ticket(ticket_id)

    if state is None:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    try:
        result = run_ticket_workflow(state)
        repository.save_ticket(result)
        return build_ticket_detail_response(result)

    except Exception as exc:
        state.errors.append(str(exc))
        state.status = "failed"
        repository.save_ticket(state)
        raise HTTPException(status_code=500, detail=f"워크플로우 실행 실패: {exc}")


@router.post("/{ticket_id}/approve", response_model=TicketActionResponse)
def approve_ticket(
    ticket_id: int,
    review_data: TicketReviewRequest,
    db: Session = Depends(get_db)
) -> TicketActionResponse:
    """
    사람 검토가 필요한 티켓을 승인 처리한다.

    Args:
        ticket_id (int): 승인할 티켓 ID
        review_data (TicketReviewRequest): 검토자 및 검토 의견 데이터
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketActionResponse: 승인 처리 결과 응답 데이터

    Raises:
        HTTPException: 티켓이 없을 때 발생
        HTTPException: 승인 가능한 상태가 아닐 때 발생
    """
    repository = TicketRepository(db)
    state = repository.get_ticket(ticket_id)

    if state is None:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    if state.status != "waiting_human_review":
        raise HTTPException(status_code=400, detail="현재 티켓은 승인 가능한 상태가 아닙니다.")

    if state.draft_reply is None:
        raise HTTPException(status_code=400, detail="승인할 답변 초안이 없습니다.")

    state.review_decision = ReviewDecision(
        reviewer=review_data.reviewer,
        decision="approved",
        comment=review_data.comment
    )
    state.final_reply = state.draft_reply
    state.status = "approved"
    state.logs.append(f"approve_ticket 완료 - reviewer={review_data.reviewer}")

    if review_data.comment:
        state.logs.append(f"approve_comment - {review_data.comment}")

    repository.save_ticket(state)

    return TicketActionResponse(
        ticket_id=ticket_id,
        status=state.status,
        message="티켓이 승인되었습니다."
    )


@router.post("/{ticket_id}/reject", response_model=TicketActionResponse)
def reject_ticket(
    ticket_id: int,
    review_data: TicketReviewRequest,
    db: Session = Depends(get_db)
) -> TicketActionResponse:
    """
    사람 검토가 필요한 티켓을 반려 처리한다.

    Args:
        ticket_id (int): 반려할 티켓 ID
        review_data (TicketReviewRequest): 검토자 및 검토 의견 데이터
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketActionResponse: 반려 처리 결과 응답 데이터

    Raises:
        HTTPException: 티켓이 없을 때 발생
        HTTPException: 반려 가능한 상태가 아닐 때 발생
    """
    repository = TicketRepository(db)
    state = repository.get_ticket(ticket_id)

    if state is None:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    if state.status != "waiting_human_review":
        raise HTTPException(status_code=400, detail="현재 티켓은 반려 가능한 상태가 아닙니다.")

    state.review_decision = ReviewDecision(
        reviewer=review_data.reviewer,
        decision="rejected",
        comment=review_data.comment
    )
    state.final_reply = None
    state.status = "rejected"
    state.logs.append(f"reject_ticket 완료 - reviewer={review_data.reviewer}")

    if review_data.comment:
        state.logs.append(f"reject_comment - {review_data.comment}")

    repository.save_ticket(state)

    return TicketActionResponse(
        ticket_id=ticket_id,
        status=state.status,
        message="티켓이 반려되었습니다."
    )


@router.post("/{ticket_id}/redraft", response_model=TicketActionResponse)
def redraft_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketActionResponse:
    """
    반려된 티켓의 답변 초안을 반려 사유를 반영하여 다시 생성한다.

    Args:
        ticket_id (int): 재작성할 티켓 ID
        db (Session): SQLAlchemy 세션 객체

    Returns:
        TicketActionResponse: 재작성 처리 결과 응답 데이터

    Raises:
        HTTPException: 티켓이 없을 때 발생
        HTTPException: 재작성 가능한 상태가 아닐 때 발생
        HTTPException: 재작성 실행 중 오류가 발생할 때 발생
    """
    repository = TicketRepository(db)
    state = repository.get_ticket(ticket_id)

    if state is None:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    if state.status not in ["rejected", "failed_redraft"]:
        raise HTTPException(
            status_code=400,
            detail="현재 티켓은 재작성 가능한 상태가 아닙니다. rejected 또는 failed_redraft 상태여야 합니다."
        )

    if state.review_decision is None:
        raise HTTPException(status_code=400, detail="재작성을 위한 review_decision 정보가 없습니다.")

    if state.review_decision.comment is None or not state.review_decision.comment.strip():
        raise HTTPException(status_code=400, detail="재작성을 위해서는 반려 코멘트가 필요합니다.")

    try:
        result = run_redraft_workflow(state)
        repository.save_ticket(result)

        return TicketActionResponse(
            ticket_id=ticket_id,
            status=result.status,
            message="티켓 답변 초안이 반려 사유를 반영하여 재작성되었습니다."
        )

    except Exception as exc:
        state.errors.append(str(exc))
        state.status = "failed_redraft"
        repository.save_ticket(state)
        raise HTTPException(status_code=500, detail=f"재작성 실행 실패: {exc}")