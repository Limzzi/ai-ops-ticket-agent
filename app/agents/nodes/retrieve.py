import json
from pathlib import Path

from app.schemas.workflow import RetrievedDocument, WorkflowState


def retrieve_context(state: WorkflowState) -> WorkflowState:
    """
    티켓 category를 기반으로 관련 FAQ 문서를 검색하여 state.retrieved_docs에 저장한다.

    Args:
        state (WorkflowState): raw_ticket와 category가 채워진 상태 객체

    Returns:
        WorkflowState: retrieved_docs가 채워진 상태 객체

    Raises:
        ValueError: raw_ticket 또는 category가 없을 때 발생
        FileNotFoundError: FAQ 파일이 존재하지 않을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("문서를 검색하려면 raw_ticket이 필요합니다.")

    if state.category is None:
        raise ValueError("문서를 검색하려면 category가 필요합니다.")

    faq_path = Path("app/data/faq.json")

    if not faq_path.exists():
        raise FileNotFoundError("FAQ 파일을 찾을 수 없습니다: app/data/faq.json")

    faq_data = json.loads(faq_path.read_text(encoding="utf-8"))
    matched_docs = []

    for item in faq_data:
        if item["category"] == state.category:
            matched_docs.append(
                RetrievedDocument(
                    source="faq.json",
                    title=item["title"],
                    content=item["content"],
                    score=0.9
                )
            )

    if not matched_docs:
        matched_docs.append(
            RetrievedDocument(
                source="faq.json",
                title="기본 일반 응대 가이드",
                content="명확한 근거가 없을 경우 추가 확인 후 안내하겠다고 답변합니다.",
                score=0.5
            )
        )

    state.retrieved_docs = matched_docs
    state.status = "context_retrieved"
    state.logs.append(f"retrieve_context 완료 - {len(matched_docs)}개 문서 검색")
    return state