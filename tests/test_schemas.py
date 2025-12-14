import json

from schemas.resume import BulletPoint, EvidenceItem, ExperienceEntry, Resume, TailoredResume


def test_resume_model_normalizes_skills():
    data = {
        "contact": {"name": "Alex Applicant"},
        "skills": ["Python ", "  Data"],
        "work_experience": [
            {
                "company": "Acme",
                "title": "Engineer",
                "bullets": [
                    {"text": "Did work", "evidence": {"text": "Did work"}}
                ],
            }
        ],
        "raw_text": "Acme Engineer",
    }
    resume = Resume.parse_obj(data)
    assert resume.skills == ["Python", "Data"]


def test_tailored_resume_parses_nested_resume():
    nested_resume = Resume(
        contact={"name": "Alex"},
        work_experience=[
            ExperienceEntry(
                company="Acme",
                title="Engineer",
                bullets=[BulletPoint(text="Did work", evidence=EvidenceItem(text="Did work"))],
            )
        ],
    )
    payload = {
        "tailored_resume": json.loads(nested_resume.json()),
        "keyword_alignment": {"found": ["python"], "missing": []},
        "questions": [],
        "missing_items": [],
    }
    tailored = TailoredResume.parse_obj(payload)
    assert tailored.tailored_resume.contact.name == "Alex"
    assert tailored.keyword_alignment.found == ["python"]
