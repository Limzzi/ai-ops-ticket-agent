from app.schemas.workflow import WorkflowState


def finalize_reply(state: WorkflowState) -> WorkflowState:
    """
    검증 결과를 바탕으로 최종 답변 상태를 확정하여 state.final_reply에 저장한다.

    Args:
        state (WorkflowState): draft_reply와 validation이 채워진 상태 객체

    Returns:
        WorkflowState: final_reply가 채워진 상태 객체

    Raises:
        ValueError: draft_reply 또는 validation이 없을 때 발생
    """
    if state.draft_reply is None:
        raise ValueError("최종 답변을 확정하려면 draft_reply가 필요합니다.")

    if state.validation is None:
        raise ValueError("최종 답변을 확정하려면 validation이 필요합니다.")

    if state.validation.needs_human_review:
        state.final_reply = None
        state.status = "waiting_human_review"
        state.logs.append("finalize_reply 보류 - human review 필요")
    else:
        state.final_reply = state.draft_reply
        state.status = "completed"
        state.logs.append("finalize_reply 완료 - 자동 처리 완료")

    return state