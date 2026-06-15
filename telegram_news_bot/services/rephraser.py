import time
from google import genai
from google.api_core import exceptions as google_exceptions
from openai import OpenAI
from ..utils.config import GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, MAX_RETRY_ATTEMPTS
from ..utils.logger import get_logger

log = get_logger(__name__)

_gemini_quota_exhausted = False
_openrouter_client = None
_groq_client = None


def _get_openrouter_client() -> OpenAI | None:
    global _openrouter_client
    if _openrouter_client is None and OPENROUTER_API_KEY:
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    return _openrouter_client


def _try_openrouter(prompt: str, title: str) -> str | None:
    client = _get_openrouter_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=15,
        )
        result = response.choices[0].message.content.strip()
        log.info(f"OpenRouter rephrase success for: {title[:50]}")
        return result
    except Exception as e:
        log.warning(f"OpenRouter rephrase failed for {title[:50]}: {e}")
        return None


def _get_groq_client() -> OpenAI | None:
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        _groq_client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY,
        )
    return _groq_client


def _try_groq(prompt: str, title: str) -> str | None:
    client = _get_groq_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            timeout=15,
        )
        result = response.choices[0].message.content.strip()
        log.info(f"Groq rephrase success for: {title[:50]}")
        return result
    except Exception as e:
        log.warning(f"Groq rephrase failed for {title[:50]}: {e}")
        return None


def reset_quota_flag():
    global _gemini_quota_exhausted
    _gemini_quota_exhausted = False


def rephrase(title: str, content: str) -> str:
    global _gemini_quota_exhausted

    prompt = (
        "You are a professional news editor for a Telegram channel. "
        "Summarize the following news article in exactly 3 clear, factual, "
        "concise sentences suitable for a general audience. "
        "Do not use emojis. Do not use hashtags. Do not add any commentary. "
        "Output only the 3 sentences, nothing else.\n\n"
        f"Title: {title}\n\nContent: {content[:1500]}"
    )

    if _gemini_quota_exhausted:
        log.warning("Gemini quota known exhausted — trying OpenRouter")
        result = _try_openrouter(prompt, title)
        if result:
            return result
        log.warning("OpenRouter failed — trying Groq")
        result = _try_groq(prompt, title)
        if result:
            return result
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        log.error(f"Failed to init Gemini client: {e}")
        result = _try_openrouter(prompt, title)
        return result if result else None

    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )
            result = response.text.strip()
            log.info(f"Gemini rephrase success for: {title[:50]}")
            return result
        except google_exceptions.ResourceExhausted as e:
            log.error(f"429 quota exhausted — aborting all Gemini calls this run")
            _gemini_quota_exhausted = True
            break
        except Exception as e:
            log.warning(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                time.sleep(2 ** attempt)

    result = _try_openrouter(prompt, title)
    if result:
        return result

    log.warning("OpenRouter failed — trying Groq")
    result = _try_groq(prompt, title)
    if result:
        return result

    log.error(f"All rephrase attempts failed for: {title[:50]}")
    return None
