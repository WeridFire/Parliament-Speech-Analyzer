"""
Capture a structural fingerprint of the exported JSON artifacts.

The refactor touches every stage between the scrapers and the payload, so we need
a way to tell "the numbers changed because I fixed something" apart from "the
numbers changed because I broke something". This records the shape of the current
output (counts, key sets, distributions) rather than the values themselves, so it
stays meaningful even as field names change.

Usage:
    python -m backend.tools.capture_baseline                 # write baseline
    python -m backend.tools.capture_baseline --compare       # diff against it
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from statistics import mean

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

PAYLOAD_DIR = PROJECT_ROOT / 'frontend' / 'public'
BASELINE_PATH = PROJECT_ROOT / 'backend' / 'tests' / 'data' / 'baseline.json'

CHAMBER_FILES = {'camera': 'camera.json', 'senato': 'senato.json'}

logger = logging.getLogger(__name__)


def _round(value, digits=2):
    return round(float(value), digits) if value is not None else None


def summarize_chamber(payload: dict) -> dict:
    """Structural summary of one chamber payload."""
    speeches = payload.get('speeches', [])
    deputies = payload.get('deputies', [])
    analytics = payload.get('analytics', {})
    by_period = payload.get('deputies_by_period', {})

    parties = sorted({s.get('party') for s in speeches if s.get('party')})
    clusters = {
        str(cid): {'label': meta.get('label'), 'count': meta.get('count')}
        for cid, meta in sorted((payload.get('clusters') or {}).items(), key=lambda kv: int(kv[0]))
    }

    dates = sorted(s['date'] for s in speeches if s.get('date'))
    speech_counts = [d.get('n_speeches', 0) for d in deputies]

    return {
        'stats': payload.get('stats', {}),
        'n_speeches': len(speeches),
        'n_deputies': len(deputies),
        'parties': parties,
        'clusters': clusters,
        'date_range': [dates[0], dates[-1]] if dates else None,
        'speech_fields': sorted(speeches[0].keys()) if speeches else [],
        'deputy_fields': sorted(deputies[0].keys()) if deputies else [],
        'deputy_speech_counts': {
            'total': sum(speech_counts),
            'mean': _round(mean(speech_counts)) if speech_counts else 0,
            'max': max(speech_counts) if speech_counts else 0,
            'singletons': sum(1 for c in speech_counts if c <= 1),
        },
        'analytics': {
            'analyzers': sorted(analytics.get('global', {}).keys()),
            'failed': sorted(
                name for name, block in analytics.get('global', {}).items()
                if isinstance(block, dict) and 'error' in block
            ),
            'n_years': len(analytics.get('by_year', {})),
            'n_months': len(analytics.get('by_month', {})),
            'years': sorted(analytics.get('by_year', {}).keys()),
        },
        'deputies_by_period': {
            'n_years': len(by_period.get('by_year', {})),
            'n_months': len(by_period.get('by_month', {})),
        },
        'rebels': {
            'n_listed': len(payload.get('rebels', [])),
            'n_scored': len(payload.get('all_rebel_scores', {})),
        },
    }


def capture(payload_dir: Path = PAYLOAD_DIR) -> dict:
    """Build the baseline document from whatever chamber files exist."""
    baseline = {'chambers': {}}

    for chamber, filename in CHAMBER_FILES.items():
        path = payload_dir / filename
        if not path.exists():
            logger.warning("Missing payload, skipping: %s", path.name)
            continue

        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        summary = summarize_chamber(payload)
        summary['bytes_on_disk'] = path.stat().st_size
        baseline['chambers'][chamber] = summary
        logger.info(
            "%s: %d speeches, %d deputies, %.1f MB",
            chamber, summary['n_speeches'], summary['n_deputies'],
            path.stat().st_size / 1e6,
        )

    return baseline


def _flatten(obj, prefix=''):
    """Flatten nested dicts to dotted paths so diffs point at a single value."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _flatten(value, f"{prefix}.{key}" if prefix else str(key))
    else:
        yield prefix, obj


def compare(current: dict, baseline: dict) -> list[str]:
    """Return human-readable differences between two baseline documents."""
    cur = dict(_flatten(current))
    base = dict(_flatten(baseline))

    diffs = []
    for key in sorted(set(cur) | set(base)):
        before, after = base.get(key, '<absent>'), cur.get(key, '<absent>')
        if before != after:
            diffs.append(f"{key}: {before!r} -> {after!r}")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--compare', action='store_true', help='Diff current payloads against the stored baseline')
    parser.add_argument('--payload-dir', type=Path, default=PAYLOAD_DIR)
    parser.add_argument('--baseline', type=Path, default=BASELINE_PATH)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    current = capture(args.payload_dir)

    if args.compare:
        if not args.baseline.exists():
            logger.error("No baseline at %s - run without --compare first", args.baseline)
            return 1

        with open(args.baseline, 'r', encoding='utf-8') as f:
            stored = json.load(f)

        diffs = compare(current, stored)
        if not diffs:
            print("No structural changes against baseline.")
            return 0

        print(f"{len(diffs)} structural change(s) against baseline:\n")
        for line in diffs:
            print(f"  {line}")
        return 0

    args.baseline.parent.mkdir(parents=True, exist_ok=True)
    with open(args.baseline, 'w', encoding='utf-8') as f:
        json.dump(current, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"Baseline written to {args.baseline}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
