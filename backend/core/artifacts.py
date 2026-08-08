"""
The one place JSON leaves the backend.

The payload used to be a single file per chamber - 45 MB for Camera, of which
14 MB was indentation and 8.4 MB was per-month analytics - and the frontend had
to download all of it before it could draw anything.

Here it is split into resources the frontend can fetch when it needs them:

    data/
      manifest.json              tiny: what exists, how big, which periods
      camera/core.json           deputies, clusters, stats - needed for first paint
      camera/speeches.json       only the map view needs this
      camera/analytics/global.json
      camera/analytics/2025.json
      camera/analytics/2025-11.json

Chunking also makes the artifacts cheap to keep in git: a re-run only rewrites
the periods whose data actually changed, and untouched chunks stay byte-identical
so git stores them once.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .serialization import dump_json, to_builtin

logger = logging.getLogger(__name__)

MANIFEST_NAME = 'manifest.json'
MANIFEST_VERSION = 2

# Guardrails: a resource crossing these means something regressed. The frontend
# fetches `core` on first paint, so it is held to the tightest budget.
SIZE_BUDGETS_MB = {
    'manifest': 0.5,
    'core': 3.0,
    'speeches': 12.0,
    'analytics': 3.0,
}


@dataclass(frozen=True)
class ResourceRef:
    """A written chunk, as the manifest describes it."""

    path: str
    bytes: int
    digest: str

    def as_dict(self) -> dict:
        return {'path': self.path, 'bytes': self.bytes, 'digest': self.digest}


@dataclass
class ChamberArtifacts:
    """Everything written for one chamber."""

    chamber: str
    filename: str
    stats: dict = field(default_factory=dict)
    periods: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            'label': self.chamber,
            'stats': self.stats,
            'periods': self.periods,
            'resources': self.resources,
        }


class ArtifactWriter:
    """Writes chunked payloads plus the manifest that indexes them."""

    def __init__(self, root: Path, indent: Optional[int] = None):
        self.root = Path(root)
        # No indentation: it cost 14 MB on Camera alone and nothing reads these
        # by eye. Use indent=2 only when debugging a payload by hand.
        self.indent = indent
        self.written: list[ResourceRef] = []

    def write(self, relative_path: str, payload: Any) -> ResourceRef:
        """Serialise one resource and return its manifest entry."""
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)

        prepared = to_builtin(payload)
        size = dump_json(prepared, target, indent=self.indent)

        digest = hashlib.sha256(target.read_bytes()).hexdigest()[:16]
        ref = ResourceRef(path=relative_path.replace('\\', '/'), bytes=size, digest=digest)

        self.written.append(ref)
        logger.debug("Wrote %s (%.2f MB)", ref.path, size / 1e6)
        return ref

    def write_chamber(
        self,
        chamber: str,
        filename: str,
        core: dict,
        speeches: list,
        analytics: dict,
    ) -> ChamberArtifacts:
        """
        Split one chamber's payload into its resources.

        `core` is what the shell needs immediately; speeches and each analytics
        period are fetched on demand.
        """
        artifacts = ChamberArtifacts(chamber=chamber, filename=filename)

        artifacts.resources['core'] = self.write(f'{filename}/core.json', core).as_dict()
        artifacts.resources['speeches'] = self.write(f'{filename}/speeches.json', speeches).as_dict()

        analytics_refs = {
            'global': self.write(
                f'{filename}/analytics/global.json', analytics.get('global', {})
            ).as_dict(),
            'by_year': {},
            'by_month': {},
        }

        for bucket, key in (('by_year', 'by_year'), ('by_month', 'by_month')):
            for period, payload in (analytics.get(key) or {}).items():
                analytics_refs[bucket][period] = self.write(
                    f'{filename}/analytics/{period}.json', payload
                ).as_dict()

        artifacts.resources['analytics'] = analytics_refs
        artifacts.stats = core.get('stats', {})
        artifacts.periods = {
            'years': sorted(analytics_refs['by_year']),
            'months': sorted(analytics_refs['by_month'], reverse=True),
        }

        return artifacts

    def write_manifest(self, chambers: list[ChamberArtifacts]) -> ResourceRef:
        """Index every chamber's resources, so the frontend can fetch lazily."""
        manifest = {
            'version': MANIFEST_VERSION,
            'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'chambers': {c.filename: c.as_dict() for c in chambers},
        }
        return self.write(MANIFEST_NAME, manifest)

    # -- reporting -----------------------------------------------------------

    def total_bytes(self) -> int:
        return sum(r.bytes for r in self.written)

    def size_report(self) -> str:
        lines = [f"{len(self.written)} resources, {self.total_bytes() / 1e6:.1f} MB total"]
        for ref in sorted(self.written, key=lambda r: -r.bytes)[:8]:
            lines.append(f"  {ref.bytes / 1e6:7.2f} MB  {ref.path}")
        return "\n".join(lines)

    def budget_violations(self) -> list[str]:
        """Resources that exceed their size budget, if any."""
        violations = []
        for ref in self.written:
            kind = _budget_kind(ref.path)
            budget = SIZE_BUDGETS_MB.get(kind)
            if budget and ref.bytes / 1e6 > budget:
                violations.append(
                    f"{ref.path}: {ref.bytes / 1e6:.1f} MB exceeds the {budget} MB budget for '{kind}'"
                )
        return violations


def _budget_kind(path: str) -> str:
    if path == MANIFEST_NAME:
        return 'manifest'
    if path.endswith('/speeches.json'):
        return 'speeches'
    if '/analytics/' in path:
        return 'analytics'
    if path.endswith('/core.json'):
        return 'core'
    return 'other'
