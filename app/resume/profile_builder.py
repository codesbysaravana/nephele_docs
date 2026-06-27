"""Builds a CandidateProfile from extracted ResumeData using heuristic
analysis of experience, projects, skills, and domains."""

import logging
import re
from typing import List

from app.models.candidate_profile import (
    CandidateLevel,
    CandidateProfile,
    ResumeData,
)

logger = logging.getLogger(__name__)

# Domain keyword mapping — maps technology / skill keywords to high-level
# domain names. Keys are lowercase for case-insensitive matching.
_DOMAIN_KEYWORDS: dict[str, str] = {
    # Web Development
    "react": "Web Development",
    "angular": "Web Development",
    "vue": "Web Development",
    "nextjs": "Web Development",
    "next.js": "Web Development",
    "html": "Web Development",
    "css": "Web Development",
    "javascript": "Web Development",
    "typescript": "Web Development",
    "django": "Web Development",
    "flask": "Web Development",
    "fastapi": "Web Development",
    "express": "Web Development",
    "node.js": "Web Development",
    "nodejs": "Web Development",
    # Data Science / ML
    "machine learning": "Machine Learning",
    "deep learning": "Machine Learning",
    "tensorflow": "Machine Learning",
    "pytorch": "Machine Learning",
    "keras": "Machine Learning",
    "scikit-learn": "Machine Learning",
    "sklearn": "Machine Learning",
    "pandas": "Data Science",
    "numpy": "Data Science",
    "data analysis": "Data Science",
    "data science": "Data Science",
    "nlp": "Machine Learning",
    "computer vision": "Machine Learning",
    # DevOps / Cloud
    "docker": "DevOps",
    "kubernetes": "DevOps",
    "k8s": "DevOps",
    "ci/cd": "DevOps",
    "jenkins": "DevOps",
    "terraform": "DevOps",
    "ansible": "DevOps",
    "aws": "Cloud Computing",
    "azure": "Cloud Computing",
    "gcp": "Cloud Computing",
    "google cloud": "Cloud Computing",
    # Mobile
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "flutter": "Mobile Development",
    "react native": "Mobile Development",
    "swift": "Mobile Development",
    "kotlin": "Mobile Development",
    # Databases
    "sql": "Database Management",
    "mysql": "Database Management",
    "postgresql": "Database Management",
    "mongodb": "Database Management",
    "redis": "Database Management",
    # Security
    "cybersecurity": "Cybersecurity",
    "penetration testing": "Cybersecurity",
    "security": "Cybersecurity",
    # Embedded / IoT
    "embedded": "Embedded Systems",
    "iot": "IoT",
    "arduino": "IoT",
    "raspberry pi": "IoT",
}


