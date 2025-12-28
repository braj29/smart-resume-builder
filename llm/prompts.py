EXTRACTION_PROMPT = """
You are a resume parser. Extract the resume into the following JSON schema and nothing else.
Schema:
{{
  "contact": {{
    "name": string|null,
    "email": string|null,
    "phone": string|null,
    "linkedin": string|null,
    "website": string|null,
    "location": string|null
  }},
  "summary": string|null,
  "work_experience": [
    {{
      "company": string,
      "title": string,
      "location": string|null,
      "start_date": string|null,
      "end_date": string|null,
      "bullets": [
        {{
          "text": string|null,
          "evidence": {{"text": string}}|null
        }}
      ]
    }}
  ],
  "education": [
    {{
      "institution": string,
      "degree": string|null,
      "field": string|null,
      "start_date": string|null,
      "end_date": string|null,
      "details": [
        {{
          "text": string|null,
          "evidence": {{"text": string}}|null
        }}
      ]
    }}
  ],
  "skills": [string],
  "projects": [
    {{
      "name": string,
      "description": string|null,
      "bullets": [
        {{
          "text": string|null,
          "evidence": {{"text": string}}|null
        }}
      ]
    }}
  ],
  "certifications": [
    {{
      "name": string,
      "issuer": string|null,
      "date": string|null,
      "evidence": {{"text": string}}|null
    }}
  ],
  "raw_text": string
}}

Rules:
- Use ONLY information found in the resume text below.
- Evidence is preferred but not required; use null when unavailable.
- Preserve chronology and factual accuracy; do not fabricate.
- If a field is missing, set it to null or an empty array.
- Return ONLY JSON.
Resume text:
{resume_text}
"""


TAILORING_PROMPT = """
You are tailoring a resume to a job description with zero fabrication.
Input JSON (ground truth with evidence): {resume_json}
Job Description: {job_description}
Target template name: {template_name}
Template source (fill the placeholders with grounded content):
{template_source}

Rules:
- Use only facts that exist in the JSON. If it is not in JSON+evidence, it cannot appear.
- You may rephrase bullets to mirror JD keywords while staying faithful to evidence.
- Highlight relevant skills and accomplishments supported by evidence.
- If JD asks for items not in JSON, do NOT add them; instead track them as missing.
- Keep chronology and dates intact.
- Evidence fields may be null when not available; do not invent evidence.

Produce a LaTeX body that fits the chosen template placeholders. Also compute:
- keyword_alignment: which JD keywords were found vs missing in resume JSON
- questions: clarifying questions for missing dates/roles if ambiguous
- missing_items: JD asks for but not evidenced in resume
Return JSON with fields:
{{
  "tailored_resume": <same schema as resume_json but with rewritten bullets/summary>,
  "keyword_alignment": {{"found": [string], "missing": [string]}},
  "questions": [string],
  "missing_items": [string]
}}
Return ONLY JSON.
"""
