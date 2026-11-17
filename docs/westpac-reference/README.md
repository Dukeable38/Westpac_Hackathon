# Westpac Online Banking: real screenshots (source of truth for the UI)

Kiel captured these on 17 Nov 2026 in his own Westpac Online Banking (desktop browser), with personal data blacked out.
**They are the base for every Radar screen.** Radar features are added *into* these pages; we don't invent our own banking chrome.
Where they disagree with `mockups/radar/index.html`, the screenshots win.

| File | Screen |
|---|---|
| `01-overview-dashboard.png` | Overview: "Your accounts" tiles, Upcoming payments, SafeBlock tile, chat pop-up |
| `02-make-a-payment.png` | Make a payment: Pay to (tabs All / Payees / BPAY / International), From, Payment details, right-hand "Multiple Payment" panel |
| `03-pay-new-payee-bsb.png` | Pay new payee, BSB & account no., with the **Check details** button (Westpac Verify / CoP) |
| `04-pay-new-payee-bpay.png` | Pay new payee, BPAY biller code + CRN, with the orange **"Stay safe from scams"** banner |

## Patterns to copy
- **Header:** red Westpac logo top-left. Top-right grey outlined buttons: "Personal Profile - Personal banking ▾", "Requests", "Notifications ▾" (red count badge), "Sign Out". Search box + "Search" button below.
- **Main nav:** Overview · Payments · Service · Westpac Rewards · Business Hub · Products · Home loans. Active tab has a red underline. Thin grey rule under the nav.
- **Page title:** large light navy ("Your accounts", "Make a payment"), with "‹ Back" in red to its left on sub-pages.
- **Primary buttons:** solid Westpac red, white bold text, small radius ("Transfer funds", "Make a payment", "Continue", "Check details"). Secondary actions are grey outlined buttons ("Pay new payee", "View") or underlined text links ("Cancel", "View more").
- **Account tiles:** white card, thin grey border, title top-left, chevron button top-right, faint Westpac mark, grey lower half holding the balance.
- **Forms:** white panel with grey border split into sections (Pay to / From / Payment details), each with a medium-size heading. Labels bold and small; inputs light grey fill with dark border; "optional" as a small green-grey tag. Help "?" circles after labels.
- **Inline info:** pale blue box with a left pointer (payment limit). Scam warning: pale orange box, orange border lines, orange "!" icon, bold "Stay safe from scams." lead-in and an underlined link.
- **Side panel:** grey box on the right ("Multiple Payment") with an icon heading, short text and an underlined link. A good slot for a Radar promo/"Attach an invoice" hint.
- Fonts are plain system sans (Arial/Helvetica look), not Anton. Anton stays for slides and title cards only.

## Where Radar fits (proposed)
- Make a payment, in the "Pay to" section: an **Attach invoice (Radar)** control next to "Pay new payee", or a row under the payee fields. Attaching starts the check and pre-fills payee/amount.
- Radar's result appears in the same visual language as the orange scam banner and the blue info box (risk-level colours from `docs/brand-kit.md`).
- Overview: a tile in the same grid as SafeBlock ("Radar invoice check · Check an invoice before you pay").
- Loading state while checking: the Radar logo in **scanning** mode (`docs/brand/radar-opening-animation.html`, add `class="scanning"` to the svg).
