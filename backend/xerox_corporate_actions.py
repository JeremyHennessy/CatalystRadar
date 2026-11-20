"""Exact, directional XRX corporate-action fixtures. Not a market-data join."""
from dataclasses import dataclass
from datetime import date
from fractions import Fraction


@dataclass(frozen=True)
class Listing:
    issuer_cik: str
    share_class: str
    symbol: str
    venue: str


@dataclass(frozen=True)
class Action:
    effective_date: date
    before: Listing
    after: Listing
    classification: str
    successor_shares_per_old_share: Fraction | None
    sources: tuple[str, ...]
    nasdaq_transfer_cusip: str | None = None
    consolidated_feed_changed: bool | None = None


LEGACY = Listing('0000108772', 'common', 'XRX', 'NYSE')
HOLDINGS_NYSE = Listing('0001770450', 'common', 'XRX', 'NYSE')
HOLDINGS_NASDAQ = Listing('0001770450', 'common', 'XRX', 'NASDAQ')

_ACTIONS = {
    (date(2019, 7, 31), LEGACY, HOLDINGS_NYSE): Action(
        date(2019, 7, 31), LEGACY, HOLDINGS_NYSE, 'SUCCESSOR_COMMON_CONVERSION',
        Fraction(1, 1), (
            'https://www.sec.gov/Archives/edgar/data/108772/000119312519208952/d781319d8k.htm',
            'https://www.sec.gov/Archives/edgar/data/1770450/000119312519208837/d767474d8k12b.htm',
            'https://www.sec.gov/Archives/edgar/data/1770450/000177045020000012/xrx-123119x10xk.htm',
        ),
    ),
    (date(2021, 9, 21), HOLDINGS_NYSE, HOLDINGS_NASDAQ): Action(
        date(2021, 9, 21), HOLDINGS_NYSE, HOLDINGS_NASDAQ, 'SAME_COMMON_LISTING_TRANSFER',
        None, (
            'https://www.sec.gov/Archives/edgar/data/1770450/000119312521276925/d189027d8a12b.htm',
            'https://www.nasdaqtrader.com/TraderNews.aspx?id=dtn2021-36',
            'https://www.sec.gov/Archives/edgar/data/1770450/000177045022000010/xrx-20211231.htm',
        ), nasdaq_transfer_cusip='98421M106', consolidated_feed_changed=True,
    ),
}


def review(effective_date: str, before: Listing, after: Listing) -> dict:
    """Resolve reviewed action terms only; no implied listed sessions or prices."""
    if (type(effective_date) is not str
            or date.fromisoformat(effective_date).isoformat() != effective_date
            or type(before) is not Listing or type(after) is not Listing
            or any(type(value) is not str for listing in (before, after)
                   for value in (listing.issuer_cik, listing.share_class,
                                 listing.symbol, listing.venue))):
        raise ValueError('exact ISO date and explicit listing keys required')
    action = _ACTIONS.get((date.fromisoformat(effective_date), before, after))
    return dict(action=action,
                status=action.classification if action else 'UNVERIFIED_ACTION',
                provider_join_verified=False, listing_continuity_verified=False,
                eligible_prices_verified=False, outcome_qualified=False)
