# Price/liquidity feed audit — November 14, 2026
## Superseded pre-connection research checkpoint
The candidate comparison below records the earlier pre-connection audit. It is not current account or collection status. By the later November 14 checkpoint, authorized Alpha Vantage raw daily collection and private persistence were verified for 11 symbols × 100 observations. Scheduled operation, complete corporate-action/halts coverage and execution suitability remain unverified. See [Operational checkpoint](operational-checkpoint.md) and [private retention](private-retention.md). No raw prices or credentials are published here.

## Best next candidate: Alpha Vantage raw daily, conditional
Official terms explicitly describe private individual investment analysis/research/testing/monitoring within personal noncommercial use; commercial use and certain financial-industry affiliations require different arrangements. Free quota is 25 API requests/day. Raw TIME_SERIES_DAILY compact data is documented; DAILY_ADJUSTED is premium. This is an appropriate API candidate to seek authorized access for a limited daily research pilot, NOT evidence of a validated execution feed. It requires an authorized API key and applicable terms/account eligibility. Do not sign up or accept terms without applicable authorization. Never infer commercial redistribution rights for a future paid app.
https://www.alphavantage.co/terms_of_service/
https://www.alphavantage.co/support/api-key/
https://www.alphavantage.co/documentation/

## Alternative: Massive Basic, entitlement ambiguity
Official plan offers $0 individual end-of-day data, five calls/minute and two years history. Prior-day bars become accessible after midnight Eastern, not live intraday. However market-data terms limit personal/noncommercial use and say display-only absent another agreement. Automated non-display analytics must have applicable entitlement clarified before calling it authorized. Do not infer broader rights from API examples or 'free' pricing. No signup performed.
https://massive.com/pricing?product=stocks
https://massive.com/knowledge-base/article/on-the-free-basic-plan-when-can-i-pull-the-previous-trading-days-data
https://massive.com/terms/market_data_terms.pdf

## Not sufficient
TXMD official issuer quote page embeds LSEG-sourced quotes delayed at least 15 minutes. Retrieved page exposes labels but no timestamped quote values. It is not a validated bulk historical API or executable quote. No hidden endpoint/entitlement circumvention attempted.
https://ir.therapeuticsmd.com/stock-information/stock-quote-chart

## Admission tests before use
- Confirm account/data-use authorization and documented endpoint entitlement; no secret in URLs saved to logs, source manifests, output or screenshots.
- Archive exact responses plus observed UTC, provider data-as-of/session, adjustment policy and license scope. Today's historical response is NOT a point-in-time snapshot from the past: future corrections/revisions cannot be hidden.
- Validate ticker/security mapping against issuer identity, session calendar and split events; reject future/stale, duplicate, missing, nonfinite or incoherent OHLCV.
- For eligibility calculate prior-session close and 20-session average dollar-volume estimate as mean(unadjusted close*reported volume), explicitly a proxy rather than actual trade-by-trade dollar turnover. Verify volume units and split consistency. Require all 20 expected sessions, no silent missing-day fill.
- Daily OHLC closes are not automatically official closing-auction execution prices. Without validated auction/condition data they support observation/event studies only, NOT the proposed LOC fill model. Missing bars do not prove a halt; halt feed is a separate source.
- Corporate-action/distribution entitlement needed for total-return reporting. Do not combine adjusted prices and separate dividend credits.
- Frozen observations can test forward 1/3/5-session returns after acquisition; no fabricated backdated knowledge or claimed intraday reaction speed. No order engine enabled by adding a feed.
