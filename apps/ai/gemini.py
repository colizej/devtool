"""
Gemini AI client — использует google-genai (актуальный SDK).
Зависимость: google-genai>=1.0
"""
import json
import logging
from decouple import config
from google import genai
from google.genai import types

logger = logging.getLogger('django')


class AIError(Exception):
    pass


# ─── Промпты ──────────────────────────────────────────────────────────────────

PROMPTS = {
    'title': """\
You are an SEO expert. A web page needs an improved title tag.

Page URL: {url}
Language of the site: {lang}
Current title: {title}
Current meta description: {meta_description}
Word count: {word_count}

Top GSC queries for this page:
{gsc_block}

Task:
- Suggest exactly 3 title variants (each max 60 characters)
- Each title should naturally include the most relevant query
- Titles must be in {lang}
- Explain in 1-2 sentences why the current title has low CTR

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "variants": ["title 1", "title 2", "title 3"],
  "explanation": "short explanation"
}}""",

    'description': """\
You are an SEO expert. A web page needs an improved meta description.

Page URL: {url}
Language of the site: {lang}
Current title: {title}
Current meta description: {meta_description}

Top GSC queries for this page:
{gsc_block}

Task:
- Suggest exactly 2 meta description variants (each 130-155 characters)
- Include a natural call-to-action
- Descriptions must be in {lang}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "variants": ["description 1", "description 2"],
  "explanation": "short explanation"
}}""",

    'h1': """\
You are an SEO expert. A web page is missing or has a poor H1 heading.

Page URL: {url}
Language of the site: {lang}
Current title: {title}
Current H1: {h1}
Word count: {word_count}

Top GSC queries for this page:
{gsc_block}

Task:
- Suggest exactly 2 H1 variants (each max 70 characters)
- H1 should differ slightly from the title — more descriptive
- Must be in {lang}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "variants": ["h1 variant 1", "h1 variant 2"],
  "explanation": "short explanation"
}}""",

    'ctr_analysis': """\
You are an SEO expert. A page has low CTR in Google Search.

Page URL: {url}
Language of the site: {lang}
Current title: {title}
Current meta description: {meta_description}

GSC performance data:
{gsc_block}

Task:
- Analyse why this page has low CTR
- Suggest the single best improved title (max 60 chars)
- Suggest the single best improved meta description (130-155 chars)
- Both must be in {lang}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "analysis": "2-3 sentence analysis",
  "title": "improved title",
  "description": "improved description"
}}""",
}


def _build_gsc_block(gsc_queries: list) -> str:
    if not gsc_queries:
        return '(no GSC data available)'
    lines = []
    for q in gsc_queries:
        lines.append(
            f"  query: \"{q['query']}\" | "
            f"impressions: {q['impressions']} | "
            f"clicks: {q['clicks']} | "
            f"CTR: {q['ctr']:.1f}% | "
            f"position: {q['position']:.1f}"
        )
    return '\n'.join(lines)


# ─── Client ───────────────────────────────────────────────────────────────────

class GeminiClient:
    MODEL = 'gemini-1.5-flash'

    def __init__(self):
        api_key = config('GEMINI_API_KEY', default='')
        if not api_key:
            raise AIError('GEMINI_API_KEY is not set. Add it to .env')
        self._client = genai.Client(api_key=api_key)

    def generate(self, rec_type: str, input_data: dict) -> tuple[dict, int]:
        """
        Build prompt → call Gemini → parse JSON response.
        Returns (result_dict, tokens_used).
        Raises AIError on failure.
        """
        if rec_type not in PROMPTS:
            raise AIError(f'Unknown rec_type: {rec_type}')

        crawl   = input_data.get('crawl', {})
        queries = input_data.get('gsc_queries', [])

        prompt = PROMPTS[rec_type].format(
            url=input_data.get('url', ''),
            lang=input_data.get('lang', 'English'),
            title=crawl.get('title', '') or '(missing)',
            meta_description=crawl.get('meta_description', '') or '(missing)',
            h1=crawl.get('h1', '') or '(missing)',
            word_count=crawl.get('word_count', 0),
            gsc_block=_build_gsc_block(queries),
        )

        try:
            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                ),
            )
        except Exception as e:
            raise AIError(f'Gemini API error: {e}') from e

        raw_text = response.text.strip() if response.text else ''
        tokens   = (response.usage_metadata.total_token_count
                    if response.usage_metadata else 0)

        # На случай если модель всё же обернула в ```
        if raw_text.startswith('```'):
            raw_text = raw_text.split('```', 2)[1]
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error('Gemini non-JSON response: %s', raw_text[:500])
            raise AIError(f'Gemini returned invalid JSON: {e}') from e

        return result, tokens
