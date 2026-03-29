"""Demo seed script — populates the database with realistic synthetic patent data.

The PatentsView API now requires an API key (free but must be requested).
This script seeds the system with plausible demo data so the prototype
functions end-to-end. Replace with real data once the API key is obtained.

Run inside the backend container:
    python -m troll_detector.seed_demo
"""

import asyncio
import json
import logging
import os
import sys
from datetime import date

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from troll_detector.models import PatentFiling
from troll_detector.scorer import compute_tps, compute_weighted_tps, is_flagged
from troll_detector.nlp import fit_vectorizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@host.docker.internal:5432/seattle_wren"
)

# Realistic synthetic patents — a mix of likely-troll and likely-legitimate filings.
# Troll-like patents: broad, vague, cross-domain, no product, AI-generated feel.
# Legitimate patents: specific, focused, single domain, clear implementation.

DEMO_PATENTS = [
    # ─── HIGH TPS (likely troll patterns) ────────────────────────────
    {
        "num": "US20260001001",
        "title": "System and Method for Utilizing Machine Learning to Optimize Digital Content Delivery Across Networked Platforms",
        "date": "2026-01-15",
        "assignee": "Nexion IP Holdings LLC",
        "cpc_codes": ["G06F", "G06N", "H04L", "G06Q", "H04W", "A61B", "B60W"],
        "abstract": "A computer-implemented method for optimizing digital content delivery comprising receiving a plurality of content items from a content source, processing said content items through a machine learning model trained on user engagement metrics, generating optimized delivery parameters based on the processed content items, and transmitting the optimized content items to one or more networked platforms. The system further comprises a feedback loop mechanism for continuously refining the machine learning model based on user interaction data collected from the networked platforms.",
        "claims": "A computer-implemented method comprising: receiving, by a processor, a plurality of content items from a content source; processing, by the processor, said content items through a machine learning model trained on user engagement metrics; generating, by the processor, optimized delivery parameters based on the processed content items; transmitting, by the processor, the optimized content items to one or more networked platforms; collecting user interaction data from the networked platforms; and refining the machine learning model based on the collected user interaction data.",
        "filing_count": 87,
        "related_texts": [
            "A system for processing digital media content using artificial intelligence algorithms to determine optimal distribution parameters across network endpoints.",
            "A method for utilizing trained neural network models to enhance digital content routing through interconnected computing platforms with feedback mechanisms.",
        ],
    },
    {
        "num": "US20260002002",
        "title": "Blockchain-Based Apparatus for Decentralized Verification of Digital Credentials in Multi-Party Environments",
        "date": "2025-11-22",
        "assignee": "Nexion IP Holdings LLC",
        "cpc_codes": ["G06F", "H04L", "G06Q", "G09C", "G06N", "E04H", "C12N"],
        "abstract": "An apparatus for decentralized verification of digital credentials comprising a distributed ledger network configured to store cryptographic representations of credential data, a verification engine operable to validate credential authenticity through consensus-based mechanisms, and an interface module for facilitating multi-party credential exchange. The apparatus further includes a smart contract execution layer for automating credential lifecycle management.",
        "claims": "An apparatus comprising: a distributed ledger network configured to store cryptographic representations of credential data; a verification engine operable to validate credential authenticity through consensus-based mechanisms; an interface module for facilitating multi-party credential exchange; and a smart contract execution layer for automating credential lifecycle management.",
        "filing_count": 87,
        "related_texts": [
            "A blockchain system for managing digital identity verification across distributed networks using cryptographic protocols and consensus algorithms.",
            "A decentralized platform for credential authentication comprising distributed storage nodes and smart contract processors for automated verification workflows.",
        ],
    },
    {
        "num": "US20260003003",
        "title": "Method for Autonomous Decision-Making in Internet-of-Things Device Networks Using Predictive Analytics",
        "date": "2026-02-08",
        "assignee": "Nexion IP Holdings LLC",
        "cpc_codes": ["H04W", "G06N", "G06F", "H04L", "G05B", "G16Y", "A01G", "B25J"],
        "abstract": "A method for enabling autonomous decision-making in Internet-of-Things device networks comprising collecting sensor data from a plurality of IoT devices, applying predictive analytics models to the collected sensor data, generating decision parameters based on the predictive analytics output, and transmitting decision instructions to the plurality of IoT devices. The method further comprises dynamically adjusting the predictive models based on environmental feedback data.",
        "claims": "A method comprising: collecting, by a central processing unit, sensor data from a plurality of IoT devices; applying, by the central processing unit, predictive analytics models to the collected sensor data; generating decision parameters based on predictive analytics output; transmitting decision instructions to the plurality of IoT devices; and dynamically adjusting predictive models based on environmental feedback data.",
        "filing_count": 87,
        "related_texts": [
            "A system for automated control of networked sensor devices using machine learning prediction models to optimize device behavior in distributed environments.",
            "A method for intelligent management of Internet-of-Things networks comprising predictive analysis engines and automated response controllers.",
        ],
    },
    {
        "num": "US20260004004",
        "title": "System for Automated Natural Language Processing of Unstructured Data in Enterprise Computing Environments",
        "date": "2026-03-01",
        "assignee": "Stratos Patent Group Inc",
        "cpc_codes": ["G06F", "G06N", "G10L"],
        "abstract": "A system for automated natural language processing comprising a data ingestion module configured to receive unstructured text data from enterprise computing systems, a language processing engine utilizing transformer-based models to extract structured information, and a knowledge graph generator for organizing extracted information into queryable relational structures. The system is configured to operate in real-time across distributed computing environments.",
        "claims": "A system comprising: a data ingestion module configured to receive unstructured text data from enterprise computing systems; a language processing engine utilizing transformer-based models to extract structured information from the unstructured text data; a knowledge graph generator for organizing extracted information into queryable relational structures; and a distributed processing framework for real-time operation across computing environments.",
        "filing_count": 45,
        "related_texts": [
            "An automated system for converting unstructured enterprise documents into structured knowledge representations using deep learning language models.",
        ],
    },
    {
        "num": "US20260005005",
        "title": "Computer-Implemented Method for AI-Driven Financial Risk Assessment in Decentralized Markets",
        "date": "2026-01-28",
        "assignee": "Stratos Patent Group Inc",
        "cpc_codes": ["G06Q", "G06N", "G06F", "H04L"],
        "abstract": "A computer-implemented method for financial risk assessment comprising receiving market data from decentralized trading platforms, processing the market data through a plurality of AI models trained on historical trading patterns, generating risk scores based on the processed data, and presenting the risk scores through a user interface configured for non-technical users. The method further comprises generating automated trading recommendations based on the computed risk scores.",
        "claims": "A method comprising: receiving, by a processor, market data from one or more decentralized trading platforms; processing the market data through a plurality of AI models trained on historical trading patterns; computing risk scores based on the processed data; presenting the risk scores through a user interface; and generating automated trading recommendations based on the computed risk scores.",
        "filing_count": 45,
        "related_texts": [
            "A financial technology system for assessing market risk using artificial intelligence algorithms applied to decentralized trading platform data.",
        ],
    },
    {
        "num": "US20260006006",
        "title": "Platform for Intelligent Automation of Software Development Lifecycle Processes",
        "date": "2025-12-15",
        "assignee": "CodeFlow Innovations LLC",
        "cpc_codes": ["G06F", "G06N"],
        "abstract": "A platform for intelligent automation of software development lifecycle processes comprising a code analysis module utilizing large language models to evaluate source code quality, a continuous integration orchestrator configured to autonomously manage build and deployment pipelines, and a defect prediction engine trained on historical bug databases. The platform enables end-to-end automation of software engineering workflows.",
        "claims": "A platform comprising: a code analysis module utilizing large language models to evaluate source code quality and generate improvement suggestions; a continuous integration orchestrator configured to autonomously manage build and deployment pipelines based on code analysis results; a defect prediction engine trained on historical software defect databases; and an integration layer connecting the modules for end-to-end workflow automation.",
        "filing_count": 23,
        "related_texts": [
            "An AI-powered system for automating software engineering tasks including code review, testing, deployment, and defect prediction across development pipelines.",
        ],
    },

    # ─── MEDIUM TPS (ambiguous) ──────────────────────────────────────
    {
        "num": "US20260007007",
        "title": "Dynamic Energy Management System for Smart Building Infrastructure Using Reinforcement Learning",
        "date": "2026-02-20",
        "assignee": "GreenGrid Technologies Inc",
        "cpc_codes": ["F24F", "G05B", "G06N"],
        "abstract": "A dynamic energy management system for smart buildings comprising a network of distributed sensors monitoring temperature, humidity, occupancy, and energy consumption; a reinforcement learning controller that optimizes HVAC, lighting, and electrical load scheduling in real-time; and a predictive maintenance module that identifies equipment degradation before failure. The system reduces total energy consumption by 15-30% in commercial buildings exceeding 50,000 square feet through zone-specific optimization profiles that adapt to seasonal patterns and occupancy schedules.",
        "claims": "A system comprising: distributed environmental sensors monitoring at least temperature, humidity, and occupancy across building zones; a reinforcement learning controller receiving sensor data and optimizing HVAC setpoints, lighting levels, and electrical load distribution; a predictive maintenance module analyzing equipment performance telemetry; and zone-specific optimization profiles adapting to diurnal and seasonal occupancy patterns.",
        "filing_count": 8,
        "related_texts": [],
    },
    {
        "num": "US20260008008",
        "title": "Method and System for Generating Synthetic Training Data for Computer Vision Applications",
        "date": "2026-01-10",
        "assignee": "DataForge AI Corp",
        "cpc_codes": ["G06T", "G06V", "G06N"],
        "abstract": "A method for generating synthetic training data for computer vision models comprising parameterized 3D scene generation using procedural asset pipelines, physically-based rendering with domain randomization of lighting, textures, and camera angles, and automatic annotation of generated images with pixel-accurate segmentation masks and bounding boxes. The system generates labeled datasets at 100x lower cost than manual annotation while achieving comparable model performance for object detection and instance segmentation tasks in industrial quality inspection scenarios.",
        "claims": "A method comprising: generating parameterized 3D scenes using procedural asset pipelines with configurable object placement and environment parameters; rendering images using physically-based rendering with domain randomization of at least lighting conditions, surface textures, and camera viewpoints; automatically generating pixel-accurate segmentation masks and bounding boxes for all rendered objects; and validating synthetic data quality by measuring trained model performance against manually annotated benchmark datasets.",
        "filing_count": 12,
        "related_texts": [],
    },

    # ─── LOW TPS (likely legitimate) ─────────────────────────────────
    {
        "num": "US20260009009",
        "title": "Compact Peristaltic Pump with Integrated Flow Sensor for Microfluidic Cell Culture Applications",
        "date": "2025-10-05",
        "assignee": "BioMicro Systems Ltd",
        "cpc_codes": ["F04B"],
        "abstract": "A compact peristaltic pump assembly designed for microfluidic cell culture applications comprising a miniaturized stepper motor driving a 3-roller head assembly, an integrated thermal flow sensor with 0.1 μL/min resolution positioned downstream of the pump head, and a closed-loop PID controller maintaining flow rate accuracy within ±2% across 0.5-500 μL/min. The pump housing measures 42mm × 28mm × 15mm and operates on 3.3V DC, enabling direct integration into organ-on-chip platforms. Biocompatible tubing with 0.5mm inner diameter passes through a compression zone of 8mm arc length.",
        "claims": "A peristaltic pump assembly for microfluidic applications comprising: a miniaturized stepper motor with a 3-roller head assembly configured for 0.5mm inner diameter tubing; an integrated thermal flow sensor positioned within 15mm downstream of the pump head providing flow rate measurement with 0.1 μL/min resolution; a closed-loop PID controller maintaining flow accuracy within ±2% across 0.5-500 μL/min; and a housing not exceeding 50mm in any dimension.",
        "filing_count": 3,
        "related_texts": [],
    },
    {
        "num": "US20260010010",
        "title": "Adaptive Cruise Control Algorithm for Heavy-Duty Commercial Vehicles with Predictive Grade Compensation",
        "date": "2026-03-15",
        "assignee": "Volvo Truck Corporation",
        "cpc_codes": ["B60W"],
        "abstract": "An adaptive cruise control algorithm specifically designed for heavy-duty commercial vehicles weighing 30,000-80,000 lbs comprising a predictive grade compensation module that uses GPS elevation data and digital terrain models to anticipate grade changes 500-2000m ahead, a gear selection optimizer that pre-selects transmission ratios based on predicted road grade and current vehicle momentum, and a following-distance controller that accounts for the 40-60% longer braking distances of loaded commercial vehicles compared to passenger cars. The algorithm reduces fuel consumption by 4-8% on hilly terrain while maintaining safe following distances per FMCSA regulations.",
        "claims": "An adaptive cruise control method for commercial vehicles exceeding 26,000 lbs GVWR comprising: receiving GPS position data and querying stored digital elevation models to predict road grade within 500-2000m ahead; computing optimal engine torque and transmission gear ratio sequences based on predicted grade profile and current vehicle mass; adjusting following distance thresholds based on calculated stopping distance for current vehicle weight and road conditions; and coordinating with engine brake and service brake systems for downhill speed control within ±2 mph of set speed.",
        "filing_count": 15,
        "related_texts": [],
    },
    {
        "num": "US20260011011",
        "title": "Immunoassay Cartridge with Integrated Sample Preparation for Point-of-Care Malaria Detection",
        "date": "2025-09-30",
        "assignee": "PATH Global Health Innovation",
        "cpc_codes": ["G01N"],
        "abstract": "A disposable immunoassay cartridge for point-of-care detection of Plasmodium falciparum and Plasmodium vivax comprising a capillary blood collection port accepting 10 μL finger-prick samples, an integrated lysis and filtration chamber that separates red blood cell debris from target antigens within 30 seconds, dual lateral flow immunochromatographic strips targeting HRP2 and pLDH biomarkers simultaneously, and a built-in positive control line. The cartridge provides results readable by eye within 15 minutes with clinical sensitivity >98% and specificity >95% at parasitemia levels ≥200 parasites/μL, and maintains stability at 40°C for 18 months without cold chain requirements.",
        "claims": "A diagnostic cartridge comprising: a capillary blood collection port configured to accept 5-20 μL whole blood samples; a lysis and filtration chamber containing dried reagents that separate cellular debris from target antigens; at least two lateral flow immunochromatographic strips configured to simultaneously detect HRP2 and pLDH biomarkers of Plasmodium species; and a positive control indicator verifying reagent activity and sample flow.",
        "filing_count": 6,
        "related_texts": [],
    },
    {
        "num": "US20260012012",
        "title": "Method for Real-Time Monitoring of Lithium-Ion Battery State-of-Health Using Electrochemical Impedance Spectroscopy",
        "date": "2026-02-01",
        "assignee": "Samsung SDI Co Ltd",
        "cpc_codes": ["H01M", "G01R"],
        "abstract": "A method for real-time battery state-of-health monitoring using onboard electrochemical impedance spectroscopy comprising injecting multi-frequency perturbation signals (0.1 Hz - 10 kHz) during normal charge/discharge cycles without interrupting battery operation, measuring impedance response across the frequency spectrum to extract charge transfer resistance and Warburg diffusion coefficient, and correlating extracted impedance parameters to remaining capacity through a physics-informed neural network trained on 5,000+ cells cycled to end-of-life. Accuracy within ±3% SOH over the 80-100% range for NMC 811 chemistry.",
        "claims": "A method for in-situ battery state-of-health estimation comprising: injecting perturbation signals spanning 0.1 Hz to 10 kHz during normal battery operation; measuring impedance response to extract at least charge transfer resistance and diffusion impedance parameters; inputting extracted parameters into a physics-informed model correlating impedance evolution to capacity fade; and reporting estimated state-of-health as percentage of rated capacity.",
        "filing_count": 42,
        "related_texts": [],
    },
]


