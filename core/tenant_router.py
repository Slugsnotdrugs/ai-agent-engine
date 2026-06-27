"""
core/tenant_router.py
────────────────────────────────────────────────────────────────────────────
Config-driven tenant routing layer that sits in front of the Orchestrator.

Callers identify themselves with a tenant_id.  The router resolves the
correct industry profile (and any tenant-level overrides) automatically —
no profile knowledge required by the caller.

Tenant data lives in industry_profiles/tenants.json.  Add / edit / disable
tenants there; no code changes or redeployment needed.

Pipeline (per request)
──────────────────────
  tenant_id + raw_input
        │
        ▼
  TenantRouter.run()
        │  looks up tenant → resolves profile + merges overrides
        ▼
  Orchestrator.run()         ← existing privacy pipeline unchanged
        │
        ▼
  TenantResult               ← OrchestratorResult + tenant metadata

Storage evolution (no interface change needed)
──────────────────────────────────────────────
  Now      → tenants.json   (TenantConfigReader)
  Later    → swap _load() to read from Postgres / Redis / REST API
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.orchestrator import Orchestrator, OrchestratorResult

logger = logging.getLogger(__name__)


# ──────────────────────────── Data structures ────────────────────────────────

@dataclass
class TenantResult:
    """
    Wraps OrchestratorResult with tenant-aware metadata.
    Everything the caller needs in one object.
    """
    tenant_id: str
    display_name: str
    orchestrator_result: OrchestratorResult

    # Convenience pass-throughs so callers don't have to drill into the nested object
    @property
    def final_text(self) -> str:
        return self.orchestrator_result.final_text

    @property
    def profile_used(self) -> str:
        return self.orchestrator_result.profile

    @property
    def elapsed_seconds(self) -> float:
        return self.orchestrator_result.elapsed_seconds

    @property
    def usage_summary(self) -> str:
        return self.orchestrator_result.cloud_response.usage_summary


# ──────────────────────────── Config reader ──────────────────────────────────

class TenantConfigReader:
    """
    Reads and validates tenant definitions from a JSON file.

    This is the only class you replace when moving from flat-file
    to a database or admin API.  The TenantRouter never calls it
    directly — it goes through the three public methods below.
    """

    def __init__(self, config_path: str | Path) -> None:
        self._path = Path(config_path)
        self._tenants: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------ public

    def get(self, tenant_id: str) -> dict[str, Any]:
        """
        Return the config dict for *tenant_id*.

        Raises
        ──────
        KeyError  : tenant not found
        PermissionError : tenant exists but active=false
        """
        if tenant_id not in self._tenants:
            raise KeyError(
                f"Unknown tenant '{tenant_id}'. "
                f"Register it in {self._path} or call list_tenants() to see available IDs."
            )
        cfg = self._tenants[tenant_id]
        if not cfg.get("active", True):
            raise PermissionError(
                f"Tenant '{tenant_id}' is currently inactive. "
                "Set active=true in tenants.json to re-enable."
            )
        return cfg

    def list_tenants(self, include_inactive: bool = False) -> list[str]:
        if include_inactive:
            return list(self._tenants)
        return [tid for tid, cfg in self._tenants.items() if cfg.get("active", True)]

    def reload(self) -> None:
        """Hot-reload without restarting the process."""
        self._load()
        logger.info("Tenant config reloaded from %s", self._path)

    # ----------------------------------------------------------------- private

    def _load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"Tenant config not found: {self._path}")

        with self._path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        self._tenants = data.get("tenants", {})

        # Basic validation
        for tid, cfg in self._tenants.items():
            if "profile" not in cfg:
                raise ValueError(
                    f"Tenant '{tid}' is missing required field 'profile' in {self._path}"
                )

        logger.debug(
            "Loaded %d tenant(s) from %s (%d active).",
            len(self._tenants),
            self._path,
            sum(1 for c in self._tenants.values() if c.get("active", True)),
        )


# ──────────────────────────── Tenant router ──────────────────────────────────

class TenantRouter:
    """
    Routes incoming requests to the correct Orchestrator profile
    based on tenant identity — callers need no profile knowledge.

    Parameters
    ──────────
    orchestrator  : configured Orchestrator instance (shared across tenants)
    tenants_path  : path to tenants.json

    Example
    ───────
    from core.tenant_router import TenantRouter
    from core.orchestrator import Orchestrator
    from core.privacy_manager import PrivacyManager
    from core.cloud_client import CloudClient

    router = TenantRouter(
        orchestrator=Orchestrator(
            privacy_manager=PrivacyManager(),
            cloud_client=CloudClient(),
            config_path="industry_profiles/template/prompts.json",
        ),
        tenants_path="industry_profiles/tenants.json",
    )

    result = router.run("clinic_nyc", "Patient Jane Doe, DOB 01/01/1980 …")
    print(result.final_text)
    print(result.profile_used)      # "medical"
    print(result.usage_summary)
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        tenants_path: str | Path,
    ) -> None:
        self._orchestrator = orchestrator
        self._tenants = TenantConfigReader(tenants_path)

        logger.info(
            "TenantRouter ready. Active tenants: %s",
            self._tenants.list_tenants(),
        )

    # ------------------------------------------------------------------ public

    def run(
        self,
        tenant_id: str,
        raw_input: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> TenantResult:
        """
        Route *raw_input* through the privacy pipeline for *tenant_id*.

        Parameters
        ──────────
        tenant_id     : registered tenant identifier (from tenants.json)
        raw_input     : original, potentially sensitive text
        extra_metadata: merged into the OrchestratorResult metadata field

        Raises
        ──────
        KeyError        : tenant_id not registered
        PermissionError : tenant is inactive
        """
        tenant_cfg = self._tenants.get(tenant_id)   # raises if unknown / inactive

        profile       = tenant_cfg["profile"]
        display_name  = tenant_cfg.get("display_name", tenant_id)
        t_overrides   = tenant_cfg.get("model_overrides", {})

        logger.info(
            "Routing tenant='%s' → profile='%s'", tenant_id, profile
        )

        # Merge tenant-level model overrides into metadata so Orchestrator
        # can pass them through to CloudClient via the profile config.
        # (A more advanced version would patch the profile config directly.)
        combined_metadata = {
            "tenant_id": tenant_id,
            "tenant_display_name": display_name,
            "tenant_model_overrides": t_overrides,
            "tenant_metadata": tenant_cfg.get("metadata", {}),
            **(extra_metadata or {}),
        }

        orch_result = self._orchestrator.run(
            raw_input=raw_input,
            profile=profile,
            extra_metadata=combined_metadata,
        )

        return TenantResult(
            tenant_id=tenant_id,
            display_name=display_name,
            orchestrator_result=orch_result,
        )

    def reload(self) -> None:
        """Hot-reload both tenant and profile configs at runtime."""
        self._tenants.reload()
        self._orchestrator.reload_profiles()
        logger.info("TenantRouter: all configs reloaded.")

    @property
    def active_tenants(self) -> list[str]:
        return self._tenants.list_tenants()

    @property
    def all_tenants(self) -> list[str]:
        return self._tenants.list_tenants(include_inactive=True)
