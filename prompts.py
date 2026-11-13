"""Visible, editable-by-developer prompt templates for the four live demonstrations."""

SHARED_PROMPT = """You are analyzing a FICTIONAL company called Northstar Cloud Ltd.
All numbers below are invented training data, not current market data.

FY2025 revenue: $120 million; FY2024 revenue: $100 million.
FY2025 gross margin: 64%; operating margin: 14%; free cash flow: $11 million.
Cash: $38 million; total debt: $24 million; customers: 2,400.
FY2025 revenue by segment: subscriptions 75%, services 25%.
The hypothetical current enterprise value is $480 million.

Create a reusable baseline investment-analysis memo from these facts ONLY.
Calculate revenue growth, net cash, EV/revenue, and FCF margin.
List key strengths, risks, and uncertainties. Clearly label estimates
and do not claim to have collected external market information.
Use concise headings and a small metrics table.
"""

BULL_PROMPT = """Using ONLY the parent baseline analysis, develop a bull-case
scenario for fictional Northstar Cloud Ltd. Assume revenue grows 20% next year,
gross margin increases to 68%, and the valuation multiple expands to 5.0x
next-year revenue. Calculate the implied next-year revenue and illustrative EV.
Explain catalysts, assumptions, and what might invalidate the thesis.
Do not incorporate any bearish branch output or external live market data.
"""

BEAR_PROMPT = """Using ONLY the parent baseline analysis, develop a bear-case
scenario for fictional Northstar Cloud Ltd. Assume revenue declines 5% next
year, gross margin contracts to 58%, and the valuation multiple compresses
to 2.5x next-year revenue. Calculate the implied next-year revenue and
illustrative EV. Explain downside drivers, assumptions, and what could
invalidate the thesis. Do not incorporate any bullish branch output or
external live market data.
"""

CONTINUE_BULL_PROMPT = """Continue the EXISTING bull-case branch only.
Add a three-item watchlist of leading indicators and a concise sensitivity
analysis for revenue growth of 15%, 20%, and 25%, keeping the bull valuation
multiple at 5.0x. Explicitly state the assumptions you inherited.
Do not introduce bearish branch reasoning.
"""

CONTINUE_BEAR_PROMPT = """Continue the EXISTING bear-case branch only.
Add a three-item risk-monitoring watchlist and a concise sensitivity analysis
for revenue change of -10%, -5%, and 0%, keeping the bear valuation
multiple at 2.5x. Explicitly state the assumptions you inherited.
Do not introduce bullish branch reasoning.
"""

RESUME_BULL_PROMPT = """We have reopened the app after saving the workflow.
Continue the bullish scenario from its last saved response. Summarize the
existing assumptions and add two specific due-diligence questions for the
fictional company's management. Do not reference the bearish branch.
"""

RESUME_BEAR_PROMPT = """We have reopened the app after saving the workflow.
Continue the bearish scenario from its last saved response. Summarize the
existing assumptions and add two specific downside-risk questions for the
fictional company's management. Do not reference the bullish branch.
"""

COMPARE_PROMPT = """You are comparing TWO INDEPENDENT hypothetical analyses of
fictional Northstar Cloud Ltd. This is not investment advice.

SHARED BASELINE:
{base}

LATEST BULL BRANCH OUTPUT:
{bull}

LATEST BEAR BRANCH OUTPUT:
{bear}

Produce a side-by-side comparison with: assumptions, revenue projections,
implied enterprise valuations, upside/downside versus the hypothetical
$480 million reference EV, major risks, and a neutral conclusion.
Do not invent new source data or claim the two branches merged server-side.
"""
