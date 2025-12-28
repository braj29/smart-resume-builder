from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class EvidenceItem(BaseModel):
    text: Optional[str] = Field(
        default=None, description="Excerpt from resume text supporting the claim."
    )


class BulletPoint(BaseModel):
    text: Optional[str] = None
    evidence: Optional[EvidenceItem] = None


class ExperienceEntry(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletPoint] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    details: List[BulletPoint] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bullets: List[BulletPoint] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    evidence: Optional[EvidenceItem] = None


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None


class Resume(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    work_experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: List[Optional[str]] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    raw_text: Optional[str] = Field(
        default=None, description="Raw extracted text for traceability"
    )

    @validator("skills", each_item=True)
    def normalize_skill(cls, v: Optional[str]) -> Optional[str]:  # type: ignore
        if v is None:
            return None
        return v.strip()


class KeywordAlignment(BaseModel):
    found: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    tailored_resume: Resume
    keyword_alignment: KeywordAlignment = Field(
        default_factory=lambda: KeywordAlignment(found=[], missing=[])
    )
    questions: List[str] = Field(
        default_factory=list,
        description="Questions for user when data is ambiguous or missing",
    )
    missing_items: List[str] = Field(
        default_factory=list,
        description="Items requested in JD but unsupported by resume evidence",
    )
    latex_content: str | None = None
