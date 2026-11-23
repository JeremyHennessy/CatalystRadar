# CatalystRadar Command Center delivery

## Baseline

Public main `219a1e6fa110d759620b555f596f5258327bce90`: a source audit parsed all 12 public HTML routes and checked 296 authored anchors. All authored local routes and static fragments resolved in that revision. This does not validate generated links, external targets or rendering. Two routes, Datasets and Operations, lack skip links. The old 14-item homepage navigation had no vertical overflow on desktop and used horizontal scrolling on phones. Datasets and Financial Review load 20 and 17 script tags respectively. Keep their evidence and stable URLs; make the research paths easier to find before changing their loading architecture.

## First redesign increment

- Command Center is the existing homepage URL. Its primary paths are ideas, company search, tracker and source health. The research library groups the existing deep links by task.
- The public homepage describes V2 as unconnected. The historical trial retains its existing saved data. No portfolio records, market-data requests, account scripts or controls are introduced.
- The home sidebar wraps on phones rather than relying on sideways scrolling. Keep original evidence sections, DOM IDs and native navigation, including the Backspace helper.
- Navigation regression tests cover the homepage's critical links, anchors and account labels. Actual desktop and phone rendering, keyboard focus, history and production paths remain release checks.

## Next checks and increments

1. Verify the redesigned homepage at desktop and phone widths: no horizontal document overflow; focus reaches the skip link and primary actions; reload only loads saved evidence.
2. Test ideas → tracker → original evidence → browser Back and company search → dossier → evidence. Verify the old deep links in the published revision.
3. Apply the same navigation to the main destinations and improve skip links and active-page cues. Keep current verified collection distinct from frozen audits.
4. Integrate an owner-appropriate V2 view only after custody and data-access boundaries are verified. No activation, new market-data entitlement or order processing follows from the redesign.
