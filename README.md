# MineSafety — Mining Safety Analytics & Decision Support

**A reproducible, data-driven framework for analyzing mining safety records, identifying recurring enforcement concerns, and supporting evidence-based safety review decisions.**

`Python` · `Pandas` · `SQL` · `Data Analytics` · `Data Validation` · `Automated Testing` · `Decision Support`

## Overview

MineSafety is an end-to-end analytical project designed to transform complex, large-scale mining safety records into structured, explainable, and reproducible recommendations.

The system integrates multiple Mine Safety and Health Administration (MSHA) data sources, including mining operations, inspection records, safety violations, accident reports, and production information.

Rather than relying on isolated statistics, MineSafety evaluates relationships between records, reconciles inconsistent reporting periods, investigates recurring safety enforcement patterns, and applies deterministic prioritization criteria to identify operations warranting further review.

The project emphasizes **analytical correctness, reproducibility, transparent reasoning, and evidence-based decision-making**.

## Key Features

- **Multi-Source Data Integration:** Combines mining, inspection, accident, production, and violation datasets.
- **Large-Scale Data Processing:** Uses Python and Pandas to process extensive administrative datasets.
- **Data Cleaning & Validation:** Identifies duplicate records, incomplete information, and conflicting identifiers.
- **Cross-Dataset Reconciliation:** Links safety violations to their corresponding inspection events.
- **Safety Analytics:** Evaluates enforcement recurrence, inspection coverage, and exposure-adjusted injury indicators.
- **Deterministic Decision Logic:** Produces reproducible rankings using explicit prioritization rules.
- **Sensitivity Analysis:** Examines whether different reporting-date and data-coverage assumptions affect recommendations.
- **Automated Validation:** Includes executable tests and structured evaluation criteria.
- **Explainable Reporting:** Generates analytical evidence, data-quality findings, and a decision memo.

## Technical Architecture

```text
            MSHA Safety Data Sources
                      |
                      v
             Data Ingestion Layer
                      |
                      v
          Cleaning & Data Validation
                      |
                      v
       Record Linking & Reconciliation
                      |
                      v
         Safety Metrics Computation
                      |
                      v
        Policy-Based Decision Engine
                      |
                      v
          Sensitivity & QA Analysis
                      |
                      v
       Reports and Structured Outputs
```

### 1. Data Ingestion & Preprocessing

The pipeline processes datasets covering:

- Mine identities and operational characteristics
- Inspection events and historical records
- Safety violations and enforcement information
- Accident and injury records
- Annual mine production and reported work hours

It standardizes identifiers, removes exact duplicates where appropriate, validates records, and prepares datasets for consistent analysis.

### 2. Analytical Processing

MineSafety performs relational analysis across datasets to distinguish individual citations from distinct inspection events.

This distinction is essential: multiple violations linked to the same inspection should not automatically be interpreted as multiple independent occasions of recurring enforcement concerns.

The pipeline also evaluates missing information, reporting-year differences, and historical coverage limitations.

### 3. Decision & Prioritization Engine

The framework applies an explicit review-funding policy to prioritize operations based on:

1. Number of qualifying distinct inspection events associated with Significant and Substantial (S&S) violations.
2. Number of inspection years containing qualifying events.
3. Number of qualifying S&S violations associated with those events.

Injury-related indicators and reported working hours provide additional context without automatically overriding the specified decision policy.

### 4. Sensitivity & Reliability Analysis

The analysis examines alternative interpretations of inspection dates, conflicting records, and source coverage.

This helps distinguish robust findings from recommendations that may depend on uncertain or incomplete data.

## Case Study: Mining Safety Review (2023–2025)

The analytical scope covers active surface crushed-limestone operations represented in the supplied mine master.

**Dataset:** 1,275 eligible operations.

Under the baseline prioritization policy, the reference analysis identifies the following leading candidates:

| Mining Operation | MSHA Mine ID | Qualifying S&S Events |
|---|---|---|
| Neely's Landing Quarry | 2300758 | 13 |
| Amrize Three Rivers Quarry | 1500100 | 10 |
| Amrize Millville Quarry | 4600027 | 9 |

**Reference recommendation:** Prioritize Neely's Landing Quarry for an independent review of recurring enforcement concerns.

The selected operation has 13 qualifying inspection events spanning two inspection years, with 53 associated S&S violations.

The recommendation remains unchanged under the five documented sensitivity scenarios.

These results represent a historical, policy-based screening exercise—not a determination of present unsafe conditions or overall mining risk.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas |
| Structured Data | CSV, TXT, SQLite |
| Data Analysis | Relational joins, aggregation, statistical indicators |
| Decision Logic | Deterministic policy-based ranking |
| Validation | Python-based automated tests |
| Execution | Bash, Docker |
| Reporting | Markdown, CSV, JSON |

## Project Structure

```text
MineSafety/
├── environment/
│   ├── Dockerfile
│   └── data/
│       └── Source datasets
├── solution/
│   ├── solve.py
│   ├── solve.sh
│   └── pdf_guidance.py
├── tests/
│   ├── test.sh
│   ├── test_outputs.py
│   └── test_weights.json
├── instruction.md
├── task_card.md
├── rubrics.json
├── task.toml
└── README.md
```

Large source datasets may be excluded from the GitHub repository because of file-size restrictions. They must be supplied separately in the expected directory structure before execution.

## Running the Project

### Requirements

- Python 3
- Project dependencies, including Pandas
- Bash-compatible environment
- Source datasets in `environment/data/`

### Execute the analytical pipeline

From the project root:

```bash
bash solution/solve.sh
```

Alternatively, inspect `solution/solve.py` for the supported direct Python execution options.

### Run validation

```bash
bash tests/test.sh
```

The test suite is designed to verify required outputs and implementation constraints.

## Engineering Challenges

**Large dataset processing:** Working with substantial administrative datasets while keeping processing structured and reproducible.

**Record reconciliation:** Connecting information from multiple sources without accidentally multiplying records or double-counting inspection events.

**Temporal consistency:** Handling differences between violation reporting years and inspection event dates.

**Data reliability:** Investigating missing, duplicated, conflicting, and incompletely linked records.

**Decision transparency:** Ensuring that recommendations can be explained through explicit rules and independently inspected evidence.

## Project Highlights

- Developed an end-to-end Python analytical pipeline.
- Integrated heterogeneous safety and operational datasets.
- Applied deterministic ranking and explainable decision logic.
- Distinguished inspection-level recurrence from individual violation counts.
- Incorporated data-quality checks and sensitivity scenarios.
- Structured automated tests and evaluation artifacts to support reproducible analysis.
- Produced evidence-oriented outputs suitable for analytical review.

## Limitations

MineSafety analyzes historical administrative records, which may contain missing information, reporting inconsistencies, and differences in inspection intensity.

Its recommendations depend on the explicitly defined decision objective and should not be interpreted as a comprehensive safety-risk assessment or evidence of current regulatory noncompliance.

The included analytical reference results should not be interpreted as independently verified predictions of future accidents.
