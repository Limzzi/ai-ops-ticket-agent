from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    """
    신규 티켓 생성 요청 데이터를 정의한다.

    Attributes:
        title (str): 티켓 제목
        content (str): 티켓 본문 내용
        customer_type (Literal["individual", "business", "vip"]): 고객 유형
        channel (Literal["email", "chat", "form"]): 문의 채널
    """

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    customer_type: Literal["individual", "business", "vip"]
    channel: Literal["email", "chat", "form"]


class TicketResponse(BaseModel):
    """
    티켓 생성 또는 조회 응답 데이터를 정의한다.

    Attributes:
        ticket_id (int): 티켓 ID
        title (str): 티켓 제목
        content (str): 티켓 본문 내용
        customer_type (str): 고객 유형
        channel (str): 문의 채널
        status (str): 현재 처리 상태
        category (Optional[str]): 분류 결과
        priority (Optional[str]): 우선순위 결과
    """

    ticket_id: int
    title: str
    content: str
    customer_type: str
    channel: str
    status: str
    category: Optional[str] = None
    priority: Optional[str] = None


class TicketDetailResponse(BaseModel):
    """
    티켓 상세 조회 응답 데이터를 정의한다.

    Attributes:
        ticket_id (int): 티켓 ID
        title (str): 티켓 제목
        content (str): 티켓 본문 내용
        customer_type (str): 고객 유형
        channel (str): 문의 채널
        status (str): 현재 처리 상태
        category (Optional[str]): 분류 결과
        priority (Optional[str]): 우선순위 결과
        draft_reply (Optional[str]): 생성된 답변 초안
        final_reply (Optional[str]): 최종 답변
        review_required (bool): 사람 검토 필요 여부
        reviewer (Optional[str]): 검토자
        review_decision (Optional[str]): 검토 결과
        review_comment (Optional[str]): 검토 의견
        logs (List[str]): 처리 로그
        errors (List[str]): 에러 로그
    """

    ticket_id: int
    title: str
    content: str
    customer_type: str
    channel: str
    status: str
    category: Optional[str] = None
    priority: Optional[str] = None
    draft_reply: Optional[str] = None
    final_reply: Optional[str] = None
    review_required: bool = False
    reviewer: Optional[str] = None
    review_decision: Optional[str] = None
    review_comment: Optional[str] = None
    logs: List[str]
    errors: List[str]


class TicketReviewRequest(BaseModel):
    """
    티켓 승인 또는 반려 요청 데이터를 정의한다.

    Attributes:
        reviewer (str): 검토자 이름 또는 식별자
        comment (Optional[str]): 검토 의견
    """

    reviewer: str = Field(..., min_length=1, max_length=100)
    comment: Optional[str] = None


class TicketActionResponse(BaseModel):
    """
    티켓 승인 또는 반려 처리 결과 응답 데이터를 정의한다.

    Attributes:
        ticket_id (int): 티켓 ID
        status (str): 변경된 티켓 상태
        message (str): 처리 결과 메시지
    """

    ticket_id: int
    status: str
    message: str