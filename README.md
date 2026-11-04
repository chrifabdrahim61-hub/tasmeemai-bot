# TASMEEM AI - Logo & Ads Prompt Bot (Telegram)

A Telegram bot that builds professional, ready-to-use prompts through a
**guided questionnaire (QCM)**: the bot asks a series of short questions -
you tap buttons or type short answers - and the final prompt is generated
from your answers. **Two creation modes:**

- 🎨 **Logo prompt** - a professional logo-generation prompt
- 📢 **Social media post (ads)** - a professional ad-creative prompt for
  your product, service or page (with the instruction to paste your logo
  image together with the prompt into the AI model)

**The whole interface speaks 3 languages: English, Français, العربية.**

Typed answers are understood in **English, French, Arabic, Algerian
Darija and Arabizi** thanks to a rule-based normalizer.

**No AI services are used.** Everything is 100% rule-based Python:
dictionaries, regular expressions and templates, following the
"Logo Prompt Engineer" master skill.

The bot produces **prompts only** - never images, never other artwork.

## Current status

**Step 8 complete + hotfix 0.8.1 (the owner can grant credits in any
syntax - /addcredits, brackets optional, one-tap self top-up buttons)
on top of Step 8 (second mode "Social media posts (ads)", @vxgix shown
after every output, admin IDs) and Step 7 (credits, referrals,
force-subscribe, Stars donations) and Step 6 + hotfix 0.6.1.**

| Action | Behaviour |
| --- | --- |
| `/start` | Menu: language row (English / Français / العربية) + the two creation modes (🎨 Logo / 📢 Social media post) + Donate / Support |
| Language buttons | Switch the interface language instantly - even in the middle of the questionnaire |
| `/lang en\|fr\|ar` | Same switch by command |
| Questionnaire | ~16 steps for a typical path: brand name, field, specialty, logo type, motif, typography, lettering feel, optional tagline, colors, style, audience, brand character, 2D/3D, background, usage, things to avoid - all translated |
| **Tap = what you get** | Every button carries its own value in the Telegram callback: pressing "Full premium 3D" stores 3D, pressing "Cafe" stores cafe, pressing "Other" opens the typed input - the wrong-selection bug (press 3D, get 2D) is gone |
| **Industry tree** | The field question (Food & Drink, Fashion & Beauty, Tech & Digital, Media & Creative, Education & Books, Sports & Fitness, Business & Services, Gaming & Esports) opens a second question listing exact specialties. **One theme per button**: Restaurant, Cafe, Fast food, Bakery... are separate choices with their own design language (30 specialties in total) |
| **"Other" = typed input** | Every "Other" button opens a free-text question where the user adds what he wants, in any language. This covers the field/specialty ("Other" field), logo type, symbol idea, colors, style, audience, brand character, background and usage |
| **Type anywhere** | On EVERY question the user can simply type instead of tapping: "3d" selects the 3D button, "قهوة" selects Cafe, "vêtements" selects Clothing brand; typing a specialty on the field question fills the whole subtree at once; anything unrecognized is kept as a personal description when the question has an Other escape |
| Smart skipping | "Symbol only" logo -> typography / lettering / tagline questions auto-skipped; a wordmark -> symbol-idea question auto-skipped; a tagline with "no text" is impossible |
| **Typed answers** | Understood in English, French, Arabic script, Darija and Arabizi: colors ("vert et blanc" = "أخضر وأبيض" = "akhdar w abyad"), activities ("بوت لتحميل الكتب" = library/bookstore), logo types ("un blason avec mes initiales" = emblem), styles ("vintage but clean" = vintage), backgrounds ("fond transparent" = isolated), usages ("business card" = print) |
| **Generate button** | Builds the final professional prompt: 12-part master structure, validated on the 100-point quality scale |
| **Deliverable** | DESIGN TYPE / DESIGN DIRECTION / IMAGE GENERATION PROMPT (copyable block - tap to copy) + quality score. The RESTRICTIONS guidelines are no longer displayed: the mandatory negative constraints live inside the prompt itself ("Strictly avoid: ...") |
| Smart defaults | "You decide" answers are resolved with industry-aware creative decisions (a tech startup defaults futuristic, a bakery defaults handcrafted, luxury lettering defaults serif, ...) |
| `/cancel` | Stop the questionnaire at any time |

