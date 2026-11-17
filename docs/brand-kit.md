# Brand kit (from Lauren's Canva, read 17 Nov 2026)

> **Renamed 17 Nov 2026: the product is now "Radar"** (see `collab/DECISIONS.md`). Colours, fonts, risk levels and icons below still apply; the "VIP" name, logo lock-ups and "Protected by VIP" copy are superseded.

## Radar logo (17 Nov 2026, previews only)
- Files: `docs/brand/radar-logo-v5-preview.png` (one signal arc) and `docs/brand/radar-logo-v6-preview.png` (two arcs).
- Mark: a document/phone shape (navy `#1F1C4F`, or white on navy) with a radar "ping" (dot + arc) cut from its top-right corner. Ping in Westpac red `#DA1710` or purple `#991AD6`.
- Wordmark: **RADAR** in a heavy, wide, letter-spaced sans; tagline **"Don't let scams fly under the radar."**
- Lock-ups: horizontal (mark left, wordmark right) and stacked; light and dark backgrounds.
- **Leaning v5** (dot + one arc): the mark is often shown small and v6's extra arc gets muddy (Kiel, 17 Nov). **Open:** final ping colour (red / purple); the wordmark font name; clean SVG/PNG exports (these files are preview sheets).

Source: "Branding Kit Lauren VIP" (Canva, comment access). This file transcribes it so code and AI agents can use it. The Canva page is the master; update this file if it changes.

## Opening animation (Delvin, 17 Nov 2026)
- File: `docs/brand/radar-opening-animation.html` (self-contained SVG + CSS, about 1.6s; light/dark toggle; respects reduced motion).
- Sequence: invoice rises in with the red dot → dot double-pulses, sending two sonar lines across the invoice → final arc settles into the v5 logo → **RADAR** wordmark and tagline fade in.
- **Loading state:** add `class="scanning"` to the `svg.logo` and the dot keeps pulsing and sweeping until you remove it. Use this while a Radar check runs.

## Name
- **Radar**. Usage: "Radar check", "Radar score 94/100", "Checked by Radar". Never "verified", "protected" or "safe".
- Subtitle on title cards: "2026 Westpac Hackathon · QUT Dean's Scholars"
- Title cards show the Westpac logo top-left on white, then a red (#DA1710) banner with white Anton title.
- In the app UI (`mockups/radar/index.html`), Radar elements use navy + the logo's red ping; Westpac's own controls keep Westpac red/maroon.

## Colours
| Role | Hex |
|---|---|
| Westpac red (primary) | `#DA1710` |
| Navy (text, headings) | `#1F1C4F` |
| Pink accent | `#FF3DDB` |
| Purple accent (VIP mark, icons) | `#991AD6` |
| Grey (secondary text) | `#706F7C` |

## Fonts
- Headings: **Anton**
- Body: **Arial**
- Accent / data (scores, codes, BSBs): **Fira Code**

## Risk levels (four, not three)
| Level | Colour | Title | Message |
|---|---|---|---|
| Low | `#1B7F4B` | Looks Good | We've checked this invoice and the supplier's details match what we have on file. You're right to go ahead. |
| Medium | `#F2A900` | Take a quick look | Something's changed on this invoice. Check it with your supplier before you pay. |
| High | `#DA1811` | Pause before paying | These bank details don't match your supplier. Please confirm them by phone first. |
| Critical | `#7A0C09` | Don't Pay this invoice | We've stopped this payment. A Westpac specialist will call you to help. |

Cards: coloured header with level name, pale tint of the same colour as body, icon + title + message.

## Icons (Westpac GEL design system names)
GenericFileIcon (Invoice), TickCircleIcon (Verified), VerifiedIcon (Protected), AlertIcon (Alert), LimitIcon (Blocked), BankIcon (Bank), NotificationIcon (Notify), PadlockTickIcon (Secure). Shown in purple `#991AD6` on a pale purple tile.

## Mood board notes (CommBank Safe, critiqued)
- Keep: bright, eye-catching colour.
- Avoid: colour not carried into scam notifications; plain, easily ignored warnings; white background; icons too small; **no instructions or next steps**. Every VIP warning must say what to do next.

## Not yet filled in
- "Tone of voice" section is empty in Canva.
- "Alert and photo guide" has placeholders only.
