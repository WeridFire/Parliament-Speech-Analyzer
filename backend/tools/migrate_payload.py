"""
Convert the legacy single-file payloads into the chunked layout.

The pipeline now writes `data/manifest.json` plus per-resource chunks, but
regenerating those from scratch means re-embedding the whole corpus. This
rebuilds them from the existing `camera.json` / `senato.json` in seconds, so the
frontend can move to the new contract immediately; the next pipeline run
produces the identical layout natively.

Field changes applied here mirror the pipeline:
  * `text` + `snippet` -> a single original-case `text`
  * `rebel_pct` -> `divergence_pct`
  * period analytics drop the corpus-level analyzers that no longer run per period

    python -m backend.tools.migrate_payload
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from backend.config import DISPLAY_TEXT_CHARS
from backend.core.artifacts import ArtifactWriter

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_DIR = PROJECT_ROOT / 'frontend' / 'public'

LEGACY_FILES = {'camera': 'camera.json', 'senate': 'senato.json'}

# Analyzers that now decline to run on a period slice (see BaseAnalyzer.supports)
PERIOD_EXCLUDED = {'temporal', 'topics'}


def migrate_speech(speech: dict) -> dict:
    """Single original-case text field; divergence naming."""
    text = speech.get('snippet') or speech.get('text') or ''

    migrated = {
        k: v for k, v in speech.items()
        if k not in ('text', 'snippet', 'rebel_pct')
    }
    migrated['text'] = text[:DISPLAY_TEXT_CHARS]
    migrated['divergence_pct'] = speech.get('rebel_pct', 0)
    return migrated


def migrate_person(person: dict) -> dict:
    migrated = {k: v for k, v in person.items() if k != 'rebel_pct'}
    migrated['divergence_pct'] = person.get('rebel_pct', 0)
    return migrated


def migrate_scores(scores: dict) -> dict:
    out = {}
    for name, info in (scores or {}).items():
        entry = {k: v for k, v in info.items() if k != 'rebel_pct'}
        entry['divergence_pct'] = info.get('rebel_pct', 0)
        out[name] = entry
    return out


def strip_period_analytics(block: dict) -> dict:
    return {name: value for name, value in (block or {}).items() if name not in PERIOD_EXCLUDED}


def migrate(payload: dict, chamber: str) -> tuple[dict, list, dict]:
    """Split a legacy payload into (core, speeches, analytics)."""
    speeches = [migrate_speech(s) for s in payload.get('speeches', [])]

    by_period = payload.get('deputies_by_period') or {}
    core = {
        'deputies': [migrate_person(d) for d in payload.get('deputies', [])],
        'deputies_by_period': {
            'global': [migrate_person(d) for d in by_period.get('global', [])],
            'by_year': {
                period: [migrate_person(d) for d in people]
                for period, people in (by_period.get('by_year') or {}).items()
            },
            'by_month': {
                period: [migrate_person(d) for d in people]
                for period, people in (by_period.get('by_month') or {}).items()
            },
            'available_periods': by_period.get('available_periods', {'years': [], 'months': []}),
        },
        'clusters': payload.get('clusters', {}),
        'rebels': [migrate_person(r) for r in payload.get('rebels', [])],
        'all_divergence_scores': migrate_scores(payload.get('all_rebel_scores')),
        'stats': {**payload.get('stats', {}), 'analytics_run': {'failed_analyzers': []}},
    }

    legacy_analytics = payload.get('analytics') or {}
    analytics = {
        'global': legacy_analytics.get('global', {}),
        'by_year': {
            period: strip_period_analytics(block)
            for period, block in (legacy_analytics.get('by_year') or {}).items()
        },
        'by_month': {
            period: strip_period_analytics(block)
            for period, block in (legacy_analytics.get('by_month') or {}).items()
        },
    }

    return core, speeches, analytics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--public-dir', type=Path, default=PUBLIC_DIR)
    parser.add_argument('--keep-legacy', action='store_true',
                        help='Do not report the legacy files as removable')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    writer = ArtifactWriter(args.public_dir / 'data')
    chambers = []
    legacy_bytes = 0

    for chamber, filename in LEGACY_FILES.items():
        source = args.public_dir / filename
        if not source.exists():
            logger.warning("Missing %s, skipping", filename)
            continue

        legacy_bytes += source.stat().st_size
        with open(source, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        core, speeches, analytics = migrate(payload, chamber)
        stem = source.stem  # camera / senato

        chambers.append(writer.write_chamber(
            chamber=chamber, filename=stem,
            core=core, speeches=speeches, analytics=analytics,
        ))
        logger.info("Converted %s: %d speeches", filename, len(speeches))

    if not chambers:
        logger.error("No legacy payloads found in %s", args.public_dir)
        return 1

    writer.write_manifest(chambers)

    print("\n" + writer.size_report())
    print(f"\nlegacy total: {legacy_bytes / 1e6:.1f} MB")
    print(f"chunked total: {writer.total_bytes() / 1e6:.1f} MB")
    if legacy_bytes:
        print(f"reduction: {(1 - writer.total_bytes() / legacy_bytes) * 100:.0f}%")

    for violation in writer.budget_violations():
        print(f"  ! {violation}")

    if not args.keep_legacy:
        print("\nThe legacy camera.json / senato.json are no longer read by the frontend.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