Mandatory restrictions are ALWAYS applied inside the generated prompt,
on top of the user's choices: no humans, no faces, no animals, no
living creatures, no sexual content, no mockups - plus any extra
"avoid" items selected.

## Step 7: credits, referrals, community & donations

### Credits economy (SQLite, survives restarts - `store.py`)

| Rule | Value |
| --- | --- |
| New user welcome grant | **5 credits** at the very first `/start` |
| Daily refill | **+3 credits** restored automatically every day (UTC boundary, applied lazily on the user's first interaction of the day) |
| Referral bonus | **+2 credits** per friend who starts the bot through your personal link |
| Generation cost | **1 credit** per generated prompt |

The balance is checked **before the questionnaire starts** (better to
know before question 1) and again on **Generate**. A broke user gets a
friendly "not enough credits" message with the ways to earn more - and
a donate button. `/credits` shows the balance, the personal referral
link (`https://t.me/<bot>?start=ref<user_id>`) and the rules. The
referrer is notified (+2) the moment a friend joins; self-invites and
re-clicked links pay nothing; language choice now also survives
restarts.

### Commands

| Command | Behaviour |
| --- | --- |
| `/start` | Referral deep-link handling, subscribe gate, menu + live credits line |
| `/credits` | Balance, daily refill, referral link, earn rules |
| `/help` | Full guide: how it works, all commands, credits rules, support contact |
| `/lang` | View/set the language by command **and** quick buttons |
| `/support` | One tap to the developer: **@vxgix** (also a Support button in the menu) |
| `/donate` | The Stars donation choices directly |
| `/admin` | Owner-only dashboard (users, referrals, credits, donations) + credit grants in any syntax (`/admin add <user_id> <amount>`, `/admin <amount>` for yourself, brackets optional) + one-tap ＋10/＋50/＋100 self top-up buttons. Matched by numeric ID (`ADMIN_IDS`) or username = `SUPPORT_HANDLE` |
| `/addcredits` | Same grant grammar as `/admin`, without the dashboard (owner-only) |
| `/cancel` | Stop the questionnaire |

All commands also work **in the middle of the questionnaire** without
losing the answers, and the BotFather command menu is published
automatically at startup.

### Owner credit grants - any syntax works (hotfix 0.8.1)

`/admin` and the new `/addcredits` accept every natural way of typing
a grant - brackets, commas and the word `add` are all optional, and a
single number means "top myself up":

```
/admin add 8974969463 45    /admin 8974969463 45
/admin <8974969463><45>     /admin 8974969463, 45
/admin 45                   (credits for yourself)
/addcredits 45              /addcredits 8974969463 45
/admin 8974969463 -10       (negative amount = remove credits)
```

The dashboard also carries one-tap buttons **＋10 ⚡ me / ＋50 ⚡ me /
＋100 ⚡ me** for instant self top-ups, and every grant answers with a
target id + amount confirmation.

### Force-subscribe (t.me/gifthubai)

Before `/start`, before the questionnaire and before generating, the
bot checks the membership of the required channel and - if needed -
sends a "Join the channel" button plus an "I joined - check" button.
Membership verdicts are cached for 5 minutes; the check button always
forces a fresh check. **Important:** add the bot to the channel as an
**admin**, otherwise Telegram refuses the membership check - in that
case the gate fails OPEN (users are never locked out by a
misconfiguration) and the incident is logged. Set
`FORCE_SUBSCRIBE=0` in `.env` to disable the gate.

### Donations (Telegram Stars)

A white-heart button - **🤍 Support the bot** - sits right under the
generated prompt (and in the menu). Pressing it shows the amount
choices **⭐ 25 / 50 / 75 / 100 Stars**; choosing one opens a Telegram
Stars invoice (currency `XTR`, no provider token needed). The checkout
is approved automatically, the donor is thanked with a white heart,
and the total donated is accumulated per user (visible in `/admin`).

## Step 8: Social media posts (ads) mode + visibility

### Two creation modes in the menu

| Button | Flow |
| --- | --- |
| 🎨 **Logo prompt** | The original logo questionnaire (unchanged, ~16 steps) |
| 📢 **Social media post (ad)** | A full professional ads questionnaire (~19 steps in a typical path) |

"Create another one" under an output re-enters the SAME mode.

### The ads questionnaire (same professional standard as the logo)

- **Trees with one theme per button**: the SAME industry tree
  (Food & Drink → Restaurant / Cafe / ...), a **goal tree**
  (Sell & promote → Promote a product / Sale / New arrival / Flash sale,
  Grow my page → Giveaway / Contest / Followers / Engagement,
  Announce → Grand opening / Event / Rebranding / Info,
  Bring clients → Bookings / Orders / Visits / Downloads), and a
  **visual-scene tree** (Product showcase → Studio / Lifestyle /
  Close-up / Flat-lay, People & lifestyle → Model / Hands / Team /
  Crowd, Graphic → Typography poster / Illustration / Shapes / Pattern,
  Food → Dish / Drink / Ingredients)
- **Brand name AND @username of the brand/page** are asked and written
  into the prompt exactly as typed
- Platform (Instagram / Facebook / TikTok / Telegram / WhatsApp / Other)
  → format (square 1:1, story 9:16, portrait 4:5, banner 16:9, cover)
  with the right pixel sizes and safe zones
- Offer details, exact headline (case-sensitive, letter for letter),
  call-to-action button, language of the on-image text (EN / FR / AR /
  bilingual / no-text mode for Canva users), logo integration, style,
  colors, audience and things to avoid
- Every "Other" opens a typed input; typing is accepted everywhere
  ("giveaway" fills the goal subtree at once), understood in English,
  French, Arabic, Darija and Arabizi

### The ads deliverable

DESIGN TYPE / DESIGN DIRECTION / IMAGE GENERATION PROMPT (copyable
block, 100-point validated) + a **HOW TO USE IT** block that literally
tells the client:

1. tap the prompt block to copy it, paste it into the AI image model;
2. **have a logo? paste/attach your logo image together with the
   prompt (same message)** - the model integrates it;
3. the brand name and @username are already inside the prompt - no
   need to retype them;
4. if the rendered text is imperfect, add the exact words in Canva.

When the client answers "No logo yet", the bot adds a tip: create the
logo first with the 🎨 Logo mode of this bot - then redo the ad.

### @vxgix after every output + admin IDs

- Every generated output (logo AND ads) closes with
  **🤍 Made with 🤍 by TASMEEM AI - DM the maker: @vxgix** (link) and a
  Support button right next to the white-heart donate button
- `/admin` (owner dashboard) now unlocks by **numeric Telegram ID**
  (`ADMIN_IDS` in `.env`, default `8974969463`) in addition to the
  support-handle username

## Example output

```
DESIGN TYPE:
Combination mark

DESIGN DIRECTION:
Handcrafted combination mark for "Café El Baraka" - a cafe and
coffee-shop brand. Palette: pure black and gold. Built to stay crisp
from a small avatar to large print.

IMAGE GENERATION PROMPT:
Create a professional logo: a combination mark (a symbol paired with
the brand name) for the brand "Café El Baraka". Visual direction: an
organic handcrafted visual construction with a warm artisanal
character. ...
```

Every delivered prompt scores **100/100** on the internal quality gate
(brand understanding, concept clarity, composition, geometry, colors,
typography, requirement preservation, technical quality, negative
constraints). Anything below 90 also triggers a visible warning.

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
cd tasmeem-ai

# 1. Install dependencies (a virtual environment is recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure the token
cp .env.example .env
# then edit .env and paste your real token:
# BOT_TOKEN=123456789:YOUR_REAL_TOKEN

# 3. IMPORTANT for the force-subscribe gate:
#    add your bot to t.me/gifthubai as an ADMIN (see the section above)

# 4. (Optional) run the tests
python -m unittest discover -s tests -v

# 5. Start the bot
python bot.py
```

Then open your bot in Telegram and send `/start`.

## Project structure

```
tasmeem-ai/
├── bot.py                  # Entry point: two-mode questionnaire state machine + gates + credits + donations
├── config.py               # Loads BOT_TOKEN from .env + support, channel, credits, ADMIN_IDS
├── store.py                # SQLite persistence: credits, referrals, language, donations
├── user_settings.py        # Per-user interface language (memory + store persistence)
├── requirements.txt
├── .env.example            # Copy to .env: token + all settings (incl. ADMIN_IDS)
├── engine/
│   ├── __init__.py
│   ├── normalizer.py       # Cleaning, matchform, language detection
│   ├── questions.py        # LOGO questionnaire: industry tree + "Other" inputs + flow logic
│   ├── questions_ads.py    # ADS questionnaire: goal tree + visual tree + platform/format/CTA/logo (Step 8)
│   ├── modes.py            # Mode registry: walks either questionnaire, picks the builder (Step 8)
│   ├── i18n.py             # Translations EN / FR / AR (~360 keys each)
│   ├── knowledge.py        # Multilingual understanding + design language per specialty
│   ├── builder.py          # 12-part logo prompt builder + 100-point validator
│   └── builder_ads.py      # Ad-creative prompt builder + 100-point validator (Step 8)
├── data/                   # Created at runtime: tasmeem.db (SQLite store)
└── tests/
    ├── test_smoke.py       # Smoke tests + output format
    ├── test_normalizer.py  # Normalizer unit tests
    ├── test_questions.py   # Logo questionnaire tree + flow tests
    ├── test_i18n.py        # Parity tests (EN/FR/AR), both modes
    ├── test_knowledge.py   # Multilingual understanding tests
    ├── test_builder.py     # Logo builder + validator tests
    ├── test_callbacks.py   # Button value contract + reported bugs + typed answers
    ├── test_flow_sim.py    # End-to-end handler simulations (taps + typing)
    ├── test_store.py       # Credits economy: start grant, daily refill, referrals, donations
    ├── test_step7.py       # Gates, credits flow, referral link, Stars donations
    ├── test_step8.py       # Ads mode, trees, builder, support tag, admin IDs (Step 8)
    └── test_admin_grant.py # Owner grants: tolerant parsing, /addcredits, quick buttons
```

## Development roadmap

| Step | Content | Status |
| --- | --- | --- |
| 1 | Project skeleton: config, `/start` | Done |
| 2 | Text normalizer + language detector | Done |
| 3 | QCM questionnaire wizard (buttons + text inputs) | Done |
| 4 | Multilingual interface (EN / FR / AR) | Done |
| 5 | Knowledge base + prompt builder (12-part structure) + validator | Done |
| 6 | Professional edition: industry tree (one theme per button), "Other" = typed input, wider brief (motif / audience / personality / lettering / tagline), no RESTRICTIONS block in the output, hardening + final tests | Done |
| 6.1 | Hotfix: value-based callback_data (tap = what you get, Other really opens the typed input), typed answers accepted on every question, custom audience support, 215 tests green | Done |
| 7 | **Credits economy (5 start / +3 daily / +2 per referral / 1 per prompt, SQLite persistence), referral deep links, force-subscribe t.me/gifthubai, support @vxgix, /credits /help /support /donate /admin commands, white-heart donation button with 25/50/75/100 Stars invoices, 254 tests green** | Done |
| 8 | **Second mode "Social media post (ads)": goal tree + visual-scene tree + platform/format + CTA + text language + logo question, brand name & @username, HOW TO USE IT block (paste your logo with the prompt), @vxgix after every output, /admin by numeric ID (8974969463), 286 tests green** | Done |
| 8.1 | **Hotfix: owner credit grants in any syntax (`/admin <8974969463><45>`, `/admin 45` = self, negative = remove), new `/addcredits` command, one-tap ＋10/＋50/＋100 self top-up buttons on the dashboard, 305 tests green** | Done |

## Security notes

- Never share your `.env` file or your bot token with anyone.
- `.env` is listed in `.gitignore` so it will not be committed by accident.
