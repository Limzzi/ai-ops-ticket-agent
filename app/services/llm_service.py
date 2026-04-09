from openai import OpenAI

from app.core.config import settings


client = OpenAI(api_key=settings.openai_api_key)


def call_llm(prompt: str, system_prompt: str = "너는 실무형 고객지원 AI 에이전트이다.") -> str:
    """
    OpenAI 모델을 호출하여 응답 텍스트를 반환한다.

    Args:
        prompt (str): 사용자 프롬프트
        system_prompt (str): 시스템 역할 프롬프트

    Returns:
        str: 모델이 생성한 응답 텍스트

    Raises:
        ValueError: prompt가 비어 있을 때 발생
        RuntimeError: 모델 응답 텍스트를 가져오지 못했을 때 발생
    """
    if not prompt.strip():
        raise ValueError("LLM을 호출하려면 prompt가 필요합니다.")

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    output_text = getattr(response, "output_text", "").strip()

    if not output_text:
        raise RuntimeError("LLM 응답 텍스트를 가져오지 못했습니다.")

    return output_text