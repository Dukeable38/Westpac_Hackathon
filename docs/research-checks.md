# Research: layered invoice checks, data sources, stats

Research sub-agent report, 16 Nov 2026, condensed. Items marked [verify] still need checking on the day.

## Core design rules
- Order checks by **cost vs evidence value**, not by data source. The bank's own records (supplier profile, flag register) are the cheapest *and* strongest signal, so they run in Tier 0.
- **Escalation is decided by deterministic policy code, never by the LLM.** The invoice is attacker-controlled input. If the model decides when to stop, a hidden-text injection can make it stop early.
- **LLM never outputs the score.** It extracts (to JSON, then validated by code), researches and explains. Jev answers yes/no/choice questions on **pre-extracted, sanitised** snippets only, never raw invoice text.
- Strip hidden text before any LLM pass, and record it as a signal (instructions hidden in an invoice are themselves a strong fraud signal).
- Score is a log-odds sum, `score = sigmoid(bias + Σ wᵢ·sᵢ)`. Each signal has a state (risk / neutral / reassuring / unknown) and a weight. Also track **coverage**: the share of high-weight signals actually evaluated.

## Tiers
| Tier | Budget | Runs | Contents |
|---|---|---|---|
| T0 Instant deterministic | <300 ms, ~$0 | Always | Hash, PDF metadata/revisions/hidden text/overlays, ABN & ACN checksums, GST maths, BSB directory, **supplier profile (changed bank details)**, **flag register**, invoice-hash reuse, CoP, duplicates |
| T1 Common red flags | 1–3 s, <1¢ | Always (cheap) | One LLM extraction pass, payment-method consistency, "bank details changed" language, urgency (Jev), ABN Lookup (status, name, GST, age), contact consistency, ATO allowlist, directory-offer pattern |
| T2 Targeted research | 5–15 s, cents | On escalation | Lookalike domains, domain age (RDAP / crt.sh / Wayback), .au eligibility ID, DNS MX/SPF/DMARC, official contact cross-check via search, web presence/scam reports, ASIC status, logo provenance |
| T3 Deep / niche | 15–60 s+ | High value or ambiguity | Render-vs-text OCR diff, prior-revision recovery ("original bank details were X"), director checks, human call-back / fraud team |

## Escalation rules (apply in order)
**Hard stop → HIGH RISK** (still run extraction + explanation):
1. Payee on flag register.
2. Changed bank details for a known ABN **and** CoP = No Match.
3. Invoice hash or template matches a fraud-flagged invoice.
4. Claims ATO/government but payment details aren't the official ones.
5. Tamper evidence in the bank-details region (incremental edit or overlay).

**Fast clear after T1 → LOW RISK** (all must hold): known supplier (≥2 prior payments to the same account for this ABN), CoP Match, amount ≤3× the supplier median, no T0 tamper flags, ABN active and name matches, no T1 flags above low.

**Escalate to T2** if any: new payee or changed details; CoP close/no match/unavailable (BPAY, PayID); score in the uncertain band (30–70); any medium T1 flag; amount above a threshold (e.g. >$5k); coverage <60%.

**Escalate to T3** if any: still uncertain after T2 and amount >$20k; conflicting strong evidence; the user's chat claim contradicts a high-weight signal (e.g. "they changed banks", which is the BEC script).

**Stop** when: HIGH with a hard-stop signal; LOW with coverage ≥80%; or the cost/latency budget is spent (show "partially verified").

## Chat rules
The LLM (or Jev, as a choice question) maps the user's message to an enumerated **context claim**. Code applies a fixed rule table:
- `NEW_BUSINESS` softens domain age, ABN age and no web presence. It does not touch tamper or flag signals.
- `SOLE_TRADER` softens free-mail address and no website.
- `TRADING_NAME` softens a CoP close match if that name is on the ABN's business-names list.
- `ORDERED_THIS` softens relationship plausibility.
- `SUPPLIER_CHANGED_BANKS` **does not lower risk**. It switches advice to "call them on a number you already had".
- `VERIFIED_BY_PHONE_KNOWN_NUMBER` reduces the changed-details signal by at most 50%.
- **Never adjustable:** flag-register hit, fraud-hash match, payment-field tampering, ATO wrong account, CoP No Match on a business account.

Chat can trigger *more* checks but can never cancel a flag.

## Check catalogue (IDs for the build)
Executor key: C = code, J = Jev, L = LLM, A = external API, M = mock.

