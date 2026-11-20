"""Owner-local, read-only PAPER_V2 portfolio. Never copy its output to Pages."""
import argparse
from html import escape

from paper_account_v2 import read_status


def _money(cents):
    return f"US${cents // 100:,}.{cents % 100:02d}"


def render(directory):
    """Validate the on-disk account anew. Return an offline HTML view."""
    s = read_status(directory)
    initial = _money(s["opening_cash_cents"])
    cash = _money(s["cash_cents"])
    opened = escape(s["opened_utc"])
    account = escape(s["account"])
    state = escape(s["account_state"])
    readiness = escape(s["readiness"])
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CatalystRadar • Paper Portfolio V2</title>
<style>
body{{background:#111611;color:#e8ece7;font:1rem/1.55 system-ui,sans-serif;margin:auto;max-width:64rem;padding:clamp(1rem,4vw,3rem)}}
article{{background:#1b241b;border:1px solid #364334;border-radius:0.75rem;padding:1rem 1.3rem;margin:1rem 0}}
dt{{font-weight:700}} dd{{margin:0 0 .8rem}} .badges{{color:#cae9ae}}
.columns{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr));gap:1rem}}
</style>
<main><header><p class="badges">CATALYSTRADAR · OWNER-LOCAL · PAPER ONLY</p>
<h1>Paper Portfolio V2</h1><p>{account} · {state} · {readiness}</p>
<p>This account is separate from the read-only November historical trial.</p></header>
<div class="columns"><article><h2>Account</h2><dl>
<dt>Initial virtual cash</dt><dd>{initial}</dd><dt>Available virtual cash</dt><dd>{cash}</dd>
<dt>Reserved cash, position cost and modeled fees</dt><dd>US$0.00 each</dd>
<dt>Real capital at risk</dt><dd>US$0.00. No brokerage connection.</dd>
<dt>Opened (UTC)</dt><dd><time datetime="{opened}">{opened}</time> (local system clock, not externally authenticated)</dd>
</dl></article><article><h2>Activity</h2><dl>
<dt>Virtual orders</dt><dd>{s["order_count"]}</dd><dt>Modeled fills</dt><dd>{s["fill_count"]}</dd>
<dt>Virtual positions</dt><dd>{s["position_count"]}</dd><dt>Automatic processing</dt><dd>Off. No orders, including pending ones.</dd>
<dt>Last qualified session / evaluation</dt><dd>None / not run</dd>
</dl></article></div>
<article><h2>Performance</h2><p>Cash-only opening balance: {cash}. No qualified market mark, strategy P&amp;L, return, or drawdown yet. Nothing here is a trading result.</p></article>
<article><h2>Why orders are blocked</h2><p>Missing admitted market data and a qualified fill-model and recovery path for this account. Research rankings alone do not authorize orders.</p></article>
<footer><p>Saved local snapshot. Regenerate from the validated account to refresh. Do not publish this file.</p></footer>
</main></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("account_directory", help="Path to the separate, owner-only account")
    args = parser.parse_args()
    print(render(args.account_directory))


if __name__ == "__main__":
    main()