class ProfileBuilder:
    """Analyses ``ResumeData`` heuristically and produces a ``CandidateProfile``
    with level classification, domain identification, and interview focus
    recommendations."""

    def build(self, resume_data: ResumeData) -> CandidateProfile:
        """Build a ``CandidateProfile`` from validated ``ResumeData``.

        Args:
            resume_data: Structured resume data produced by the extractor.

        Returns:
            A fully populated ``CandidateProfile``.
        """

        project_count = len(resume_data.projects)
        total_years = self._estimate_experience_years(resume_data.experience)
        candidate_level = self._determine_level(total_years, project_count)
        primary_domains = self._identify_domains(resume_data)
        strength_areas = self._identify_strengths(resume_data)
        interview_focus = self._recommend_focus(
            resume_data, candidate_level, strength_areas, primary_domains
        )

        profile = CandidateProfile(
            resume_data=resume_data,
            candidate_level=candidate_level,
            primary_domains=primary_domains,
            strength_areas=strength_areas,
            project_count=project_count,
            total_experience_years=round(total_years, 1),
            recommended_interview_focus=interview_focus,
        )

        logger.info(
            "Profile built — level=%s, years=%.1f, projects=%d, domains=%s",
            candidate_level.value,
            total_years,
            project_count,
            primary_domains,
        )
        return profile

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_experience_years(
        experiences: list,  # List[Experience]
    ) -> float:
        """Parse experience durations heuristically and sum total years.

        Handles patterns like:
        - "2 years"
        - "6 months"
        - "1 year 3 months"
        - "Jan 2020 - Mar 2022"  (falls back to year-diff)
        - "3 yrs"
        - "2019 - 2023"
        """

        total_years = 0.0

        for exp in experiences:
            duration = exp.duration.strip().lower() if exp.duration else ""
            if not duration:
                continue

            parsed = 0.0

            # Pattern: "X year(s)" or "X yr(s)"
            year_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|yr)s?", duration)
            if year_match:
                parsed += float(year_match.group(1))

            # Pattern: "X month(s)" or "X mo(s)"
            month_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:month|mo)s?", duration)
            if month_match:
                parsed += float(month_match.group(1)) / 12.0

            # Fallback: "YYYY - YYYY" (4-digit years)
            if parsed == 0.0:
                year_range = re.findall(r"(\d{4})", duration)
                if len(year_range) >= 2:
                    start_year = int(year_range[0])
                    end_year = int(year_range[-1])
                    diff = end_year - start_year
                    if 0 < diff <= 50:
                        parsed = float(diff)

            # Fallback: "X+ years" or bare number
            if parsed == 0.0:
                bare_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*$", duration)
                if bare_match:
                    parsed = float(bare_match.group(1))

            total_years += parsed
            logger.debug("Duration '%s' → %.2f years", exp.duration, parsed)

        return total_years

    @staticmethod
    def _determine_level(
        total_years: float, project_count: int
    ) -> CandidateLevel:
        """Classify the candidate level.

        Rules:
        - ADVANCED: 5+ years OR 6+ projects
        - INTERMEDIATE: 2-4 years AND 2-5 projects
        - BEGINNER: everything else (0-1 years or < 2 projects)
        """

        if total_years >= 5 or project_count >= 6:
            return CandidateLevel.ADVANCED
        if total_years >= 2 and project_count >= 2:
            return CandidateLevel.INTERMEDIATE
        return CandidateLevel.BEGINNER

    @staticmethod
    def _identify_domains(resume_data: ResumeData) -> List[str]:
        """Identify primary domains from skills, technologies, and explicit
        resume domains."""

        domains: set[str] = set()

        # Include explicitly listed domains from the LLM extraction
        for domain in resume_data.domains:
            if domain.strip():
                domains.add(domain.strip())

        # Map skills and technologies to domains
        all_terms = [s.lower() for s in resume_data.skills + resume_data.technologies]
        for term in all_terms:
            for keyword, domain in _DOMAIN_KEYWORDS.items():
                if keyword in term:
                    domains.add(domain)

        return sorted(domains) if domains else ["General Software Development"]

    @staticmethod
    def _identify_strengths(resume_data: ResumeData) -> List[str]:
        """Identify strength areas based on skill / technology frequency and
        project coverage."""

        strengths: list[str] = []

        if len(resume_data.skills) >= 5:
            strengths.append("Broad Skill Set")
        if len(resume_data.projects) >= 3:
            strengths.append("Project Experience")
        if len(resume_data.certifications) >= 1:
            strengths.append("Certified Professional")
        if len(resume_data.experience) >= 2:
            strengths.append("Industry Experience")
        if len(resume_data.technologies) >= 5:
            strengths.append("Technology Breadth")

        # Check for specific tech depth
        tech_lower = [t.lower() for t in resume_data.technologies]
        if any(t in tech_lower for t in ("python", "java", "c++", "go", "rust")):
            strengths.append("Core Programming Languages")
        if any(t in tech_lower for t in ("aws", "gcp", "azure")):
            strengths.append("Cloud Platform Experience")

        return strengths if strengths else ["General"]

    @staticmethod
    def _recommend_focus(
        resume_data: ResumeData,
        level: CandidateLevel,
        strengths: List[str],
        domains: List[str],
    ) -> List[str]:
        """Recommend interview focus areas based on profile characteristics."""

        focus: list[str] = []

        # Always include top skills
        if resume_data.skills:
            focus.append(f"Technical depth in {', '.join(resume_data.skills[:3])}")

        # Domain-specific focus
        for domain in domains[:2]:
            focus.append(f"{domain} concepts and best practices")

        # Level-calibrated focus
        if level == CandidateLevel.BEGINNER:
            focus.append("Fundamentals and problem-solving approach")
            focus.append("Learning ability and growth mindset")
        elif level == CandidateLevel.INTERMEDIATE:
            focus.append("System design basics and trade-off analysis")
            focus.append("Team collaboration and code review practices")
        else:  # ADVANCED
            focus.append("Architecture and system design at scale")
            focus.append("Technical leadership and mentoring")

        # Project-specific focus
        if resume_data.projects:
            focus.append(
                f"Deep dive into project: {resume_data.projects[0].title or 'Primary project'}"
            )

        return focus[:6]  # Cap at 6 focus areas
