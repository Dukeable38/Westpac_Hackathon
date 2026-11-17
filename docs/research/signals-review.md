# Radar signal review

Research checked **17 November 2026**. Australian primary sources are preferred. A signal is evidence, not a conclusion; weak signals must not become hard stops by themselves.

## Findings and gaps

Scamwatch describes payment-redirection fraud as a legitimate-looking invoice with substituted payee details and explicitly recommends verifying changes using independently sourced contact details. It also names unexpected invoices and subtly changed email/web domains as warning signs ([Scamwatch, accessed 17 Nov 2026](https://www.scamwatch.gov.au/types-of-scams/business-email-compromise-scams)). Cyber.gov.au likewise identifies edited invoice contact/bank details, urgency, secrecy and lookalike domains, and recommends a consistent verification process ([Cyber.gov.au, accessed 17 Nov 2026](https://www.cyber.gov.au/publication/protecting-against-business-email-compromise)). These sources validate C1, C19, C20, C30 and the known-number callback rule.

The invoice alone cannot prove that its sending mailbox is genuine: Scamwatch notes that the message may come from a compromised real account and even remain in the real thread. Radar should therefore accept email-envelope evidence when available (From, Reply-To, authenticated domain) but must not treat its absence as reassuring ([Scamwatch fake-invoice alert, accessed 17 Nov 2026](https://www.scamwatch.gov.au/about-us/news-and-alerts/scam-alert-fake-business-invoice-scams)).

Cyber.gov.au warns that QR codes hide link destinations and may lead to malicious sites or downloads. Radar should extract PDF annotations and QR destinations without opening them, then compare their domains and payment identifiers with the stated supplier ([Cyber.gov.au phishing guidance, accessed 17 Nov 2026](https://www.cyber.gov.au/guidance/learn-about-phishing-scams)).

AUSTRAC lists accounts receiving deposits from multiple third parties, unrelated parties sharing beneficiaries, rounded transactions inconsistent with a profile, and many customers paying one beneficiary as suspicious patterns. A bank can therefore add cross-customer payee reuse and account-profile signals that a standalone invoice checker cannot ([AUSTRAC banking indicators, accessed 17 Nov 2026](https://www.austrac.gov.au/industry-and-business/education-and-resources/publications-and-resources/indicators-suspicious-activity-banking-sector)). These are high-value escalation signals but require bank-side data and human/fraud controls; they are not automatic fraud findings.

The ATO requires tax invoices to identify the seller and ABN, issue date, supplied items/quantity/price, and GST treatment; only GST-registered entities may issue a tax invoice ([ATO tax invoices, accessed 17 Nov 2026](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/tax-invoices), [ATO invoice setup, accessed 17 Nov 2026](https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/record-keeping-for-business/setting-up-and-managing-records/setting-up-your-business-invoices)). This supports C10/C21/C22 plus date, identity and line-item consistency, but missing fields usually mean “invalid tax invoice/manual review”, not “scam”. ASIC provides company name, identifiers, registration date and status through its registers; officeholder detail may require paid extracts, so C36 is feasible while C40 is not a demo priority ([ASIC registers, accessed 17 Nov 2026](https://www.asic.gov.au/online-services/search-asic-registers/company-and-organisation-registers)).

## Changes to existing checks

| ID | Recommendation | Reason |
|---|---|---|
| C3 | Treat Westpac Verify/CoP as an existing bank input, not a Radar claim; No Match is a hard stop only with C1 or an independently strong identity mismatch. | Avoids duplicating Westpac Verify and reduces false alarms for trading names. |
| C5 | Keep exact fraud-hash match High/Critical; move fuzzy cross-supplier template reuse to new C48. | Exact known-fraud evidence and generic template similarity have very different precision. |
| C10 | Expand to ATO-required identity/date/line-item/GST consistency; Medium, not hard stop. | Invalid tax invoices can be mistakes. |
| C12 | Compare producer and modification pattern with supplier history; keep Medium and never hard stop alone. | Canva/Word is common and not suspicious without a change from history. |
| C16 | Include URI annotations, launch actions and extracted QR destinations; suspicious destination is High, generic links Medium/neutral. | Directly supported by cyber guidance; safe static parsing only. |
| C17 | Mark as an enabler, exclude from score/confidence denominator, and treat extraction failure as lower confidence. | It is plumbing, not evidence for or against fraud. |
| C29 | Keep Low and never hard stop. | Grammar/formatting creates cultural and small-business false positives. |
| C31 | Rename evidence to “first certificate/archive observation”; do not call it registration age. | crt.sh/Wayback dates are proxies, not ownership/registration proof. |
| C33 | Missing SPF/DMARC lowers confidence or adds Low risk only; a strong policy is not reassuring by itself. | Email controls reduce spoofing but do not prevent mailbox compromise. |
| C35 | Absence of reviews is unknown/weak; verified scam reports may be High. | New legitimate businesses have little web presence. |
| C37 | Deprioritise; logo reuse is normal and scammers can copy legitimate branding. | Low precision and poor demo value. |
| C40 | Skeleton only; paid/privacy-sensitive officeholder data and weak invoice-level causality. | ASIC free data is better used for C36. |
| C41 | Model as workflow/resolution, not a scored check or confidence denominator. | Human referral resolves uncertainty; it is not invoice evidence. |

## Proposed checks

`feeds` names downstream checks or decisions informed by the signal.

| ID | Name | Plain-English description | Tier | Executor / source | Weight | Hard stop | Chat-adjustable | feeds | Effort | Demo today |
|---|---|---|---:|---|---|---|---|---|---|---|
| C42 | Embedded payment link / QR destination | Extracts links and QR destinations without opening them and checks whether the destination conflicts with the supplier or printed payment details. | 0 | code; PDF annotations + QR decoder; Cyber.gov.au | High on mismatch | no | no | C16,C30 | M | yes, skeleton without QR decoder |
| C43 | Account-name/entity-type mismatch | Flags a personal account name for a company supplier, or an unrelated company name, after normalising trading names. | 1 | code; extracted payee + ABN entity type + CoP | Med–High | only with C1/CoP No Match | trading-name evidence only | C3,C24 | S | yes |
| C44 | Invoice chronology anomaly | Detects future issue dates, due-before-issue dates and implausibly stale invoices. | 0 | code; extracted dates | Low–Med | no | contractual explanation | C6,C20 | S | yes |
| C45 | Invoice sequence/cadence anomaly | Compares invoice number and timing with this supplier’s prior invoices. | 1 | code; supplier history | Low–Med | no | yes | C6 | M | yes with seed |
| C46 | Approval-threshold / round-amount anomaly | Flags amounts unusually close to the customer’s approval limit or unusually round relative to history. | 0 | code; customer controls + history; AUSTRAC | Low | no | yes | C7 | S | yes with seed |
| C47 | Cross-customer payee reuse / mule pattern | Detects one new account receiving invoices for many unrelated suppliers or customers. | 0 | bank code/data; AUSTRAC | High | fraud-team rule only | no | C2,C41 | M | yes with fictional seed |
| C48 | Template reuse across unrelated suppliers | Uses layout/text fingerprints to find the same invoice template presented as unrelated suppliers. | 0 | code; bank corpus | Med–High | no | no | C5,C47 | M | yes with fictional seed |
| C49 | Sender / Reply-To / authenticated-domain mismatch | Compares email envelope and SPF/DKIM/DMARC result with invoice contacts and known supplier history. | 0 | code; original email headers | High on authenticated mismatch | no | no | C26,C30,C33 | M | no (upload is PDF-only) |
| C50 | Supplier domain changed from history | Detects a newly seen sender/email domain for a known supplier even when the spelling is not a lookalike. | 1 | code; supplier history | Med–High | no | known-number callback only | C30,C31,C49 | S | yes with seed |
| C51 | Currency / geography mismatch | Flags foreign currency or bank geography inconsistent with a domestic supplier and customer history. | 0 | code; extracted currency + history | Med | no | yes | C7,C28 | S | yes with seed |
| C52 | BPAY biller and CRN consistency | Validates biller-code format, expected biller identity and available CRN rules instead of treating all BPAY fields as equivalent. | 0 | code + bank/BPAY directory | Med–High | known bad biller only | no | C3,C18 | M | skeleton (directory unavailable) |

PayID display-name comparison belongs in C3 rather than a new Radar check: it is the PayID/CoP equivalent of the bank’s existing beneficiary-name result.

## Priority shortlist

1. **C44 chronology** — cheap, visible on every Nathan fixture, deterministic.
2. **C43 account/entity mismatch** — directly explains personal-account diversion.
3. **C42 embedded links/QR** — strong demo story and static PDF safety value.
4. **C50 supplier-domain change** — high BEC value with existing history.
5. **C47 cross-customer payee reuse** — uniquely bank-grade and high fraud-catching value.
6. **C48 template reuse** — complements exact hashes and cross-customer evidence.
7. **C51 currency/geography mismatch** — cheap and understandable.
8. **C52 BPAY consistency** — useful coverage, skeleton until a reliable directory/rule source exists.

## Confidence formula

Confidence is **weighted applicable evidence coverage**, separate from score:

`confidence = Σ importance(check) for applicable risk/neutral/reassuring results ÷ Σ importance(check) for applicable checks`

Importance is High=3, Medium=2, Low=1, enablers/workflows=0. `unknown` stays in the denominator when the check was applicable but unavailable; `not_applicable` and payment-method-specific checks for another method are excluded from both sides. Skeletons return `unknown`, never fake neutral evidence. Labels: `high ≥ 0.80`, `partial ≥ 0.50`, otherwise `low`. A Low risk result with low confidence must use qualified advice such as “No major warning signs in the checks completed; important checks were unavailable,” never “Looks good.”

Offline fake/replay examples after TASK-004b (these measure evidence coverage, not model accuracy):

| Invoice | Risk result | Confidence |
|---|---|---:|
| 01 Tallowwood clean | Low | 0.812 high |
| 02 Tallowwood changed bank | Critical | 0.717 partial |
| 03 Brightwater fake | High | 0.538 partial |
| 04 Fernhill new business | Medium | 0.716 partial |
| Nathan N1 Larana | High | 0.441 low |
| Nathan N2 Bowing | High | 0.446 low |
| Nathan N3 Skype | High | 0.446 low |
| Nathan N4 Fusion | High | 0.446 low |

Nathan results are deliberately low-confidence: the fake extractor misses most fields, so their High result is not presented as a reliable fraud conclusion.
