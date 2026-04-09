from sqlalchemy import Boolean, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.db.base import Base


class TicketModel(Base):
    """
    티켓 상태 정보를 저장하는 데이터베이스 모델이다.

    Attributes:
        id (int): 티켓 ID
        title (str): 티켓 제목
        content (str): 티켓 본문
        customer_type (str): 고객 유형
        channel (str): 문의 채널
        status (str): 현재 상태
        category (Optional[str]): 분류 결과
        priority (Optional[str]): 우선순위 결과
        draft_reply (Optional[str]): 생성된 답변 초안
        final_reply (Optional[str]): 최종 답변
        review_required (bool): 사람 검토 필요 여부
        reviewer (Optional[str]): 검토자
        review_decision (Optional[str]): 검토 결과
        review_comment (Optional[str]): 검토 의견
        logs (str): 로그 문자열
        errors (str): 에러 문자열
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    customer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(100), nullable=False, default="created")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    draft_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    review_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    logs: Mapped[str] = mapped_column(Text, nullable=False, default="")
    errors: Mapped[str] = mapped_column(Text, nullable=False, default="")