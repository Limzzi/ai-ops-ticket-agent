from langgraph.graph import END, START, StateGraph

from app.agents.nodes.classify import classify_ticket
from app.agents.nodes.draft import draft_reply
from app.agents.nodes.finalize import finalize_reply
from app.agents.nodes.redraft import redraft_reply
from app.agents.nodes.retrieve import retrieve_context
from app.agents.nodes.validate import validate_reply
from app.agents.state import AgentState
from app.schemas.workflow import WorkflowState


def classify_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 티켓 분류 노드로 동작하며 category와 priority를 설정한다.

    Args:
        state (AgentState): raw_ticket가 채워진 상태 객체

    Returns:
        AgentState: 분류 결과가 반영된 상태 객체
    """
    return classify_ticket(state)


def retrieve_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 문맥 검색 노드로 동작하며 retrieved_docs를 설정한다.

    Args:
        state (AgentState): raw_ticket와 category가 채워진 상태 객체

    Returns:
        AgentState: 검색 결과가 반영된 상태 객체
    """
    return retrieve_context(state)


def draft_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 초안 생성 노드로 동작하며 draft_reply를 설정한다.

    Args:
        state (AgentState): 초안 생성에 필요한 정보가 채워진 상태 객체

    Returns:
        AgentState: draft_reply가 반영된 상태 객체
    """
    return draft_reply(state)


def validate_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 답변 검증 노드로 동작하며 validation을 설정한다.

    Args:
        state (AgentState): draft_reply가 채워진 상태 객체

    Returns:
        AgentState: validation이 반영된 상태 객체
    """
    return validate_reply(state)


def finalize_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 최종 확정 노드로 동작하며 final_reply와 status를 결정한다.

    Args:
        state (AgentState): validation이 채워진 상태 객체

    Returns:
        AgentState: 최종 상태가 반영된 상태 객체
    """
    return finalize_reply(state)


def redraft_node(state: AgentState) -> AgentState:
    """
    LangGraph에서 재작성 노드로 동작하며 반려 사유를 반영한 새 초안을 생성한다.

    Args:
        state (AgentState): review_decision이 채워진 상태 객체

    Returns:
        AgentState: 새 draft_reply가 반영된 상태 객체
    """
    return redraft_reply(state)


def route_after_validation(state: AgentState) -> str:
    """
    검증 결과를 바탕으로 다음 노드 경로를 결정한다.

    Args:
        state (AgentState): validation이 채워진 상태 객체

    Returns:
        str: 다음으로 이동할 노드 이름

    Raises:
        ValueError: validation이 없을 때 발생
    """
    if state.validation is None:
        raise ValueError("검증 라우팅을 하려면 validation이 필요합니다.")

    if state.validation.needs_human_review:
        state.logs.append("route_after_validation - human_review 경로 선택")
        return "finalize"

    state.logs.append("route_after_validation - auto_finalize 경로 선택")
    return "finalize"


def build_ticket_graph():
    """
    기본 티켓 처리 워크플로우 그래프를 생성한다.

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 객체
    """
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("classify", classify_node)
    graph_builder.add_node("retrieve", retrieve_node)
    graph_builder.add_node("draft", draft_node)
    graph_builder.add_node("validate", validate_node)
    graph_builder.add_node("finalize", finalize_node)

    graph_builder.add_edge(START, "classify")
    graph_builder.add_edge("classify", "retrieve")
    graph_builder.add_edge("retrieve", "draft")
    graph_builder.add_edge("draft", "validate")
    graph_builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "finalize": "finalize",
        }
    )
    graph_builder.add_edge("finalize", END)

    return graph_builder.compile()


def build_redraft_graph():
    """
    반려된 티켓의 재작성 워크플로우 그래프를 생성한다.

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 객체
    """
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("retrieve", retrieve_node)
    graph_builder.add_node("redraft", redraft_node)
    graph_builder.add_node("validate", validate_node)
    graph_builder.add_node("finalize", finalize_node)

    graph_builder.add_edge(START, "retrieve")
    graph_builder.add_edge("retrieve", "redraft")
    graph_builder.add_edge("redraft", "validate")
    graph_builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "finalize": "finalize",
        }
    )
    graph_builder.add_edge("finalize", END)

    return graph_builder.compile()


ticket_graph = build_ticket_graph()
redraft_graph = build_redraft_graph()


def run_ticket_workflow(state: WorkflowState) -> WorkflowState:
    """
    LangGraph 기반 기본 티켓 처리 워크플로우를 실행한다.

    Args:
        state (WorkflowState): raw_ticket가 채워진 초기 상태 객체

    Returns:
        WorkflowState: 전체 노드 실행 결과가 반영된 상태 객체

    Raises:
        ValueError: workflow 실행에 필요한 초기 상태가 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("워크플로우를 실행하려면 raw_ticket이 필요합니다.")

    result = ticket_graph.invoke(state)

    if isinstance(result, WorkflowState):
        return result

    return WorkflowState.model_validate(result)


def run_redraft_workflow(state: WorkflowState) -> WorkflowState:
    """
    LangGraph 기반 재작성 워크플로우를 실행한다.

    Args:
        state (WorkflowState): redraft에 필요한 상태가 채워진 상태 객체

    Returns:
        WorkflowState: 재작성 및 재검증 결과가 반영된 상태 객체

    Raises:
        ValueError: redraft 실행에 필요한 상태가 없을 때 발생
    """
    if state.raw_ticket is None:
        raise ValueError("redraft workflow를 실행하려면 raw_ticket이 필요합니다.")

    if state.status != "rejected":
        raise ValueError("redraft workflow는 rejected 상태의 티켓만 실행할 수 있습니다.")

    if state.review_decision is None:
        raise ValueError("redraft workflow를 실행하려면 review_decision이 필요합니다.")

    result = redraft_graph.invoke(state)

    if isinstance(result, WorkflowState):
        return result

    return WorkflowState.model_validate(result)