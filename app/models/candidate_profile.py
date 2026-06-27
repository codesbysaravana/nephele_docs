"""Pydantic v2 models for resume data and candidate profiling."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class CandidateLevel(str, Enum):
    """Classification of candidate experience level."""

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class Education(BaseModel):
    """A single education entry from a resume."""

    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    year: str = ""


class Project(BaseModel):
    """A single project entry from a resume."""

    title: str = ""
    description: str = ""
    technologies: List[str] = []


class Experience(BaseModel):
    """A single work experience entry from a resume."""

    role: str = ""
    company: str = ""
    duration: str = ""
    description: str = ""


class ResumeData(BaseModel):
    """Validated structured output from LLM resume extraction.

    All fields have safe defaults so partial LLM responses still
    produce a valid object.
    """

    name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = []
    technologies: List[str] = []
    projects: List[Project] = []
    experience: List[Experience] = []
    education: List[Education] = []
    certifications: List[str] = []
    domains: List[str] = []


class CandidateProfile(BaseModel):
    """Higher-level assessment built from ResumeData.

    Produced by the ProfileBuilder after heuristic analysis of the
    raw resume data.
    """

    resume_data: ResumeData
    candidate_level: CandidateLevel = CandidateLevel.BEGINNER
    primary_domains: List[str] = []
    strength_areas: List[str] = []
    project_count: int = 0
    total_experience_years: float = 0.0
    recommended_interview_focus: List[str] = []