async def seed_demo():
    logger.info("Starting demo data seed...")

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    # Ensure tables exist
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS patent_filings (
            id              SERIAL PRIMARY KEY,
            application_num TEXT UNIQUE NOT NULL,
            title           TEXT,
            filing_date     DATE,
            inventor_name   TEXT DEFAULT '',
            assignee        TEXT DEFAULT '',
            cpc_codes       TEXT[] DEFAULT '{}',
            claims_text     TEXT DEFAULT '',
            abstract_text   TEXT DEFAULT '',
            tps_score       REAL DEFAULT 0,
            tps_breakdown   JSONB DEFAULT '{}',
            flagged         BOOLEAN DEFAULT FALSE,
            analyzed_at     TIMESTAMPTZ DEFAULT now()
        )
    """)

    inserted = 0
    flagged_count = 0
    all_texts = []
    all_ids = []

    for p in DEMO_PATENTS:
        filing = PatentFiling(
            application_num=p["num"],
            title=p["title"],
            abstract_text=p["abstract"],
            claims_text=p["claims"],
            assignee=p["assignee"],
            cpc_codes=p["cpc_codes"],
        )
        if p.get("date"):
            filing.filing_date = date.fromisoformat(p["date"])

        # Compute TPS with realistic metadata
        breakdown = compute_tps(
            filing,
            assignee_filing_count=p.get("filing_count", 0),
            assignee_cpc_codes=p.get("cpc_codes", []),
            related_claims_texts=p.get("related_texts") or None,
        )

        tps = compute_weighted_tps(breakdown)
        flagged = is_flagged(tps)

        try:
            await pool.execute(
                """INSERT INTO patent_filings
                   (application_num, title, filing_date, assignee, cpc_codes,
                    claims_text, abstract_text, tps_score, tps_breakdown, flagged)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (application_num) DO UPDATE
                   SET tps_score = $8, tps_breakdown = $9, flagged = $10, analyzed_at = now()""",
                p["num"], p["title"],
                filing.filing_date,
                p["assignee"],
                p["cpc_codes"],
                p["claims"],
                p["abstract"],
                tps, json.dumps(breakdown.to_dict()), flagged,
            )
            inserted += 1
            if flagged:
                flagged_count += 1
            # Add to vectorizer corpus (all patents, not just flagged)
            text = p["claims"] or p["abstract"]
            all_texts.append(text)
            all_ids.append(p["num"])
            logger.info(f"  {p['num']}: TPS={tps:.1f} {'FLAGGED' if flagged else 'ok'} — {p['title'][:60]}")
        except Exception as e:
            logger.warning(f"Failed to insert {p['num']}: {e}")

    # Fit vectorizer on ALL patent texts (flagged ones are the corpus for risk assessment)
    flagged_texts = []
    flagged_ids = []
    for i, p in enumerate(DEMO_PATENTS):
        text = p["claims"] or p["abstract"]
        # Check if this patent was flagged
        filing = PatentFiling(application_num=p["num"], title=p["title"],
                              abstract_text=p["abstract"], claims_text=p["claims"])
        bd = compute_tps(filing, p.get("filing_count", 0), p.get("cpc_codes", []),
                         p.get("related_texts") or None)
        tps = compute_weighted_tps(bd)
        if is_flagged(tps):
            flagged_texts.append(text)
            flagged_ids.append(p["num"])

    if flagged_texts:
        fit_vectorizer(flagged_texts, flagged_ids)
        logger.info(f"Vectorizer fitted on {len(flagged_texts)} flagged patents")

    logger.info(f"Done: {inserted} inserted, {flagged_count} flagged")

    total = await pool.fetchval("SELECT COUNT(*) FROM patent_filings")
    total_flagged = await pool.fetchval("SELECT COUNT(*) FROM patent_filings WHERE flagged = TRUE")
    logger.info(f"Database totals: {total} patents, {total_flagged} flagged")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(seed_demo())
