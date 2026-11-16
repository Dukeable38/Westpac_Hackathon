# Build plan: Invoice Scam Checker (hackathon MVP)

Owner: Kiel · Builder: Paul (+ AI coding tools, overnight Mon 16 Nov) · Demo freeze: Tue 17 Nov, 12:30pm

This is the spec for the overnight build. Read it with `research-checks.md` (check catalogue, escalation and chat rules) and `pipeline.html` (diagram). The UI target is `../mockups/index.html`, so copy its layout, copy and colours rather than inventing new ones. Test fixtures live in `../demo/`.

Fallback assumption: Lauren and Nathan may not deliver. Everything the demo needs (seed data, 4 test invoices, UI, script beats) is already in this repo, so the build does not depend on them. Treat anything they send as an upgrade.

---

## 1. What "done" looks like (demo acceptance)

The video demo is four invoices uploaded in a row. Each one must produce this result, every time, offline:

| # | File | Expected band | Score (approx.) | Must show |
|---|---|---|---|---|
| 1 | `01-tallowwood-clean.pdf` | Looks genuine | 90–98 | Fast clear after Tier 1; Tier 2 "not needed"; reasons are reassuring (paid 14× to this account, CoP match, ABN active) |
| 2 | `02-tallowwood-changed-bank.pdf` | High risk | ≤15 | Locked flags: bank details changed for known supplier + CoP no match; PDF edited after creation with an overlay on the bank details; original details recovered (064-118 / 1048 2291); lookalike email domain. Chat "they told me they changed banks" does **not** raise the score and switches advice to "call them on 07 5550 2184 (the number on your earlier invoices)" |
| 3 | `03-brightwater-sloppy-fake.pdf` | High risk | ≤15 | Invalid ABN checksum, GST maths wrong, "BPAY" with only a BSB, 24-hour urgency, payee on the warning register, **hidden instruction to the AI** found and shown as a locked flag |
| 4 | `04-fernhill-new-business.pdf` | Check before paying → Looks genuine | ~58 → ~81 | New payee, ABN 7 weeks old, domain 6 weeks old, thin web presence. Chat "Yes, new business, I met the owner at the expo and ordered this" moves it to green; the panel shows which signals were softened and which were not |

Plus: every result can be saved as a payment receipt holding file name, SHA-256 and score. The PDF itself is discarded.

If time runs out, the order of priority is: #2 > #4 > #3 > #1 > receipt > everything else.

---

## 2. Architecture

```
Browser (single page, from mockups/index.html)
   │  POST /api/check (multipart PDF + customer_id)
   │  GET  /api/check/{id}/events   (SSE: tier progress, signals as they land)
   │  POST /api/check/{id}/chat     (message → claim → re-score)
   │  POST /api/check/{id}/decision (pay | hold | report) → receipt
   ▼
FastAPI (Python 3.11)
   ├── pdf_forensics.py   pypdf + pdfplumber: text, metadata, revisions, hidden text, overlays
   ├── extract.py         one LLM call → JSON (Pydantic-validated), from SANITISED text only
   ├── checks/            one module per check ID (C1…C41), each returns Signal
   ├── policy.py          deterministic tier escalation + stop rules (NO LLM here)
   ├── score.py           log-odds sum → 0–100, coverage %, reasons ordered by weight
   ├── chat.py            LLM maps message → enumerated ContextClaim; code applies rule table
   ├── sources/           abn.py, dns.py, rdap.py, crtsh.py, search.py, cop_mock.py, register_mock.py
   │                      every call goes through cache.py (record/replay, see §6)
   └── db.sqlite          seeded from demo/seed/seed.json
```

Recommended stack: FastAPI + pypdf + pdfplumber + SQLite + plain HTML/JS front end (lift the mock-up). Avoid a React build step unless Paul prefers it; the mock-up is already the front end.

LLM: whatever the hackathon provides ("Jev" in the research notes). Wrap it in `llm.py` with two functions only: `extract(sanitised_text) -> InvoiceJSON` and `classify(question, choices, snippet) -> choice`. Swapping providers then only touches one file.

---

## 3. Data model

