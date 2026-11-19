# COHR historical ticker collision

The same ticker and exchange can refer to different securities. On June 30,
2022, Nasdaq's COHR was **Coherent, Inc.** common stock, SEC CIK 0000021510 and
CUSIP 192479103. Nasdaq reported June 30 as the last trading date and a halt
after that day's after-hours session. The merger closed before the July 1 open;
July 5 was the effective suspension date, not the last trading date. Each old
common share was converted into the right to receive US$220 cash and 0.91 shares
of the acquirer's common stock. This is a merger conversion, not a ticker rename
of the old security.
[Exchange notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=eca2022-159) ·
[Target merger filing](https://www.sec.gov/Archives/edgar/data/21510/000110465922076572/tm2220124d1_8k.htm)

**II-VI Incorporated** was the acquirer, SEC CIK 0000820318. Its July 1 filing
identifies its Nasdaq common as IIVI. On September 8, the same registrant changed
its name to **Coherent Corp.** and its Nasdaq common ticker to COHR. The OCC memo
separately identifies its new underlying common CUSIP as 19247G107 for the
September 8 change. The two COHR/Nasdaq anchors thus must not be treated as one
security.
[Acquirer merger filing](https://www.sec.gov/Archives/edgar/data/820318/000119312522186770/d307343d8k.htm) ·
[Acquirer name and ticker filing](https://www.sec.gov/Archives/edgar/data/820318/000119312522240836/d347635d8k.htm) ·
[OCC memo 50993](https://infomemo.theocc.com/infomemos?number=50993)

On February 23, 2023, the acquirer's common started trading on the NYSE as COHR.
Its separate 6% Series A mandatory convertible preferred stock traded on the
NYSE as IIVI. IIVI alone is therefore not sufficient to distinguish the common
and preferred across dates and exchanges.
[Issuer transfer completion](https://ir.coherent.com/news-releases/news-release-details/coherent-corp-began-trading-nyse)

The offline checker compares those five exact date-symbol-venue assertions.
Unlisted dates and venues remain unknown; it does not extrapolate continuous
listing, carry the CUSIP into a different evidence date, map a market-data
vendor's instrument, join prices and halts, or qualify returns. The 2026 Coherent
study cutoff and endpoint dates are unchanged. No trading or data requests are
part of this package.

Run `python3 -m unittest discover -s backend -p test_cohr_listing_anchors.py`.
