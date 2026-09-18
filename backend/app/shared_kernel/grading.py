# Pure functions shared by the workers app (vetting promotion) and the jobs
# app (match scoring) — no I/O, no port/DI needed (ADR-007).
from app.shared_kernel.enums import GradeEnum

GRADE_RANK: dict[GradeEnum, int] = {
    GradeEnum.REGISTERED: 0,
    GradeEnum.IDENTIFIED: 1,
    GradeEnum.APPRENTICE: 2,
    GradeEnum.JOURNEYMAN: 3,
    GradeEnum.EXPERT: 4,
}


def meets_minimum_grade(grade: GradeEnum | None, minimum: GradeEnum) -> bool:
    """True if `grade` is at least as senior as `minimum` in the GradeEnum progression."""
    if grade is None:
        return False
    return GRADE_RANK[grade] >= GRADE_RANK[minimum]
