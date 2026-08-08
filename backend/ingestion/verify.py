"""
Coverage check for the ingestion layer.

Answers the question the old scraper could not: of the sittings that officially
exist, how many did we actually collect? A run that is being blocked, or that is
quietly missing months, shows up here as a number instead of as a suspiciously
small dataset.

    python -m backend.ingestion.verify --source both --months 15
    python -m backend.ingestion.verify --source camera --limit 3   # quick probe

Exits non-zero when a chamber is blocked or collects nothing, so it is usable as
a pre-flight check before a full export.
"""

import argparse
import logging
import sys

from backend.config import LEGISLATURE, MONTHS_BACK

from .rosters import build_roster_index
from .sparql import SparqlError

logger = logging.getLogger(__name__)


def check_rosters(legislature: int) -> bool:
    print("\n=== Rosters ===")
    try:
        index = build_roster_index(legislature=legislature)
    except SparqlError as e:
        print(f"  FAILED: {e}")
        return False

    by_chamber = {}
    for entry in index.entries:
        by_chamber.setdefault(entry.chamber, []).append(entry)

    for chamber, entries in sorted(by_chamber.items()):
        with_party = sum(1 for e in entries if e.party)
        print(f"  {chamber:8} {len(entries):4} members ({with_party} with a group)")

    if not index.entries:
        print("  FAILED: register is empty - name validation would reject everything")
        return False

    # Spot-check the matching strategies against real names from the register.
    sample = index.entries[0]
    checks = [
        (sample.full_name, 'exact'),
        (sample.surname.upper(), 'surname'),
        (f"{sample.first_name} {sample.surname}", 'reversed'),
    ]
    print("  matcher:")
    for probe, expected in checks:
        match = index.match(probe)
        status = 'ok' if match else 'MISS'
        strategy = match.strategy if match else '-'
        print(f"    {probe!r:40} -> {status:4} via {strategy} (wanted {expected})")

    return True


def check_chamber(chamber: str, months_back: int, limit: int | None, use_cloudscraper: bool) -> bool:
    from . import fetch_source_speeches

    print(f"\n=== {chamber} ===")

    try:
        df, report = fetch_source_speeches(
            chamber,
            months_back=months_back,
            use_cloudscraper=use_cloudscraper,
            limit=limit,
        )
    except SparqlError as e:
        print(f"  open data unreachable: {e}")
        return False

    print(f"  sittings known (open data): {report.known}")
    print(f"  fetched:                    {report.fetched} ({report.from_cache} from cache)")
    print(f"  parsed with speeches:       {report.parsed}")
    print(f"  speeches:                   {report.speeches}")
    print(f"  blocked by challenge:       {report.blocked}")
    print(f"  failed:                     {report.failed}")
    print(f"  coverage:                   {report.coverage:.0f}%")

    if not df.empty:
        print(f"  date range:                 {df['date'].min()} .. {df['date'].max()}")
        print(f"  distinct speakers:          {df['deputy'].nunique()}")
        ambiguous = int(df['match_ambiguous'].sum()) if 'match_ambiguous' in df else 0
        print(f"  ambiguous attributions:     {ambiguous}")
        if 'match_strategy' in df:
            counts = df['match_strategy'].value_counts().to_dict()
            print(f"  match strategies:           {counts}")

    for error in report.errors[:5]:
        print(f"    ! {error}")

    if report.blocked:
        print(
            f"  -> {report.blocked} sittings sit behind an anti-bot challenge.\n"
            f"     Install Playwright (pip install playwright && playwright install chromium)\n"
            f"     for the browser transport, or run from an unchallenged network."
        )

    return report.ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', '-s', choices=['camera', 'senate', 'both'], default='both')
    parser.add_argument('--months', '-m', type=int, default=MONTHS_BACK)
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Only probe N sittings per chamber')
    parser.add_argument('--legislature', type=int, default=LEGISLATURE)
    parser.add_argument('--cloudscraper', action='store_true')
    parser.add_argument('--skip-rosters', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format='%(levelname)s %(name)s: %(message)s',
    )

    print(f"Ingestion check - legislature {args.legislature}, {args.months} months back")

    healthy = True
    if not args.skip_rosters:
        healthy &= check_rosters(args.legislature)

    chambers = ['camera', 'senate'] if args.source == 'both' else [args.source]
    for chamber in chambers:
        healthy &= check_chamber(chamber, args.months, args.limit, args.cloudscraper)

    print("\n" + ("All checks passed." if healthy else "Some checks failed (see above)."))
    return 0 if healthy else 1


if __name__ == '__main__':
    sys.exit(main())
