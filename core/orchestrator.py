"""
core/orchestrator.py
────────────────────────────────────────────────────────────────────────────
Central orchestration layer for the hybrid-privacy AI agent engine.

Pipeline (per request)
──────────────────────
  raw input
      │
      ▼
  PrivacyManager.mask()          ← runs locally, never leaves the network
      │  masked_text + entity_map
      ▼
  PromptBuilder.build()          ← injects system/user prompts from profile
      │  messages list
      ▼
  CloudClient.complete()         ← clean data sent to cloud model
      │  CloudResponse (masked reply)
      ▼
  PrivacyManager.unmask()        ← entity_map re-injected locally
      │
      ▼
  OrchestratorResult             ← returned to caller
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.cloud_client import CloudClient, CloudResponse
from core.privacy_manager import PrivacyManager        # your existing module

logger = logging.getLogger(__name__)


# ──────────────────────────── Data structures ────────────────────────────────

@dataclass
class OrchestratorResult:
    """Full audit trail returned to the caller after one pipeline run."""
    final_text: str                    # unmasked, ready-to-use response
    masked_input: str                  # what was actually sent to the cloud
    masked_output: str                 # raw cloud reply (still masked)
    cloud_response: CloudResponse      # full cloud metadata
    profile: str                       # which industry profile was used
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────── Config reader ──────────────────────────────────

class ProfileConfigReader:
    """
    Reads industry profile configurations from a JSON file.

    Expected file layout (see industry_profiles/template/prompts.json):
    {
      "profiles": {
        "<profile_name>": {
          "system_prompt": "...",
          "user_prompt_template": "...",   // use {input} as the placeholder
          "model_overrides": {},           // optional: temperature, max_tokens …
          "metadata": {}                   // arbitrary extra fields
        }
      }
    }
    """

    def __init__(self, config_path: str | Path) -> None:
        self._path = Path(config_path)
        self._data: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------ public

    def get_profile(self, name: str) -> dict[str, Any]:
        """Return the config dict for *name*, raising KeyError if absent."""
        profiles = self._data.get("profiles", {})
        if name not in profiles:
            available = list(profiles)
            raise KeyError(
                f"Profile '{name}' not found. Available: {available}"
            )
        return profiles[name]

    def list_profiles(self) -> list[str]:
        return list(self._data.get("profiles", {}).keys())

    def reload(self) -> None:
        """Hot-reload the JSON file without restarting the process."""
        self._load()
        logger.info("Profile config reloaded from %s", self._path)

    # ----------------------------------------------------------------- private

    def _load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(
                f"Profile config not found: {self._path}"
            )
        with self._path.open(encoding="utf-8") as fh:
            self._data = json.load(fh)
        logger.debug(
            "Loaded %d profile(s) from %s",
            len(self._data.get("profiles", {})),
            self._path,
        )


# ──────────────────────────── Prompt builder ─────────────────────────────────

class PromptBuilder:
    """Turns a profile config + masked input into an OpenAI messages list."""

    @staticmethod
    def build(
        profile_config: dict[str, Any],
        masked_input: str,
    ) -> list[dict[str, str]]:
        """
        Construct the messages array.

        The user_prompt_template supports one placeholder: {input}
        Additional placeholders can be added via profile_config["variables"].
        """
        system_prompt: str = profile_config.get("system_prompt", "")
        user_template: str = profile_config.get(
            "user_prompt_template", "{input}"
        )
        variables: dict[str, str] = profile_config.get("variables", {})

        # Merge provided variables; always override {input}
        render_ctx = {**variables, "input": masked_input}

        try:
            user_content = user_template.format(**render_ctx)
        except KeyError as exc:
            raise ValueError(
                f"Prompt template references undefined variable {exc}. "
                f"Add it to the profile's 'variables' dict."
            ) from exc

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})
        return messages


# ──────────────────────────── Orchestrator ───────────────────────────────────

class Orchestrator:
    """
    High-level pipeline controller.

    Parameters
    ──────────
    privacy_manager  : PrivacyManager instance (local masking / unmasking)
    cloud_client     : CloudClient instance (remote inference)
    config_path      : path to prompts.json (or any ProfileConfigReader-compatible JSON)
    default_profile  : profile name used when none is passed to .run()

    Example
    ───────
    from core.orchestrator import Orchestrator
    from core.privacy_manager import PrivacyManager
    from core.cloud_client import CloudClient

    orch = Orchestrator(
        privacy_manager=PrivacyManager(),
        cloud_client=CloudClient(),
        config_path="industry_profiles/template/prompts.json",
        default_profile="general",
    )
    result = orch.run("Patient John Doe (DOB 1990-01-01) has hypertension.", profile="medical")
    print(result.final_text)
    """

    def __init__(
        self,
        privacy_manager: PrivacyManager,
        cloud_client: CloudClient,
        config_path: str | Path,
        default_profile: str = "general",
    ) -> None:
        self._pm = privacy_manager
        self._cloud = cloud_client
        self._config = ProfileConfigReader(config_path)
        self._default_profile = default_profile

        logger.info(
            "Orchestrator ready. Profiles available: %s",
            self._config.list_profiles(),
        )

    # ------------------------------------------------------------------ public

    def run(
        self,
        raw_input: str,
        profile: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> OrchestratorResult:
        """
        Execute the full privacy-preserving pipeline synchronously.

        Parameters
        ──────────
        raw_input      : original, potentially sensitive text
        profile        : industry profile key (falls back to default_profile)
        extra_metadata : arbitrary dict merged into the result's metadata field
        """
        profile_name = profile or self._default_profile
        t_start = time.perf_counter()

        # 1. Local masking ──────────────────────────────────────────────────
        logger.debug("[%s] Masking input (%d chars).", profile_name, len(raw_input))
        masked_text, entity_map = self._pm.mask(raw_input)

        # 2. Profile + prompt construction ─────────────────────────────────
        profile_config = self._config.get_profile(profile_name)
        messages = PromptBuilder.build(profile_config, masked_text)
        model_overrides: dict[str, Any] = profile_config.get("model_overrides", {})

        # 3. Cloud inference ────────────────────────────────────────────────
        logger.debug("[%s] Sending masked request to cloud.", profile_name)
        cloud_response = self._cloud.complete(messages, **model_overrides)

        # 4. Local unmasking ────────────────────────────────────────────────
        logger.debug("[%s] Unmasking cloud response.", profile_name)
        final_text = self._pm.unmask(cloud_response.content, entity_map)

        elapsed = time.perf_counter() - t_start
        logger.info(
            "[%s] Pipeline complete in %.2fs. %s",
            profile_name, elapsed, cloud_response.usage_summary,
        )

        return OrchestratorResult(
            final_text=final_text,
            masked_input=masked_text,
            masked_output=cloud_response.content,
            cloud_response=cloud_response,
            profile=profile_name,
            elapsed_seconds=elapsed,
            metadata={
                **(extra_metadata or {}),
                "entity_count": len(entity_map),
                "profile_metadata": profile_config.get("metadata", {}),
            },
        )

    def reload_profiles(self) -> None:
        """Hot-reload profile JSON without restarting. Safe to call at runtime."""
        self._config.reload()

    @property
    def available_profiles(self) -> list[str]:
        return self._config.list_profiles()
