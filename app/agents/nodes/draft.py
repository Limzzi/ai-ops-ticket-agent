from app.schemas.workflow import WorkflowState
from app.services.llm_service import call_llm


def build_reply_prompt(state: WorkflowState) -> str:
    """
    답변 초안 생성을 위한 프롬프트를 구성한다.

    Args:
        state (WorkflowState): raw_ticket, category, priority, retrieved_docs가 채워진 상태 객체

    Returns:
        str: LLM에 전달할 프롬프트 문자열

    Raises:
        ValueError: 답변 초안 생성에 필요한 상태 값이 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("프롬프트를 만들려면 raw_ticket이 필요합니다.")

    if state.category is None:
        raise ValueError("프롬프트를 만들려면 category가 필요합니다.")

    if state.priority is None:
        raise ValueError("프롬프트를 만들려면 priority가 필요합니다.")

    context_text = "\n\n".join(
        [f"[문서 제목] {doc.title}\n[문서 내용] {doc.content}" for doc in state.retrieved_docs]
    )

    prompt = f"""
다음 고객 문의에 대해 고객지원 답변 초안을 작성하라.

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

[작성 규칙]
1. 답변은 반드시 한국어로 작성한다.
2. 정중하고 실무적인 톤으로 작성한다.
3. 참고 문서에 없는 사실을 단정하지 않는다.
4. 필요한 경우 추가 정보가 필요하다고 안내한다.
5. 답변은 고객에게 바로 보낼 수 있는 형태의 자연스러운 문장으로 작성한다.
6. 불필요한 머리말이나 설명 없이 답변 본문만 출력한다.
""".strip()

    return prompt


def draft_reply(state: WorkflowState) -> WorkflowState:
    """
    검색된 문맥을 기반으로 고객 답변 초안을 생성하여 state.draft_reply에 저장한다.

    Args:
        state (WorkflowState): raw_ticket, category, priority가 채워진 상태 객체

    Returns:
        WorkflowState: draft_reply가 채워진 상태 객체

    Raises:
        ValueError: 답변 초안 생성에 필요한 상태 값이 없을 때 발생
    """
    prompt = build_reply_prompt(state)
    response_text = call_llm(prompt)

    state.draft_reply = response_text.strip()
    state.status = "draft_created"
    state.logs.append("draft_reply 완료")
    return state