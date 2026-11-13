import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.models.organization import Organization
from app.services.ai.grok_client import grok_client

logger = logging.getLogger("neurohr.intelligence.sentiment")

# Controlled Theme Taxonomy with curated regex patterns
THEME_TAXONOMY = {
    "Workload": r"\b(workload|overtime|burnout|long hours|task distribution|deadline|understaffed|capacity|bandwidth|exhausted|crunch|swamped|heavy load)\b",
    "Management": r"\b(manager|leadership|supervisor|micromanag|transparency|supportive|direction|guidance|executive|trust|communication from lead)\b",
    "Compensation": r"\b(salary|pay|compensation|bonus|raise|equity|market rate|remuneration|wage|underpaid)\b",
    "Career Growth": r"\b(growth|promotion|career|advancement|progression|opportunity|path|mobility|climb|next level)\b",
    "Work-Life Balance": r"\b(work-life|work life|balance|flexibility|remote|wfh|hybrid|family|pto|vacation|leave|personal time|flexible hours)\b",
    "Team Culture": r"\b(team|culture|collaboration|colleagues|peers|environment|inclusive|friendly|toxic|respect|camaraderie|morale)\b",
    "Recognition": r"\b(recognition|appreciated|reward|credit|valued|acknowledge|unnoticed|shoutout|celebrate)\b",
    "Training & Development": r"\b(training|learning|upskill|mentorship|courses|development|certifications|budget for learn|workshop)\b",
    "Benefits & Perks": r"\b(health insurance|benefits|wellness|perks|retirement|pension|stipend|gym|medical|dental)\b",
    "Tools & Infrastructure": r"\b(tools|software|hardware|equipment|laptop|system|infrastructure|technology|ui|slow system|buggy)\b"
}

CATEGORY_THEME_FALLBACK = {
    "WORKLOAD": "Workload",
    "MANAGEMENT": "Management",
    "BENEFITS": "Benefits & Perks",
    "CAREER": "Career Growth",
    "CULTURE": "Team Culture",
    "WORKPLACE": "Work-Life Balance",
    "ENGAGEMENT": "Recognition",
    "EXIT": "Career Growth"
}


WORKPLACE_LEXICON = {
    "burnout": -2.8,
    "burned out": -2.8,
    "overworked": -2.5,
    "underpaid": -2.6,
    "micromanage": -2.7,
    "micromanaged": -2.7,
    "micromanagement": -2.7,
    "understaffed": -2.3,
    "exhausting": -2.4,
    "exhausted": -2.4,
    "toxic": -3.2,
    "unrealistic": -2.1,
    "frustrating": -2.4,
    "frustration": -2.4,
    "unfair": -2.2,
    "supportive": 2.6,
    "collaborative": 2.4,
    "empowering": 2.8,
    "rewarding": 2.7,
    "transparent": 2.3,
    "fair": 2.0,
    "appreciation": 2.5,
    "appreciated": 2.5,
    "valued": 2.3,
    "mentorship": 2.2,
}


def get_org_id(org_link: Any) -> Any:
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link


