"""
Orchestrateur de migration -- MigrationEngine.
Porte depuis braze_migration/engine.py.
Ajout : connecteur CSV, deduplication par email, support stop.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from services.migration.connectors.base import BaseConnector
from services.migration.connectors.brevo import BrevoConnector
from services.migration.connectors.demo import DemoConnector
from services.migration.connectors.salesforce_mc import SalesforceMarketingCloudConnector
from services.migration.connectors.csv_connector import CsvConnector
from services.migration.exporters.braze import BrazeExporter, deduplicate_contacts_by_email
from services.migration.mappers.base_mapper import BaseMapper
from services.migration.mappers.brevo_mapper import BrevoMapper
from services.migration.mappers.demo_mapper import DemoMapper
from services.migration.mappers.salesforce_mc_mapper import SalesforceMarketingCloudMapper
from services.migration.mappers.csv_mapper import CsvMapper

logger = logging.getLogger(__name__)

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "demo": DemoConnector,
    "brevo": BrevoConnector,
    "salesforce_mc": SalesforceMarketingCloudConnector,
    "sfmc": SalesforceMarketingCloudConnector,  # alias frontend
    "csv": CsvConnector,
}

MAPPER_REGISTRY: dict[str, type[BaseMapper]] = {
    "demo": DemoMapper,
    "brevo": BrevoMapper,
    "salesforce_mc": SalesforceMarketingCloudMapper,
    "sfmc": SalesforceMarketingCloudMapper,  # alias frontend
    "csv": CsvMapper,
}

# Paliers du mode warmup (pourcentage du total)
DEFAULT_WARMUP_STAGES = [1, 5, 10, 25, 50, 100]
# Seuil d'erreur max par palier (%) avant arret automatique
DEFAULT_MAX_ERROR_RATE = 5.0


@dataclass
class WarmupStageResult:
    """Resultat d'un palier de warmup."""
    stage_index: int
    stage_percent: int
    contacts_in_stage: int
    success: int = 0
    failed: int = 0
    error_rate: float = 0.0
    duration_seconds: float = 0.0
    status: str = "pending"  # pending, running, completed, failed, skipped, stopped


@dataclass
class WarmupResult:
    """Resultat complet d'un warmup."""
    total_contacts: int = 0
    stages: list[WarmupStageResult] = field(default_factory=list)
    stopped_at_stage: int | None = None
    stop_reason: str | None = None

    @property
    def total_success(self) -> int:
        return sum(s.success for s in self.stages)

    @property
    def total_failed(self) -> int:
        return sum(s.failed for s in self.stages)

    @property
    def total_migrated(self) -> int:
        return self.total_success + self.total_failed

    @property
    def overall_error_rate(self) -> float:
        if self.total_migrated == 0:
            return 0.0
        return (self.total_failed / self.total_migrated) * 100


