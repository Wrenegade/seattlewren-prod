---
title: "Patent Troll Defense System (Beta)"
description: "Free tool for independent inventors: check if your idea overlaps with flagged troll-pattern patents, get a risk score, and generate a defense package."
date: 2026-03-29
categories:
  - Data
layout: photo
type: "data"
image:
draft: false
---

## What This Is

A free, public utility that detects mass-filed, AI-generated patent claims and helps independent inventors defend themselves.  No signup, no paywall, no tracking.

This tool monitors patent filings for troll patterns — high-volume filers, broad vague claims, filings across unrelated technology domains, AI-generated language — and assigns each a **Troll Probability Score (TPS)**.  You describe your invention in plain language, and the system tells you if it overlaps with anything suspicious.

Built overnight as a working prototype of [provisional patent application #64/020,008](/blog/patent-post/).  Every dollar raised past operating costs goes to the [Pancreatic Cancer Action Network](https://www.pancan.org/).

---

## Try It

Describe your invention, product, or idea.  The system compares it against flagged patents and returns a risk score, overlapping claims, and a defense package with prior art search links and a template demand letter response.

<iframe src="/troll-defense.html" width="100%" height="1800" style="border:none;"></iframe>

---

## How the Scoring Works

Each patent is scored on six factors (four active, two pending data sources):

| Factor | What It Measures | Status |
|--------|-----------------|--------|
| **Filing Volume** | How many patents has this entity filed recently? | Active |
| **Domain Dispersion** | Are they filing across unrelated technology areas? | Active |
| **Claim Breadth** | How vague and broad are the independent claims? | Active |
| **Linguistic Fingerprinting** | Does the text look AI-generated? | Active |
| Commercial Activity | Does the filer actually make products? | Pending (needs business registry API) |
| Litigation History | Do they have a history of suing without products? | Pending (needs PACER access) |

Patents scoring above 55 are flagged.  The system currently monitors demo data — live USPTO data will flow once we connect to the PatentsView API.

---

## Sources & Background

- [I Filed a Patent to Kill Patent Trolls — And You Can Help](/blog/patent-post/) — the full story
- [The Raw Tape](/blog/patent-raw/) — unedited transcript of the research and drafting process
- [AI Sketchiness You Should Know](/blog/you-should-know/) — the running list that started this
- [USPTO Third-Party Preissuance Submissions](https://www.uspto.gov/patents/initiatives/third-party-preissuance-submissions) — the free mechanism for killing troll patents before they're granted
