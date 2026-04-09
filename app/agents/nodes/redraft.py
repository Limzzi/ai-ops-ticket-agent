from app.schemas.workflow import WorkflowState
from app.services.llm_service import call_llm


def build_redraft_prompt(state: WorkflowState) -> str:
    """
    반려 사유를 반영한 답변 재작성 프롬프트를 구성한다.

    Args:
        state (WorkflowState): raw_ticket, category, priority, retrieved_docs, draft_reply, review_decision이 채워진 상태 객체

    Returns:
        str: LLM에 전달할 재작성 프롬프트 문자열

    Raises:
        ValueError: 재작성에 필요한 상태 값이 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("재작성 프롬프트를 만들려면 raw_ticket이 필요합니다.")

    if state.category is None:
        raise ValueError("재작성 프롬프트를 만들려면 category가 필요합니다.")

    if state.priority is None:
        raise ValueError("재작성 프롬프트를 만들려면 priority가 필요합니다.")

    if not state.retrieved_docs:
        raise ValueError("재작성 프롬프트를 만들려면 retrieved_docs가 필요합니다.")

    if state.draft_reply is None:
        raise ValueError("재작성 프롬프트를 만들려면 draft_reply가 필요합니다.")

    if state.review_decision is None:
        raise ValueError("재작성 프롬프트를 만들려면 review_decision이 필요합니다.")

    if state.review_decision.comment is None or not state.review_decision.comment.strip():
        raise ValueError("재작성 프롬프트를 만들려면 review comment가 필요합니다.")

    context_text = "\n\n".join(
        [f"[문서 제목] {doc.title}\n[문서 내용] {doc.content}" for doc in state.retrieved_docs]
    )

    prompt = f"""
다음 고객 문의에 대한 기존 답변 초안이 사람 검토자에 의해 반려되었다.
반려 사유를 반드시 반영하여 답변을 다시 작성하라.

[고객 문의]
제목: {state.raw_ticket.title}
내용: {state.raw_ticket.content}
고객 유형: {state.raw_ticket.customer_type}
채널: {state.raw_ticket.channel}

[분류 결과]
카테고리: {state.category}
우선순위: {state.priority}

[참고 문서]
{context_text}

[기존 답변 초안]
{state.draft_reply}

[반려 사유]
검토자: {state.review_decision.reviewer}
코멘트: {state.review_decision.comment}

[재작성 규칙]
1. 반드시 반려 사유를 반영한다.
2. 참고 문서에 없는 사실을 단정하지 않는다.
3. 환불, 결제, 기술 원인 등 민감한 내용은 확정적으로 말하지 않는다.
4. 필요한 경우 추가 확인이 필요하다고 안내한다.
5. 답변은 한국어로 작성한다.
6. 고객에게 바로 보낼 수 있는 자연스러운 답변 본문만 출력한다.
""".strip()

    return prompt


def redraft_reply(state: WorkflowState) -> WorkflowState:
    """
    반려 사유를 반영하여 답변 초안을 다시 생성하고 state.draft_reply에 저장한다.

    Args:
        state (WorkflowState): 재작성에 필요한 정보가 채워진 상태 객체

    Returns:
        WorkflowState: 새 draft_reply가 저장된 상태 객체

    Raises:
        ValueError: 재작성에 필요한 상태 값이 없을 때 발생
    """
    prompt = build_redraft_prompt(state)
    response_text = call_llm(prompt)

    state.draft_reply = response_text.strip()
    state.final_reply = None
    state.status = "redrafted"
    state.logs.append("redraft_reply 완료")

    return state