"""Rule-based prompt engine for the TASMEEM AI bot.

Modules (no AI, pure Python):
- normalizer.py    - text cleaning + language detection
                     used for typed answers in the questionnaire
- questions.py     - the LOGO questionnaire: industry tree (one theme
                     per button), "Other" typed inputs, flow + summary
- questions_ads.py - the SOCIAL MEDIA POST (ads) questionnaire: goal
                     tree, visual-scene tree, platform -> format, CTA,
                     text language, logo question (Step 8)
- modes.py         - the registry that walks either questionnaire and
                     selects the matching builder (Step 8)
- i18n.py          - interface translations EN / FR / AR
- knowledge.py     - multilingual understanding (colors, activities,
                     categories, styles, usages) + design language per
                     specialty
- builder.py       - 12-part LOGO prompt assembly + 100-point validator
- builder_ads.py   - ad-creative prompt assembly + 100-point validator
                     + how-to-use data (paste the logo with the prompt)
"""