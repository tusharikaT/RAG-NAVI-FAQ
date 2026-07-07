# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

---

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources — such as AMC (Asset Management Company) websites, AMFI, and SEBI.

> **The system must strictly avoid providing investment advice, opinions, or recommendations.**  
> Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:

- Answers **factual queries** about mutual fund schemes
- Uses a **curated corpus** of official documents
- Provides **concise, source-backed responses**

---

## Target Users

| User Type | Description |
|---|---|
| **Retail Investors** | Comparing mutual fund schemes |
| **Customer Support & Content Teams** | Handling repetitive mutual fund queries |

---

## Scope of Work

### 1. Corpus Definition

- **Selected AMC:** [Navi Mutual Fund](https://www.navimutualfund.com/)
- **Total Schemes Selected:** 15 funds across diverse categories
- **Data Sources:** Official Groww fund pages, Navi AMC factsheets, AMFI/SEBI documents

#### Selected Mutual Fund Schemes

| # | Fund Name | Category | Groww URL |
|---|---|---|---|
| 1 | Navi Nifty 50 Index Fund – Direct Growth | Large Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-50-index-fund-direct-growth) |
| 2 | Navi Nifty Next 50 Index Fund – Direct Growth | Large Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-next-50-index-fund-direct-growth) |
| 3 | Navi Nifty IT Index Fund – Direct Growth | Sectoral – Technology | [View on Groww](https://groww.in/mutual-funds/navi-nifty-it-index-fund-direct-growth) |
| 4 | Navi Nifty Midcap 150 Index Fund – Direct Growth | Mid Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-midcap-150-index-fund-direct-growth) |
| 5 | Navi Flexi Cap Fund – Direct Growth | Flexi Cap | [View on Groww](https://groww.in/mutual-funds/navi-flexi-cap-fund-direct-growth) |
| 6 | Navi Nifty India Manufacturing Index Fund – Direct Growth | Sectoral – Manufacturing | [View on Groww](https://groww.in/mutual-funds/navi-nifty-india-manufacturing-index-fund-direct-growth) |
| 7 | Navi Nifty Smallcap250 Momentum Quality 100 Index Fund – Direct Growth | Small Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-smallcap250-momentum-quality-100-index-fund-direct-growth) |
| 8 | Navi Nifty Bank Index Fund – Direct Growth | Sectoral – Banking | [View on Groww](https://groww.in/mutual-funds/navi-nifty-bank-index-fund-direct-growth) |
| 9 | Navi Nifty 500 Multicap 50:25:25 Index Fund – Direct Growth | Multi Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-500-multicap-50:25:25-index-fund-direct-growth) |
| 10 | Navi ELSS Tax Saver Nifty 50 Index Fund – Direct Growth | ELSS / Tax Saving | [View on Groww](https://groww.in/mutual-funds/navi-elss-tax-saver-nifty-50-index-fund-direct-growth) |
| 11 | Navi Nifty MidSmallcap 400 Index Fund – Direct Growth | Mid & Small Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-nifty-midsmallcap-400-index-fund-direct-growth) |
| 12 | Navi Large & Midcap Fund – Direct Growth | Large & Mid Cap | [View on Groww](https://groww.in/mutual-funds/navi-large-midcap-fund-direct-growth) |
| 13 | Navi Liquid Fund – Direct Growth | Liquid / Debt | [View on Groww](https://groww.in/mutual-funds/navi-liquid-fund-direct-growth) |
| 14 | Navi Aggressive Hybrid Fund – Direct Growth | Hybrid – Aggressive | [View on Groww](https://groww.in/mutual-funds/navi-aggressive-hybrid-fund-direct-growth) |
| 15 | Navi BSE Sensex Index Fund – Direct Growth | Large Cap / Index | [View on Groww](https://groww.in/mutual-funds/navi-bse-sensex-index-fund-direct-growth) |

#### Confirmed Corpus URLs

The following **15 official Groww fund pages** are the finalized primary data sources for the RAG pipeline:

| # | Corpus URL |
|---|---|
| 1 | https://groww.in/mutual-funds/navi-nifty-50-index-fund-direct-growth |
| 2 | https://groww.in/mutual-funds/navi-nifty-next-50-index-fund-direct-growth |
| 3 | https://groww.in/mutual-funds/navi-nifty-it-index-fund-direct-growth |
| 4 | https://groww.in/mutual-funds/navi-nifty-midcap-150-index-fund-direct-growth |
| 5 | https://groww.in/mutual-funds/navi-flexi-cap-fund-direct-growth |
| 6 | https://groww.in/mutual-funds/navi-nifty-india-manufacturing-index-fund-direct-growth |
| 7 | https://groww.in/mutual-funds/navi-nifty-smallcap250-momentum-quality-100-index-fund-direct-growth |
| 8 | https://groww.in/mutual-funds/navi-nifty-bank-index-fund-direct-growth |
| 9 | https://groww.in/mutual-funds/navi-nifty-500-multicap-50:25:25-index-fund-direct-growth |
| 10 | https://groww.in/mutual-funds/navi-elss-tax-saver-nifty-50-index-fund-direct-growth |
| 11 | https://groww.in/mutual-funds/navi-nifty-midsmallcap-400-index-fund-direct-growth |
| 12 | https://groww.in/mutual-funds/navi-large-midcap-fund-direct-growth |
| 13 | https://groww.in/mutual-funds/navi-liquid-fund-direct-growth |
| 14 | https://groww.in/mutual-funds/navi-aggressive-hybrid-fund-direct-growth |
| 15 | https://groww.in/mutual-funds/navi-bse-sensex-index-fund-direct-growth |

> **Note:** Additional supplementary documents (KIM, SID, AMFI fund pages, SEBI disclosures) may be added per scheme as needed during corpus expansion.

---

### 2. FAQ Assistant Requirements

The assistant must answer **facts-only** queries, such as:

- Expense ratio of a scheme
- Exit load details
- Minimum SIP amount
- ELSS lock-in period
- Riskometer classification
- Benchmark index
- Process to download statements or capital gains reports

**Response Constraints:**

| Constraint | Requirement |
|---|---|
| **Length** | Maximum 3 sentences per response |
| **Citation** | Exactly one source link per response |
| **Footer** | `"Last updated from sources: <date>"` |

---

### 3. Refusal Handling

The assistant must **refuse** non-factual or advisory queries, such as:

- *"Should I invest in this fund?"*
- *"Which fund is better?"*

Refusal responses must:

- Be polite and clearly worded
- Reinforce the **facts-only limitation**
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

---

### 4. User Interface (Minimal)

The solution must include a simple interface with:

- [ ] A **welcome message**
- [ ] **Three example questions**
- [ ] A visible disclaimer:

> **"Facts-only. No investment advice."**

---

## Constraints

### Data & Sources
- Use **only official public sources** (AMC, AMFI, SEBI)
- Do **not** use third-party blogs or aggregator websites

### Privacy & Security
Do **not** collect, store, or process:
- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

### Content Restrictions
- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries → provide a link to the **official factsheet only**

### Transparency
- Responses must be **short, factual, and verifiable**
- Every answer must include a **source link** and **last updated date**

---

## Expected Deliverables

| Deliverable | Details |
|---|---|
| **README Document** | Setup instructions, selected AMC & schemes, architecture overview (RAG approach), known limitations |
| **Disclaimer Snippet** | `"Facts-only. No investment advice."` |

---

## Success Criteria

- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

---

## Summary

The goal is to build a **trustworthy, transparent, and compliant** mutual fund FAQ assistant that prioritizes **accuracy over intelligence**. The system should ensure that users receive only verified, source-backed financial information — without any advisory bias or speculative content.

---

> **Disclaimer:** *Facts-only. No investment advice.*
