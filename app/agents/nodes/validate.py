from app.schemas.workflow import ValidationResult, WorkflowState


def validate_reply(state: WorkflowState) -> WorkflowState:
    """
    draft_reply를 검증하고, 결과를 state.validation에 저장한다.

    Args:
        state (WorkflowState): draft_reply와 retrieved_docs가 채워진 상태 객체

    Returns:
        WorkflowState: validation이 채워진 상태 객체

    Raises:
        ValueError: draft_reply가 없을 때 발생
    """
    if state.draft_reply is None:
        raise ValueError("답변을 검증하려면 draft_reply가 필요합니다.")

    issues = []
    risk_level = "low"
    needs_human_review = False

    draft_text = state.draft_reply.strip()

    if len(draft_text) < 20:
        issues.append("답변 길이가 너무 짧습니다.")

    risky_phrases = ["반드시", "확실히", "무조건", "100%"]
    for phrase in risky_phrases:
        if phrase in draft_text:
            issues.append(f"단정적 표현이 포함되어 있습니다: {phrase}")
            risk_level = "medium"

    if ("환불" in draft_text or "결제 취소" in draft_text) and state.category == "billing":
        needs_human_review = True
        risk_level = "high"
        issues.append("환불/결제 관련 답변은 사람 검토가 필요합니다.")

    if state.category == "technical" and "원인이 확인되었습니다" in draft_text:
        needs_human_review = True
        risk_level = "high"
        issues.append("기술 원인을 확정적으로 안내하고 있어 사람 검토가 필요합니다.")

    state.validation = ValidationResult(
        is_valid=len(issues) == 0,
        issues=issues,
        risk_level=risk_level,
        needs_human_review=needs_human_review
    )
    state.review_required = needs_human_review
    state.status = "validated"
    state.logs.append(
        f"validate_reply 완료 - is_valid={state.validation.is_valid}, "
        f"risk_level={state.validation.risk_level}, "
        f"needs_human_review={state.validation.needs_human_review}"
    )

    return state