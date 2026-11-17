import logging
import uuid

from app.apps.jobs.domain.eligibility import (
    SIMILARITY_MATCH_THRESHOLD,
    EligibilityAction,
    MatchBasis,
    audit_eligibility_denial,
    evaluate_job_eligibility,
    inferred_specialist_trade,
    trades_worth_scanning,
)
from app.shared_kernel.enums import TradeEnum


def test_worker_with_the_jobs_trade_is_eligible():
    result = evaluate_job_eligibility(
        job_trade=TradeEnum.PLUMBING,
        problem_description="Geyser leaking",
        worker_skills={TradeEnum.PLUMBING, TradeEnum.SOLAR},
    )
    assert result.is_eligible
    assert result.matched_by == MatchBasis.TRADE


def test_solar_installer_cannot_take_a_plumbing_job_and_is_told_why():
    result = evaluate_job_eligibility(
        job_trade=TradeEnum.PLUMBING,
        problem_description="Geyser leaking in the bathroom",
        worker_skills={TradeEnum.SOLAR},
    )
    assert not result.is_eligible
    assert result.matched_by is None
    assert "needs plumbing" in result.reason
    assert "solar installation" in result.reason


def test_specific_trade_jobs_are_never_widened_by_similarity():
    # Declared ELECTRICAL but described like plumbing: still needs an electrician.
    result = evaluate_job_eligibility(
        job_trade=TradeEnum.ELECTRICAL,
        problem_description="Geyser leaking in the bathroom, water everywhere",
        worker_skills={TradeEnum.PLUMBING},
    )
    assert not result.is_eligible


def test_clear_general_job_opens_to_the_matching_specialist():
    result = evaluate_job_eligibility(
        job_trade=TradeEnum.GENERAL_MAINTENANCE,
        problem_description="Geyser leaking in the bathroom, water everywhere",
        worker_skills={TradeEnum.PLUMBING},
    )
    assert result.is_eligible
    assert result.matched_by == MatchBasis.SIMILARITY
    assert result.similarity_score is not None
    assert result.similarity_score >= SIMILARITY_MATCH_THRESHOLD


def test_vague_general_job_stays_with_general_maintenance_workers():
    assert inferred_specialist_trade(TradeEnum.GENERAL_MAINTENANCE, "Need help with odd jobs") == (
        None,
        0.0,
    )
    trade, score = inferred_specialist_trade(
        TradeEnum.GENERAL_MAINTENANCE, "Build a wardrobe and fix cupboard doors"
    )
    assert trade is None
    assert score < SIMILARITY_MATCH_THRESHOLD
    assert not evaluate_job_eligibility(
        job_trade=TradeEnum.GENERAL_MAINTENANCE,
        problem_description="Need help with odd jobs",
        worker_skills={TradeEnum.PLUMBING},
    ).is_eligible


def test_worker_without_skills_is_asked_to_add_them():
    result = evaluate_job_eligibility(
        job_trade=TradeEnum.SOLAR, problem_description="Inverter beeping", worker_skills=set()
    )
    assert not result.is_eligible
    assert "Add your skills" in result.reason


def test_trades_worth_scanning_adds_general_jobs_only_for_skilled_workers():
    assert trades_worth_scanning({TradeEnum.SOLAR}) == [
        TradeEnum.GENERAL_MAINTENANCE,
        TradeEnum.SOLAR,
    ]
    assert trades_worth_scanning(set()) == []


def test_denials_are_audit_logged_with_structured_fields(caplog):
    eligibility = evaluate_job_eligibility(
        job_trade=TradeEnum.PLUMBING,
        problem_description="Burst pipe",
        worker_skills={TradeEnum.SOLAR},
    )
    worker_id, job_id = uuid.uuid4(), uuid.uuid4()
    with caplog.at_level(logging.WARNING, logger="maricho-api"):
        audit_eligibility_denial(
            action=EligibilityAction.OFFER,
            worker_id=worker_id,
            job_id=job_id,
            eligibility=eligibility,
            worker_skills={TradeEnum.SOLAR},
        )
    record = next(r for r in caplog.records if "job eligibility denied" in r.getMessage())
    assert record.audit["event"] == "job_eligibility_denied"
    assert record.audit["action"] == "OFFER"
    assert record.audit["required_trade"] == "PLUMBING"
    assert record.audit["worker_skills"] == ["SOLAR"]
    assert record.audit["job_id"] == str(job_id)
