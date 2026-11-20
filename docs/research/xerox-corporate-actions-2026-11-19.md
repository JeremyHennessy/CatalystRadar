# Xerox (XRX): two distinct identity changes

**Scope:** two reviewed actions only, no provider instruments or historical returns.
Query the offline fixture in `backend/xerox_corporate_actions.py` by exact
action date and directional common-stock listing keys. It is not a point-in-time
symbol master or a price adjustment engine.

| Effective date | Before → after | Confirmed evidence |
| --- | --- | --- |
| 2019-07-31 | Xerox Corporation (CIK 0000108772), NYSE XRX common → Xerox Holdings Corporation (CIK 0001770450), NYSE XRX common | Holding-company reorganization. Each legacy common share converted into one Holdings common share. The old issuer remained a wholly owned subsidiary; the ticker alone does not identify the old issuer. |
| 2021-09-21 | Xerox Holdings, NYSE XRX common → Xerox Holdings, Nasdaq Global Select Market XRX common | Same common stock and CUSIP 98421M106 on both sides per Nasdaq's notice. The consolidated quote and trade feed changed at the transfer. Not a second conversion. |

- **2019:** The [legacy 8-K](https://www.sec.gov/Archives/edgar/data/108772/000119312519208952/d781319d8k.htm)
  says legacy common ceased trading July 31. The
  [successor 8-K12B](https://www.sec.gov/Archives/edgar/data/1770450/000119312519208837/d767474d8k12b.htm)
  documents completed conversion, but calls August 1 trading an expectation.
  The [combined 2019 annual report](https://www.sec.gov/Archives/edgar/data/1770450/000177045020000012/xrx-123119x10xk.htm)
  subsequently confirms the NYSE ticker. None of these is a first-print record.
- **2021:** The [exchange registration](https://www.sec.gov/Archives/edgar/data/1770450/000119312521276925/d189027d8a12b.htm)
  records the intended transfer at market open, the
  [Nasdaq transfer notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=dtn2021-36)
  supplies date-specific symbol/CUSIP and feed details, and the
  [2021 annual report](https://www.sec.gov/Archives/edgar/data/1770450/000177045022000010/xrx-20211231.htm)
  confirms the Nasdaq listing. The transfer notice does not verify that a
  particular data vendor joined the histories correctly.

Compared with the prior COHR collision, one-for-one here is a documented legal
conversion, not a conclusion that can be applied to unrelated ticker reuse.
Neither XRX fixture establishes observed trading sessions, consistent
adjustments, licensed prices, a vendor mapping, or an outcome. No price series
was fetched or modified.
