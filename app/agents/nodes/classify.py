from app.schemas.workflow import WorkflowState


def classify_ticket(state: WorkflowState) -> WorkflowState:
    """
    티켓 내용을 분석하여 category와 priority를 분류한다.

    Args:
        state (WorkflowState): raw_ticket가 채워진 상태 객체

    Returns:
        WorkflowState: category와 priority가 채워진 상태 객체

    Raises:
        ValueError: raw_ticket이 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("티켓을 분류하려면 raw_ticket이 필요합니다.")

    content = state.raw_ticket.content.lower()
    title = state.raw_ticket.title.lower()
    combined_text = f"{title} {content}"

    if "환불" in combined_text or "refund" in combined_text or "결제" in combined_text:
        state.category = "billing"
        state.priority = "high"
    elif (
        "오류" in combined_text
        or "error" in combined_text
        or "bug" in combined_text
        or "로그인" in combined_text
        or "접속" in combined_text
    ):
        state.category = "technical"
        state.priority = "high"
    elif (
        "사용법" in combined_text
        or "어떻게" in combined_text
        or "가이드" in combined_text
        or "방법" in combined_text
    ):
        state.category = "guidance"
        state.priority = "medium"
    else:
        state.category = "general"
        state.priority = "low"

    state.status = "classified"
    state.logs.append(
        f"classify_ticket 완료 - category={state.category}, priority={state.priority}"
    )
    return state