| ID | Check | Tier | Exec | Weight | Chat-adjustable |
|---|---|---|---|---|---|
| C1 | Changed bank details for a known supplier ABN | T0 | C (supplier profile) | High | Only by known-number call-back (≤50%) |
| C2 | Flag register hit (account/PayID/ABN/email) | T0 | C | High, hard stop | No |
| C3 | Confirmation of Payee result | T0 | M | High (no match) / Med (close) | Close match via TRADING_NAME |
| C4 | New payee + high amount | T0 | C | Med | Slightly |
| C5 | Invoice hash / template seen before (fraud or duplicate) | T0 | C | High / Med | No / yes for retainer |
| C6 | Duplicate invoice number or amount | T0 | C | Med | Yes |
| C7 | Amount anomaly vs supplier history | T0 | C | Low–Med | Yes |
| C8 | ABN checksum (mod 89) | T0 | C | High if invalid | No |
| C9 | ACN checksum | T0 | C | Med | No |
| C10 | GST maths and tax-invoice validity | T0 | C | Med | GST-free items |
| C11 | BSB validity and bank-name match (AusPayNet) | T0 | C | Med (mismatch High) | No |
| C12 | PDF metadata (online editor, mod ≫ create date) | T0 | C | Med | "I re-saved it" |
| C13 | Incremental updates editing payment fields | T0 | C | High | No |
| C14 | Hidden text, zero-width chars, homoglyphs | T0 | C | Med–High | No |
| C15 | Overlay or annotation over the bank details | T0 | C | High | No |
| C16 | Embedded JS, launch actions, odd links | T0 | C | Med | No |
| C17 | Structured extraction + internal consistency | T1 | L + C | enabler | n/a |
| C18 | Payment-method inconsistency (BPAY vs BSB, two accounts) | T1 | C + J | Med–High | No |
| C19 | "Bank details have changed" language | T1 | J | High with C1 | No |
| C20 | Urgency / pressure / secrecy language | T1 | J | Med | "genuinely overdue" |
| C21 | ABN Lookup: active, name match, entity type | T1 | A | High (cancelled) / Med | TRADING_NAME |
| C22 | GST charged but not GST-registered | T1 | A + C | Med–High | Just registered |
| C23 | ABN age vs claimed history | T1 | A + C + J | Low–Med | NEW_BUSINESS |
| C24 | Real ABN, but payee or email belongs to someone else | T1 | C | High | Factoring → check new entity |
| C25 | ATO / government official payment-details allowlist | T1 | C | High, hard stop | No |
| C26 | Contact consistency (email vs website domain, free-mail, area code) | T1 | C | Low–Med | SOLE_TRADER |
| C27 | Directory / domain-renewal offer disguised as invoice | T1 | J + C | High | "I have a listing" |
| C28 | Relationship plausibility (fits the customer's business?) | T1 | J + C | Med | ORDERED_THIS |
| C29 | Spelling / formatting quality | T1 | L → J | Low | Yes |
| C30 | Lookalike domain (dnstwist-style) | T2 | C + search | High | No |
| C31 | Domain age (RDAP; for .au use crt.sh / Wayback) | T2 | A | Med | NEW_BUSINESS |
| C32 | .au registrant eligibility ID ≠ invoice ABN | T2 | A/M | Med–High | Agency-registered |
| C33 | Email DNS posture (MX/SPF/DMARC) | T2 | A | Low | Yes |
| C34 | Official contact details cross-check | T2 | L + search | Med–High | "they moved" (address only) |
| C35 | Web presence / scam reports | T2 | L + search | Med (scam hits High) | Absence only |
| C36 | ASIC company status | T2 | data.gov.au CSV | Med–High | No |
| C37 | Logo provenance | T2 | C | Low–Med | Yes |
| C38 | Render-vs-text OCR forensics on payment fields | T3 | C (+L vision) | High | No |
| C39 | Prior-revision recovery ("original details were…") | T3 | C + L | High | No |
| C40 | Director / officeholder checks | T3 | M | Low–Med | — |
| C41 | Human call-back / fraud-team referral | T3 | workflow | resolves | — |

**Demo priority (build these well):** C1, C2, C3, C13/C15, C19, C21, C24, C25, C27, C30.

## Data sources (hackathon realism)
- **Live:** ABN Lookup JSON (free GUID; register today, it arrives by email), DNS over HTTPS (Cloudflare), RDAP, crt.sh, Wayback CDX, Tavily (free dev tier [verify]).
- **Download once:** AusPayNet BSB file, ASIC companies and business-names CSVs (data.gov.au).
- **Mock:** CoP, PayID resolution, AFCX/flag register, supplier profiles/payment history (seed SQLite: 3 customers, ~10 suppliers, 1 changed-account case, 1 flagged mule), Scamwatch, ASIC officeholders, .au WHOIS.
- **Cache every external call** behind a flag so the demo can't fail live.
- ATO official payment details allowlist: verify current values on ato.gov.au "How to pay".

## Pitch stats (verified by the agent, with sources)
- Australians reported **A$2.18b** in scam losses in 2025, up 7.8% (NASC Targeting Scams 2025).
- **Payment redirection: A$166.8m in 2025**, #2 by loss, **up 9.3%**, one of the few major types still rising (NASC; ACCC release).
- **False billing was the most-reported scam type for small businesses**, and NASC says it is generally payment redirection / BEC (NASC p.40–41).
- About **30% of scam victims don't report** (ABS, cited by NASC).
- BEC with financial loss = **15% of business cybercrime reports**; average cybercrime cost per small-business report is **A$56,600** (all cybercrime, not BEC-only) (ASD Cyber Threat Report 2024–25).
- **94% of scam value reported by Westpac Institutional Bank customers was BEC** (Westpac IQ, Aug 2025).
- **Confirmation of Payee: >150m checks in year one**, >100 institutions. One bank saw >570k payments abandoned after No Match (AP+, Jul 2026).
- **Scams Prevention Framework:** banks designated on 28 May 2026 and must comply by **31 Mar 2027**. Principles: prevent, detect, report (actionable intelligence), disrupt, respond.
- Avoid: "Westpac BEC down 25%" (no source), "A$94k average BEC cost" (unverified).

**Pitch line:** "Payment redirection cost Australians A$166.8m last year and is one of the only major scam types still growing. From March 2027 banks must detect and disrupt scams and share intelligence. Our checker does all three before the money leaves."

## What we add beyond existing defences
CoP checks only the name the user typed, not the invoice: a fake supplier with a genuinely named mule account gets a full Match. Westpac Verify knows "the bank has never paid this account" but not "*you* always pay this ABN to account A". SaferPay asks generic questions that coached victims answer "correctly". AFCX is reactive: it learns about an account only after the first victims. We add document evidence, customer-specific supplier memory, BPAY/PayID coverage, and **proactive** intelligence (invoice hashes and templates flagged before the mule account reaches AFCX).
