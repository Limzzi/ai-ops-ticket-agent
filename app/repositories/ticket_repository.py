from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.ticket import TicketModel
from app.schemas.ticket import TicketCreate, TicketResponse
from app.schemas.workflow import ReviewDecision, WorkflowState


class TicketRepository:
    """
    SQLAlchemy 기반 티켓 저장소를 관리한다.
    """

    def __init__(self, db: Session) -> None:
        """
        저장소를 초기화한다.

        Args:
            db (Session): SQLAlchemy 세션 객체
        """
        self.db = db

    def create_ticket(self, ticket_data: TicketCreate) -> WorkflowState:
        """
        신규 티켓을 생성하고 초기 WorkflowState를 저장한다.

        Args:
            ticket_data (TicketCreate): 사용자가 입력한 티켓 생성 데이터

        Returns:
            WorkflowState: 저장된 초기 상태 객체
        """
        ticket = TicketModel(
            title=ticket_data.title,
            content=ticket_data.content,
            customer_type=ticket_data.customer_type,
            channel=ticket_data.channel,
            status="created",
            logs="create_ticket 완료 - DB 저장됨"
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        return self._to_workflow_state(ticket)

    def get_ticket(self, ticket_id: int) -> Optional[WorkflowState]:
        """
        티켓 ID로 저장된 WorkflowState를 조회한다.

        Args:
            ticket_id (int): 조회할 티켓 ID

        Returns:
            Optional[WorkflowState]: 저장된 상태 객체. 없으면 None
        """
        ticket = self.db.query(TicketModel).filter(TicketModel.id == ticket_id).first()

        if ticket is None:
            return None

        return self._to_workflow_state(ticket)

    def save_ticket(self, state: WorkflowState) -> WorkflowState:
        """
        WorkflowState를 데이터베이스에 저장하거나 갱신한다.

        Args:
            state (WorkflowState): 저장할 상태 객체

        Returns:
            WorkflowState: 저장된 상태 객체

        Raises:
            ValueError: ticket_id 또는 raw_ticket이 없을 때 발생
        """
        if state.ticket_id is None:
            raise ValueError("티켓을 저장하려면 ticket_id가 필요합니다.")

        if state.raw_ticket is None:
            raise ValueError("티켓을 저장하려면 raw_ticket이 필요합니다.")

        ticket = self.db.query(TicketModel).filter(TicketModel.id == state.ticket_id).first()

        if ticket is None:
            raise ValueError("저장할 대상 티켓이 존재하지 않습니다.")

        ticket.title = state.raw_ticket.title
        ticket.content = state.raw_ticket.content
        ticket.customer_type = state.raw_ticket.customer_type
        ticket.channel = state.raw_ticket.channel

        ticket.status = state.status
        ticket.category = state.category
        ticket.priority = state.priority
        ticket.draft_reply = state.draft_reply
        ticket.final_reply = state.final_reply
        ticket.review_required = state.review_required

        if state.review_decision is not None:
            ticket.reviewer = state.review_decision.reviewer
            ticket.review_decision = state.review_decision.decision
            ticket.review_comment = state.review_decision.comment
        else:
            ticket.reviewer = None
            ticket.review_decision = None
            ticket.review_comment = None

        ticket.logs = self._serialize_list(state.logs)
        ticket.errors = self._serialize_list(state.errors)

        self.db.commit()
        self.db.refresh(ticket)

        return self._to_workflow_state(ticket)

    def list_tickets(self) -> List[WorkflowState]:
        """
        저장된 전체 티켓 목록을 반환한다.

        Returns:
            List[WorkflowState]: 전체 티켓 상태 목록
        """
        tickets = self.db.query(TicketModel).order_by(TicketModel.id.desc()).all()
        return [self._to_workflow_state(ticket) for ticket in tickets]

    def to_ticket_response(self, state: WorkflowState) -> TicketResponse:
        """
        WorkflowState를 TicketResponse 형식으로 변환한다.

        Args:
            state (WorkflowState): 변환할 상태 객체

        Returns:
            TicketResponse: API 응답용 티켓 데이터

        Raises:
            ValueError: raw_ticket 또는 ticket_id가 없을 때 발생
        """
        if state.raw_ticket is None:
            raise ValueError("응답을 만들려면 raw_ticket이 필요합니다.")

        if state.ticket_id is None:
            raise ValueError("응답을 만들려면 ticket_id가 필요합니다.")

        return TicketResponse(
            ticket_id=state.ticket_id,
            title=state.raw_ticket.title,
            content=state.raw_ticket.content,
            customer_type=state.raw_ticket.customer_type,
            channel=state.raw_ticket.channel,
            status=state.status,
            category=state.category,
            priority=state.priority
        )

    def _to_workflow_state(self, ticket: TicketModel) -> WorkflowState:
        """
        TicketModel을 WorkflowState로 변환한다.

        Args:
            ticket (TicketModel): 데이터베이스 티켓 모델

        Returns:
            WorkflowState: 변환된 상태 객체
        """
        review_decision = None

        if ticket.reviewer and ticket.review_decision:
            review_decision = ReviewDecision(
                reviewer=ticket.reviewer,
                decision=ticket.review_decision,
                comment=ticket.review_comment
            )

        return WorkflowState(
            ticket_id=ticket.id,
            raw_ticket=TicketCreate(
                title=ticket.title,
                content=ticket.content,
                customer_type=ticket.customer_type,
                channel=ticket.channel
            ),
            status=ticket.status,
            category=ticket.category,
            priority=ticket.priority,
            draft_reply=ticket.draft_reply,
            final_reply=ticket.final_reply,
            review_required=ticket.review_required,
            review_decision=review_decision,
            logs=self._deserialize_list(ticket.logs),
            errors=self._deserialize_list(ticket.errors)
        )

    def _serialize_list(self, values: List[str]) -> str:
        """
        문자열 리스트를 줄바꿈 기반 문자열로 직렬화한다.

        Args:
            values (List[str]): 직렬화할 문자열 리스트

        Returns:
            str: 직렬화된 문자열
        """
        return "\n".join(values)

    def _deserialize_list(self, value: str) -> List[str]:
        """
        줄바꿈 기반 문자열을 문자열 리스트로 역직렬화한다.

        Args:
            value (str): 역직렬화할 문자열

        Returns:
            List[str]: 역직렬화된 문자열 리스트
        """
        if not value.strip():
            return []

        return value.split("\n")
    

    def filter_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[WorkflowState]:
        """
        상태, 카테고리, 우선순위 조건으로 티켓 목록을 조회한다.

        Args:
            status (Optional[str]): 조회할 상태 값
            category (Optional[str]): 조회할 카테고리 값
            priority (Optional[str]): 조회할 우선순위 값

        Returns:
            List[WorkflowState]: 조건에 맞는 티켓 상태 목록
        """
        query = self.db.query(TicketModel)

        if status:
            query = query.filter(TicketModel.status == status)

        if category:
            query = query.filter(TicketModel.category == category)

        if priority:
            query = query.filter(TicketModel.priority == priority)

        tickets = query.order_by(TicketModel.id.desc()).all()
        return [self._to_workflow_state(ticket) for ticket in tickets]
    

    def get_review_queue(self) -> List[WorkflowState]:
        """
        사람 검토가 필요한 티켓 목록을 조회한다.

        Returns:
            List[WorkflowState]: waiting_human_review 상태의 티켓 목록
        """
        tickets = (
            self.db.query(TicketModel)
            .filter(TicketModel.status == "waiting_human_review")
            .order_by(TicketModel.id.desc())
            .all()
        )
        return [self._to_workflow_state(ticket) for ticket in tickets]
    

    def get_failed_tickets(self) -> List[WorkflowState]:
        """
        실패 상태의 티켓 목록을 조회한다.

        Returns:
            List[WorkflowState]: failed 또는 failed_redraft 상태의 티켓 목록
        """
        tickets = (
            self.db.query(TicketModel)
            .filter(TicketModel.status.in_(["failed", "failed_redraft"]))
            .order_by(TicketModel.id.desc())
            .all()
        )
        return [self._to_workflow_state(ticket) for ticket in tickets]