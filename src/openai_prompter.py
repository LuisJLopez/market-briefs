"""
openai_prompter.py

Prompt architecture (based on OpenAI best practices):
  - System message:  stable persona + hard rules + banned phrases.
  - User message:    session-specific description + 3 tailored few-shot examples.

Each section has its own three examples so the model learns the correct tone,
content focus, and format for THAT specific time slot — not a generic tweet.
Few-shot examples are more effective than prose instructions for controlling
style, so every rule in the system prompt is also reinforced by example.

Temperature 0.3: consistent quality without sounding robotic.
Model: configurable via OPENAI_MODEL env var (default: gpt-4o).
"""

import config
from openai import OpenAI

logger = config.logger

# ---------------------------------------------------------------------------
# System prompt — persona, hard constraints, and banned phrases.
# Stable across all sessions; only the user message changes per session.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a sharp financial market analyst with a large following on X (Twitter).
You post brief, high-signal market commentary — direct, factual, opinionated, and human.

Hard rules — follow every one precisely:
1. Output exactly one tweet and nothing else. No label, no preamble, no explanation.
2. Maximum 280 characters (Twitter counts supplementary Unicode chars as 2 — keep well under).
3. Use 𝗺𝗮𝘁𝗵𝗲𝗺𝗮𝘁𝗶𝗰𝗮𝗹 𝘀𝗮𝗻𝘀-𝘀𝗲𝗿𝗶𝗳 𝗯𝗼𝗹𝗱 unicode to highlight 2–3 key terms or figures \
(the same style used in the examples). Never use markdown **bold** or *italics*.
4. 1–2 emojis maximum. Purposeful and professional — never stacked, never crypto-bro.
5. At most 1 hashtag.
6. Prefix every stock or index ticker with $ (e.g. $SPY, $NVDA, $FTSE).
7. No double-quote characters anywhere in the tweet.
8. Do not mention today's date or any specific date.
9. Do not use fabricated specific numbers (prices, % moves) unless they are from \
your training knowledge. Speak in directional terms if unsure of exact figures.