class MigrationEngine:
    """Orchestrateur principal de la migration."""

    def __init__(
        self,
        source_platform: str,
        source_config: dict[str, Any],
        braze_config: dict[str, Any],
        field_mapping: dict[str, str] | None = None,
    ):
        if source_platform not in CONNECTOR_REGISTRY:
            raise ValueError(
                f"Unknown platform: {source_platform}. "
                f"Available: {list(CONNECTOR_REGISTRY.keys())}"
            )

        self.source_platform = source_platform
        self.connector = CONNECTOR_REGISTRY[source_platform](source_config)
        self.mapper = MAPPER_REGISTRY[source_platform](field_mapping)
        self.exporter = BrazeExporter(braze_config)

    def test_connections(self) -> dict[str, bool]:
        source_ok = self.connector.test_connection()
        braze_ok = self.exporter.test_connection()
        return {"source": source_ok, "braze": braze_ok}

    def run(
        self,
        migrate_contacts: bool = True,
        migrate_segments: bool = True,
        migrate_templates: bool = True,
        migrate_events: bool = False,
        contact_limit: int | None = None,
        deduplicate_by_email: bool = False,
    ) -> dict[str, Any]:
        """Lance la migration complete."""
        results: dict[str, Any] = {}

        if migrate_contacts:
            logger.info("Fetching contacts...")
            contacts = self.connector.fetch_contacts(limit=contact_limit)
            logger.info(f"Transforming {len(contacts)} contacts...")
            contacts = self.mapper.transform_contacts(contacts)

            if deduplicate_by_email:
                original_count = len(contacts)
                contacts = deduplicate_contacts_by_email(contacts)
                logger.info(
                    f"Deduplication: {original_count} -> {len(contacts)} contacts"
                )

            logger.info("Exporting contacts to Braze...")
            results["contacts"] = self.exporter.export_contacts(contacts)

            # Gerer les SMS subscriptions si necessaire
            sms_result = self.exporter.set_sms_subscription(contacts)
            if sms_result.get("success", 0) > 0 or sms_result.get("failed", 0) > 0:
                results["sms_subscriptions"] = sms_result

        if migrate_segments:
            logger.info("Fetching segments...")
            segments = self.connector.fetch_segments()
            logger.info(f"Transforming {len(segments)} segments...")
            segments = self.mapper.transform_segments(segments)
            results["segments"] = {"fetched": len(segments)}

        if migrate_templates:
            logger.info("Fetching templates...")
            templates = self.connector.fetch_templates()
            logger.info(f"Transforming {len(templates)} templates...")
            templates = self.mapper.transform_templates(templates)
            logger.info("Exporting templates to Braze...")
            results["templates"] = self.exporter.export_templates(templates)

        if migrate_events:
            logger.info("Fetching events...")
            events = self.connector.fetch_events()
            logger.info(f"Transforming {len(events)} events...")
            events = self.mapper.transform_events(events)
            logger.info("Exporting events to Braze...")
            results["events"] = self.exporter.export_events(events)

        return results

    def run_warmup(
        self,
        stages: list[int] | None = None,
        max_error_rate: float = DEFAULT_MAX_ERROR_RATE,
        pause_between_stages: int = 0,
        auto_stop_on_error: bool = True,
        on_stage_start: Callable[[WarmupStageResult], None] | None = None,
        on_stage_complete: Callable[[WarmupStageResult], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
        deduplicate_by_email: bool = False,
    ) -> WarmupResult:
        """Lance une migration en mode warmup (paliers progressifs).

        Args:
            stages: Liste de pourcentages pour les paliers (ex: [1, 5, 10, 25, 50, 100])
            max_error_rate: Taux d'erreur max (%) avant arret automatique du palier
            pause_between_stages: Pause en secondes entre chaque palier
            auto_stop_on_error: Stopper automatiquement si le taux d'erreur depasse le seuil
            on_stage_start: Callback appele au debut de chaque palier
            on_stage_complete: Callback appele a la fin de chaque palier
            should_stop: Callback verifie entre les paliers pour arret manuel
            deduplicate_by_email: Deduplication par email avant export
        """
        stages = stages or DEFAULT_WARMUP_STAGES

        # Recuperer tous les contacts
        logger.info("Warmup: fetching all contacts from source...")
        all_contacts = self.connector.fetch_contacts()
        total = len(all_contacts)
        logger.info(f"Warmup: {total} contacts found")

        # Transformer tous les contacts
        logger.info("Warmup: transforming contacts...")
        all_contacts = self.mapper.transform_contacts(all_contacts)

        # Deduplication si demandee
        if deduplicate_by_email:
            original_count = len(all_contacts)
            all_contacts = deduplicate_contacts_by_email(all_contacts)
            total = len(all_contacts)
            logger.info(f"Warmup deduplication: {original_count} -> {total} contacts")

        result = WarmupResult(total_contacts=total)
        migrated_so_far = 0

        for stage_idx, percent in enumerate(stages):
            # Calculer la tranche de contacts pour ce palier
            target_count = max(1, int(total * percent / 100))
            stage_count = target_count - migrated_so_far

            if stage_count <= 0:
                # Ce palier n'a rien de nouveau a migrer
                stage_result = WarmupStageResult(
                    stage_index=stage_idx,
                    stage_percent=percent,
                    contacts_in_stage=0,
                    status="skipped",
                )
                result.stages.append(stage_result)
                continue

            stage_contacts = all_contacts[migrated_so_far: migrated_so_far + stage_count]

            stage_result = WarmupStageResult(
                stage_index=stage_idx,
                stage_percent=percent,
                contacts_in_stage=len(stage_contacts),
                status="running",
            )
            result.stages.append(stage_result)

            if on_stage_start:
                on_stage_start(stage_result)

            logger.info(
                f"Warmup palier {stage_idx + 1}/{len(stages)}: "
                f"{percent}% - {len(stage_contacts)} contacts "
                f"(cumul: {migrated_so_far + len(stage_contacts)}/{total})"
            )

            # Exporter ce palier
            start_time = time.time()
            export_result = self.exporter.export_contacts(stage_contacts)
            elapsed = time.time() - start_time

            stage_result.success = export_result["success"]
            stage_result.failed = export_result["failed"]
            stage_result.duration_seconds = round(elapsed, 2)

            stage_total = stage_result.success + stage_result.failed
            stage_result.error_rate = (
                (stage_result.failed / stage_total * 100) if stage_total > 0 else 0.0
            )

            migrated_so_far += len(stage_contacts)

            # Verifier le taux d'erreur
            if auto_stop_on_error and stage_result.error_rate > max_error_rate:
                stage_result.status = "failed"
                result.stopped_at_stage = stage_idx
                result.stop_reason = (
                    f"Taux d'erreur {stage_result.error_rate:.1f}% "
                    f"depasse le seuil de {max_error_rate}%"
                )
                logger.warning(f"Warmup STOPPED: {result.stop_reason}")
                if on_stage_complete:
                    on_stage_complete(stage_result)
                break

            stage_result.status = "completed"

            if on_stage_complete:
                on_stage_complete(stage_result)

            logger.info(
                f"Warmup palier {stage_idx + 1} termine: "
                f"{stage_result.success} OK, {stage_result.failed} KO "
                f"({stage_result.error_rate:.1f}% erreurs) - {elapsed:.1f}s"
            )

            # Verifier arret manuel
            if should_stop and should_stop():
                result.stopped_at_stage = stage_idx
                result.stop_reason = "Arret manuel demande"
                logger.info("Warmup: arret manuel")
                break

            # Pause entre les paliers (sauf le dernier)
            if pause_between_stages > 0 and stage_idx < len(stages) - 1:
                logger.info(f"Warmup: pause de {pause_between_stages}s avant le prochain palier...")
                time.sleep(pause_between_stages)

        logger.info(
            f"Warmup termine: {result.total_success} succes, "
            f"{result.total_failed} echoues sur {result.total_contacts} total "
            f"({result.overall_error_rate:.1f}% erreurs)"
        )

        return result