```python
class Signal(BaseModel):
    id: str              # "C1"
    name: str            # "Bank details changed for a known supplier"
    tier: int            # 0..3
    state: Literal["risk", "neutral", "reassuring", "unknown"]
    weight: float        # log-odds contribution when state == risk (negative) / reassuring (positive)
    evidence: str        # one plain-English line shown to the customer
    locked: bool         # True = chat can never soften it
    softened_by: str | None = None   # ContextClaim that softened it, shown in UI

class CheckResult(BaseModel):
    check_id: str
    file_name: str
    sha256: str
    extracted: InvoiceJSON
    signals: list[Signal]
    score: int           # 0..100, higher = more confident it's genuine
    band: Literal["genuine", "check", "high_risk"]
    coverage: float      # share of high-weight signals actually evaluated
    tiers_run: list[int]
    advice: str          # the one next action we recommend
```

Bands: **≥80 Looks genuine**, **50–79 Check before paying**, **<50 High risk**. Any hard-stop signal forces High risk regardless of the sum.

`InvoiceJSON` fields: supplier_name, abn, acn, email, phone, website, invoice_number, invoice_date, due_date, line_items[], subtotal, gst, total, payment_methods[] (each: type BSB|PAYID|BPAY, bsb, account_number, account_name, payid, biller_code, reference), free_text_notes[].

---

## 4. Scoring

`score = round(100 * sigmoid(bias + Σ wᵢ·sᵢ))`, where sᵢ = −1 risk, 0 neutral/unknown, +1 reassuring. Start with `bias = +1.5` (most invoices are fine) and tune weights so the four fixtures hit the table in §1. Store the weights in `weights.yaml` so tuning doesn't touch code.

Starting weights (log-odds):

| Weight class | w | Examples |
|---|---|---|
| Hard stop | force band | C2 register hit, C13/C15 payment-field tampering, C25 ATO wrong account, C1+C3 no match |
| High | 2.0 | C1, C3 no match, C8 invalid, C14 hidden instructions, C21 cancelled, C24, C30 |
| Medium | 1.0 | C3 close, C4, C10, C12, C18, C19, C20, C23, C31 |
| Low | 0.4 | C7, C26, C29, C33, C35 absence |
| Reassuring | +0.8 to +1.5 | prior payments to same account (+1.5), CoP match (+1.0), ABN active + name match (+0.8) |

The UI shows each signal's contribution as "points" (difference in the final score with vs without that signal). Compute this in `score.py` so the front end only displays it.

---

## 5. Checks to build (in order)

Build the **demo set** properly; stub the rest as `state="unknown"` so coverage % is honest.

| Priority | IDs | Notes |
|---|---|---|
| P0 (demo needs it) | C1, C2, C3, C4, C8, C10, C13, C14, C15, C18, C19, C20, C21, C23, C26, C30, C31, C39 | C39 = read the earlier revision and report the original bank details. This is the "wow" moment for #2 |
| P1 | C5, C6, C7, C11, C12, C24, C25, C29, C35 | C25 needs the official ATO payment details. Verify on ato.gov.au "How to pay" before hard-coding |
| P2 / stub | everything else | Return `unknown` with a reason ("not checked in this demo") |

Implementation hints:
- **C13 / C15 / C39:** `pypdf` reader; count `%%EOF` markers / xref sections (>1 = incremental update). For each revision, extract text and diff payment fields. Detect overlays as: a filled white rectangle or a later content stream drawn over the bbox of text matching BSB/account regexes (pdfplumber gives `rects` and `chars` with coordinates).
- **C14:** pdfplumber chars where `non_stroking_color` ≈ white on a white page, font size < 3pt, or text outside the media box; also zero-width Unicode and Cyrillic/Greek homoglyphs in names, emails and URLs. **Strip this text before any LLM call** and turn it into a signal. If it contains instruction-like text ("AI", "assistant", "ignore", "mark as"), set weight High and `locked=True`.
- **C8:** ABN mod-89; ACN mod-10 (see research notes).
- **C10:** recompute GST = 10% of taxable subtotal, tolerance 2c.
- **C30:** compare email/website domain to the supplier profile's known domain (Levenshtein ≤2, or dnstwist-style permutations).
- **C31:** for `.com.au` RDAP gives no dates, so use the earliest certificate from crt.sh, fall back to Wayback CDX first capture.

---

## 6. External data: live, cached, or mocked

**Every external call goes through `cache.py`** keyed by (source, normalised query). Env flag `DEMO_MODE=replay` serves only from `demo/cache/*.json`, so the recorded demo cannot fail on wifi. Record the cache once on Tuesday morning with `DEMO_MODE=record`.