Banned phrases — these make the account sound like a bot. Never use them:
"Stay tuned", "stay invested", "stay sharp", "stay focused", "stay informed", "stay vigilant",
"stay ahead of the curve", "stay profitable", "keep an eye on", "keep tabs on",
"folks", "traders!", "remember:", "don't miss", "more updates", "stay tuned for more".
"""

# ---------------------------------------------------------------------------
# Session prompts — each section has a description + 3 tailored examples.
# Examples are the most important part: they define tone, structure, and
# content focus for each specific time slot.
# ---------------------------------------------------------------------------

_SESSIONS: dict[str, dict] = {

    "us_pre_open": {
        "description": (
            "US equity pre-market: futures direction, key levels, and the "
            "one macro catalyst that will drive the open today."
        ),
        "examples": [
            "𝗙𝘂𝘁𝘂𝗿𝗲𝘀 flat ahead of the open. $SPY holding 530, $QQQ the laggard. "
            "𝗖𝗣𝗜 at 08:30 is the swing point — a hot print kills the rate-cut trade. "
            "First 15 minutes will tell you everything. 📊 #markets",

            "Pre-market: $SPY +0.3%, $QQQ leading. 𝗡𝘃𝗶𝗱𝗶𝗮 up again in thin volume. "
            "𝗙𝗲𝗱 𝗿𝗵𝗲𝘁𝗼𝗿𝗶𝗰 at 09:00 is the risk — one hawkish line flips this fast. "
            "Cautiously bullish into the open. 📈",

            "𝗘𝘂𝗿𝗼𝗽𝗲 sold off hard this morning and US futures are following. "
            "$SPY -0.4% pre-market. 𝗕𝗼𝗻𝗱 𝘆𝗶𝗲𝗹𝗱𝘀 pushing higher again — dollar with it. "
            "Gap down likely. Watch how fast buyers step in. 📉",
        ],
    },

    "us_post_close": {
        "description": (
            "US equity post-close: how the session closed, the standout mover, "
            "and what the price action signals going into tomorrow."
        ),
        "examples": [
            "𝗦&𝗣 closed +0.6%, third straight green session. Tech carried the load — "
            "$NVDA and $MSFT hit fresh highs. 𝗕𝗼𝗻𝗱 𝘆𝗶𝗲𝗹𝗱𝘀 pulled back from the highs. "
            "That's what gave equities the room. 📈",

            "Ugly close. $SPY reversed off the open and faded all day. "
            "𝗖𝗼𝗻𝘀𝘂𝗺𝗲𝗿 𝗱𝗶𝘀𝗰𝗿𝗲𝘁𝗶𝗼𝗻𝗮𝗿𝘆 the worst sector — weak guidance crushed sentiment. "
            "𝗩𝗜𝗫 ticked back up. Caution warranted tomorrow. 📉",

            "Mixed session but the undercurrent matters: $IWM outperformed $SPY. "
            "𝗦𝗺𝗮𝗹𝗹 𝗰𝗮𝗽 𝗿𝗼𝘁𝗮𝘁𝗶𝗼𝗻 is real. That's a healthy sign — breadth expanding, "
            "not just the Mag 7 carrying the index. 👀 #markets",
        ],
    },

    "uk_pre_open": {
        "description": (
            "UK equity pre-open: Wall St overnight close, Asian session direction, "
            "and the macro or data catalyst FTSE traders are watching today."
        ),
        "examples": [
            "𝗪𝗮𝗹𝗹 𝗦𝘁 closed +0.7% overnight — tech led. Asia followed through positively. "
            "FTSE futures pointing green. Watch GBP/USD — sterling's been range-bound "
            "and any break moves the 𝗺𝗶𝗻𝗲𝗿𝘀 fast. 📊",

            "US sold off into yesterday's close and 𝗔𝘀𝗶𝗮 couldn't shrug it off. "
            "FTSE futures -0.3% pre-market. 𝗢𝗶𝗹 up overnight — energy names the one bright spot. "
            "BOE speakers at 10:00. Expect a choppy open. 📉 #markets",

            "𝗔𝘀𝗶𝗮 mixed, Japan outperforming on yen weakness. FTSE likely to open flat. "
            "𝗨𝗞 𝗖𝗣𝗜 data at 07:00 is the catalyst — hotter than expected means BOE holds "
            "longer and REITs get hit. Know what you own before the print. 📈",
        ],
    },

    "uk_close": {
        "description": (
            "UK equity close: how the FTSE ended the session, the leading sector or mover, "
            "and the takeaway for tonight's Wall St session."
        ),
        "examples": [
            "𝗙𝗧𝗦𝗘 𝟭𝟬𝟬 closed green — miners led after iron ore bounced. $AAL and $GLEN "
            "both up over 2%. 𝗚𝗕𝗣/𝗨𝗦𝗗 held the 1.27 level all session. "
            "Risk mood is holding. Watch Wall St for confirmation tonight. 📈 #markets",

            "𝗙𝗧𝗦𝗘 gave back the morning gains into the close. "
            "𝗙𝗶𝗻𝗮𝗻𝗰𝗶𝗮𝗹𝘀 dragged — NIM concerns hitting $BARC and $LLOY. "
            "Housebuilders the exception, catching a bid on softer mortgage data. "
            "Sterling +0.4% a quiet tailwind for importers. 👀",

            "Flat session on the 𝗙𝗧𝗦𝗘. Defensives outperformed cyclicals — "
            "late-cycle rotation showing up again. $AZN the standout. "
            "𝗪𝗮𝗹𝗹 𝗦𝘁 open in 90 mins will be the real test of whether this holds. 📊",
        ],
    },

    "liquidity": {
        "description": (
            "Global liquidity update: Fed balance sheet movement, M2 money supply trend, "
            "and the implication for equity risk appetite. The thesis: rising Fed liquidity "
            "is the structural bid under markets."
        ),
        "examples": [
            "𝗙𝗲𝗱 balance sheet expanded again this week. 𝗠𝟮 growing at 3.9% YoY. "
            "The liquidity tap is open — historically that is the floor under equities. "
            "This is why dips keep getting bought. Don't fight the flow. 💧 #macro",

            "𝗚𝗹𝗼𝗯𝗮𝗹 𝗠𝟮 accelerating — ECB and Fed both net adding liquidity this month. "
            "Rate cuts aren't even needed when the 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝘀𝗵𝗲𝗲𝘁 is expanding. "
            "Risk assets have a structural bid. That's the macro reality right now. 💧",

            "𝗠𝟮 growth rate ticking down slightly — still positive but decelerating. "
            "The rate of change is what matters here, not the level. "
            "𝗘𝗾𝘂𝗶𝘁𝘆 𝗿𝗶𝘀𝗸 stays supported but the liquidity tailwind is easing. "
            "Worth monitoring. 📊 #macro",
        ],
    },

    "gold": {
        "description": (
            "Gold market: current price action and sentiment, and the macro driver "
            "(real yields, dollar, central bank buying, geopolitics) behind today's move."
        ),
        "examples": [
            "$𝗚𝗢𝗟𝗗 pushing higher. 𝗥𝗲𝗮𝗹 𝘆𝗶𝗲𝗹𝗱𝘀 ticked down, dollar softening — "
            "the two inputs that matter most for gold aligned today. "
            "Momentum is constructive. $3,100 held all week. 🏅",

            "𝗚𝗼𝗹𝗱 flat despite a weaker dollar today — that is actually a warning sign. "
            "When it can't rally on dollar weakness, distribution is likely. "
            "𝗖𝗲𝗻𝘁𝗿𝗮𝗹 𝗯𝗮𝗻𝗸 buying provides a floor but the momentum has stalled. 👀 #gold",

            "$𝗚𝗢𝗟𝗗 breaking out after weeks of consolidation. This isn't retail — "
            "it's 𝗰𝗲𝗻𝘁𝗿𝗮𝗹 𝗯𝗮𝗻𝗸 accumulation plus a geopolitical premium. "
            "New highs look likely if $3,250 holds as support. 🏅",
        ],
    },

    "nbis": {
        "description": (
            "NBIS (Nebius Group) and other stocks being accumulated by major institutions "
            "like NVIDIA — price action, thesis, and current market sentiment around them."
        ),
        "examples": [
            "$𝗡𝗕𝗜𝗦 quietly building. 𝗡𝗩𝗜𝗗𝗜𝗔-backed AI infrastructure play "
            "with a clear European growth runway. While $NVDA gets the headlines, "
            "$NBIS is where serious money is positioning. 📈",

            "𝗜𝗻𝘀𝘁𝗶𝘁𝘂𝘁𝗶𝗼𝗻𝗮𝗹 𝗮𝗰𝗰𝘂𝗺𝘂𝗹𝗮𝘁𝗶𝗼𝗻 in $NBIS continues. "
            "NVIDIA's stake signals conviction in the AI cloud buildout thesis. "
            "This is a 𝗹𝗼𝗻𝗴-𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 bet — not a trade. 📊 #AI",

            "Following 𝗡𝗩𝗜𝗗𝗜𝗔's money: $𝗡𝗕𝗜𝗦 is the pick-and-shovel "
            "AI infrastructure name worth understanding. Growing revenue, "
            "NVIDIA investment, EU market focus. Still small cap — but the thesis is intact. 👀",
        ],
    },

    "market_sentiment": {
        "description": (
            "Overall market sentiment snapshot: fear/greed balance, VIX level, "
            "and what current positioning tells us about near-term risk."
        ),
        "examples": [
            "𝗙𝗲𝗮𝗿 & 𝗚𝗿𝗲𝗲𝗱 index at 72 — deep Greed territory. 𝗩𝗜𝗫 at 14, complacent. "
            "This is when you tighten stops, not chase. "
            "Markets can stay irrational longer than you can stay solvent — but don't forget it. 📊",

            "Something interesting in the sentiment data: 𝗿𝗲𝘁𝗮𝗶𝗹 𝗯𝘂𝗹𝗹𝗶𝘀𝗵, "
            "𝗶𝗻𝘀𝘁𝗶𝘁𝘂𝘁𝗶𝗼𝗻𝘀 quietly trimming. That divergence historically resolves downward. "
            "Don't confuse price momentum with fundamentals right now. 👀 #markets",

            "𝗩𝗜𝗫 spiked this morning, pulled back by midday. "
            "Classic fear-and-recovery pattern — not capitulation, not a flush. "
            "𝗦𝗺𝗮𝗿𝘁 𝗺𝗼𝗻𝗲𝘆 used the morning dip to add. Volatility isn't the enemy if positioned right. 📈",
        ],
    },

    "test_event": {
        "description": (
            "Weekly market summary: the 2-3 most important macro and market events "
            "from this week, and what they signal going into next week."
        ),
        "examples": [
            "This week: 𝗙𝗲𝗱 held rates, $SPY gained on the week, $NVDA hit another ATH. "
            "𝗢𝗶𝗹 down on demand fears. Earnings beat mostly but guidance was cautious. "
            "Decent week — but the complacency is building. 📊 #weeklyreview",

            "Week in review: 𝗖𝗣𝗜 came in hotter than expected — rate-cut bets faded fast. "
            "$SPY negative on the week. 𝗚𝗼𝗹𝗱 the outperformer, dollar stronger. "
            "Risk-off was the clear theme. Next week: more data to navigate. 📉",

            "Busy week. FTSE and $SPY both closed positive. "
            "𝗘𝗮𝗿𝗻𝗶𝗻𝗴𝘀 drove most of the moves — tech beat, consumer missed. "
            "𝗖𝗲𝗻𝘁𝗿𝗮𝗹 𝗯𝗮𝗻𝗸𝘀 in focus next week. Breadth improving. 📈 #markets",
        ],
    },

    "sunday_briefing": {
        "description": (
            "Sunday Briefing: the key macro events, central bank decisions, and data "
            "prints to watch in the week ahead — and why they matter."
        ),
        "examples": [
            "Week ahead: 𝗙𝗢𝗠𝗖 minutes Wednesday, 𝗖𝗣𝗜 Thursday. "
            "Earnings from $MSFT, $AMZN, $META. Positioning is stretched — "
            "any macro surprise will have an outsized impact. Know what you own. 📊 #weekahead",

            "Key events this week: 𝗕𝗢𝗘 decision Thursday, UK jobs Tuesday. "
            "$AAPL and $GOOGL report earnings. 𝗙𝗲𝗱 on hold but data flow will "
            "price the next move. Expect volatility around the big prints. 📅 #macro",

            "Quiet on macro data this week — the 𝗲𝗮𝗿𝗻𝗶𝗻𝗴𝘀 calendar dominates. "
            "$NVDA reports Thursday — most watched print of the quarter. "
            "Options pricing a large move. 𝗩𝗜𝗫 will react. Have a plan before it reports. 👀 #earnings",
        ],
    },

    "sunday_earning": {
        "description": (
            "Earnings preview: the most important company results expected this week, "
            "what the street is pricing in, and the key metric that will move the stock."
        ),
        "examples": [
            "𝗘𝗮𝗿𝗻𝗶𝗻𝗴𝘀 this week: $MSFT Monday, $GOOGL Tuesday, $META Wednesday. "
            "The bar is high after last quarter's beats — any miss on 𝗰𝗹𝗼𝘂𝗱 𝗴𝗿𝗼𝘄𝘁𝗵 "
            "will be punished fast. Guidance matters more than the beat. 📊 #earnings",

            "$𝗡𝗩𝗗𝗔 reports Thursday — street expects another blowout quarter. "
            "𝗗𝗮𝘁𝗮 𝗰𝗲𝗻𝘁𝗿𝗲 𝗿𝗲𝘃𝗲𝗻𝘂𝗲 is the key line to watch. "
            "Guidance moves $QQQ — options are pricing a big move. Position accordingly. 👀 #earnings",

            "Lighter week for earnings. $WMT and $HD report — "
            "𝗰𝗼𝗻𝘀𝘂𝗺𝗲𝗿 𝗵𝗲𝗮𝗹𝘁𝗵 is the read-through. "
            "With sentiment under pressure, any miss on 𝘀𝗮𝗺𝗲-𝘀𝘁𝗼𝗿𝗲 𝘀𝗮𝗹𝗲𝘀 will sting. "
            "Retail sector on watch. 📉 #earnings",
        ],
    },
}


class Prompter:

    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    def generate_financial_tweet(self, section: str) -> str:
        logger.info("Generating tweet — section: %s | model: %s", section, self.model)

        session = _SESSIONS.get(section)
        if session is None:
            raise ValueError(
                f"Unknown section: '{section}'. Valid sections: {sorted(_SESSIONS.keys())}"
            )

        examples_block = "\n\n".join(session["examples"])
        user_message = (
            f"Session: {session['description']}\n\n"
            "### Style examples — match this format and voice exactly. "
            "Do NOT copy these verbatim; use them only to calibrate tone and structure.\n\n"
            f"{examples_block}\n\n"
            "### Now write one tweet for this session:"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=150,
            temperature=0.3,
        )

        tweet = response.choices[0].message.content.strip()
        tweet = tweet.replace("**", "")  # strip accidental markdown bold
        tweet = tweet.strip('"')         # strip wrapping double-quotes

        char_count = len(tweet)
        if char_count > 280:
            logger.warning(
                "Tweet exceeds 280 chars (%d) — may be truncated by X. Section: %s",
                char_count,
                section,
            )

        logger.info("Tweet ready (%d chars) | %s | %s", char_count, section, tweet)
        return tweet
