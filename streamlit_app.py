import requests
import streamlit as st

st.set_page_config(
    page_title="AI Ticket Admin",
    layout="wide"
)

if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None


# =========================
# 최소 스타일
# =========================
st.markdown(
    """
    <style>
    .metric-box {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    }

    .metric-title {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
    }

    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    .status-created {
        background-color: #e5e7eb;
        color: #374151;
    }

    .status-review {
        background-color: #fef3c7;
        color: #92400e;
    }

    .status-approved {
        background-color: #dcfce7;
        color: #166534;
    }

    .status-rejected {
        background-color: #fee2e2;
        color: #991b1b;
    }

    .status-completed {
        background-color: #dbeafe;
        color: #1d4ed8;
    }

    .status-failed {
        background-color: #f3e8ff;
        color: #7e22ce;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# API 주소
# =========================
st.sidebar.title("설정")
API_BASE = st.sidebar.text_input("API 주소", "http://localhost:8000")


# =========================
# 매핑
# =========================
customer_type_map = {
    "개인": "individual",
    "기업": "business"
}

channel_map = {
    "이메일": "email",
    "채팅": "chat"
}

status_map = {
    "created": "생성됨",
    "waiting_human_review": "검토 대기",
    "approved": "승인됨",
    "rejected": "반려됨",
    "completed": "완료됨",
    "failed": "실패",
    "failed_redraft": "재작성 실패"
}

category_map = {
    "billing": "결제",
    "technical": "기술",
    "general": "일반"
}

priority_map = {
    "low": "낮음",
    "medium": "보통",
    "high": "높음"
}

status_filter_map = {
    "전체": None,
    "생성됨": "created",
    "검토 대기": "waiting_human_review",
    "승인됨": "approved",
    "반려됨": "rejected",
    "완료됨": "completed",
    "실패": "failed",
    "재작성 실패": "failed_redraft"
}

category_filter_map = {
    "전체": None,
    "결제": "billing",
    "기술": "technical",
    "일반": "general"
}

priority_filter_map = {
    "전체": None,
    "낮음": "low",
    "보통": "medium",
    "높음": "high"
}


def get_status_badge_html(status: str) -> str:
    """
    상태값에 맞는 HTML 배지를 반환한다.

    Args:
        status (str): 티켓 상태값

    Returns:
        str: HTML badge 문자열
    """
    status_label = status_map.get(status, status)

    if status == "created":
        css_class = "status-created"
    elif status == "waiting_human_review":
        css_class = "status-review"
    elif status == "approved":
        css_class = "status-approved"
    elif status == "rejected":
        css_class = "status-rejected"
    elif status == "completed":
        css_class = "status-completed"
    else:
        css_class = "status-failed"

    return f'<span class="status-badge {css_class}">{status_label}</span>'


def safe_get_json(url: str, params: dict = None):
    """
    GET 요청을 보내고 JSON 응답을 반환한다.

    Args:
        url (str): 요청할 URL
        params (dict): 쿼리 파라미터

    Returns:
        list | dict | None: 성공 시 JSON 데이터, 실패 시 None
    """
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        st.error(f"GET 요청 실패: {response.text}")
        return None
    except requests.RequestException as exc:
        st.error(f"서버 연결 실패: {exc}")
        return None


def safe_post_json(url: str, payload: dict = None):
    """
    POST 요청을 보내고 JSON 응답을 반환한다.

    Args:
        url (str): 요청할 URL
        payload (dict): 요청 바디 데이터

    Returns:
        dict | None: 성공 시 JSON 데이터, 실패 시 None
    """
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        st.error(f"POST 요청 실패: {response.text}")
        return None
    except requests.RequestException as exc:
        st.error(f"서버 연결 실패: {exc}")
        return None


# =========================
# 제목
# =========================
st.title("🎫 AI Ops Ticket Admin Dashboard")
st.caption("실무형 AI 티켓 처리 워크플로우를 운영하고 검토하는 관리자 화면")


# =========================
# 데이터 불러오기
# =========================
all_tickets = safe_get_json(f"{API_BASE}/tickets") or []
review_queue = safe_get_json(f"{API_BASE}/tickets/review-queue") or []
failed_tickets = safe_get_json(f"{API_BASE}/tickets/failed") or []

approved_count = sum(1 for ticket in all_tickets if ticket.get("status") == "approved")


# =========================
# 상단 요약 카드
# =========================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">전체 티켓</div>
            <div class="metric-value">{len(all_tickets)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">검토 대기</div>
            <div class="metric-value">{len(review_queue)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">승인됨</div>
            <div class="metric-value">{approved_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">실패</div>
            <div class="metric-value">{len(failed_tickets)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 사이드바 빠른 보기
# =========================
st.sidebar.markdown("---")
quick_view = st.sidebar.radio(
    "빠른 보기",
    ["전체 티켓", "검토 대기", "실패 티켓"]
)


# =========================
# 티켓 생성
# =========================
st.markdown("---")
st.subheader("➕ 티켓 생성")

with st.form("create_ticket"):
    title = st.text_input("제목")
    content = st.text_area("내용")
    customer_type_label = st.selectbox("고객 유형", list(customer_type_map.keys()))
    channel_label = st.selectbox("채널", list(channel_map.keys()))

    submitted = st.form_submit_button("티켓 생성")

    if submitted:
        customer_type = customer_type_map[customer_type_label]
        channel = channel_map[channel_label]

        with st.spinner("티켓 생성 중입니다..."):
            result = safe_post_json(
                f"{API_BASE}/tickets",
                {
                    "title": title,
                    "content": content,
                    "customer_type": customer_type,
                    "channel": channel
                }
            )

        if result:
            st.success("티켓 생성 성공")
            st.rerun()


# =========================
# 티켓 조회 필터
# =========================
st.markdown("---")
st.subheader("📋 티켓 조회")

f1, f2, f3 = st.columns(3)

with f1:
    status_label = st.selectbox("상태", list(status_filter_map.keys()))

with f2:
    category_label = st.selectbox("카테고리", list(category_filter_map.keys()))

with f3:
    priority_label = st.selectbox("우선순위", list(priority_filter_map.keys()))

status_filter = status_filter_map[status_label]
category_filter = category_filter_map[category_label]
priority_filter = priority_filter_map[priority_label]

params = {}
if status_filter:
    params["status"] = status_filter
if category_filter:
    params["category"] = category_filter
if priority_filter:
    params["priority"] = priority_filter

filtered_tickets = safe_get_json(f"{API_BASE}/tickets", params=params) or []

if quick_view == "전체 티켓":
    tickets = filtered_tickets
elif quick_view == "검토 대기":
    tickets = review_queue
else:
    tickets = failed_tickets


# =========================
# 티켓 목록
# =========================
st.markdown("---")
st.subheader("📄 티켓 목록")

if not tickets:
    st.info("표시할 티켓이 없습니다.")
else:
    for ticket in tickets:
        ticket_id = ticket["ticket_id"]
        ticket_status = ticket.get("status")

        status_html = get_status_badge_html(ticket_status)
        category_label = category_map.get(ticket.get("category"), ticket.get("category"))
        priority_label = priority_map.get(ticket.get("priority"), ticket.get("priority"))

        with st.expander(f"[{ticket_id}] {ticket['title']}"):
            st.markdown(status_html, unsafe_allow_html=True)
            st.write(f"**카테고리:** {category_label}")
            st.write(f"**우선순위:** {priority_label}")

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                if ticket_status == "created":
                    if st.button("실행", key=f"run_{ticket_id}"):
                        with st.spinner("워크플로우 실행 중입니다..."):
                            result = safe_post_json(f"{API_BASE}/tickets/{ticket_id}/run")
                        if result:
                            st.success("워크플로우 실행 완료")
                            st.rerun()

            with c2:
                if ticket_status == "waiting_human_review":
                    if st.button("승인", key=f"approve_{ticket_id}"):
                        with st.spinner("승인 처리 중입니다..."):
                            result = safe_post_json(
                                f"{API_BASE}/tickets/{ticket_id}/approve",
                                {"reviewer": "admin", "comment": "관리자 승인 완료"}
                            )
                        if result:
                            st.success("승인 완료")
                            st.rerun()

            with c3:
                if ticket_status == "waiting_human_review":
                    if st.button("반려", key=f"reject_{ticket_id}"):
                        with st.spinner("반려 처리 중입니다..."):
                            result = safe_post_json(
                                f"{API_BASE}/tickets/{ticket_id}/reject",
                                {"reviewer": "admin", "comment": "표현 수정이 필요합니다."}
                            )
                        if result:
                            st.warning("반려 처리 완료")
                            st.rerun()

            with c4:
                if ticket_status in ["rejected", "failed_redraft"]:
                    if st.button("재작성", key=f"redraft_{ticket_id}"):
                        with st.spinner("답변을 재작성하는 중입니다..."):
                            result = safe_post_json(f"{API_BASE}/tickets/{ticket_id}/redraft")
                        if result:
                            st.success("재작성 완료")
                            st.rerun()

            with c5:
                if st.button("상세 보기", key=f"detail_{ticket_id}"):
                    st.session_state.selected_ticket_id = ticket_id
                    st.rerun()


# =========================
# 선택한 티켓 상세
# =========================
st.markdown("---")
st.subheader("📝 선택한 티켓 상세")

selected_ticket_id = st.session_state.selected_ticket_id

if selected_ticket_id is None:
    st.info("상세 보기를 누른 티켓이 없습니다.")
else:
    with st.spinner("상세 정보를 불러오는 중입니다..."):
        detail = safe_get_json(f"{API_BASE}/tickets/{selected_ticket_id}")

    if detail:
        st.write(f"**티켓 ID:** {detail.get('ticket_id')}")
        st.write(f"**제목:** {detail.get('title')}")
        st.write(f"**내용:** {detail.get('content')}")
        st.write(f"**상태:** {status_map.get(detail.get('status'), detail.get('status'))}")
        st.write(f"**카테고리:** {category_map.get(detail.get('category'), detail.get('category'))}")
        st.write(f"**우선순위:** {priority_map.get(detail.get('priority'), detail.get('priority'))}")

        st.markdown("#### Draft Reply")
        st.write(detail.get("draft_reply") or "-")

        st.markdown("#### Final Reply")
        st.write(detail.get("final_reply") or "-")

        st.markdown("#### 검토 정보")
        st.write(f"**검토자:** {detail.get('reviewer') or '-'}")
        st.write(f"**검토 결과:** {detail.get('review_decision') or '-'}")
        st.write(f"**검토 코멘트:** {detail.get('review_comment') or '-'}")

        st.markdown("#### Logs")
        logs = detail.get("logs", [])
        if logs:
            for log in logs:
                st.code(log)
        else:
            st.write("-")

        st.markdown("#### Errors")
        errors = detail.get("errors", [])
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.write("-")