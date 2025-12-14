from __future__ import annotations

import json
from typing import Tuple

from schemas.resume import Resume, TailoredResume

from .client import OpenAIClient
from .prompts import EXTRACTION_PROMPT, TAILORING_PROMPT


def extract_resume_json(api_key: str, model: str, raw_text: str) -> Resume:
    client = OpenAIClient(api_key=api_key, model=model)
    prompt = EXTRACTION_PROMPT.format(resume_text=raw_text)
    data = client.chat_json(prompt)
    resume = Resume.parse_obj(data)
    resume.raw_text = raw_text
    return resume


def tailor_resume(
    api_key: str,
    model: str,
    resume: Resume,
    job_description: str,
    template_name: str,
    template_source: str,
) -> TailoredResume:
    client = OpenAIClient(api_key=api_key, model=model)
    payload = json.loads(resume.json())
    prompt = TAILORING_PROMPT.format(
        resume_json=json.dumps(payload),
        job_description=job_description,
        template_name=template_name,
        template_source=template_source,
    )
    data = client.chat_json(prompt)
    return TailoredResume.parse_obj(data)


def run_pipeline(
    api_key: str,
    model: str,
    raw_text: str,
    job_description: str,
    template_name: str,
    template_source: str,
) -> Tuple[Resume, TailoredResume]:
    resume = extract_resume_json(api_key, model, raw_text)
    tailored = tailor_resume(
        api_key, model, resume, job_description, template_name, template_source
    )
    return resume, tailored
