"""Bounded dated listing evidence for the historical COHR collision, not a price adapter."""
from datetime import date

OLD_FILING = 'https://www.sec.gov/Archives/edgar/data/21510/000110465922076572/tm2220124d1_8k.htm'
NASDAQ_MERGER = 'https://www.nasdaqtrader.com/TraderNews.aspx?id=eca2022-159'
ACQUIRER_FILING = 'https://www.sec.gov/Archives/edgar/data/820318/000119312522186770/d307343d8k.htm'
RENAME_FILING = 'https://www.sec.gov/Archives/edgar/data/820318/000119312522240836/d347635d8k.htm'
OCC_NOTICE = 'https://infomemo.theocc.com/infomemos?number=50993'
NYSE_TRANSFER = 'https://ir.coherent.com/news-releases/news-release-details/coherent-corp-began-trading-nyse'

# These are narrow, manually reviewed session-date anchors, not complete periods.
# The CUSIP applies only at the dated observation that establishes it.
ANCHORS = {
    ('2022-06-30', 'COHR', 'NASDAQ'):
        ('0000021510', 'common', '192479103', (NASDAQ_MERGER, OLD_FILING)),
    ('2022-07-01', 'IIVI', 'NASDAQ'):
        ('0000820318', 'common', None, (ACQUIRER_FILING,)),
    ('2022-09-08', 'COHR', 'NASDAQ'):
        ('0000820318', 'common', '19247G107', (RENAME_FILING, OCC_NOTICE)),
    ('2023-02-23', 'COHR', 'NYSE'):
        ('0000820318', 'common', None, (RENAME_FILING, NYSE_TRANSFER)),
    ('2023-02-23', 'IIVI', 'NYSE'):
        ('0000820318', 'series_A_mandatory_convertible_preferred', None,
         (RENAME_FILING, NYSE_TRANSFER)),
}


def lookup(session, symbol, venue):
    """Recognize only an exact evidence date, reported symbol and venue."""
    if (type(session) is not str or date.fromisoformat(session).isoformat() != session
            or type(symbol) is not str or type(venue) is not str):
        raise ValueError('exact ISO date, reported symbol and venue required')
    anchor = ANCHORS.get((session, symbol, venue))
    cik, share_class, cusip, sources = anchor if anchor else (None, None, None, ())
    return dict(session=session, reported_symbol=symbol, venue=venue, issuer_cik=cik,
                share_class=share_class, cusip_as_reported=cusip, sources=sources,
                status='DATED_LISTING_ANCHOR' if anchor else 'UNVERIFIED_DATE_OR_LISTING',
                provider_instrument_id=None, price_join_performed=False,
                listing_continuity_verified=False)


def compare(first, second):
    """Compare exact listed anchors without inferring tradability or continuity."""
    a, b = lookup(*first), lookup(*second)
    if None in (a['issuer_cik'], b['issuer_cik']):
        status = 'UNVERIFIED_ANCHOR'
    elif a['issuer_cik'] != b['issuer_cik']:
        status = 'DIFFERENT_ISSUER'
    elif a['share_class'] != b['share_class']:
        status = 'DIFFERENT_SHARE_CLASS'
    else:
        status = 'SAME_ISSUER_CLASS_AT_ANCHORS_ONLY'
    return dict(first=a, second=b, status=status, provider_join_verified=False,
                listing_continuity_verified=False, outcome_qualified=False)
