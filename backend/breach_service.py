"""
Pluggable Breach Data Source — Interface + Adapters
====================================================
Switch implementation via BREACH_CHECKER env var: "hibp" | "mock"

HIBP (Have I Been Pwned):
  - Gold standard, 700+ breaches, $3.50/month API key
  - Requires HIBP_API_KEY env var
  - Rate limited: 1 req / 1.5s

Mock:
  - Returns fake breach data for testing / demo
  - No API key needed
"""

import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)


# ── Data Transfer Objects ──────────────────────────

@dataclass
class BreachResult:
    """Single breach record returned by any adapter."""
    source_name: str
    breach_date: Optional[date] = None
    data_classes: List[str] = field(default_factory=list)
    severity: str = "medium"  # low | medium | high | critical


# ── Abstract Interface ─────────────────────────────

class BreachChecker(ABC):
    """Abstract interface — implement this for any breach data source."""

    @abstractmethod
    async def check(self, email: str) -> List[BreachResult]:
        """Check an email against breach database. Returns list of breaches."""
        ...

    @staticmethod
    def classify_severity(data_classes: List[str]) -> str:
        """Heuristic severity based on data types exposed."""
        critical_types = {"Passwords", "Credit cards", "Bank account numbers", "Social security numbers"}
        high_types = {"Phone numbers", "Physical addresses", "IP addresses", "Dates of birth"}
        exposed = set(data_classes)
        if exposed & critical_types:
            return "critical"
        if exposed & high_types:
            return "high"
        if "Email addresses" in exposed or "Usernames" in exposed:
            return "medium"
        return "low"


# ── HIBP Adapter ───────────────────────────────────

class HIBPAdapter(BreachChecker):
    """Have I Been Pwned API v3 adapter."""

    BASE_URL = "https://haveibeenpwned.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HIBP_API_KEY", "")
        if not self.api_key:
            logger.warning("HIBP_API_KEY not set — HIBP adapter will return errors")

    async def check(self, email: str) -> List[BreachResult]:
        if not self.api_key:
            logger.error("HIBP API key not configured")
            return []

        headers = {
            "hibp-api-key": self.api_key,
            "user-agent": "ShieldOps-BreachMonitor/1.0",
        }
        results: List[BreachResult] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/breachedaccount/{email}",
                    headers=headers,
                    params={"truncateResponse": "false"},
                )

                if resp.status_code == 404:
                    return []  # no breaches found
                if resp.status_code == 429:
                    logger.warning("HIBP rate limited — retry later")
                    return []
                resp.raise_for_status()

                for breach in resp.json():
                    breach_date = None
                    if breach.get("BreachDate"):
                        try:
                            breach_date = date.fromisoformat(breach["BreachDate"])
                        except ValueError:
                            pass
                    data_classes = breach.get("DataClasses", [])
                    results.append(BreachResult(
                        source_name=breach.get("Name", "Unknown"),
                        breach_date=breach_date,
                        data_classes=data_classes,
                        severity=self.classify_severity(data_classes),
                    ))
        except httpx.HTTPError as e:
            logger.error(f"HIBP API error: {e}")

        return results


# ── Mock Adapter (for testing / demo) ─────────────

class MockBreachAdapter(BreachChecker):
    """Returns realistic fake breach data for testing."""

    MOCK_BREACHES = [
        BreachResult(
            source_name="LinkedIn",
            breach_date=date(2012, 5, 5),
            data_classes=["Email addresses", "Passwords"],
            severity="critical",
        ),
        BreachResult(
            source_name="Adobe",
            breach_date=date(2013, 10, 4),
            data_classes=["Email addresses", "Passwords", "Usernames"],
            severity="critical",
        ),
        BreachResult(
            source_name="Dropbox",
            breach_date=date(2012, 7, 1),
            data_classes=["Email addresses", "Passwords"],
            severity="critical",
        ),
        BreachResult(
            source_name="Canva",
            breach_date=date(2019, 5, 24),
            data_classes=["Email addresses", "Usernames", "Geographic locations"],
            severity="medium",
        ),
        BreachResult(
            source_name="MyFitnessPal",
            breach_date=date(2018, 2, 1),
            data_classes=["Email addresses", "IP addresses", "Passwords", "Usernames"],
            severity="high",
        ),
    ]

    async def check(self, email: str) -> List[BreachResult]:
        """Return a deterministic subset of mock breaches based on email hash."""
        email_hash = int(hashlib.md5(email.encode()).hexdigest(), 16)
        count = (email_hash % len(self.MOCK_BREACHES)) + 1
        return self.MOCK_BREACHES[:count]


# ── Factory ────────────────────────────────────────

def get_breach_checker() -> BreachChecker:
    """Factory: returns the configured breach checker based on BREACH_CHECKER env var."""
    checker_type = os.getenv("BREACH_CHECKER", "mock").lower()
    if checker_type == "hibp":
        return HIBPAdapter()
    return MockBreachAdapter()
