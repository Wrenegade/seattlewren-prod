# Session Transfer Notes — March 22, 2026

## Context
Jonny is building SeattleWren.com (testing at jonnywren.com). Nonpartisan, systems-diagnosis editorial voice. "Aim for Mediocre" brand philosophy. He's a data engineer/analyst with 30 years experience — prefers terminal-based data exploration, no fluff, educate him with facts and let him write in his own voice.

## Blog Series Architecture
Connected series: National Debt → GDP Growth → AI Opportunity → Healthcare Inefficiency → "The middle class is a derivative of inefficiency"

### Core Analogies Established
- **National Debt**: Total accumulated amount the government has borrowed and not yet paid back. Family analogy: you make $100K/yr, spend $106K/yr, already owe $122K — all on credit cards, house is paid off. No assets backing the debt.
- **GDP**: Total value of everything the country produces in a year (calendar year, Jan-Dec).
- **Federal Spending**: The $106K. Revenue is the $100K (mostly taxes). The $6K gap = deficit (this year's shortfall added to debt).
- **Debt-to-GDP Ratio**: ~122% — we owe more than we make annually.
- **Interest Rate**: Weighted avg ~3.3-3.4% across all Treasury debt, but rising as near-zero pandemic-era bonds roll over to 4.5%+ rates. Interest payments now exceed defense spending.

### GDP Growth Levers (Chapter 1 Foundation)
Three inputs: More Labor, More Capital, Total Factor Productivity (TFP).
- Labor is tapped out: birth rates at 1.62, boomers retiring 10K/day, women's participation plateaued at ~57%, only immigration left as growth lever.
- Labor participation: 62.4% — was lower post-WWII (~58%) but women entering workforce drove it to 67% peak in 2000. Now men are bailing.
- Men dropping out → "how are they living?" → disability system → the whole SSDI rabbit hole.

## SSDI Data Analysis (Core Asset)

### Key File
`data/disability_data/ssdi_25year_highlights.xlsx` — three tabs:
1. **SSDI 25-Year Highlights**: Beneficiaries, avg monthly benefit, terminations, term%, avg age (2000-2024)
2. **Terminations by Reason**: RTW, Died, Aged Out (FRA), Medical Improvement with percentages (2003-2024, 22 years)
3. **RTW by State**: 51 jurisdictions × 22 years, RTW% against total beneficiary pool

### Source Files
- `data/disability_data/pdf/di_asr00.pdf` through `di_asr24.pdf` (25 annual statistical report PDFs)
- `data/disability_data/xlsx/di_asr03.xlsx` through `di_asr24.xlsx` (22 Excel source files)

### Key Numbers
- Beneficiary trend: 6M → 10.2M peak → 8.6M (decline driven by aging/death, NOT return to work)
- **Monthly intake**: 62,500 average (peaked 85,500/mo in 2010, now ~49,500/mo)
- **RTW rate**: Never exceeded 8.2% of terminations; under 1% of total beneficiary pool annually
- **Died + Aged Out = 84-91% of all terminations** consistently
- Death rates declining (41.4% → 28.8%) — people living longer on benefits
- Aged out rates rising (44.6% → 60%) — Boomers hitting retirement age
- State RTW% ranges from 0.2% (West Virginia) to 1.5% (DC)
- 18.8 million people awarded SSDI over 25 years

### The Hook
"2,000 people will enter the disability system tomorrow. Only 200 of them will ever go back to work. Here's why — and here's what can be done."

### The Two Charts Concept
Rich intake data (claims processed, awards, demographics) vs. blank page for outcomes (no one is tracking return to work, AND THAT'S THE PROBLEM).

## Policy Proposal: Private Sector Tax Incentive for SSDI RTW

### Mechanism
- Company hires SSDI beneficiary, gets guaranteed Year 1 tax credit (e.g., $15K)
- Must employ minimum 6 months
- Employer is break-even to profitable just for trying — no risk
- If employee stays into Year 2, employer has trained worker at market rate with zero hiring cost
- Government saves ~$18K/yr per person off rolls + gains tax revenue = $25K swing per person
- $15K credit pays for itself in 7 months even at 1-in-3 success rate

### Self-Sorting Market Mechanism
- Employers naturally cherry-pick most employable first (back injuries who can WFH, managed mental health, recession casualties)
- Pool shrinks to truly disabled in 3-5 years without any bureaucrat making subjective determinations
- Solves cliff effect: employer takes the risk, not the employee
- Creates competition for the candidate pool — "a run on disabled talent"

### State-Level Pilot Angle
- State-level RTW data exists for 22 years (Tab 3 in Excel file) to baseline any pilot
- States can layer matching incentive on top of federal credit ($10K fed + $5K state)
- State specialization by industry:
  - **Washington**: Tech heavy. "Here's $70K to sit at a desk and tag training data."
  - **West Virginia**: Healthcare data. Turn the state with the most disability into the state that's best at managing health care data via AI.
- Parallel to subsidized childcare model (Jonny's 7 years in early learning) — subsidy seeds the ecosystem, ecosystem sustains itself

### Political Cover
- Politicians don't have to campaign on it — slip it into policy, let private sector execute
- WOTC already exists as precedent, just needs meaningful credit amount (old $2,400 was worthless)
- Brand message: "The government is fine. People have thought of this stuff before. They're not dumb, broken, or illwilled. You're just ignorant...so was I, until AI. Welcome to the revolution!"

## Next Steps (Not Yet Done)
1. **Build interactive tax credit calculator** for the website — employer P&L for 6-month trial, government break-even timeline, projected RTW rate increase at various adoption levels, 5-year fiscal impact. Parameterized by tax credit amount. Based on real SSDI data.
2. **State pilot scenario modeler** alongside the calculator
3. **Explore what jobs RTW people go to** — DC's 1.5% likely government jobs, not private sector. Need BLS cross-reference or Ticket to Work outcome studies.
4. **Write the actual blog posts** — Jonny writes in his own voice, data supports the narrative

## Technical Notes
- Excel file built with openpyxl, recalculated with LibreOffice recalc script at `/sessions/sweet-vibrant-turing/mnt/.skills/skills/xlsx/scripts/recalc.py`
- Table numbering differs across years: Table 50 (terminations) was Table 46 in 2003-2004; Table 56 (state RTW) was Table 51 in 2003, Table 52 in 2004
- State table RTW% is against total beneficiary pool (not terminations) — that's why values are 0.2-1.5% not 5-8%