class SentimentAnalysisService:
    _analyzer: Optional[SentimentIntensityAnalyzer] = None
    MODEL_NAME: str = "vader-sentiment"
    MODEL_VERSION: str = "3.3.2"

    @classmethod
    def get_analyzer(cls) -> SentimentIntensityAnalyzer:
        if cls._analyzer is None:
            analyzer = SentimentIntensityAnalyzer()
            analyzer.lexicon.update(WORKPLACE_LEXICON)
            cls._analyzer = analyzer
        return cls._analyzer

    @classmethod
    def analyze_text(cls, text: str) -> Dict[str, Any]:
        """
        Deterministic, reproducible sentiment scoring using VADER NLP.
        Produces compound valence (-1.0 to 1.0) and normalized pos/neu/neg proportions.
        Classification threshold:
        - compound >= 0.05: POSITIVE
        - compound <= -0.05: NEGATIVE
        - -0.05 < compound < 0.05: NEUTRAL
        """
        cleaned_text = text.strip() if text else ""
        if not cleaned_text:
            return {
                "sentiment": "NEUTRAL",
                "sentiment_score": {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "compound": 0.0},
                "model_name": cls.MODEL_NAME,
                "model_version": cls.MODEL_VERSION,
                "analyzed_at": datetime.now(timezone.utc)
            }

        analyzer = cls.get_analyzer()
        scores = analyzer.polarity_scores(cleaned_text)

        compound = scores["compound"]
        if compound >= 0.05:
            sentiment = "POSITIVE"
        elif compound <= -0.05:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"

        return {
            "sentiment": sentiment,
            "sentiment_score": {
                "positive": round(float(scores["pos"]), 4),
                "neutral": round(float(scores["neu"]), 4),
                "negative": round(float(scores["neg"]), 4),
                "compound": round(float(compound), 4)
            },
            "model_name": cls.MODEL_NAME,
            "model_version": cls.MODEL_VERSION,
            "analyzed_at": datetime.now(timezone.utc)
        }

    @classmethod
    async def analyze_feedback(
        cls,
        feedback: EmployeeFeedback,
        force_reanalyze: bool = False
    ) -> SentimentResult:
        """
        Analyze a single feedback record and persist SentimentResult.
        Adheres to Requirement 25: skips re-analysis if already analyzed with same model version.
        """
        org_ref = feedback.organization_id.to_ref() if hasattr(feedback.organization_id, "to_ref") else feedback.organization_id
        org_id = get_org_id(feedback.organization_id)

        existing_res = await SentimentResult.find_one({
            "feedback_id": feedback.feedback_id,
            "organization_id.$id": org_id
        })

        if existing_res and not force_reanalyze:
            if existing_res.model_name == cls.MODEL_NAME and existing_res.model_version == cls.MODEL_VERSION:
                return existing_res

        analysis = cls.analyze_text(feedback.feedback_text)

        if existing_res:
            existing_res.sentiment = analysis["sentiment"]
            existing_res.sentiment_score = analysis["sentiment_score"]
            existing_res.model_name = analysis["model_name"]
            existing_res.model_version = analysis["model_version"]
            existing_res.analyzed_at = analysis["analyzed_at"]
            await existing_res.save()
            return existing_res
        else:
            res = SentimentResult(
                organization_id=org_ref,
                feedback_id=feedback.feedback_id,
                employee_id=feedback.employee_id,
                sentiment=analysis["sentiment"],
                sentiment_score=analysis["sentiment_score"],
                model_name=analysis["model_name"],
                model_version=analysis["model_version"],
                analyzed_at=analysis["analyzed_at"]
            )
            await res.insert()
            return res

    @classmethod
    async def analyze_batch(
        cls,
        feedbacks: List[EmployeeFeedback],
        force_reanalyze: bool = False
    ) -> Tuple[int, int, int, Dict[str, int]]:
        """
        Batch analyze feedbacks for current organization.
        Returns: (total_evaluated, analyzed_count, skipped_count, sentiment_counts)
        """
        analyzed_count = 0
        skipped_count = 0
        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}

        for fb in feedbacks:
            org_id = get_org_id(fb.organization_id)
            existing = await SentimentResult.find_one({
                "feedback_id": fb.feedback_id,
                "organization_id.$id": org_id
            })

            if existing and not force_reanalyze and existing.model_version == cls.MODEL_VERSION:
                skipped_count += 1
                counts[existing.sentiment] = counts.get(existing.sentiment, 0) + 1
            else:
                res = await cls.analyze_feedback(fb, force_reanalyze=True)
                analyzed_count += 1
                counts[res.sentiment] = counts.get(res.sentiment, 0) + 1

        return len(feedbacks), analyzed_count, skipped_count, counts

    @classmethod
    def extract_themes(
        cls,
        feedbacks: List[EmployeeFeedback],
        sentiments_map: Dict[str, SentimentResult]
    ) -> List[Dict[str, Any]]:
        """
        Identify common workplace themes from stored feedback using taxonomy regex and category mapping.
        Calculates counts, percentage of total feedback, and positive/neutral/negative distribution.
        """
        if not feedbacks:
            return []

        theme_counts = defaultdict(int)
        theme_sentiments = defaultdict(lambda: {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0})
        total_items = len(feedbacks)

        for fb in feedbacks:
            matched_themes = set()
            text_lower = fb.feedback_text.lower()

            for theme_name, pattern in THEME_TAXONOMY.items():
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matched_themes.add(theme_name)

            # Fallback if no regex match was found but category gives a strong hint
            if not matched_themes:
                cat_upper = fb.category.upper()
                if cat_upper in CATEGORY_THEME_FALLBACK:
                    matched_themes.add(CATEGORY_THEME_FALLBACK[cat_upper])

            res = sentiments_map.get(fb.feedback_id)
            sent = res.sentiment if res else "NEUTRAL"

            for t in matched_themes:
                theme_counts[t] += 1
                theme_sentiments[t][sent] += 1

        result = []
        for theme_name, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / total_items) * 100, 1)
            result.append({
                "theme": theme_name,
                "count": count,
                "percentage": pct,
                "positive_count": theme_sentiments[theme_name]["POSITIVE"],
                "neutral_count": theme_sentiments[theme_name]["NEUTRAL"],
                "negative_count": theme_sentiments[theme_name]["NEGATIVE"],
            })

        return result

    @classmethod
    def aggregate_department_sentiment(
        cls,
        feedbacks: List[EmployeeFeedback],
        sentiments_map: Dict[str, SentimentResult]
    ) -> List[Dict[str, Any]]:
        """
        Computes department-level sentiment aggregations from stored feedback.
        """
        if not feedbacks:
            return []

        dept_groups = defaultdict(lambda: {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "total": 0})

        for fb in feedbacks:
            res = sentiments_map.get(fb.feedback_id)
            sent = res.sentiment if res else "NEUTRAL"
            dept = fb.department.strip() or "General"
            dept_groups[dept][sent] += 1
            dept_groups[dept]["total"] += 1

        items = []
        for dept, data in sorted(dept_groups.items(), key=lambda x: x[1]["total"], reverse=True):
            tot = data["total"]
            pos = data["POSITIVE"]
            neu = data["NEUTRAL"]
            neg = data["NEGATIVE"]
            items.append({
                "department": dept,
                "total_feedback": tot,
                "positive_count": pos,
                "neutral_count": neu,
                "negative_count": neg,
                "positive_pct": round((pos / tot) * 100, 1) if tot > 0 else 0.0,
                "neutral_pct": round((neu / tot) * 100, 1) if tot > 0 else 0.0,
                "negative_pct": round((neg / tot) * 100, 1) if tot > 0 else 0.0,
            })

        return items

    @classmethod
    def aggregate_trends(
        cls,
        feedbacks: List[EmployeeFeedback],
        sentiments_map: Dict[str, SentimentResult]
    ) -> List[Dict[str, Any]]:
        """
        Computes monthly sentiment trends using actual submitted_at timestamps.
        """
        if not feedbacks:
            return []

        period_groups = defaultdict(lambda: {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "total": 0})

        for fb in feedbacks:
            dt = fb.submitted_at or fb.created_at
            period = dt.strftime("%Y-%m")
            res = sentiments_map.get(fb.feedback_id)
            sent = res.sentiment if res else "NEUTRAL"
            period_groups[period][sent] += 1
            period_groups[period]["total"] += 1

        trends = []
        for period in sorted(period_groups.keys()):
            data = period_groups[period]
            tot = data["total"]
            pos = data["POSITIVE"]
            neu = data["NEUTRAL"]
            neg = data["NEGATIVE"]
            trends.append({
                "period": period,
                "positive_pct": round((pos / tot) * 100, 1) if tot > 0 else 0.0,
                "neutral_pct": round((neu / tot) * 100, 1) if tot > 0 else 0.0,
                "negative_pct": round((neg / tot) * 100, 1) if tot > 0 else 0.0,
                "total_count": tot
            })

        return trends

    @classmethod
    async def generate_ai_insight(
        cls,
        overall_stats: Dict[str, float],
        top_themes: List[Dict[str, Any]],
        dept_stats: List[Dict[str, Any]],
        department_filter: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Generate executive HR insight using Grok over aggregated context without PII.
        Fallback to deterministic template if Grok is offline or unconfigured.
        """
        total = int(overall_stats.get("total", 0))
        if total == 0:
            return "No sentiment data available for generating workplace insights.", False

        theme_names = [t["theme"] for t in top_themes[:3]]
        themes_text = ", ".join(theme_names) if theme_names else "Workplace environment"

        # Determine dominant sentiment
        pos_pct = overall_stats.get("positive_pct", 0.0)
        neu_pct = overall_stats.get("neutral_pct", 0.0)
        neg_pct = overall_stats.get("negative_pct", 0.0)

        dominant = "positive" if pos_pct >= max(neu_pct, neg_pct) else ("neutral" if neu_pct >= neg_pct else "negative")
        dominant_pct = pos_pct if dominant == "positive" else (neu_pct if dominant == "neutral" else neg_pct)

        # Build fallback summary
        if department_filter:
            fallback = (
                f"Within the {department_filter} department, sentiment is predominantly {dominant} "
                f"({dominant_pct}%). The primary topics identified in recent employee feedback include "
                f"{themes_text}."
            )
        else:
            fallback = (
                f"Overall workplace sentiment is predominantly {dominant} ({dominant_pct}% positive, "
                f"{neu_pct}% neutral, {neg_pct}% negative across {total} analyzed responses). "
                f"The key focus themes emerging from authorized feedback are {themes_text}."
            )

        if not grok_client.is_configured:
            return fallback, False

        # Structured context for Grok (ZERO PII, aggregated only)
        structured_context = {
            "scope": f"Department: {department_filter}" if department_filter else "Organization-Wide",
            "total_analyzed_responses": total,
            "overall_sentiment": {
                "positive_percentage": pos_pct,
                "neutral_percentage": neu_pct,
                "negative_percentage": neg_pct
            },
            "top_themes": [
                {
                    "theme": t["theme"],
                    "frequency_count": t["count"],
                    "positive_count": t["positive_count"],
                    "negative_count": t["negative_count"]
                }
                for t in top_themes[:4]
            ],
            "department_highlights": [
                {"department": d["department"], "positive_pct": d["positive_pct"], "negative_pct": d["negative_pct"]}
                for d in dept_stats[:3]
            ]
        }

        system_prompt = (
            "You are an expert HR Organizational Psychologist for NeuroHR X. "
            "Your task is to write a concise, actionable, and professional executive insight (2-3 sentences max) "
            "summarizing the provided workplace sentiment metrics. "
            "CRITICAL RULES: Base your summary EXCLUSIVELY on the provided numbers and themes. "
            "DO NOT invent facts, do not make assumptions beyond the data, and do not reference any individual employees."
        )

        user_prompt = f"Here are the aggregated workplace sentiment metrics:\n{structured_context}\n\nPlease generate a concise executive HR insight."

        try:
            insight_text = await grok_client.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=250
            )
            return insight_text.strip(), True
        except Exception as e:
            logger.warning("Grok AI insight generation failed or timed out: %s. Using fallback.", str(e))
            return fallback, False
