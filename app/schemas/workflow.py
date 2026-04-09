from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.ticket import TicketCreate


class RetrievedDocument(BaseModel):
    """
    검색된 참고 문서 정보를 정의한다.

    Attributes:
        source (str): 문서 출처
        title (str): 문서 제목
        content (str): 문서 본문
        score (float): 검색 유사도 또는 점수
    """

    source: str
    title: str
    content: str
    score: float = Field(ge=0.0, le=1.0)


class ValidationResult(BaseModel):
    """
    답변 검증 결과를 정의한다.

    Attributes:
        is_valid (bool): 검증 통과 여부
        issues (List[str]): 발견된 문제 목록
        risk_level (Literal["low", "medium", "high"]): 위험도
        needs_human_review (bool): 사람 검토 필요 여부
    """

    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"]
    needs_human_review: bool


class ReviewDecision(BaseModel):
    """
    사람 검토 결과 정보를 정의한다.

    Attributes:
        reviewer (str): 검토자 이름 또는 식별자
        decision (Literal["approved", "rejected"]): 검토 결정
        comment (Optional[str]): 검토 의견
    """

    reviewer: str
    decision: Literal["approved", "rejected"]
    comment: Optional[str] = None


class WorkflowState(BaseModel):
    """
    티켓 처리 워크플로우 전체 상태를 정의한다.

    Attributes:
        ticket_id (Optional[int]): 티켓 ID
        raw_ticket (Optional[TicketCreate]): 원본 티켓 입력 데이터
        status (str): 현재 워크플로우 상태
        category (Optional[str]): 문의 카테고리
        priority (Optional[str]): 문의 우선순위
        retrieved_docs (List[RetrievedDocument]): 검색된 참고 문서 목록
        draft_reply (Optional[str]): 생성된 답변 초안
        validation (Optional[ValidationResult]): 검증 결과
        review_required (bool): 승인 필요 여부
        review_decision (Optional[ReviewDecision]): 사람 검토 결과
        final_reply (Optional[str]): 최종 확정 답변
        logs (List[str]): 처리 로그
        errors (List[str]): 에러 로그
    """

    ticket_id: Optional[int] = None
    raw_ticket: Optional[TicketCreate] = None
    status: str = "created"
    category: Optional[str] = None
    priority: Optional[str] = None
    retrieved_docs: List[RetrievedDocument] = Field(default_factory=list)
    draft_reply: Optional[str] = None
    validation: Optional[ValidationResult] = None
    review_required: bool = False
    review_decision: Optional[ReviewDecision] = None
    final_reply: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)