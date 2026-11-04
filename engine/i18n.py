"""Internationalization for TASMEEM AI (Step 6).

All user-facing strings live here in three languages:
    en - English
    fr - Francais
    ar - Arabic (simple MSA, Algerian-friendly)

Key conventions:
- menu_*, lang_*, btn_*, summary_* ... general interface strings
- q_<question_id>       : prompt of one question
- opt_<question_id>_<option_value> : label of one option
- sum_<question_id>     : display name of one answer in the summary

The parity test (tests/test_i18n.py) guarantees that every key exists in
every language and that all question/option keys match the questionnaire
definition in engine/questions.py.

The final image-generation PROMPT is always built in English (master
skill, section 12) - this file only translates the conversation.
"""

from __future__ import annotations

from typing import Dict, Optional

LANGS = ("en", "fr", "ar")
DEFAULT_LANG = "en"

LANGUAGE_NATIVE = {
    "en": "English",
    "fr": "Français",
    "ar": "العربية",
}

STRINGS: Dict[str, Dict[str, str]] = {
    # ------------------------------------------------------------------
    # ENGLISH
    # ------------------------------------------------------------------
    "en": {
        "menu_text": (
            "Welcome to <b>TASMEEM AI</b>.\n\n"
            "Choose a creation mode - I ask you quick questions (buttons or "
            "typing, in your language) and I build a professional, "
            "ready-to-use prompt from your answers:\n\n"
            "🎨 <b>Logo</b> - a professional logo-generation prompt\n"
            "📢 <b>Social media post (ad)</b> - a professional ad-creative "
            "prompt for your product, service or page\n\n"
            "<b>Commands:</b>\n"
            "/credits - your credits and referral link\n"
            "/lang - change the interface language\n"
            "/help - how to use the bot\n"
            "/donate - support the bot\n"
            "/cancel - stop the questionnaire at any time\n\n"
            "I return professional text prompts, never images."
        ),
        "menu_button": "Create my logo prompt",
        "lang_set": "Language set to: <b>{label}</b>",
        "lang_usage": (
            "<b>Interface language</b>\n"
            "Current language: {current}\n\n"
            "<b>Usage:</b>\n"
            "<code>/lang en</code> - English\n"
            "<code>/lang fr</code> - Français\n"
            "<code>/lang ar</code> - العربية"
        ),
        "lang_unknown": "Unknown language. Available: en, fr, ar.",
        "cancel_text": "Questionnaire cancelled. Send /start when you want to create a logo prompt.",
        "outside_text": "Send /start to create your logo prompt.",
        "need_input_text": (
            "Please answer the current question - tap a button or type text - "
            "or send /cancel to stop."
        ),
        "invalid_text": (
            "That answer is empty or too long (max {max_len} characters). "
            "Please try again."
        ),
        "stale_question": "That question was already answered. Here is the current one:",
        "custom_noted": (
            "Noted - I will use your description: “{text}”\n\n"
            "Next question:"
        ),
        "type_instead_hint": (
            "I did not recognize that. Tap one of the buttons - and if "
            "nothing fits, describe it in a few words."
        ),
        "summary_note": (
            "Questionnaire complete - here is what I collected:\n\n"
            "{summary}"
        ),
        "prompt_intro": (
            "Here is your professional logo prompt.\n"
            "Tap the prompt block to copy it, then paste it into your "
            "favorite image generator."
        ),
        "prompt_score": "Prompt quality score: {score}/100",
        "prompt_warning": (
            "The prompt scored below the quality threshold - press Restart "
            "to refine your answers and try again."
        ),
        "btn_generate": "Generate the prompt",
        "btn_restart": "Restart",
        "btn_new": "Create another one",
        "btn_done": "Done",
        "summary_avoid": "Avoid",
        "summary_empty": "- (no answers yet)",

        # -- questions -----------------------------------------------------
        "q_brand_name": (
            "What is the exact brand name?\n\n"
            "Type it now - it will be kept exactly as you write it, "
            "including capitalization, spaces and punctuation, because the "
            "prompt reproduces it letter for letter. Or press the button "
            "below if the logo should carry no name at all."
        ),
        "opt_brand_name_skip": "Skip - no name",
        "q_industry": (
            "What field is your brand in?\n\n"
            "Pick the closest field first - I will then ask for your exact "
            "specialty, because a cafe and a restaurant do not get the same "
            "design language. If nothing fits, choose Other and describe it."
        ),
        "opt_industry_food": "Food & Drink",
        "opt_industry_fashion": "Fashion & Beauty",
        "opt_industry_tech": "Tech & Digital",
        "opt_industry_media": "Media & Creative",
        "opt_industry_education": "Education & Books",
        "opt_industry_sports": "Sports & Fitness",
        "opt_industry_services": "Business & Services",
        "opt_industry_gaming": "Gaming & Esports",
        "opt_industry_other": "Other (I will describe it)",
        "q_industry_food": (
            "Food & Drink - what is your exact specialty?\n\n"
            "Each choice has its own design codes: a cafe feels cozy and "
            "warm, fast food feels bold and fast, a bakery feels homemade. "
            "Pick the one that matches your business."
        ),
        "opt_industry_food_restaurant": "Restaurant",
        "opt_industry_food_cafe": "Cafe (coffee)",
        "opt_industry_food_fastfood": "Fast food",
        "opt_industry_food_bakery": "Bakery & pastry",
        "opt_industry_food_juice": "Juice & cold drinks",
        "opt_industry_food_other": "Other (I will describe it)",
        "q_industry_fashion": (
            "Fashion & Beauty - what is your exact specialty?\n\n"
            "A clothing brand, a barbershop and a jewelry house do not "
            "speak the same visual language. Pick yours."
        ),
        "opt_industry_fashion_clothing": "Clothing brand",
        "opt_industry_fashion_beauty": "Beauty & cosmetics",
        "opt_industry_fashion_barber": "Barber & hair salon",
        "opt_industry_fashion_perfume": "Perfume & fragrance",
        "opt_industry_fashion_jewelry": "Jewelry & accessories",
        "opt_industry_fashion_other": "Other (I will describe it)",
        "q_industry_tech": (
            "Tech & Digital - what is your exact specialty?\n\n"
            "A startup, an app developer and a cybersecurity firm each "
            "carry a different attitude. Pick yours."
        ),
        "opt_industry_tech_startup": "AI & tech startup",
        "opt_industry_tech_dev": "App & software development",
        "opt_industry_tech_web": "Web agency & digital services",
        "opt_industry_tech_cyber": "IT & cybersecurity",
        "opt_industry_tech_other": "Other (I will describe it)",
        "q_industry_media": (
            "Media & Creative - what is your exact specialty?\n\n"
            "Photography, video, graphic design and social media each have "
            "their own icon vocabulary. Pick yours."
        ),
        "opt_industry_media_photo": "Photography",
        "opt_industry_media_video": "Video & filming",
        "opt_industry_media_design": "Graphic design",
        "opt_industry_media_marketing": "Marketing & social media",
        "opt_industry_media_other": "Other (I will describe it)",
        "q_industry_education": (
            "Education & Books - what is your exact specialty?\n\n"
            "A school, a bookstore and a training center do not attract "
            "the same audience. Pick yours."
        ),
        "opt_industry_education_school": "School & tutoring",
        "opt_industry_education_library": "Library & bookstore",
        "opt_industry_education_training": "Courses & training",
        "opt_industry_education_other": "Other (I will describe it)",
        "q_industry_sports": (
            "Sports & Fitness - what is your exact specialty?\n\n"
            "A gym, a sports club and a personal coach build very different "
            "identities. Pick yours."
        ),
        "opt_industry_sports_gym": "Gym & fitness",
        "opt_industry_sports_club": "Sports club & team",
        "opt_industry_sports_coach": "Personal coach",
        "opt_industry_sports_other": "Other (I will describe it)",
        "q_industry_services": (
            "Business & Services - what is your exact specialty?\n\n"
            "Delivery, real estate, construction and shops each rely on "
            "their own symbols. Pick yours."
        ),
        "opt_industry_services_delivery": "Delivery & transport",
        "opt_industry_services_realestate": "Real estate",
        "opt_industry_services_construction": "Construction & BTP",
        "opt_industry_services_shop": "Shop & e-commerce",
        "opt_industry_services_other": "Other (I will describe it)",
        "q_industry_gaming": (
            "Gaming & Esports - what is your exact specialty?\n\n"
            "An esports team needs an aggressive crest, a game studio "
            "needs a playful universe. Pick yours."
        ),
        "opt_industry_gaming_team": "Gaming brand & esports team",
        "opt_industry_gaming_studio": "Game studio & developer",
        "opt_industry_gaming_other": "Other (I will describe it)",
        "q_industry_text": (
            "Describe your activity in a few words - add everything you "
            "want me to know.\n\n"
            "Any language works: English, French, Arabic, Darija or "
            "Arabizi (example: 'bot for downloading books', 'بوت لتحميل "
            "الكتب', 'livraison de poulet grillé')."
        ),
        "q_category": (
            "What type of logo do you want?\n\n"
            "Symbol = an icon alone. Lettermark = stylized initials. "
            "Wordmark = the name set as the logo. Combination = icon + "
            "name. Emblem = the name inside a badge. If you have something "
            "else in mind, choose Other and describe it."
        ),
        "opt_category_symbol": "Symbol only (icon)",
        "opt_category_lettermark": "Letters / initials (lettermark)",
        "opt_category_wordmark": "Brand name as text (wordmark)",
        "opt_category_combination": "Symbol + name (combination)",
        "opt_category_abstract": "Abstract shape",
        "opt_category_emblem": "Badge / emblem",
        "opt_category_auto": "You decide for me",
        "opt_category_other": "Other (I will describe it)",
        "q_category_text": (
            "Describe the logo type you want in your own words - add "
            "everything you want.\n\n"
            "Example: 'a shield with my initials inside'."
        ),
        "q_motif": (
            "What should the symbol evoke?\n\n"
            "This is the heart of the concept: the main idea the icon is "
            "built from. Pick a direction, or let me choose creatively "
            "from your field."
        ),
        "opt_motif_object": "An object from my activity",
        "opt_motif_letter": "My initial letter (as a shape)",
        "opt_motif_geometric": "Pure geometric shapes",
        "opt_motif_nature": "Nature (leaf, mountain, wave...)",
        "opt_motif_premium": "Premium symbol (crown, star...)",
        "opt_motif_auto": "You decide",
        "opt_motif_other": "Other (I will describe it)",
        "q_motif_text": (
            "Describe what the symbol should evoke - add everything you "
            "want.\n\n"
            "Example: 'a lion merged with a coffee cup, without drawing a "
            "real animal'."
        ),
        "q_typography": (
            "Should the logo include any text?\n\n"
            "Name = the full brand name. Initials = a monogram. Name under "
            "the symbol = the classic combination lockup."
        ),
        "opt_typography_none": "No text at all",
        "opt_typography_name": "The brand name",
        "opt_typography_initials": "Initials only",
        "opt_typography_name_under": "Name under the symbol",
        "opt_typography_auto": "You decide",
        "q_font_style": (
            "What feel should the lettering have?\n\n"
            "The lettering carries the brand character: sharp and modern, "
            "classic and serif, rounded and friendly, or handwritten."
        ),
        "opt_font_style_modern_sans": "Modern & clean",
        "opt_font_style_classic_serif": "Classic serif",
        "opt_font_style_rounded": "Rounded & friendly",
        "opt_font_style_script": "Script / handwritten",
        "opt_font_style_geometric": "Geometric & minimal",
        "opt_font_style_auto": "You decide",
        "q_tagline": (
            "Add a short slogan under the name?\n\n"
            "Type your exact tagline (up to 60 characters) and it will be "
            "rendered in small letters under the brand name - spelled "
            "exactly as you write it. Or press the button for a logo "
            "without any slogan."
        ),
        "opt_tagline_skip": "Skip - no slogan",
        "q_colors": (
            "Which color palette do you prefer?\n\n"
            "Colors decide how the logo feels: blue reassures, gold "
            "signals luxury, red stimulates appetite. A professional logo "
            "stays between 1 and 3 colors."
        ),
        "opt_colors_blue_white": "Blue & white",
        "opt_colors_green_white": "Green & white",
        "opt_colors_black_gold": "Black & gold",
        "opt_colors_red_white": "Red & white",
        "opt_colors_dark_premium": "Dark & premium",
        "opt_colors_soft_pastel": "Soft pastels",
        "opt_colors_bold_vivid": "Bold & vivid",
        "opt_colors_surprise": "Surprise me",
        "opt_colors_other": "Other (I will type them)",
        "q_colors_text": (
            "Type the colors you want - add everything you want.\n\n"
            "Any language is fine, for example: 'green and white', "
            "'vert et or', 'أخضر وأبيض', 'akhdar w abyad'."
        ),
        "q_style": (
            "Which visual style fits your brand best?\n\n"
            "Think of it as the design era: minimalist is timeless, "
            "futuristic is high-tech, vintage feels heritage, handcrafted "
            "feels warm and artisanal."
        ),
        "opt_style_minimalist": "Minimalist",
        "opt_style_maximalist": "Maximalist (rich, detailed)",
        "opt_style_modern": "Modern",
        "opt_style_luxury": "Luxury / premium",
        "opt_style_futuristic": "Futuristic",
        "opt_style_vintage": "Vintage / retro",
        "opt_style_handcrafted": "Handcrafted / organic",
        "opt_style_auto": "You decide",
        "opt_style_other": "Other (I will describe it)",
        "q_style_text": (
            "Describe the style you want - add everything you want.\n\n"
            "Example: 'like an old pharmacy sign, but cleaner'."
        ),
        "q_audience": (
            "Who is your main audience?\n\n"
            "The same brand does not speak the same way to teenagers, "
            "families or companies - the design adapts to them. If your "
            "audience is something else, choose Other and describe it."
        ),
        "opt_audience_young": "Young & trendy",
        "opt_audience_family": "Families",
        "opt_audience_business": "Companies & professionals",
        "opt_audience_premium": "High-end clients",
        "opt_audience_local": "Local community",
        "opt_audience_broad": "A bit of everything",
        "opt_audience_auto": "You decide",
        "opt_audience_other": "Other (I will describe it)",
        "q_audience_text": (
            "Describe your audience in your own words - add everything "
            "you want.\n\n"
            "Example: 'university students', 'des etudiants', "
            "'طلاب الجامعة'."
        ),
        "q_personality": (
            "If your brand were a person, what character would it have?\n\n"
            "This sets the attitude of every curve and line in the logo."
        ),
        "opt_personality_bold": "Bold & powerful",
        "opt_personality_calm": "Calm & trustworthy",
        "opt_personality_playful": "Playful & friendly",
        "opt_personality_elegant": "Elegant & refined",
        "opt_personality_innovative": "Innovative & modern",
        "opt_personality_auto": "You decide",
        "opt_personality_other": "Other (I will describe it)",
        "q_personality_text": (
            "Describe your brand character in your own words - add "
            "everything you want.\n\n"
            "Example: 'serious at work, but with a small wink'."
        ),
        "q_dimension": (
            "Flat or dimensional rendering?\n\n"
            "Flat vector is the timeless standard for logos; 3D renders "
            "look premium but age faster. When in doubt, stay flat or "
            "slightly 3D."
        ),
        "opt_dimension_flat": "Flat vector (2D)",
        "opt_dimension_slight_3d": "Slightly 3D",
        "opt_dimension_full_3d": "Full premium 3D",
        "opt_dimension_auto": "You decide",
        "q_background": (
            "Which background do you prefer?\n\n"
            "Pure white is the safest for generators; dark backgrounds "
            "make gold and neon pop; isolated means no visible background "
            "at all (transparent-ready)."
        ),
        "opt_background_white": "Pure white",
        "opt_background_dark": "Dark",
        "opt_background_isolated": "Isolated (no visible background)",
        "opt_background_auto": "You decide",
        "opt_background_other": "Other (I will describe it)",
        "q_background_text": (
            "Describe the background you want - add everything you "
            "want.\n\n"
            "Example: 'deep green background' or 'fond bleu nuit'."
        ),
        "q_usage": (
            "Where will the logo be used most?\n\n"
            "This guides composition, proportions and safe margins: a "
            "Telegram avatar must stay readable at tiny sizes, while a "
            "website header can breathe horizontally."
        ),
        "opt_usage_telegram_avatar": "Telegram avatar (square)",
        "opt_usage_website": "Website header",
        "opt_usage_social": "Social media posts",
        "opt_usage_print": "Print / packaging",
        "opt_usage_everywhere": "Everywhere",
        "opt_usage_other": "Other (I will describe it)",
        "q_usage_text": (
            "Where will the logo be used? Describe it - add everything "
            "you want.\n\n"
            "Example: 'on my delivery trucks and the storefront'."
        ),
        "q_exclusions": (
            "Anything to avoid?\n\n"
            "Tap an item to toggle it, then press Done. Mandatory "
            "restrictions (no humans, no animals, no faces) are always "
            "applied automatically, whether you select things here or not."
        ),
        "opt_exclusions_neon": "Neon effects",
        "opt_exclusions_gradients": "Gradients",
        "opt_exclusions_shadows": "Shadows",
        "opt_exclusions_decorations": "Extra decorations",
        "opt_exclusions_complex": "Complex details",

        # -- summary labels --------------------------------------------------
        "sum_brand_name": "Brand name",
        "sum_industry": "Field",
        "sum_industry_leaf": "Specialty",
        "sum_industry_text": "Activity",
        "sum_category": "Logo type",
        "sum_category_text": "Type (your words)",
        "sum_motif": "Symbol idea",
        "sum_motif_text": "Symbol idea (your words)",
        "sum_typography": "Typography",
        "sum_font_style": "Lettering feel",
        "sum_tagline": "Slogan",
        "sum_colors": "Colors",
        "sum_colors_text": "Colors (typed)",
        "sum_style": "Style",
        "sum_style_text": "Style (your words)",
        "sum_audience": "Audience",
        "sum_audience_text": "Audience (your words)",
        "sum_personality": "Character",
        "sum_personality_text": "Character (your words)",
        "sum_dimension": "Rendering",
        "sum_background": "Background",
        "sum_background_text": "Background (your words)",
        "sum_usage": "Used on",
        "sum_usage_text": "Usage (your words)",

        # -- Step 7: help, support, credits, referral, force-sub, donations --
        "help_text": (
            "<b>TASMEEM AI - help</b>\n\n"
            "I turn your answers into a professional, ready-to-use prompt:\n"
            "🎨 a <b>LOGO</b> prompt for image generation\n"
            "📢 a <b>SOCIAL MEDIA POST (ad)</b> prompt for your product, "
            "service or page\n\n"
            "<b>How it works</b>\n"
            "1. Send /start and choose a mode (logo or ad)\n"
            "2. Answer the quick questions - buttons or typing, in your language\n"
            "3. Copy the generated prompt into your favorite image generator\n"
            "4. If you have a logo, paste your logo image together with the "
            "prompt\n\n"
            "<b>Commands</b>\n"
            "/start - open the menu\n"
            "/credits - your credits + referral link\n"
            "/lang - change the interface language\n"
            "/donate - support the bot with Stars\n"
            "/support - contact support\n"
            "/cancel - stop the questionnaire\n\n"
            "<b>Credits</b>\n"
            "1 prompt = 1 credit. +{refill} free credits are added every day, "
            "and you earn +{bonus} credits for every friend who starts the bot "
            "with your personal link.\n\n"
            "Support: {support}"
        ),
        "support_text": (
            "Need a human? Contact the developer - he answers as fast as "
            "possible:\n{support}"
        ),
        "menu_credits": "💳 Credits: <b>{credits}</b> (+{refill} free every day)",
        "credits_text": (
            "💳 <b>Your credits: {credits}</b>\n\n"
            "✨ +{refill} free credits are added automatically every day.\n"
            "🎁 Invite friends: +{bonus} credits for each friend who starts "
            "the bot with your personal link:\n{link}\n\n"
            "⚙️ 1 generated prompt = 1 credit."
        ),
        "not_enough": (
            "😢 Not enough credits.\n\n"
            "A generated prompt costs {cost} credit and your balance is "
            "{credits}.\n\n"
            "✨ +{refill} free credits are added every day.\n"
            "🎁 Invite friends: +{bonus} credits each.\n"
            "🤍 Or support the bot with a donation below."
        ),
        "ref_bonus_notify": (
            "🎁 <b>+{bonus} credits!</b>\n"
            "A friend just started TASMEEM AI with your link."
        ),
        "fs_required": (
            "🔒 <b>One quick step before we start</b>\n\n"
            "TASMEEM AI is free - the only thing we ask is to join our "
            "channel. Updates, tips and free drops are posted there.\n\n"
            "Join here: {channel_link}\n\n"
            "Already joined? Press the button below."
        ),
        "fs_still": (
            "You still need to join the channel first. "
            "Press Join, then check again."
        ),
        "btn_join": "📢 Join the channel",
        "btn_check": "✅ I joined - check",
        "btn_donate": "🤍 Support the bot",
        "btn_support": "🆘 Support",
        "donate_intro": (
            "🤍 <b>Support TASMEEM AI</b>\n\n"
            "The bot is free and stays free. If it helps you, a small "
            "donation in Telegram Stars keeps it running and improving.\n\n"
            "Choose an amount:"
        ),
        "donate_desc": "Donation to support TASMEEM AI",
        "donate_thanks": (
            "🤍 <b>Thank you for your {stars}-Stars donation!</b>\n"
            "Your support keeps TASMEEM AI free and improving."
        ),
        "out_credits": "💳 Credits left: <b>{credits}</b> (+{refill} free tomorrow)",
        # -- Step 8: ads mode, support tag, admin (appended) -----
        "btn_mode_logo": '🎨 Logo prompt',
        "btn_mode_ads": '📢 Social media post (ad)',
        "prompt_intro_ads": 'Here is your professional ad-creative prompt.\nTap the prompt block to copy it, then paste it into your favorite image generator - together with your logo if you have one.',
        "ads_howto": '📋 <b>How to use it:</b>\n1. Tap the prompt block above to copy it, then paste it into your AI image model.\n2. Have a logo? <b>Paste/attach your logo image together with the prompt</b> (same message) - the model will integrate it.\n3. Your brand name and @username are already written inside the prompt - no need to retype them.\n4. If the rendered text is not perfect, generate the visual and add your exact words in Canva or similar.',
        "ads_howto_nologo": '💡 Tip: you have no logo yet - create it first with the 🎨 Logo mode of this bot, then redo your ad.',
        "out_support": '<b>Made with 🤍 by TASMEEM AI</b> - for anything custom or any help, DM the maker: {support}',
        "sum_ad_leaf": 'Details',
        "q_ad_brand_name": 'What is the exact brand or page name for this post?\n\nType it now - it will be kept exactly as you write it (capitalization, spaces, punctuation) and written into the prompt letter for letter. Or press the button if the visual should carry no name.',
        "opt_ad_brand_name_skip": 'Skip - no name',
        "q_ad_username": 'What is the @username of your brand or page?\n\nExample: @mybrand - it goes into the prompt so the AI model can place it on the visual (or you can paste it together with the prompt). No username? Press the button.',
        "opt_ad_username_skip": 'Skip - no username',
        "q_ad_goal": 'What is this post for?\n\nThe goal decides the whole composition: a flash sale needs urgency and a big price zone, a giveaway needs excitement, an announcement needs clarity. Pick the closest goal - I will then ask for the exact type.',
        "opt_ad_goal_sales": 'Sell & promote',
        "opt_ad_goal_growth": 'Grow my page',
        "opt_ad_goal_announce": 'Announce something',
        "opt_ad_goal_traffic": 'Bring clients & orders',
        "opt_ad_goal_other": 'Other (I will describe it)',
        "q_ad_goal_sales": 'Sell & promote - what exactly is the goal?',
        "opt_ad_goal_sales_product": 'Promote a product',
        "opt_ad_goal_sales_discount": 'Sale / discount / promo code',
        "opt_ad_goal_sales_new": 'New arrival / launch',
        "opt_ad_goal_sales_flash": 'Flash sale / limited offer',
        "opt_ad_goal_sales_other": 'Other (I will describe it)',
        "q_ad_goal_growth": 'Grow my page - what exactly is the goal?',
        "opt_ad_goal_growth_giveaway": 'Giveaway',
        "opt_ad_goal_growth_contest": 'Contest / challenge',
        "opt_ad_goal_growth_follow": 'Get more followers',
        "opt_ad_goal_growth_engage": 'Engagement post (question / poll)',
        "opt_ad_goal_growth_other": 'Other (I will describe it)',
        "q_ad_goal_announce": 'Announce something - what exactly is the goal?',
        "opt_ad_goal_announce_opening": 'Grand opening',
        "opt_ad_goal_announce_event": 'Event / invitation',
        "opt_ad_goal_announce_rebrand": 'Rebranding / new look',
        "opt_ad_goal_announce_info": 'General announcement',
        "opt_ad_goal_announce_other": 'Other (I will describe it)',
        "q_ad_goal_traffic": 'Bring clients & orders - what exactly is the goal?',
        "opt_ad_goal_traffic_booking": 'Bookings / appointments',
        "opt_ad_goal_traffic_order": 'Direct orders / menu',
        "opt_ad_goal_traffic_visit": 'Store / website visits',
        "opt_ad_goal_traffic_download": 'App / bot downloads',
        "opt_ad_goal_traffic_other": 'Other (I will describe it)',
        "q_ad_goal_text": "Describe the goal of the post in your own words - add everything you want.\n\nExample: 'summer sale -30% on the whole shop', 'تخفيضات الصيف', 'SOLDES D'ÉTÉ'.",
        "q_ad_platform": 'Where will this post be published?\n\nEach platform has its own codes: Instagram loves clean aesthetics, TikTok needs bold contrast, a Telegram post stays readable on small screens. Nothing fits? Choose Other.',
        "opt_ad_platform_instagram": 'Instagram',
        "opt_ad_platform_facebook": 'Facebook',
        "opt_ad_platform_tiktok": 'TikTok',
        "opt_ad_platform_telegram": 'Telegram',
        "opt_ad_platform_whatsapp": 'WhatsApp status',
        "opt_ad_platform_other": 'Other (I will describe it)',
        "q_ad_platform_text": "Which platform or place is it? Describe it - add everything you want.\n\nExample: 'Snapchat', 'LinkedIn page', 'printed flyer'.",
        "q_ad_format": 'Which format do you need?\n\nSquare is the classic feed post, 9:16 fills stories and reels full-screen, 4:5 takes more room in the feed, 16:9 works as a wide banner or a page cover.',
        "opt_ad_format_square": 'Square post (1:1)',
        "opt_ad_format_story": 'Story / Reels (9:16)',
        "opt_ad_format_portrait": 'Portrait post (4:5)',
        "opt_ad_format_banner": 'Wide banner (16:9)',
        "opt_ad_format_cover": 'Page cover',
        "opt_ad_format_auto": 'You decide',
        "opt_ad_format_other": 'Other (I will describe it)',
        "q_ad_format_text": "Describe the format you want - add everything you want.\n\nExample: 'two story frames', 'banner for my YouTube channel'.",
        "q_ad_offer": "What exactly are you promoting?\n\nDescribe the product, service, price, discount, date or place - everything the visual must show truthfully (example: 'pizza medium 2000 DA, free delivery'). Or press the button if you prefer to keep it general.",
        "opt_ad_offer_skip": 'Skip - no details',
        "q_ad_cta": 'Which call-to-action should appear on the visual?\n\nThe CTA is the small button or banner that tells people what to do next: buy, book, write, follow...',
        "opt_ad_cta_shop_now": 'Shop now',
        "opt_ad_cta_order_now": 'Order now',
        "opt_ad_cta_book_now": 'Book now',
        "opt_ad_cta_learn_more": 'Learn more',
        "opt_ad_cta_dm": 'Send us a message',
        "opt_ad_cta_call": 'Call now',
        "opt_ad_cta_whatsapp": 'WhatsApp us',
        "opt_ad_cta_follow": 'Follow us',
        "opt_ad_cta_visit": 'Visit us',
        "opt_ad_cta_auto": 'You decide',
        "opt_ad_cta_other": 'Other (I will describe it)',
        "q_ad_cta_text": "Type the exact call-to-action text - add everything you want.\n\nExample: 'Book your seat', 'Commandez ici', 'احجز مقعدك'.",
        "q_ad_lang_text": "Which language for the text ON the visual?\n\nThe AI model must render the exact words: choosing the language avoids mixed alphabets. 'No text' gives you a clean visual and you add the words yourself in Canva or similar.",
        "opt_ad_lang_text_en": 'English',
        "opt_ad_lang_text_fr": 'French',
        "opt_ad_lang_text_ar": 'Arabic',
        "opt_ad_lang_text_ar_en": 'Arabic + English',
        "opt_ad_lang_text_fr_en": 'French + English',
        "opt_ad_lang_text_none": 'No text on the visual',
        "opt_ad_lang_text_other": 'Other (I will describe it)',
        "q_ad_lang_text_text": "Which language(s) for the text on the visual? Describe it - add everything you want.\n\nExample: 'arabic dialect with a small english price tag'.",
        "q_ad_headline": 'What is the exact headline text to write on the visual?\n\nType it exactly as it must appear (up to 80 characters) - spelling, capitalization and punctuation are kept letter for letter. Or press the button and I choose a short punchy line for you.',
        "opt_ad_headline_skip": 'You decide for me',
        "q_ad_visual": 'What should the visual show?\n\nThis is the heart of the ad: a product alone, people using it, a graphic poster or an appetizing food shot. Pick a family first - I will then ask for the exact scene.',
        "opt_ad_visual_product": 'Product showcase',
        "opt_ad_visual_people": 'People & lifestyle',
        "opt_ad_visual_graphic": 'Graphic & typography',
        "opt_ad_visual_food": 'Food & drink shots',
        "opt_ad_visual_auto": 'You decide',
        "opt_ad_visual_other": 'Other (I will describe it)',
        "q_ad_visual_product": 'Product showcase - which scene fits best?',
        "opt_ad_visual_product_studio": 'Clean studio shot',
        "opt_ad_visual_product_lifestyle": 'Lifestyle scene (in real use)',
        "opt_ad_visual_product_detail": 'Close-up on the details',
        "opt_ad_visual_product_flatlay": 'Flat-lay top view',
        "opt_ad_visual_product_other": 'Other (I will describe it)',
        "q_ad_visual_people": 'People & lifestyle - which scene fits best?',
        "opt_ad_visual_people_model": 'A model presenting it',
        "opt_ad_visual_people_hands": 'Hands holding the product',
        "opt_ad_visual_people_team": 'The team / staff',
        "opt_ad_visual_people_crowd": 'An event crowd',
        "opt_ad_visual_people_other": 'Other (I will describe it)',
        "q_ad_visual_graphic": 'Graphic & typography - which scene fits best?',
        "opt_ad_visual_graphic_typographic": 'Bold typography poster',
        "opt_ad_visual_graphic_illustration": 'Custom illustration',
        "opt_ad_visual_graphic_shapes": 'Abstract shapes & gradients',
        "opt_ad_visual_graphic_pattern": 'Branded pattern',
        "opt_ad_visual_graphic_other": 'Other (I will describe it)',
        "q_ad_visual_food": 'Food & drink shots - which scene fits best?',
        "opt_ad_visual_food_dish": 'Plated dish',
        "opt_ad_visual_food_drink": 'Drink / beverage shot',
        "opt_ad_visual_food_ingredients": 'Fresh ingredients',
        "opt_ad_visual_food_other": 'Other (I will describe it)',
        "q_ad_visual_text": "Describe what the visual should show - add everything you want.\n\nExample: 'my blue sneaker floating with paint splashes', 'صحن كسكس مع الخضرة', 'une boîte de chocolats ouverte'.",
        "q_ad_logo": 'Do you have a logo to place on the visual?\n\nIf yes, at the end I will tell you to PASTE YOUR LOGO IMAGE together with the prompt into the AI model - that is how it gets integrated. If you have no logo yet, you can create it with the Logo mode of this bot first.',
        "opt_ad_logo_yes": "Yes - I'll attach it",
        "opt_ad_logo_no": 'No logo yet',
        "opt_ad_logo_name_only": 'Use the name as the mark',
        "opt_ad_logo_auto": 'You decide',
        # -- Step 8: summary display names -------------------------------
        "sum_ad_brand_name": 'Brand / page name',
        "sum_ad_username": 'Page username',
        "sum_ad_goal": 'Post goal',
        "sum_ad_goal_text": 'Goal (your words)',
        "sum_ad_platform": 'Platform',
        "sum_ad_platform_text": 'Platform (your words)',
        "sum_ad_format": 'Format',
        "sum_ad_format_text": 'Format (your words)',
        "sum_ad_offer": 'Offer',
        "sum_ad_cta": 'Call-to-action',
        "sum_ad_cta_text": 'CTA (your words)',
        "sum_ad_lang_text": 'Text language',
        "sum_ad_lang_text_text": 'Text language (your words)',
        "sum_ad_headline": 'Headline',
        "sum_ad_visual": 'Visual scene',
        "sum_ad_visual_text": 'Visual (your words)',
        "sum_ad_logo": 'Logo',
    },
    # ------------------------------------------------------------------
    # FRANCAIS
    # ------------------------------------------------------------------
    "fr": {
        "menu_text": (
            "Bienvenue sur <b>TASMEEM AI</b>.\n\n"
            "Choisis un mode de création - je te pose des questions rapides "
            "(boutons ou texte, dans ta langue) et je construis un prompt "
            "professionnel prêt à l'emploi à partir de tes réponses :\n\n"
            "🎨 <b>Logo</b> - un prompt professionnel de génération de logo\n"
            "📢 <b>Post réseaux sociaux (pub)</b> - un prompt publicitaire "
            "pro pour ton produit, ton service ou ta page\n\n"
            "<b>Commandes :</b>\n"
            "/credits - tes crédits et ton lien de parrainage\n"
            "/lang - changer la langue de l'interface\n"
            "/help - mode d'emploi du bot\n"
            "/donate - soutenir le bot\n"
            "/cancel - arrêter le questionnaire à tout moment\n\n"
            "Je renvoie des prompts texte professionnels, jamais des images."
        ),
        "menu_button": "Créer mon prompt de logo",
        "lang_set": "Langue définie sur : <b>{label}</b>",
        "lang_usage": (
            "<b>Langue de l'interface</b>\n"
            "Langue actuelle : {current}\n\n"
            "<b>Usage :</b>\n"
            "<code>/lang en</code> - English\n"
            "<code>/lang fr</code> - Français\n"
            "<code>/lang ar</code> - العربية"
        ),
        "lang_unknown": "Langue inconnue. Langues disponibles : en, fr, ar.",
        "cancel_text": "Questionnaire annulé. Envoie /start quand tu veux créer un prompt de logo.",
        "outside_text": "Envoie /start pour créer ton prompt de logo.",
        "need_input_text": (
            "Réponds à la question en cours - appuie sur un bouton ou tape du "
            "texte - ou envoie /cancel pour arrêter."
        ),
        "invalid_text": (
            "Cette réponse est vide ou trop longue (max {max_len} caractères). "
            "Réessaie s'il te plaît."
        ),
        "stale_question": "Cette question a déjà été répondue. Voici la question en cours :",
        "custom_noted": (
            "Bien noté - j'utiliserai ta description : « {text} »\n\n"
            "Question suivante :"
        ),
        "type_instead_hint": (
            "Je n'ai pas reconnu. Appuie sur l'un des boutons - et si rien "
            "ne correspond, décris-le en quelques mots."
        ),
        "summary_note": (
            "Questionnaire terminé - voici ce que j'ai collecté :\n\n"
            "{summary}"
        ),
        "prompt_intro": (
            "Voici ton prompt de logo professionnel.\n"
            "Touche le bloc du prompt pour le copier, puis colle-le dans ton "
            "générateur d'images préféré."
        ),
        "prompt_score": "Score de qualité du prompt : {score}/100",
        "prompt_warning": (
            "Le prompt est en dessous du seuil de qualité - appuie sur "
            "Recommencer pour affiner tes réponses et réessayer."
        ),
        "btn_generate": "Générer le prompt",
        "btn_restart": "Recommencer",
        "btn_new": "Créer un autre",
        "btn_done": "Terminé",
        "summary_avoid": "À éviter",
        "summary_empty": "- (aucune réponse pour l'instant)",

        # -- questions -----------------------------------------------------
        "q_brand_name": (
            "Quel est le nom exact de la marque ?\n\n"
            "Tape-le maintenant - il sera gardé exactement comme tu l'écris, "
            "majuscules, espaces et ponctuation comprises, car le prompt le "
            "reproduit lettre par lettre. Ou appuie sur le bouton ci-dessous "
            "si le logo ne doit porter aucun nom."
        ),
        "opt_brand_name_skip": "Passer - sans nom",
        "q_industry": (
            "Dans quel domaine se trouve ta marque ?\n\n"
            "Choisis d'abord le domaine le plus proche - je demanderai ensuite "
            "ta spécialité exacte, car un cafe et un restaurant n'ont pas le "
            "même langage de design. Si rien ne convient, choisis Autre et "
            "décris-le."
        ),
        "opt_industry_food": "Food & Drink",
        "opt_industry_fashion": "Mode & Beauté",
        "opt_industry_tech": "Tech & Digital",
        "opt_industry_media": "Média & Création",
        "opt_industry_education": "Éducation & Livres",
        "opt_industry_sports": "Sport & Fitness",
        "opt_industry_services": "Business & Services",
        "opt_industry_gaming": "Gaming & Esport",
        "opt_industry_other": "Autre (je vais le décrire)",
        "q_industry_food": (
            "Food & Drink - quelle est ta spécialité exacte ?\n\n"
            "Chaque choix a ses propres codes : un cafe fait cosy et chaud, "
            "le fast food fait bold et rapide, la boulangerie fait fait-maison. "
            "Choisis celle qui correspond à ton business."
        ),
        "opt_industry_food_restaurant": "Restaurant",
        "opt_industry_food_cafe": "Café (coffee)",
        "opt_industry_food_fastfood": "Fast food",
        "opt_industry_food_bakery": "Boulangerie & pâtisserie",
        "opt_industry_food_juice": "Jus & boissons fraîches",
        "opt_industry_food_other": "Autre (je vais le décrire)",
        "q_industry_fashion": (
            "Mode & Beauté - quelle est ta spécialité exacte ?\n\n"
            "Une marque de vêtements, un salon de coiffure et une maison de "
            "joaillerie ne parlent pas le même langage visuel. Choisis la "
            "tienne."
        ),
        "opt_industry_fashion_clothing": "Marque de vêtements",
        "opt_industry_fashion_beauty": "Beauté & cosmétiques",
        "opt_industry_fashion_barber": "Barbier & salon de coiffure",
        "opt_industry_fashion_perfume": "Parfum & fragrance",
        "opt_industry_fashion_jewelry": "Bijoux & accessoires",
        "opt_industry_fashion_other": "Autre (je vais le décrire)",
        "q_industry_tech": (
            "Tech & Digital - quelle est ta spécialité exacte ?\n\n"
            "Une startup, un développeur d'applications et une entreprise de "
            "cybersécurité n'ont pas la même attitude. Choisis la tienne."
        ),
        "opt_industry_tech_startup": "Startup IA & tech",
        "opt_industry_tech_dev": "Développement d'apps & logiciels",
        "opt_industry_tech_web": "Agence web & services digitaux",
        "opt_industry_tech_cyber": "IT & cybersécurité",
        "opt_industry_tech_other": "Autre (je vais le décrire)",
        "q_industry_media": (
            "Média & Création - quelle est ta spécialité exacte ?\n\n"
            "Photo, vidéo, design graphique et réseaux sociaux ont chacun "
            "leur vocabulaire d'icônes. Choisis le tien."
        ),
        "opt_industry_media_photo": "Photographie",
        "opt_industry_media_video": "Vidéo & tournage",
        "opt_industry_media_design": "Design graphique",
        "opt_industry_media_marketing": "Marketing & réseaux sociaux",
        "opt_industry_media_other": "Autre (je vais le décrire)",
        "q_industry_education": (
            "Éducation & Livres - quelle est ta spécialité exacte ?\n\n"
            "Une école, une librairie et un centre de formation n'attirent "
            "pas le même public. Choisis la tienne."
        ),
        "opt_industry_education_school": "École & cours de soutien",
        "opt_industry_education_library": "Bibliothèque & librairie",
        "opt_industry_education_training": "Cours & formation",
        "opt_industry_education_other": "Autre (je vais le décrire)",
        "q_industry_sports": (
            "Sport & Fitness - quelle est ta spécialité exacte ?\n\n"
            "Une salle de sport, un club de sport et un coach personnel "
            "construisent des identités très différentes. Choisis la tienne."
        ),
        "opt_industry_sports_gym": "Salle de sport & fitness",
        "opt_industry_sports_club": "Club & équipe de sport",
        "opt_industry_sports_coach": "Coach personnel",
        "opt_industry_sports_other": "Autre (je vais le décrire)",
        "q_industry_services": (
            "Business & Services - quelle est ta spécialité exacte ?\n\n"
            "Livraison, immobilier, construction et commerce ont chacun "
            "leurs symboles. Choisis le tien."
        ),
        "opt_industry_services_delivery": "Livraison & transport",
        "opt_industry_services_realestate": "Immobilier",
        "opt_industry_services_construction": "Construction & BTP",
        "opt_industry_services_shop": "Boutique & e-commerce",
        "opt_industry_services_other": "Autre (je vais le décrire)",
        "q_industry_gaming": (
            "Gaming & Esport - quelle est ta spécialité exacte ?\n\n"
            "Une équipe esport a besoin d'un blason agressif, un studio de "
            "jeu d'un univers ludique. Choisis la tienne."
        ),
        "opt_industry_gaming_team": "Marque gaming & équipe esport",
        "opt_industry_gaming_studio": "Studio & développeur de jeux",
        "opt_industry_gaming_other": "Autre (je vais le décrire)",
        "q_industry_text": (
            "Décris ton activité en quelques mots - ajoute tout ce que tu "
            "veux que je sache.\n\n"
            "Toutes les langues marchent : français, anglais, arabe, darija "
            "ou arabizi (exemple : 'bot pour télécharger des livres', "
            "'بوت لتحميل الكتب', 'livraison de poulet grillé')."
        ),
        "q_category": (
            "Quel type de logo veux-tu ?\n\n"
            "Symbole = une icône seule. Lettermark = initiales stylisées. "
            "Wordmark = le nom posé en logo. Combinaison = icône + nom. "
            "Emblème = le nom dans un badge. Si tu vois autre chose, "
            "choisis Autre et décris-le."
        ),
        "opt_category_symbol": "Symbole seul (icône)",
        "opt_category_lettermark": "Lettres / initiales (lettermark)",
        "opt_category_wordmark": "Nom de la marque en texte (wordmark)",
        "opt_category_combination": "Symbole + nom (combinaison)",
        "opt_category_abstract": "Forme abstraite",
        "opt_category_emblem": "Badge / emblème",
        "opt_category_auto": "Décide pour moi",
        "opt_category_other": "Autre (je vais le décrire)",
        "q_category_text": (
            "Décris le type de logo que tu veux avec tes mots - ajoute tout "
            "ce que tu veux.\n\n"
            "Exemple : 'un blason avec mes initiales dedans'."
        ),
        "q_motif": (
            "Que doit évoquer le symbole ?\n\n"
            "C'est le coeur du concept : l'idée principale dont l'icône est "
            "faite. Choisis une direction, ou laisse-moi choisir avec "
            "créativité dans ton domaine."
        ),
        "opt_motif_object": "Un objet de mon activité",
        "opt_motif_letter": "Ma lettre initiale (en forme)",
        "opt_motif_geometric": "Formes géométriques pures",
        "opt_motif_nature": "Nature (feuille, montagne, vague...)",
        "opt_motif_premium": "Symbole premium (couronne, étoile...)",
        "opt_motif_auto": "Tu décides",
        "opt_motif_other": "Autre (je vais le décrire)",
        "q_motif_text": (
            "Décris ce que le symbole doit évoquer - ajoute tout ce que tu "
            "veux.\n\n"
            "Exemple : 'un lion fondu avec une tasse de café, sans dessiner "
            "un vrai animal'."
        ),
        "q_typography": (
            "Le logo doit-il contenir du texte ?\n\n"
            "Nom = le nom complet de la marque. Initiales = un monogramme. "
            "Nom sous le symbole = le classique combinaison."
        ),
        "opt_typography_none": "Aucun texte",
        "opt_typography_name": "Le nom de la marque",
        "opt_typography_initials": "Initiales seulement",
        "opt_typography_name_under": "Nom sous le symbole",
        "opt_typography_auto": "Tu décides",
        "q_font_style": (
            "Quel caractère pour les lettres ?\n\n"
            "La typographie porte le caractère de la marque : net et "
            "moderne, classique avec serif, arrondi et sympathique, ou "
            "manuscrit."
        ),
        "opt_font_style_modern_sans": "Moderne & net",
        "opt_font_style_classic_serif": "Serif classique",
        "opt_font_style_rounded": "Arrondi & sympathique",
        "opt_font_style_script": "Script / manuscrit",
        "opt_font_style_geometric": "Géométrique & minimal",
        "opt_font_style_auto": "Tu décides",
        "q_tagline": (
            "Ajouter un court slogan sous le nom ?\n\n"
            "Tape ton slogan exact (60 caractères max) et il sera affiché "
            "en petites lettres sous le nom de la marque - écrit exactement "
            "comme tu le tapes. Ou appuie sur le bouton pour un logo sans "
            "slogan."
        ),
        "opt_tagline_skip": "Passer - sans slogan",
        "q_colors": (
            "Quelle palette de couleurs préfères-tu ?\n\n"
            "Les couleurs décident de la sensation : le bleu rassure, l'or "
            "signale le luxe, le rouge ouvre l'appétit. Un logo professionnel "
            "reste entre 1 et 3 couleurs."
        ),
        "opt_colors_blue_white": "Bleu & blanc",
        "opt_colors_green_white": "Vert & blanc",
        "opt_colors_black_gold": "Noir & or",
        "opt_colors_red_white": "Rouge & blanc",
        "opt_colors_dark_premium": "Sombre & premium",
        "opt_colors_soft_pastel": "Pastels doux",
        "opt_colors_bold_vivid": "Vif & coloré",
        "opt_colors_surprise": "Surprends-moi",
        "opt_colors_other": "Autre (je vais les taper)",
        "q_colors_text": (
            "Tape les couleurs que tu veux - ajoute tout ce que tu veux.\n\n"
            "N'importe quelle langue, par exemple : 'vert et blanc', "
            "'vert et or', 'أخضر وأبيض', 'akhdar w abyad'."
        ),
        "q_style": (
            "Quel style visuel correspond le mieux à ta marque ?\n\n"
            "Pense « époque du design » : minimaliste est intemporel, "
            "futuriste fait haute technologie, vintage fait héritage, "
            "artisanal fait chaud et fait-main."
        ),
        "opt_style_minimalist": "Minimaliste",
        "opt_style_maximalist": "Maximaliste (riche, détaillé)",
        "opt_style_modern": "Moderne",
        "opt_style_luxury": "Luxe / premium",
        "opt_style_futuristic": "Futuriste",
        "opt_style_vintage": "Vintage / rétro",
        "opt_style_handcrafted": "Artisanal / organique",
        "opt_style_auto": "Tu décides",
        "opt_style_other": "Autre (je vais le décrire)",
        "q_style_text": (
            "Décris le style que tu veux - ajoute tout ce que tu veux.\n\n"
            "Exemple : 'comme une vieille enseigne de pharmacie, mais plus "
            "propre'."
        ),
        "q_audience": (
            "Qui est ton public principal ?\n\n"
            "La même marque ne parle pas pareil aux ados, aux familles ou "
            "aux entreprises - le design s'adapte à eux. Si ton public est "
            "autre, choisis Autre et décris-le."
        ),
        "opt_audience_young": "Jeunes & tendance",
        "opt_audience_family": "Familles",
        "opt_audience_business": "Entreprises & professionnels",
        "opt_audience_premium": "Clientèle haut de gamme",
        "opt_audience_local": "Communauté locale",
        "opt_audience_broad": "Un peu de tout",
        "opt_audience_auto": "Tu décides",
        "opt_audience_other": "Autre (je vais le décrire)",
        "q_audience_text": (
            "Décris ton public avec tes mots - ajoute tout ce que tu "
            "veux.\n\n"
            "Exemple : 'des étudiants', 'طلاب الجامعة'."
        ),
        "q_personality": (
            "Si ta marque était une personne, quel caractère aurait-elle ?\n\n"
            "Cela donne l'attitude de chaque courbe et de chaque ligne du "
            "logo."
        ),
        "opt_personality_bold": "Bold & puissant",
        "opt_personality_calm": "Calme & rassurant",
        "opt_personality_playful": "Joueur & sympathique",
        "opt_personality_elegant": "Élégant & raffiné",
        "opt_personality_innovative": "Innovant & moderne",
        "opt_personality_auto": "Tu décides",
        "opt_personality_other": "Autre (je vais le décrire)",
        "q_personality_text": (
            "Décris le caractère de ta marque avec tes mots - ajoute tout "
            "ce que tu veux.\n\n"
            "Exemple : 'sérieux au travail, mais avec un petit clin d'oeil'."
        ),
        "q_dimension": (
            "Rendu plat ou en relief ?\n\n"
            "Le vecteur plat est le standard intemporel du logo ; la 3D "
            "fait premium mais vieillit plus vite. Dans le doute, reste "
            "plat ou légèrement 3D."
        ),
        "opt_dimension_flat": "Vecteur plat (2D)",
        "opt_dimension_slight_3d": "Légèrement 3D",
        "opt_dimension_full_3d": "3D premium complet",
        "opt_dimension_auto": "Tu décides",
        "q_background": (
            "Quel fond préfères-tu ?\n\n"
            "Le blanc pur est le plus sûr pour les générateurs ; les fonds "
            "sombres font ressortir l'or ; isolé veut dire aucun fond "
            "visible (prêt pour la transparence)."
        ),
        "opt_background_white": "Blanc pur",
        "opt_background_dark": "Sombre",
        "opt_background_isolated": "Isolé (sans fond visible)",
        "opt_background_auto": "Tu décides",
        "opt_background_other": "Autre (je vais le décrire)",
        "q_background_text": (
            "Décris le fond que tu veux - ajoute tout ce que tu veux.\n\n"
            "Exemple : 'fond vert foncé' ou 'fond bleu nuit'."
        ),
        "q_usage": (
            "Où le logo sera-t-il le plus utilisé ?\n\n"
            "Cela guide la composition, les proportions et les marges de "
            "sécurité : un avatar Telegram doit rester lisible en tout "
            "petit, un en-tête de site peut respirer."
        ),
        "opt_usage_telegram_avatar": "Avatar Telegram (carré)",
        "opt_usage_website": "En-tête de site web",
        "opt_usage_social": "Posts sur les réseaux sociaux",
        "opt_usage_print": "Impression / packaging",
        "opt_usage_everywhere": "Partout",
        "opt_usage_other": "Autre (je vais le décrire)",
        "q_usage_text": (
            "Où le logo sera-t-il utilisé ? Décris-le - ajoute tout ce que "
            "tu veux.\n\n"
            "Exemple : 'sur mes camions de livraison et la façade du "
            "magasin'."
        ),
        "q_exclusions": (
            "Quelque chose à éviter ?\n\n"
            "Touche un élément pour l'activer ou le désactiver, puis appuie "
            "sur Terminé. Les restrictions obligatoires (pas d'humains, pas "
            "d'animaux, pas de visages) sont toujours appliquées "
            "automatiquement, que tu coches ou non."
        ),
        "opt_exclusions_neon": "Effets néon",
        "opt_exclusions_gradients": "Dégradés",
        "opt_exclusions_shadows": "Ombres",
        "opt_exclusions_decorations": "Décorations superflues",
        "opt_exclusions_complex": "Détails complexes",

        # -- summary labels --------------------------------------------------
        "sum_brand_name": "Nom de la marque",
        "sum_industry": "Domaine",
        "sum_industry_leaf": "Spécialité",
        "sum_industry_text": "Activité",
        "sum_category": "Type de logo",
        "sum_category_text": "Type (tes mots)",
        "sum_motif": "Idée du symbole",
        "sum_motif_text": "Idée du symbole (tes mots)",
        "sum_typography": "Typographie",
        "sum_font_style": "Style des lettres",
        "sum_tagline": "Slogan",
        "sum_colors": "Couleurs",
        "sum_colors_text": "Couleurs (tapées)",
        "sum_style": "Style",
        "sum_style_text": "Style (tes mots)",
        "sum_audience": "Public",
        "sum_audience_text": "Public (tes mots)",
        "sum_personality": "Caractère",
        "sum_personality_text": "Caractère (tes mots)",
        "sum_dimension": "Rendu",
        "sum_background": "Fond",
        "sum_background_text": "Fond (tes mots)",
        "sum_usage": "Utilisé sur",
        "sum_usage_text": "Usage (tes mots)",

        # -- Etape 7 : aide, support, credits, parrainage, canal, dons --------
        "help_text": (
            "<b>TASMEEM AI - aide</b>\n\n"
            "Je transforme tes réponses en un prompt professionnel prêt à "
            "l'emploi :\n"
            "🎨 un prompt de <b>LOGO</b> pour la génération d'image\n"
            "📢 un prompt de <b>POST RÉSEAUX SOCIAUX (pub)</b> pour ton "
            "produit, ton service ou ta page\n\n"
            "<b>Comment ça marche</b>\n"
            "1. Envoie /start et choisis un mode (logo ou pub)\n"
            "2. Réponds aux questions rapides - boutons ou texte, dans ta langue\n"
            "3. Copie le prompt généré dans ton générateur d'images préféré\n"
            "4. Si tu as un logo, colle l'image de ton logo en même temps "
            "que le prompt\n\n"
            "<b>Commandes</b>\n"
            "/start - ouvrir le menu\n"
            "/credits - tes crédits + ton lien de parrainage\n"
            "/lang - changer la langue de l'interface\n"
            "/donate - soutenir le bot avec des Stars\n"
            "/support - contacter le support\n"
            "/cancel - arrêter le questionnaire\n\n"
            "<b>Crédits</b>\n"
            "1 prompt = 1 crédit. +{refill} crédits gratuits sont ajoutés "
            "chaque jour, et tu gagnes +{bonus} crédits pour chaque ami qui "
            "démarre le bot avec ton lien personnel.\n\n"
            "Support : {support}"
        ),
        "support_text": (
            "Besoin d'un humain ? Contacte le développeur - il répond au "
            "plus vite :\n{support}"
        ),
        "menu_credits": "💳 Crédits : <b>{credits}</b> (+{refill} gratuits chaque jour)",
        "credits_text": (
            "💳 <b>Tes crédits : {credits}</b>\n\n"
            "✨ +{refill} crédits gratuits sont ajoutés automatiquement chaque "
            "jour.\n"
            "🎁 Invite des amis : +{bonus} crédits pour chaque ami qui démarre "
            "le bot avec ton lien personnel :\n{link}\n\n"
            "⚙️ 1 prompt généré = 1 crédit."
        ),
        "not_enough": (
            "😢 Pas assez de crédits.\n\n"
            "Un prompt généré coûte {cost} crédit et ton solde est de "
            "{credits}.\n\n"
            "✨ +{refill} crédits gratuits sont ajoutés chaque jour.\n"
            "🎁 Invite des amis : +{bonus} crédits chacun.\n"
            "🤍 Ou soutiens le bot avec un don ci-dessous."
        ),
        "ref_bonus_notify": (
            "🎁 <b>+{bonus} crédits !</b>\n"
            "Un ami vient de démarrer TASMEEM AI avec ton lien."
        ),
        "fs_required": (
            "🔒 <b>Une petite étape avant de commencer</b>\n\n"
            "TASMEEM AI est gratuit - la seule chose qu'on demande, c'est de "
            "rejoindre notre canal. Actus, astuces et drops gratuits y sont "
            "publiés.\n\n"
            "Rejoins-nous ici : {channel_link}\n\n"
            "Déjà membre ? Appuie sur le bouton ci-dessous."
        ),
        "fs_still": (
            "Tu dois d'abord rejoindre le canal. Appuie sur Rejoindre, "
            "puis vérifie à nouveau."
        ),
        "btn_join": "📢 Rejoindre le canal",
        "btn_check": "✅ J'ai rejoint - vérifier",
        "btn_donate": "🤍 Soutenir le bot",
        "btn_support": "🆘 Support",
        "donate_intro": (
            "🤍 <b>Soutenir TASMEEM AI</b>\n\n"
            "Le bot est gratuit et le reste. S'il t'aide, un petit don en "
            "Stars Telegram le fait tourner et progresser.\n\n"
            "Choisis un montant :"
        ),
        "donate_desc": "Don pour soutenir TASMEEM AI",
        "donate_thanks": (
            "🤍 <b>Merci pour ton don de {stars} Stars !</b>\n"
            "Ton soutien garde TASMEEM AI gratuit et en progrès."
        ),
        "out_credits": "💳 Crédits restants : <b>{credits}</b> (+{refill} gratuits demain)",
        # -- Step 8: ads mode, support tag, admin (appended) -----
        "btn_mode_logo": '🎨 Prompt de logo',
        "btn_mode_ads": '📢 Post réseaux sociaux (pub)',
        "prompt_intro_ads": "Voici ton prompt publicitaire professionnel.\nTouche le bloc de prompt pour le copier, puis colle-le dans ton générateur d'images préféré - avec ton logo si tu en as un.",
        "ads_howto": "📋 <b>Comment l'utiliser :</b>\n1. Touche le bloc de prompt ci-dessus pour le copier, puis colle-le dans ton modèle d'images IA.\n2. Tu as un logo ? <b>Colle/joins l'image de ton logo en même temps que le prompt</b> (même message) - le modèle l'intégrera.\n3. Le nom de ta marque et ton @pseudo sont déjà écrits dans le prompt - inutile de les retaper.\n4. Si le texte généré n'est pas parfait, génère le visuel puis ajoute tes mots exacts dans Canva ou similaire.",
        "ads_howto_nologo": "💡 Astuce : tu n'as pas encore de logo - crée-le d'abord avec le mode 🎨 Logo de ce bot, puis refais ta pub.",
        "out_support": "<b>Fait avec 🤍 par TASMEEM AI</b> - pour toute demande perso ou de l'aide, écris au créateur : {support}",
        "sum_ad_leaf": 'Détail',
        "q_ad_brand_name": "Quel est le nom exact de ta marque ou de ta page pour ce post ?\n\nTape-le maintenant - il sera gardé exactement comme tu l'écris (majuscules, espaces, ponctuation) et écrit dans le prompt lettre par lettre. Ou appuie sur le bouton si le visuel ne porte aucun nom.",
        "opt_ad_brand_name_skip": 'Passer - sans nom',
        "q_ad_username": "Quel est le @pseudo de ta marque ou de ta page ?\n\nExemple : @mamarque - il va dans le prompt pour que le modèle IA puisse l'afficher sur le visuel (ou tu peux le coller en même temps que le prompt). Pas de pseudo ? Appuie sur le bouton.",
        "opt_ad_username_skip": 'Passer - sans pseudo',
        "q_ad_goal": "Le post sert à quoi ?\n\nLe but décide toute la composition : une vente flash a besoin d'urgence et d'une grosse zone prix, un giveaway a besoin d'excitation, une annonce a besoin de clarté. Choisis le but le plus proche - je demanderai ensuite le type exact.",
        "opt_ad_goal_sales": 'Vendre & promouvoir',
        "opt_ad_goal_growth": 'Faire grandir ma page',
        "opt_ad_goal_announce": 'Annoncer quelque chose',
        "opt_ad_goal_traffic": 'Amener des clients & commandes',
        "opt_ad_goal_other": 'Autre (je décris)',
        "q_ad_goal_sales": 'Vendre & promouvoir - quel but exactement ?',
        "opt_ad_goal_sales_product": 'Promouvoir un produit',
        "opt_ad_goal_sales_discount": 'Solde / réduction / code promo',
        "opt_ad_goal_sales_new": 'Nouveauté / lancement',
        "opt_ad_goal_sales_flash": 'Vente flash / offre limitée',
        "opt_ad_goal_sales_other": 'Autre (je décris)',
        "q_ad_goal_growth": 'Faire grandir ma page - quel but exactement ?',
        "opt_ad_goal_growth_giveaway": 'Giveaway (cadeau)',
        "opt_ad_goal_growth_contest": 'Concours / challenge',
        "opt_ad_goal_growth_follow": 'Gagner des abonnés',
        "opt_ad_goal_growth_engage": "Post d'engagement (question / sondage)",
        "opt_ad_goal_growth_other": 'Autre (je décris)',
        "q_ad_goal_announce": 'Annoncer quelque chose - quel but exactement ?',
        "opt_ad_goal_announce_opening": 'Grande ouverture',
        "opt_ad_goal_announce_event": 'Événement / invitation',
        "opt_ad_goal_announce_rebrand": 'Nouvelle image / rebranding',
        "opt_ad_goal_announce_info": 'Annonce générale',
        "opt_ad_goal_announce_other": 'Autre (je décris)',
        "q_ad_goal_traffic": 'Amener des clients & commandes - quel but exactement ?',
        "opt_ad_goal_traffic_booking": 'Réservations / rendez-vous',
        "opt_ad_goal_traffic_order": 'Commandes directes / menu',
        "opt_ad_goal_traffic_visit": 'Visites boutique / site web',
        "opt_ad_goal_traffic_download": 'Téléchargements app / bot',
        "opt_ad_goal_traffic_other": 'Autre (je décris)',
        "q_ad_goal_text": "Décris le but du post avec tes mots - ajoute tout ce que tu veux.\n\nExemple : 'soldes d'été -30% sur tout le magasin', 'تخفيضات الصيف', 'RAMADAN OFFER'.",
        "q_ad_platform": "Où sera publié ce post ?\n\nChaque plateforme a ses codes : Instagram aime l'esthétique propre, TikTok a besoin de contraste fort, un post Telegram reste lisible sur petit écran. Rien ne convient ? Choisis Autre.",
        "opt_ad_platform_instagram": 'Instagram',
        "opt_ad_platform_facebook": 'Facebook',
        "opt_ad_platform_tiktok": 'TikTok',
        "opt_ad_platform_telegram": 'Telegram',
        "opt_ad_platform_whatsapp": 'Statut WhatsApp',
        "opt_ad_platform_other": 'Autre (je décris)',
        "q_ad_platform_text": "Sur quelle plateforme ou quel endroit ? Décris - ajoute tout ce que tu veux.\n\nExemple : 'Snapchat', 'page LinkedIn', 'flyer imprimé'.",
        "q_ad_format": 'Quel format te faut-il ?\n\nLe carré est le post classique, le 9:16 remplit les stories et reels en plein écran, le 4:5 prend plus de place dans le fil, le 16:9 sert de bannière large ou de couverture de page.',
        "opt_ad_format_square": 'Post carré (1:1)',
        "opt_ad_format_story": 'Story / Reels (9:16)',
        "opt_ad_format_portrait": 'Post portrait (4:5)',
        "opt_ad_format_banner": 'Bannière large (16:9)',
        "opt_ad_format_cover": 'Couverture de page',
        "opt_ad_format_auto": 'Tu décides',
        "opt_ad_format_other": 'Autre (je décris)',
        "q_ad_format_text": "Décris le format voulu - ajoute tout ce que tu veux.\n\nExemple : 'deux frames de story', 'bannière pour ma chaîne YouTube'.",
        "q_ad_offer": "Qu'est-ce que tu promeus exactement ?\n\nDécris le produit, le service, le prix, la réduction, la date ou le lieu - tout ce que le visuel doit montrer fidèlement (exemple : 'pizza medium 2000 DA, livraison gratuite'). Ou appuie sur le bouton pour rester général.",
        "opt_ad_offer_skip": 'Passer - sans détails',
        "q_ad_cta": "Quel appel à l'action (CTA) doit apparaître sur le visuel ?\n\nLe CTA, c'est le petit bouton ou bandeau qui dit aux gens quoi faire ensuite : acheter, réserver, écrire, suivre...",
        "opt_ad_cta_shop_now": 'Acheter maintenant',
        "opt_ad_cta_order_now": 'Commander maintenant',
        "opt_ad_cta_book_now": 'Réserver maintenant',
        "opt_ad_cta_learn_more": 'En savoir plus',
        "opt_ad_cta_dm": 'Écris-nous',
        "opt_ad_cta_call": 'Appeler maintenant',
        "opt_ad_cta_whatsapp": 'WhatsApp',
        "opt_ad_cta_follow": 'Suis-nous',
        "opt_ad_cta_visit": 'Venez nous voir',
        "opt_ad_cta_auto": 'Tu décides',
        "opt_ad_cta_other": 'Autre (je décris)',
        "q_ad_cta_text": "Tape le texte exact de l'appel à l'action - ajoute tout ce que tu veux.\n\nExemple : 'Réserve ta place', 'Commandez ici', 'اطلب الآن'.",
        "q_ad_lang_text": "Quelle langue pour le texte SUR le visuel ?\n\nLe modèle IA doit écrire les mots exacts : choisir la langue évite les alphabets mélangés. 'Sans texte' te donne un visuel propre et tu ajoutes les mots toi-même dans Canva ou similaire.",
        "opt_ad_lang_text_en": 'Anglais',
        "opt_ad_lang_text_fr": 'Français',
        "opt_ad_lang_text_ar": 'Arabe',
        "opt_ad_lang_text_ar_en": 'Arabe + Anglais',
        "opt_ad_lang_text_fr_en": 'Français + Anglais',
        "opt_ad_lang_text_none": 'Sans texte sur le visuel',
        "opt_ad_lang_text_other": 'Autre (je décris)',
        "q_ad_lang_text_text": "Quelle(s) langue(s) pour le texte du visuel ? Décris - ajoute tout ce que tu veux.\n\nExemple : 'arabe dialectal avec un petit prix en anglais'.",
        "q_ad_headline": 'Quel est le texte exact du titre à écrire sur le visuel ?\n\nTape-le exactement comme il doit apparaître (80 caractères max) - orthographe, majuscules et ponctuation sont gardées lettre par lettre. Ou appuie sur le bouton et je choisis un titre court et percutant pour toi.',
        "opt_ad_headline_skip": 'Tu décides pour moi',
        "q_ad_visual": "Que doit montrer le visuel ?\n\nC'est le cœur de la pub : un produit seul, des gens qui l'utilisent, une affiche graphique ou un shot de food appétissant. Choisis d'abord une famille - je demanderai ensuite la scène exacte.",
        "opt_ad_visual_product": 'Mise en avant produit',
        "opt_ad_visual_people": 'Personnes & lifestyle',
        "opt_ad_visual_graphic": 'Graphique & typographie',
        "opt_ad_visual_food": 'Shots food & boissons',
        "opt_ad_visual_auto": 'Tu décides',
        "opt_ad_visual_other": 'Autre (je décris)',
        "q_ad_visual_product": 'Mise en avant produit - quelle scène convient le mieux ?',
        "opt_ad_visual_product_studio": 'Shot studio sur fond propre',
        "opt_ad_visual_product_lifestyle": 'Scène lifestyle (en vraie utilisation)',
        "opt_ad_visual_product_detail": 'Gros plan sur les détails',
        "opt_ad_visual_product_flatlay": 'Flat-lay vue du dessus',
        "opt_ad_visual_product_other": 'Autre (je décris)',
        "q_ad_visual_people": 'Personnes & lifestyle - quelle scène convient le mieux ?',
        "opt_ad_visual_people_model": 'Un mannequin qui le présente',
        "opt_ad_visual_people_hands": 'Des mains qui tiennent le produit',
        "opt_ad_visual_people_team": "L'équipe / le staff",
        "opt_ad_visual_people_crowd": 'Une foule en événement',
        "opt_ad_visual_people_other": 'Autre (je décris)',
        "q_ad_visual_graphic": 'Graphique & typographie - quelle scène convient le mieux ?',
        "opt_ad_visual_graphic_typographic": 'Affiche typographique audacieuse',
        "opt_ad_visual_graphic_illustration": 'Illustration sur mesure',
        "opt_ad_visual_graphic_shapes": 'Formes abstraites & dégradés',
        "opt_ad_visual_graphic_pattern": 'Motif de marque répété',
        "opt_ad_visual_graphic_other": 'Autre (je décris)',
        "q_ad_visual_food": 'Shots food & boissons - quelle scène convient le mieux ?',
        "opt_ad_visual_food_dish": 'Plat dressé',
        "opt_ad_visual_food_drink": 'Boisson / beverage',
        "opt_ad_visual_food_ingredients": 'Ingrédients frais',
        "opt_ad_visual_food_other": 'Autre (je décris)',
        "q_ad_visual_text": "Décris ce que le visuel doit montrer - ajoute tout ce que tu veux.\n\nExemple : 'ma basket bleue qui flotte avec des éclaboussures de peinture', 'صحن كسكس مع الخضرة', 'une boîte de chocolats ouverte'.",
        "q_ad_logo": "As-tu un logo à placer sur le visuel ?\n\nSi oui, à la fin je te dirai de COLLER L'IMAGE DE TON LOGO en même temps que le prompt dans le modèle IA - c'est comme ça qu'il sera intégré. Si tu n'as pas encore de logo, tu peux le créer d'abord avec le mode Logo de ce bot.",
        "opt_ad_logo_yes": 'Oui - je le joins',
        "opt_ad_logo_no": 'Pas encore de logo',
        "opt_ad_logo_name_only": 'Utiliser le nom comme marque',
        "opt_ad_logo_auto": 'Tu décides',
        # -- Step 8: summary display names -------------------------------
        "sum_ad_brand_name": 'Nom de marque / page',
        "sum_ad_username": '@Pseudo de la page',
        "sum_ad_goal": 'But du post',
        "sum_ad_goal_text": 'But (tes mots)',
        "sum_ad_platform": 'Plateforme',
        "sum_ad_platform_text": 'Plateforme (tes mots)',
        "sum_ad_format": 'Format',
        "sum_ad_format_text": 'Format (tes mots)',
        "sum_ad_offer": 'Offre',
        "sum_ad_cta": "Appel à l'action",
        "sum_ad_cta_text": 'CTA (tes mots)',
        "sum_ad_lang_text": 'Langue du texte',
        "sum_ad_lang_text_text": 'Langue du texte (tes mots)',
        "sum_ad_headline": 'Titre',
        "sum_ad_visual": 'Scène du visuel',
        "sum_ad_visual_text": 'Visuel (tes mots)',
        "sum_ad_logo": 'Logo',
    },
    # ------------------------------------------------------------------
    # ARABIC (simple MSA, Algerian-friendly)
    # ------------------------------------------------------------------
    "ar": {
        "menu_text": (
            "مرحبًا بك في <b>TASMEEM AI</b>.\n\n"
            "اختر وضع الإنشاء - سأسألك أسئلة سريعة (أزرار أو كتابة، بلغتك) "
            "وأبني لك من إجاباتك برومبت احترافيًا جاهزًا للاستعمال:\n\n"
            "🎨 <b>شعار</b> - برومبت احترافي لتوليد الشعارات\n"
            "📢 <b>منشور إعلاني (سوشيال ميديا)</b> - برومبت إعلاني احترافي "
            "لمنتجك أو خدمتك أو صفحتك\n\n"
            "<b>الأوامر:</b>\n"
            "/credits - رصيدك ورابط الدعوة\n"
            "/lang - تغيير لغة الواجهة\n"
            "/help - طريقة الاستخدام\n"
            "/donate - دعم البوت\n"
            "/cancel - إيقاف الأسئلة في أي وقت\n\n"
            "أعيد برومبتات نصية احترافية فقط، وليس صورًا."
        ),
        "menu_button": "أنشئ برومبت الشعار",
        "lang_set": "تم ضبط اللغة على: <b>{label}</b>",
        "lang_usage": (
            "<b>لغة الواجهة</b>\n"
            "اللغة الحالية: {current}\n\n"
            "<b>الاستخدام:</b>\n"
            "<code>/lang en</code> - English\n"
            "<code>/lang fr</code> - Français\n"
            "<code>/lang ar</code> - العربية"
        ),
        "lang_unknown": "لغة غير معروفة. اللغات المتاحة: en، fr، ar.",
        "cancel_text": "تم إيقاف الأسئلة. أرسل /start عندما تريد إنشاء برومبت شعار.",
        "outside_text": "أرسل /start لإنشاء برومبت الشعار.",
        "need_input_text": (
            "أجب على السؤال الحالي - اضغط زرًا أو اكتب نصًا - "
            "أو أرسل /cancel للإيقاف."
        ),
        "invalid_text": (
            "الإجابة فارغة أو طويلة جدًا (الحد الأقصى {max_len} حرفًا). "
            "حاول مرة أخرى."
        ),
        "stale_question": "تمت الإجابة على هذا السؤال بالفعل. هذا هو السؤال الحالي:",
        "custom_noted": (
            "حسناً - سأستخدم وصفك: «{text}»\n\n"
            "السؤال التالي:"
        ),
        "type_instead_hint": (
            "لم أفهم قصدك. اضغط على أحد الأزرار - وإذا لم يناسبك شيء، "
            "صفه ببضع كلمات."
        ),
        "summary_note": (
            "اكتملت الأسئلة - هذا ما جمعته:\n\n"
            "{summary}"
        ),
        "prompt_intro": (
            "هذا هو برومبت الشعار الاحترافي الخاص بك.\n"
            "اضغط على كتلة البرومبت لنسخها، ثم الصقها في مولّد الصور المفضل لديك."
        ),
        "prompt_score": "تقييم جودة البرومبت: {score}/100",
        "prompt_warning": (
            "البرومبت أقل من عتبة الجودة - اضغط «إعادة من البداية» "
            "لتحسين إجاباتك والمحاولة مجددًا."
        ),
        "btn_generate": "أنشئ البرومبت",
        "btn_restart": "إعادة من البداية",
        "btn_new": "أنشئ برومبت آخر",
        "btn_done": "تم",
        "summary_avoid": "تجنّب",
        "summary_empty": "- (لا إجابات بعد)",

        # -- questions -----------------------------------------------------
        "q_brand_name": (
            "ما هو الاسم الدقيق للعلامة التجارية؟\n\n"
            "اكتبه الآن - سيُحفظ تمامًا كما تكتبه، بنفس الحروف الكبيرة "
            "والمسافات وعلامات الترقيم، لأن البرومبت يعيد إنتاجها حرفًا "
            "بحرف. أو اضغط على الزر إذا كان الشعار بدون اسم."
        ),
        "opt_brand_name_skip": "تخطي - بدون اسم",
        "q_industry": (
            "في أي مجال تعمل علامتك التجارية؟\n\n"
            "اختر المجال الأقرب أولًا - ثم سأسألك عن تخصصك الدقيق، لأن "
            "المقهى والمطعم لا يشتركان في نفس لغة التصميم. إذا لم يناسبك "
            "شيء، اختر «أخرى» وصفها."
        ),
        "opt_industry_food": "طعام وشراب",
        "opt_industry_fashion": "أزياء وجمال",
        "opt_industry_tech": "تكنولوجيا وديجيتال",
        "opt_industry_media": "إعلام وإبداع",
        "opt_industry_education": "تعليم وكتب",
        "opt_industry_sports": "رياضة ولياقة",
        "opt_industry_services": "أعمال وخدمات",
        "opt_industry_gaming": "ألعاب ورياضة إلكترونية",
        "opt_industry_other": "أخرى (سأصفها)",
        "q_industry_food": (
            "طعام وشراب - ما هو تخصصك الدقيق؟\n\n"
            "لكل خيار شيفرته التصميمية الخاصة: المقهى دافئ ومريح، الوجبات "
            "السريعة جريئة وسريعة، المخبزة طعم بيتي. اختر ما يناسب نشاطك."
        ),
        "opt_industry_food_restaurant": "مطعم",
        "opt_industry_food_cafe": "مقهى (قهوة)",
        "opt_industry_food_fastfood": "وجبات سريعة",
        "opt_industry_food_bakery": "مخبزة وحلويات",
        "opt_industry_food_juice": "عصائر ومشروبات باردة",
        "opt_industry_food_other": "أخرى (سأصفها)",
        "q_industry_fashion": (
            "أزياء وجمال - ما هو تخصصك الدقيق؟\n\n"
            "علامة ملابس وصالون حلاقة ودار مجوهرات لا تتحدث بنفس اللغة "
            "البصرية. اختر تخصصك."
        ),
        "opt_industry_fashion_clothing": "علامة ملابس",
        "opt_industry_fashion_beauty": "جمال ومستحضرات تجميل",
        "opt_industry_fashion_barber": "حلاق وصالون حلاقة",
        "opt_industry_fashion_perfume": "عطور",
        "opt_industry_fashion_jewelry": "مجوهرات وإكسسوارات",
        "opt_industry_fashion_other": "أخرى (سأصفها)",
        "q_industry_tech": (
            "تكنولوجيا وديجيتال - ما هو تخصصك الدقيق؟\n\n"
            "الشركة الناشئة ومطوّر التطبيقات وشركة الأمن السيبراني لكل "
            "منهم روح مختلفة. اختر تخصصك."
        ),
        "opt_industry_tech_startup": "شركة ناشئة (ذكاء اصطناعي)",
        "opt_industry_tech_dev": "تطوير تطبيقات وبرمجيات",
        "opt_industry_tech_web": "وكالة ويب وخدمات رقمية",
        "opt_industry_tech_cyber": "معلوميات وأمن سيبراني",
        "opt_industry_tech_other": "أخرى (سأصفها)",
        "q_industry_media": (
            "إعلام وإبداع - ما هو تخصصك الدقيق؟\n\n"
            "التصوير والفيديو والتصميم الجرافيكي والسوشيال ميديا، لكل "
            "واحد مفرداته الخاصة في الأيقونات. اختر تخصصك."
        ),
        "opt_industry_media_photo": "تصوير فوتوغرافي",
        "opt_industry_media_video": "فيديو وتصوير",
        "opt_industry_media_design": "تصميم جرافيكي",
        "opt_industry_media_marketing": "تسويق وسوشيال ميديا",
        "opt_industry_media_other": "أخرى (سأصفها)",
        "q_industry_education": (
            "تعليم وكتب - ما هو تخصصك الدقيق؟\n\n"
            "المدرسة والمكتبة ومركز التكوين لا تجذب نفس الجمهور. اختر تخصصك."
        ),
        "opt_industry_education_school": "مدرسة ودروس مساعدة",
        "opt_industry_education_library": "مكتبة وبيع كتب",
        "opt_industry_education_training": "دورات وتكوين",
        "opt_industry_education_other": "أخرى (سأصفها)",
        "q_industry_sports": (
            "رياضة ولياقة - ما هو تخصصك الدقيق؟\n\n"
            "قاعة رياضية ونادٍ رياضي ومدرب شخصي يبنون هويات مختلفة جدًا. "
            "اختر تخصصك."
        ),
        "opt_industry_sports_gym": "قاعة رياضية ولياقة",
        "opt_industry_sports_club": "نادٍ وفريق رياضي",
        "opt_industry_sports_coach": "مدرب شخصي",
        "opt_industry_sports_other": "أخرى (سأصفها)",
        "q_industry_services": (
            "أعمال وخدمات - ما هو تخصصك الدقيق؟\n\n"
            "التوصيل والعقارات والبناء والتجارة، لكل واحد رموزه الخاصة. "
            "اختر تخصصك."
        ),
        "opt_industry_services_delivery": "توصيل ونقل",
        "opt_industry_services_realestate": "عقارات",
        "opt_industry_services_construction": "بناء وأشغال",
        "opt_industry_services_shop": "متجر وبيع أونلاين",
        "opt_industry_services_other": "أخرى (سأصفها)",
        "q_industry_gaming": (
            "ألعاب ورياضة إلكترونية - ما هو تخصصك الدقيق؟\n\n"
            "فريق إي سبورتس يحتاج شعارًا قويًا، واستوديو ألعاب يحتاج عالمًا "
            "مرحًا. اختر تخصصك."
        ),
        "opt_industry_gaming_team": "علامة قيمنق وفريق إي سبورتس",
        "opt_industry_gaming_studio": "استوديو تطوير ألعاب",
        "opt_industry_gaming_other": "أخرى (سأصفها)",
        "q_industry_text": (
            "صف نشاطك في كلمات قليلة - أضف كل ما تريدني أن أعرفه.\n\n"
            "بأي لغة: العربية، الفرنسية، الإنجليزية، الدارجة أو العربيزي "
            "(مثال: 'بوت لتحميل الكتب'، 'livraison de poulet grillé')."
        ),
        "q_category": (
            "ما نوع الشعار الذي تريده؟\n\n"
            "رمز = أيقونة وحدها. Lettermark = الأحرف الأولى منمّقة. "
            "Wordmark = الاسم نفسه كشعار. دمج = أيقونة + اسم. إمبريم = "
            "الاسم داخل شارة. إذا كان لديك شيء آخر، اختر «أخرى» وصفها."
        ),
        "opt_category_symbol": "رمز فقط (أيقونة)",
        "opt_category_lettermark": "الأحرف الأولى (lettermark)",
        "opt_category_wordmark": "اسم العلامة نصًا (wordmark)",
        "opt_category_combination": "رمز + اسم (دمج)",
        "opt_category_abstract": "شكل تجريدي",
        "opt_category_emblem": "شارة / إمبريم",
        "opt_category_auto": "اختر أنت لي",
        "opt_category_other": "أخرى (سأصفها)",
        "q_category_text": (
            "صف نوع الشعار الذي تريده بكلماتك - أضف كل ما تريد.\n\n"
            "مثال: 'درع مع أحروفي الأولى بداخله'."
        ),
        "q_motif": (
            "ماذا يجب أن يوحي الرمز؟\n\n"
            "هذه هي قلب الفكرة: الفكرة الرئيسية التي تُبنى منها الأيقونة. "
            "اختر اتجاهًا، أو دعني أختار بإبداع من مجالك."
        ),
        "opt_motif_object": "شيء من نشاطي",
        "opt_motif_letter": "حرفي الأول (كشكل)",
        "opt_motif_geometric": "أشكال هندسية بحتة",
        "opt_motif_nature": "طبيعة (ورقة، جبل، موجة...)",
        "opt_motif_premium": "رمز فاخر (تاج، نجمة...)",
        "opt_motif_auto": "اختر أنت",
        "opt_motif_other": "أخرى (سأصفها)",
        "q_motif_text": (
            "صف ماذا يجب أن يوحي الرمز - أضف كل ما تريد.\n\n"
            "مثال: 'أسد مدموج مع فنجان قهوة، دون رسم حيوان حقيقي'."
        ),
        "q_typography": (
            "هل يحتوي الشعار على نص؟\n\n"
            "الاسم = اسم العلامة كاملًا. الأحرف الأولى = مونوغرام. الاسم "
            "تحت الرمز = التوليفة الكلاسيكية."
        ),
        "opt_typography_none": "بدون نص نهائيًا",
        "opt_typography_name": "اسم العلامة",
        "opt_typography_initials": "الأحرف الأولى فقط",
        "opt_typography_name_under": "الاسم تحت الرمز",
        "opt_typography_auto": "اختر أنت",
        "q_font_style": (
            "ما طابع الحروف الذي تريده؟\n\n"
            "الحروف تحمل شخصية العلامة: حاد وعصري، كلاسيكي بأرجل (serif)، "
            "مستدير وودود، أو مكتوب بخط اليد."
        ),
        "opt_font_style_modern_sans": "عصري ونظيف",
        "opt_font_style_classic_serif": "كلاسيكي (serif)",
        "opt_font_style_rounded": "مستدير وودود",
        "opt_font_style_script": "خط يد / سكريبت",
        "opt_font_style_geometric": "هندسي ومينيمال",
        "opt_font_style_auto": "اختر أنت",
        "q_tagline": (
            "أضف شعارًا قصيرًا (slogan) تحت الاسم؟\n\n"
            "اكتب العبارة الدقيقة (60 حرفًا كحد أقصى) وستُعرض بحروف صغيرة "
            "تحت اسم العلامة - بنفس الكتابة حرفيًا. أو اضغط على الزر لشعار "
            "بدون عبارة."
        ),
        "opt_tagline_skip": "تخطي - بدون عبارة",
        "q_colors": (
            "ما لوحة الألوان التي تفضلها؟\n\n"
            "الألوان تحدد إحساس الشعار: الأزرق يطمئن، الذهبي يوحي بالفخامة، "
            "الأحمر يفتح الشهية. الشعار الاحترافي يبقى بين لون وثلاثة."
        ),
        "opt_colors_blue_white": "أزرق وأبيض",
        "opt_colors_green_white": "أخضر وأبيض",
        "opt_colors_black_gold": "أسود وذهبي",
        "opt_colors_red_white": "أحمر وأبيض",
        "opt_colors_dark_premium": "غامق وفاخر",
        "opt_colors_soft_pastel": "باستيل هادئة",
        "opt_colors_bold_vivid": "جريء وزاهي",
        "opt_colors_surprise": "فاجئني",
        "opt_colors_other": "أخرى (سأكتبها)",
        "q_colors_text": (
            "اكتب الألوان التي تريدها - أضف كل ما تريد.\n\n"
            "بأي لغة، مثل: 'أخضر وأبيض'، 'vert et or'، 'akhdar w abyad'."
        ),
        "q_style": (
            "ما الأسلوب البصري الذي يناسب علامتك؟\n\n"
            "فكّر فيه كـ«حقبة تصميم»: المينيمال خالد، المستقبلي يوحي "
            "بالتكنولوجيا، الفينتاج يوحي بالأصالة، واليدوي يوحي بالدفء."
        ),
        "opt_style_minimalist": "بسيط (مينيمال)",
        "opt_style_maximalist": "غني بالتفاصيل (ماكسيمال)",
        "opt_style_modern": "عصري",
        "opt_style_luxury": "فاخر",
        "opt_style_futuristic": "مستقبلي",
        "opt_style_vintage": "فينتاج / ريترو",
        "opt_style_handcrafted": "يدوي / طبيعي",
        "opt_style_auto": "اختر أنت",
        "opt_style_other": "أخرى (سأصفها)",
        "q_style_text": (
            "صف الأسلوب الذي تريده - أضف كل ما تريد.\n\n"
            "مثال: 'مثل لافتة صيدلية قديمة، لكن أنظف'."
        ),
        "q_audience": (
            "من جمهورك الأساسي؟\n\n"
            "نفس العلامة لا تخاطب المراهقين والعائلات والشركات بنفس الطريقة "
            "- التصميم يتكيف معهم. وإذا كان جمهورك شيئًا آخر، اختر «أخرى» "
            "وصفه."
        ),
        "opt_audience_young": "شباب وعصريين",
        "opt_audience_family": "عائلات",
        "opt_audience_business": "شركات ومهنيون",
        "opt_audience_premium": "زبائن راقون",
        "opt_audience_local": "مجتمع محلي",
        "opt_audience_broad": "قليلاً من كل شيء",
        "opt_audience_auto": "اختر أنت",
        "opt_audience_other": "أخرى (سأصفها)",
        "q_audience_text": (
            "صف جمهورك بكلماتك - أضف كل ما تريد.\n\n"
            "مثال: 'طلاب الجامعة', 'des etudiants'."
        ),
        "q_personality": (
            "لو كانت علامتك شخصًا، ما طابعه؟\n\n"
            "هذا يحدد موقف كل منحنى وكل خط في الشعار."
        ),
        "opt_personality_bold": "قوي وجريء",
        "opt_personality_calm": "هادئ وموثوق",
        "opt_personality_playful": "مرح وودود",
        "opt_personality_elegant": "أنيق وراقٍ",
        "opt_personality_innovative": "مبتكر وعصري",
        "opt_personality_auto": "اختر أنت",
        "opt_personality_other": "أخرى (سأصفها)",
        "q_personality_text": (
            "صف شخصية علامتك بكلماتك - أضف كل ما تريد.\n\n"
            "مثال: 'جاد في العمل، لكن مع غمزة صغيرة'."
        ),
        "q_dimension": (
            "الرسم: مسطح أم ثلاثي الأبعاد؟\n\n"
            "الفيكتور المسطح هو المعيار الخالد للشعارات؛ ثلاثي الأبعاد يبدو "
            "فاخرًا لكنه يقدّم أسرع. عند الشك، اختر مسطحًا أو 3D خفيفًا."
        ),
        "opt_dimension_flat": "فيكتور مسطح (2D)",
        "opt_dimension_slight_3d": "ثلاثي الأبعاد خفيف",
        "opt_dimension_full_3d": "ثلاثي أبعاد كامل وفاخر",
        "opt_dimension_auto": "اختر أنت",
        "q_background": (
            "ما الخلفية التي تفضلها؟\n\n"
            "الأبيض النقي هو الأأمن مع مولدات الصور؛ الخلفيات الغامقة تُبرز "
            "الذهبي؛ «معزول» يعني بدون خلفية ظاهرة إطلاقًا (جاهز "
            "للشفافية)."
        ),
        "opt_background_white": "أبيض نقي",
        "opt_background_dark": "غامقة",
        "opt_background_isolated": "معزول (بدون خلفية ظاهرة)",
        "opt_background_auto": "اختر أنت",
        "opt_background_other": "أخرى (سأصفها)",
        "q_background_text": (
            "صف الخلفية التي تريدها - أضف كل ما تريد.\n\n"
            "مثال: 'خلفية خضراء غامقة' أو 'fond bleu nuit'."
        ),
        "q_usage": (
            "أين سيُستخدم الشعار أكثر؟\n\n"
            "هذا يحدد التكوين والنسب والهوامش الآمنة: صورة البروفايل في "
            "تيليغرام يجب أن تبقى مقروءة في الحجم الصغير جدًا، أما ترويسة "
            "الموقع فتتنفس أفقيًا."
        ),
        "opt_usage_telegram_avatar": "صورة بروفايل تيليغرام (مربع)",
        "opt_usage_website": "ترويسة موقع إلكتروني",
        "opt_usage_social": "منشورات سوشيال ميديا",
        "opt_usage_print": "طباعة / تغليف",
        "opt_usage_everywhere": "في كل مكان",
        "opt_usage_other": "أخرى (سأصفها)",
        "q_usage_text": (
            "أين سيُستخدم الشعار؟ صِف ذلك - أضف كل ما تريد.\n\n"
            "مثال: 'على شاحنات التوصيل وواجهة المحل'."
        ),
        "q_exclusions": (
            "هل هناك شيء تريد تجنبه؟\n\n"
            "اضغط على العنصر لتفعيله أو إلغائه، ثم اضغط «تم». القيود "
            "الإلزامية (بدون بشر، بدون حيوانات، بدون وجوه) تُطبق دائمًا "
            "تلقائيًا، سواء اخترت شيئًا هنا أم لا."
        ),
        "opt_exclusions_neon": "تأثيرات نيون",
        "opt_exclusions_gradients": "تدرجات لونية",
        "opt_exclusions_shadows": "ظلال",
        "opt_exclusions_decorations": "زخارف زائدة",
        "opt_exclusions_complex": "تفاصيل معقدة",

        # -- summary labels --------------------------------------------------
        "sum_brand_name": "اسم العلامة",
        "sum_industry": "المجال",
        "sum_industry_leaf": "التخصص",
        "sum_industry_text": "النشاط",
        "sum_category": "نوع الشعار",
        "sum_category_text": "النوع (بكلماتك)",
        "sum_motif": "فكرة الرمز",
        "sum_motif_text": "فكرة الرمز (بكلماتك)",
        "sum_typography": "النص في الشعار",
        "sum_font_style": "طابع الحروف",
        "sum_tagline": "العبارة (slogan)",
        "sum_colors": "الألوان",
        "sum_colors_text": "الألوان (مكتوبة)",
        "sum_style": "الأسلوب",
        "sum_style_text": "الأسلوب (بكلماتك)",
        "sum_audience": "الجمهور",
        "sum_audience_text": "الجمهور (بكلماتك)",
        "sum_personality": "الطابع",
        "sum_personality_text": "الطابع (بكلماتك)",
        "sum_dimension": "الرسم",
        "sum_background": "الخلفية",
        "sum_background_text": "الخلفية (بكلماتك)",
        "sum_usage": "يُستخدم في",
        "sum_usage_text": "الاستخدام (بكلماتك)",

        # -- الخطوة 7: المساعدة، الدعم، الأرصدة، الدعوات، القناة، التبرعات ---
        "help_text": (
            "<b>TASMEEM AI - المساعدة</b>\n\n"
            "أحوّل إجاباتك إلى برومبت احترافي جاهز:\n"
            "🎨 برومبت <b>شعار</b> لتوليد الصور\n"
            "📢 برومبت <b>منشور إعلاني (سوشيال ميديا)</b> لمنتجك أو خدمتك أو "
            "صفحتك\n\n"
            "<b>كيف يعمل</b>\n"
            "1. أرسل /start واختر الوضع (شعار أو إعلان)\n"
            "2. أجب على الأسئلة السريعة - أزرار أو كتابة، بأي لغة\n"
            "3. انسخ البرومبت الجاهز والصقه في مولّد الصور المفضل لديك\n"
            "4. إذا كان لديك شعار، الصق صورة الشعار مع البرومبت\n\n"
            "<b>الأوامر</b>\n"
            "/start - فتح القائمة\n"
            "/credits - رصيدك ورابط الدعوة\n"
            "/lang - تغيير لغة الواجهة\n"
            "/donate - دعم البوت بالنجوم\n"
            "/support - التواصل مع الدعم\n"
            "/cancel - إيقاف الأسئلة\n\n"
            "<b>الأرصدة</b>\n"
            "1 برومبت = 1 رصيد. تُضاف +{refill} أرصدة مجانية كل يوم، وتربح "
            "+{bonus} رصيد عن كل صديق يفتح البوت عبر رابطك الخاص.\n\n"
            "الدعم: {support}"
        ),
        "support_text": (
            "تحتاج مساعدة بشريّة؟ راسل المطوّر مباشرة وسيجيبك في أسرع وقت:\n{support}"
        ),
        "menu_credits": "💳 الرصيد: <b>{credits}</b> (+{refill} مجانية كل يوم)",
        "credits_text": (
            "💳 <b>رصيدك: {credits}</b>\n\n"
            "✨ تُضاف +{refill} أرصدة مجانية تلقائيًا كل يوم.\n"
            "🎁 ادعُ أصدقاءك: +{bonus} رصيد عن كل صديق يفتح البوت عبر رابطك "
            "الخاص:\n{link}\n\n"
            "⚙️ كل برومبت مولّد = 1 رصيد."
        ),
        "not_enough": (
            "😢 الرصيد غير كافٍ.\n\n"
            "ثمن البرومبت المولّد {cost} رصيد ورصيدك الحالي {credits}.\n\n"
            "✨ تُضاف +{refill} أرصدة مجانية كل يوم.\n"
            "🎁 أو ادعُ أصدقاءك: +{bonus} رصيد لكل صديق.\n"
            "🤍 أو ادعم البوت بتبرّع في الأسفل."
        ),
        "ref_bonus_notify": (
            "🎁 <b>+{bonus} أرصدة!</b>\n"
            "صديق فتح TASMEEM AI للتو عبر رابطك."
        ),
        "fs_required": (
            "🔒 <b>خطوة سريعة قبل البدء</b>\n\n"
            "TASMEEM AI مجاني - الطلب الوحيد هو الانضمام إلى قناتنا. هناك "
            "تُنشر التحديثات والنصائح والهدايا المجانية.\n\n"
            "انضم من هنا: {channel_link}\n\n"
            "انضممت بالفعل؟ اضغط على الزر في الأسفل."
        ),
        "fs_still": (
            "يجب الانضمام إلى القناة أولًا. اضغط على زر الانضمام ثم "
            "تحقق مرة أخرى."
        ),
        "btn_join": "📢 الانضمام إلى القناة",
        "btn_check": "✅ انضممت - تحقق",
        "btn_donate": "🤍 دعم البوت",
        "btn_support": "🆘 الدعم",
        "donate_intro": (
            "🤍 <b>دعم TASMEEM AI</b>\n\n"
            "البوت مجاني وسيبقى مجانيًا. إن كان مفيدًا لك، تبرّع صغير بالنجوم "
            "يجعله يعمل ويتطور.\n\n"
            "اختر المبلغ:"
        ),
        "donate_desc": "تبرّع لدعم TASMEEM AI",
        "donate_thanks": (
            "🤍 <b>شكرًا على تبرّعك بـ {stars} نجمة!</b>\n"
            "دعمك يبقي TASMEEM AI مجانيًا ومتطورًا."
        ),
        "out_credits": "💳 الرصيد المتبقي: <b>{credits}</b> (+{refill} مجانية غدًا)",
        # -- Step 8: ads mode, support tag, admin (appended) -----
        "btn_mode_logo": '🎨 برومبت شعار',
        "btn_mode_ads": '📢 منشور إعلاني (سوشيال ميديا)',
        "prompt_intro_ads": 'هذا هو برومبتك الإعلاني الاحترافي.\nاضغط على كتلة البرومبت لنسخها، ثم الصقها في مولّد الصور المفضل لديك - مع صورة شعارك إن كان لديك.',
        "ads_howto": '📋 <b>كيف تستعمله:</b>\n1. اضغط على كتلة البرومبت في الأعلى لنسخها، ثم الصقها في نموذج الصور الذكي.\n2. عندك شعار؟ <b>الصق/أرفق صورة الشعار مع البرومبت</b> (في نفس الرسالة) - وسيدمجه النموذج في التصميم.\n3. اسم علامتك و@معرّف صفحتك مكتوبان أصلًا داخل البرومبت - لا حاجة لإعادة كتابتهما.\n4. إذا لم يكن النص المولّد مثاليًا، ولّد الصورة ثم أضف كلماتك الدقيقة في Canva أو ما يشبهها.',
        "ads_howto_nologo": '💡 نصيحة: ليس لديك شعار بعد - أنشئه أولًا مع وضع 🎨 الشعار في هذا البوت، ثم أعد تصميم إعلانك.',
        "out_support": '<b>صُنع بـ 🤍 من TASMEEM AI</b> - لأي طلب خاص أو أي مساعدة، راسل المطوّر: {support}',
        "sum_ad_leaf": 'التفاصيل',
        "q_ad_brand_name": 'ما هو الاسم الدقيق لعلامتك أو صفحتك لهذا المنشور؟\n\nاكتبه الآن - سيُحفظ تمامًا كما تكتبه (الحروف الكبيرة، المسافات، علامات الترقيم) ويُكتب في البرومبت حرفًا بحرف. أو اضغط الزر إذا كنت تريد التصميم بدون اسم.',
        "opt_ad_brand_name_skip": 'تخطي - بدون اسم',
        "q_ad_username": 'ما هو @معرّف علامتك أو صفحتك؟\n\nمثال: @mybrand - سيُضاف إلى البرومبت ليضعها نموذج الذكاء الاصطناعي على التصميم (أو يمكنك لصقه مع البرومبت). لا يوجد معرّف؟ اضغط الزر.',
        "opt_ad_username_skip": 'تخطي - بدون معرّف',
        "q_ad_goal": 'ما هدف هذا المنشور؟\n\nالهدف يحدد التصميم كله: التخفيض السريع يحتاج إلحاحًا ومنطقة سعر واضحة، والسحوبة تحتاج حماسًا، والإعلان يحتاج وضوحًا. اختر الهدف الأقرب - ثم سأسألك عن النوع الدقيق.',
        "opt_ad_goal_sales": 'بيع والترويج',
        "opt_ad_goal_growth": 'تنمية صفحتي',
        "opt_ad_goal_announce": 'الإعلان عن شيء',
        "opt_ad_goal_traffic": 'جلب زبائن وطلبات',
        "opt_ad_goal_other": 'أخرى (سأصفها)',
        "q_ad_goal_sales": 'بيع والترويج - ما الهدف بالضبط؟',
        "opt_ad_goal_sales_product": 'الترويج لمنتج',
        "opt_ad_goal_sales_discount": 'تخفيضات / كود خصم',
        "opt_ad_goal_sales_new": 'منتج جديد / إطلاق',
        "opt_ad_goal_sales_flash": 'عرض سريع / لفترة محدودة',
        "opt_ad_goal_sales_other": 'أخرى (سأصفها)',
        "q_ad_goal_growth": 'تنمية صفحتي - ما الهدف بالضبط؟',
        "opt_ad_goal_growth_giveaway": 'سحوبة (giveaway)',
        "opt_ad_goal_growth_contest": 'مسابقة / تحدٍّ',
        "opt_ad_goal_growth_follow": 'زيادة المتابعين',
        "opt_ad_goal_growth_engage": 'منشور تفاعل (سؤال / استفتاء)',
        "opt_ad_goal_growth_other": 'أخرى (سأصفها)',
        "q_ad_goal_announce": 'الإعلان عن شيء - ما الهدف بالضبط؟',
        "opt_ad_goal_announce_opening": 'افتتاح كبير',
        "opt_ad_goal_announce_event": 'حدث / دعوة',
        "opt_ad_goal_announce_rebrand": 'هوية جديدة',
        "opt_ad_goal_announce_info": 'إعلان عام',
        "opt_ad_goal_announce_other": 'أخرى (سأصفها)',
        "q_ad_goal_traffic": 'جلب زبائن وطلبات - ما الهدف بالضبط؟',
        "opt_ad_goal_traffic_booking": 'حجوزات / مواعيد',
        "opt_ad_goal_traffic_order": 'طلبات مباشرة / قائمة طعام',
        "opt_ad_goal_traffic_visit": 'زيارات المتجر / الموقع',
        "opt_ad_goal_traffic_download": 'تحميل تطبيق / بوت',
        "opt_ad_goal_traffic_other": 'أخرى (سأصفها)',
        "q_ad_goal_text": "صف هدف المنشور بكلماتك - أضف كل ما تريد.\n\nمثال: 'تخفيضات الصيف -30% على كل المتجر', 'SOLDES D'ÉTÉ', 'عرض رمضان'.",
        "q_ad_platform": 'أين سيُنشر هذا المنشور؟\n\nلكل منصة أجواؤها: إنستغرام تحب الجمالية النظيفة، وتيك توك يحتاج تباينًا قويًا، ومنشور تيليغرام يبقى مقروءًا على الشاشات الصغيرة. لا شيء يناسبك؟ اختر «أخرى».',
        "opt_ad_platform_instagram": 'إنستغرام',
        "opt_ad_platform_facebook": 'فيسبوك',
        "opt_ad_platform_tiktok": 'تيك توك',
        "opt_ad_platform_telegram": 'تيليغرام',
        "opt_ad_platform_whatsapp": 'حالة واتساب',
        "opt_ad_platform_other": 'أخرى (سأصفها)',
        "q_ad_platform_text": "على أي منصة أو مكان؟ صفه - أضف كل ما تريد.\n\nمثال: 'سناب شات', 'صفحة لينكد إن', 'فلاير مطبوع'.",
        "q_ad_format": 'أي صيغة تحتاج؟\n\nالمربع هو المنشور الكلاسيكي، و9:16 يملأ الستوري والريلز بكامل الشاشة، و4:5 يأخذ مساحة أكبر في الصفحة، و16:9 يناسب البانر العريض أو غلاف الصفحة.',
        "opt_ad_format_square": 'منشور مربع (1:1)',
        "opt_ad_format_story": 'ستوري / ريلز (9:16)',
        "opt_ad_format_portrait": 'منشور عمودي (4:5)',
        "opt_ad_format_banner": 'بانر عريض (16:9)',
        "opt_ad_format_cover": 'غلاف صفحة',
        "opt_ad_format_auto": 'أنت تقرر',
        "opt_ad_format_other": 'أخرى (سأصفها)',
        "q_ad_format_text": "صف الصيغة التي تريدها - أضف كل ما تريد.\n\nمثال: 'إطاري ستوري', 'بانر لقناتي على يوتيوب'.",
        "q_ad_offer": "ما الذي تروّج له بالضبط؟\n\nصف المنتج أو الخدمة أو السعر أو التخفيض أو التاريخ أو المكان - كل ما يجب أن يُظهره التصميم بصدق (مثال: 'بيتزا وسط 2000 دج مع توصيل مجاني'). أو اضغط الزر لإبقائه عامًا.",
        "opt_ad_offer_skip": 'تخطي - بدون تفاصيل',
        "q_ad_cta": 'أي دعوة لاتخاذ إجراء (CTA) تظهر على التصميم؟\n\nالـCTA هو الزر الصغير أو الشريط الذي يخبر الناس بما يفعله تاليًا: اشترِ، احجز، راسلنا، تابعنا...',
        "opt_ad_cta_shop_now": 'اشترِ الآن',
        "opt_ad_cta_order_now": 'اطلب الآن',
        "opt_ad_cta_book_now": 'احجز الآن',
        "opt_ad_cta_learn_more": 'اعرف المزيد',
        "opt_ad_cta_dm": 'راسلنا',
        "opt_ad_cta_call": 'اتصل الآن',
        "opt_ad_cta_whatsapp": 'واتساب',
        "opt_ad_cta_follow": 'تابعنا',
        "opt_ad_cta_visit": 'زورونا',
        "opt_ad_cta_auto": 'أنت تقرر',
        "opt_ad_cta_other": 'أخرى (سأصفها)',
        "q_ad_cta_text": "اكتب نص دعوة الإجراء بالضبط - أضف كل ما تريد.\n\nمثال: 'احجز مقعدك', 'Commandez ici', 'Get yours today'.",
        "q_ad_lang_text": 'أي لغة للنصوص على التصميم؟\n\nنموذج الذكاء الاصطناعي سيكتب الكلمات الحرفية: اختيار اللغة يمنع خلط الحروف. «بدون نص» يعطيك تصميمًا نظيفًا وتضيف الكلمات بنفسك في Canva أو ما يشبهها.',
        "opt_ad_lang_text_en": 'الإنجليزية',
        "opt_ad_lang_text_fr": 'الفرنسية',
        "opt_ad_lang_text_ar": 'العربية',
        "opt_ad_lang_text_ar_en": 'عربية + إنجليزية',
        "opt_ad_lang_text_fr_en": 'فرنسية + إنجليزية',
        "opt_ad_lang_text_none": 'بدون نص على التصميم',
        "opt_ad_lang_text_other": 'أخرى (سأصفها)',
        "q_ad_lang_text_text": "أي لغة أو لغات للنص على التصميم؟ صِفها - أضف كل ما تريد.\n\nمثال: 'عربية دارجة مع سعر صغير بالإنجليزية'.",
        "q_ad_headline": 'ما نص العنوان الدقيق الذي سيُكتب على التصميم؟\n\nاكتبه تمامًا كما يجب أن يظهر (80 حرفًا كحد أقصى) - الإملاء والحروف الكبيرة وعلامات الترقيم تُحفظ حرفًا بحرف. أو اضغط الزر وأنا أختار لك عنوانًا قصيرًا قويًا.',
        "opt_ad_headline_skip": 'أنت تقرر لي',
        "q_ad_visual": 'ماذا يُظهر التصميم؟\n\nهذا هو قلب الإعلان: منتج بمفرده، أشخاص يستعملونه، ملصق جرافيكي، أو لقطة طعام شهية. اختر العائلة أولًا - ثم سأسألك عن المشهد الدقيق.',
        "opt_ad_visual_product": 'إبراز المنتج',
        "opt_ad_visual_people": 'أشخاص ولايف ستايل',
        "opt_ad_visual_graphic": 'جرافيك وتايبوغرافي',
        "opt_ad_visual_food": 'لقطات طعام وشراب',
        "opt_ad_visual_auto": 'أنت تقرر',
        "opt_ad_visual_other": 'أخرى (سأصفها)',
        "q_ad_visual_product": 'إبراز المنتج - أي مشهد يناسبك أكثر؟',
        "opt_ad_visual_product_studio": 'لقطة استوديو نظيفة',
        "opt_ad_visual_product_lifestyle": 'مشهد لايف ستايل (استعمال حقيقي)',
        "opt_ad_visual_product_detail": 'لقطة مقربة على التفاصيل',
        "opt_ad_visual_product_flatlay": 'فلات لاي من الأعلى',
        "opt_ad_visual_product_other": 'أخرى (سأصفها)',
        "q_ad_visual_people": 'أشخاص ولايف ستايل - أي مشهد يناسبك أكثر؟',
        "opt_ad_visual_people_model": 'عارض يقدّم المنتج',
        "opt_ad_visual_people_hands": 'أيادٍ تمسك المنتج',
        "opt_ad_visual_people_team": 'الفريق / الطاقم',
        "opt_ad_visual_people_crowd": 'حشد في حدث',
        "opt_ad_visual_people_other": 'أخرى (سأصفها)',
        "q_ad_visual_graphic": 'جرافيك وتايبوغرافي - أي مشهد يناسبك أكثر؟',
        "opt_ad_visual_graphic_typographic": 'ملصق تايبوغرافي جسور',
        "opt_ad_visual_graphic_illustration": 'رسم توضيحي مخصص',
        "opt_ad_visual_graphic_shapes": 'أشكال مجردة وتدرجات',
        "opt_ad_visual_graphic_pattern": 'نقشة بصرية متكررة',
        "opt_ad_visual_graphic_other": 'أخرى (سأصفها)',
        "q_ad_visual_food": 'لقطات طعام وشراب - أي مشهد يناسبك أكثر؟',
        "opt_ad_visual_food_dish": 'طبق مُعد للتقديم',
        "opt_ad_visual_food_drink": 'لقطة شراب / مشروب',
        "opt_ad_visual_food_ingredients": 'مكونات طازجة',
        "opt_ad_visual_food_other": 'أخرى (سأصفها)',
        "q_ad_visual_text": "صف ما يجب أن يُظهره التصميم - أضف كل ما تريد.\n\nمثال: 'حذائي الأزرق يطفو مع رذاذ ألوان', 'une boîte de chocolats ouverte', 'علبة شوكولاتة مفتوحة'.",
        "q_ad_logo": 'هل لديك شعار لوضعه على التصميم؟\n\nإن نعم، في النهاية سأطلب منك لصق صورة شعارك مع البرومبت في نموذج الذكاء الاصطناعي - هكذا يُدمج بشكل صحيح. وإن لم يكن لديك شعار بعد، يمكنك إنشاؤه أولًا مع وضع الشعار في هذا البوت.',
        "opt_ad_logo_yes": 'نعم - سأرفقه',
        "opt_ad_logo_no": 'لا شعار بعد',
        "opt_ad_logo_name_only": 'استخدم الاسم كعلامة',
        "opt_ad_logo_auto": 'أنت تقرر',
        # -- Step 8: summary display names -------------------------------
        "sum_ad_brand_name": 'اسم العلامة / الصفحة',
        "sum_ad_username": 'معرّف الصفحة',
        "sum_ad_goal": 'هدف المنشور',
        "sum_ad_goal_text": 'الهدف (بكلماتك)',
        "sum_ad_platform": 'المنصة',
        "sum_ad_platform_text": 'المنصة (بكلماتك)',
        "sum_ad_format": 'الصيغة',
        "sum_ad_format_text": 'الصيغة (بكلماتك)',
        "sum_ad_offer": 'العرض',
        "sum_ad_cta": 'دعوة الإجراء',
        "sum_ad_cta_text": 'دعوة الإجراء (بكلماتك)',
        "sum_ad_lang_text": 'لغة النص',
        "sum_ad_lang_text_text": 'لغة النص (بكلماتك)',
        "sum_ad_headline": 'العنوان',
        "sum_ad_visual": 'مشهد التصميم',
        "sum_ad_visual_text": 'التصميم (بكلماتك)',
        "sum_ad_logo": 'الشعار',
    },
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def get(lang: str, key: str) -> Optional[str]:
    """Exact lookup, no fallback. None when missing."""
    return STRINGS.get(lang, {}).get(key)


def t(lang: str, key: str, **kwargs) -> str:
    """Translate with English fallback, then the key itself."""
    template = get(lang, key)
    if template is None:
        template = get(DEFAULT_LANG, key)
    if template is None:
        return key
    if kwargs:
        return template.format(**kwargs)
    return template


def all_keys() -> set:
    """Union of all keys across languages."""
    keys = set()
    for table in STRINGS.values():
        keys.update(table.keys())
    return keys
