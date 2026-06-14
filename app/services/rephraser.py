import time
from google import genai
from groq import Groq
from app.utils.config import GEMINI_API_KEY, GROQ_API_KEY
from app.utils.logger import logger
from app.database.queries import insert_log

PROMPT_TEMPLATE = """
Summarize the following crypto news article in exactly 3 sentences in English.
Be concise, factual, and suitable for a Telegram news channel.
Do not add opinions. Output only the 3-sentence summary, nothing else.

Title: {title}
Content: {content}
""".strip()


def rephrase(title: str, content: str, article_id: str = None) -> str:
    """
    Try Gemini → Groq → raw fallback.
    Always returns a non-empty string in English.
    """
    prompt = PROMPT_TEMPLATE.format(title=title, content=content[:2000])

    # ── Try Gemini ─────────────────────────────────
    result = _try_gemini(prompt)
    if result:
        return result

    insert_log("AI", "Gemini failed — trying Groq", article_id)

    # ── Try Groq ───────────────────────────────────
    result = _try_groq(prompt)
    if result:
        return result

    insert_log("AI", "Groq failed — using raw content fallback", article_id)

    # ── Raw fallback ───────────────────────────────
    return content[:300].strip() + "..."


def _try_gemini(prompt: str) -> str | None:
    for attempt in range(2):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = resp.text.strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None


def _try_groq(prompt: str) -> str | None:
    for attempt in range(2):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            chat = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            text = chat.choices[0].message.content.strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Groq attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None