| Source | Mode | Note |
|---|---|---|
| ABN Lookup JSON | Live + mock override | Register for the GUID **today** (arrives by email). Fixture ABNs are made up, so `sources/abn.py` first checks `demo/seed/seed.json → abn_registry` and only goes live for other ABNs |
| Confirmation of Payee | Mock | Return Match / Close match / No match / Unavailable from `seed.json → cop` |
| Warning register (flag register) | Mock | `seed.json → flag_register` |
| Supplier profiles / payment history | Mock (SQLite) | `seed.json → customers[].suppliers[]` |
| DNS (MX/SPF/DMARC) | Live via Cloudflare DoH, cached | Fixture domains won't resolve, so seed them in the cache |
| crt.sh / Wayback / RDAP | Seeded cache | Same: fixture domains are fictional |
| Web search | Seeded cache | Tavily or similar for real queries; fixtures use canned results |
| BSB directory | Download once | AusPayNet BSB file; fall back to the `bsb_directory` stub in seed.json |

---

## 7. Policy engine (tiers)

Implement the escalation rules in `research-checks.md` literally, as ordered `if` statements in `policy.py`. Emit an SSE event when each tier starts and finishes and when each signal lands. The UI animates these, and they are the visual proof of the "medical screening" story.

Fast-clear (#1) must visibly **skip** Tier 2 with the label "Not needed: fast clear". Escalation (#2, #3, #4) must show *why* it escalated ("new payee", "changed bank details", "uncertain score").

Latency budget for the demo: Tier 0+1 under 4s, Tier 2 under 10s (cached, so this is easy). Add an artificial ~300 ms per check in `DEMO_MODE` so the progress animation is readable on video.

---

## 8. Chat

1. User message → `llm.classify()` returns one or more `ContextClaim`s from the enum in `research-checks.md`, or `NONE`.
2. `chat.py` applies the rule table: softening multiplies the weight (e.g. ×0.3); locked signals are untouched; `SUPPLIER_CHANGED_BANKS` changes `advice`, not the score.
3. Re-score and return the **diff**: which signals changed, old → new score. The UI shows "Softened by your answer" chips on the changed signals and "Not affected by chat" on locked ones.
4. The assistant's reply text is generated by the LLM *from the diff*, never free-form about the invoice.

Canned assistant openers per band (LLM can paraphrase):
- High risk: "I found something serious. Before you pay, here's what I'd do…"
- Check: "A few things I couldn't confirm. Can you tell me more about this supplier?"
- Genuine: "This looks consistent with your past payments to this supplier."

---

## 9. Receipt

On decision, store: `{receipt_id, customer_id, file_name, sha256, score, band, signals_summary, decision, decided_at}`. Delete the uploaded PDF from disk. The UI shows the receipt card from the mock-up. Bonus: a "Verify a file" button that hashes a dropped file client-side (`crypto.subtle.digest`) and says whether it matches a stored receipt. This demos the "edited after payment" dispute story with fixture #1 vs #2.

---

## 10. Timeline

| When | What | Who |
|---|---|---|
| Mon evening | Repo scaffold, seed loader, PDF forensics (C13/C14/C15/C39), score + policy, API skeleton | Paul (AI tools) |
| Mon overnight | Remaining P0 checks, chat, SSE, front end wired to mock-up | Paul (AI tools) |
| Tue 9:30 | Run all 4 fixtures; tune `weights.yaml` to hit §1 table | Kiel + Paul |
| Tue 10:30 | Record cache (`DEMO_MODE=record`), switch to replay | Paul |
| Tue 12:30 | **Feature freeze.** Only copy and bug fixes after this | All |
| Tue 1–3pm | Record video. If the live app misbehaves, record the mock-up (it plays all 4 scenarios) | All |

---

## 11. Guardrails (don't skip)

- The LLM never sees raw invoice text, only sanitised text after C14 stripping.
- The LLM never produces the score, the band, or the escalation decision.
- Chat can add checks but can never cancel a locked flag.
- Fictional businesses only. Fixture ABNs are checksum-valid but invented: before the video, look each one up on abr.business.gov.au and regenerate any that resolve to a real entity. Phone numbers use the ACMA fictional range (07 5550 xxxx).
- No real Westpac logo in the video UI. Use the colours and our product name.
