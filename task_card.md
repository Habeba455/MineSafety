# Task description

An independent advisory team must select one currently active U.S. surface crushed-limestone operation for a funded review of recurring Significant and Substantial (S&S) enforcement concerns in 2023–2025.

The revised funding policy prioritizes the greatest number of distinct qualifying inspection events. A qualifying event requires an inspection record in the review period and an associated S&S violation recorded in the same review period. Ties are resolved by the number of inspection years containing qualifying events, then by the number of associated S&S violations. A remaining tie must be disclosed.

Injury experience, work-hour exposure and inspection activity contextualize the review. They do not enter a weighted selection score. There is no minimum-hours eligibility threshold and no requirement for complete annual exposure reporting to remain eligible.

The analyst produces recommendation.md, analysis/summary.csv, analysis/sensitivity.csv and analysis/data_quality.json under /workspace/output/.

# Complexity justification

The following challenges arise from the supplied records. They are observed source characteristics, not claims that synthetic anomalies were planted.

## 1. Violation records versus inspection events

Several S&S violations can arise from one inspection event. A correct analysis distinguishes violation volume from recurrence across separate events and links records using mine and event identifiers together. A careless analysis can inflate recurrence by counting citation rows as independent inspection occasions.

For the selected mine, 53 S&S violation records correspond to 13 qualifying events. However, this mine also leads raw S&S violation counts in the original 243-mine cohort. The evidence does not establish that confusing these measures necessarily changes the selected operation. This is a measurement challenge, not yet a validated decision-changing crux.

## 2. Reporting-window reconciliation

An in-window violation can refer to an event whose inspection record falls outside the review period. A correct analysis distinguishes historical linkage from qualifying in-window linkage and discloses differences between reported calendar year and inspection dates. A careless analysis may count every historically linked event as qualifying.

For mine 2300781, the supplied violation records reference nine distinct S&S-associated events, but only eight have qualifying inspection records under the baseline calendar-year interpretation. Seventeen of its twenty S&S violations link to those qualifying events. This changes comparative evidence, although the tested interpretations do not change the selected mine.

## 3. Eligibility versus exposure completeness

The eligible population is determined by current mine-master status, mine type and commodity. Work-hour coverage supports contextual injury comparisons; it does not determine review eligibility. A correct analysis retains operations with incomplete exposure, reports coverage, and distinguishes missing values from zero.

The former three-year/150,000-hour filter produced 243 operations. The revised scope contains 1,275 eligible operations. A careless implementation can silently retain the old restriction, omit eligible operations, or calculate rates using incompatible reporting coverage.

## 4. Recurrence versus underlying risk

The specified decision concerns documented recurrence under a funding policy. A correct submission discusses inspection intensity, injury-based alternatives and limitations without claiming the highest underlying risk or present unsafe conditions. A careless submission may replace the funding policy with an arbitrary injury/enforcement weighting or equate administrative records with current safety conditions.

## Complexity limitation requiring review

A decision-changing analytical crux has not yet been demonstrated for this revision. Correcting the original ambiguity makes the funding policy explicit, but may simplify the decision substantially. The winning answer remains unchanged under the tested source-date and coverage interpretations. This task card therefore does not claim that the package already meets the handbook's difficulty and crux requirements.

# Taxonomy tags

- Multi-source administrative data analysis
- Entity resolution and relational joins
- Reporting-window reconciliation
- Data-quality investigation
- Exposure-aware injury comparison
- Policy-based prioritization
- Sensitivity analysis
- Evidence synthesis and decision reporting

Analytical objectives: identify the operation with the greatest qualifying recurrence; assess how source coverage and reconciliation affect that selection.

Reasoning phases:

- Explore: establish source coverage, status, identifiers and reporting periods.
- Hypothesize: examine whether apparent recurrence reflects multiple events, concentrated citations, or reporting differences.
- Analyze: reconcile sources and calculate the required comparison measures.
- Synthesize: assess limitations, competing evidence and sensitivity results.
- Recommend: select one operation under the stated funding policy and define the review focus.

# Expected difficulty range

Difficulty is unmeasured. No model evaluation sweeps have been run for this revision, and it must not be labeled validated hard.

Potential failure modes include counting violation rows instead of events, admitting out-of-window inspection events, retaining the former hours-based eligibility restriction, and substituting injury-rate priorities for the stated recurrence policy. None has yet been demonstrated to cause strong models to choose a different mine consistently.

The Task-Quality Guide's stricter stated sweep target is a strong-model mean below 0.5, no strong trial above 0.7, and weak-model means at least 0.25 below the strong-model means, based on four attempts per model. Other handbook sections describe different limits; the current project configuration or project lead must resolve the applicable acceptance settings. No compliance with any sweep threshold is claimed here.

# Ground truth recommendation and rationale

The revised baseline selects NEELY'S LANDING QUARRY, MSHA Mine ID 2300758, from 1,275 eligible operations.

| Operation | Mine ID | Qualifying S&S inspection events | Inspection years with qualifying events | S&S violations linked to qualifying events |
|---|---|---:|---:|---:|
| NEELY'S LANDING QUARRY | 2300758 | 13 | 2 | 53 |
| Amrize Three Rivers Quarry | 1500100 | 10 | 3 | 37 |
| Amrize Millville Quarry | 4600027 | 9 | 3 | 22 |

The selected mine wins on the primary criterion: 13 qualifying events exceed the closest competitor's 10. The tie-breakers are not needed. Its qualifying inspection events span two inspection calendar years under the baseline; this must not be confused with the three violation-reporting years represented by its citation records.

The selected mine has 243,150 reported work hours, four records in the reference solution's selected accident-severity categories, an injury-record rate of 3.290150 per 200,000 hours, 157 total violations, 53 S&S violations and 30 in-window inspection events. These are contextual measures and do not enter a composite decision score.

An operation with a higher injury rate can merit a different review under a different funding purpose. It does not outrank the selected mine under this task's recurrence policy merely because its injury rate is higher.

The implementation tests five scenarios:

1. Reported inspection calendar year: baseline.
2. Exclusion of conflicting or missing inspection-year assignments.
3. Inspection start year instead of reported calendar year.
4. Inspection end year instead of reported calendar year.
5. A coverage stress bound admitting S&S events lacking qualifying inspection records.

All five select mine 2300758 with 13 events in the supplied data. The fifth scenario deliberately relaxes the baseline evidence requirement and is labeled a stress bound; it is not an alternative baseline accepted by the funding policy. Stability in these scenarios does not prove completeness of the sources or robustness to every possible interpretation.

This recommendation prioritizes independent investigation of historical recurrence. It is not a finding of present unsafe conditions, current noncompliance or the highest underlying safety risk.

# Expected reasoning trajectory

Establish the active surface crushed-limestone population from the supplied mine master and disclose the status snapshot's limitations. Reconcile violation records with inspection events, distinguishing in-window qualification from historical association and violation counts from event counts.

Calculate recurrence under the stated priorities, retaining all eligible operations. Use work-hour and accident data to contextualize injury-based alternatives without changing the funding objective. Examine material source-window and coverage uncertainties and report their effect on the choice.

Produce a decision memorandum, complete comparison CSV, sensitivity CSV and structured data-quality record. Derive comparisons from the supplied records rather than manually inserted competitor figures.

# Validation status and outstanding package work

- The revised reference script has run successfully against the supplied data and generated all four deliverables.
- Its output selected mine 2300758 from 1,275 operations.
- The output verifier's 19 check functions passed against those outputs and all failed against empty output when invoked directly.
- Twelve deliberately corrupted output variants triggered failures; heading, punctuation, row-order and column-order changes remained accepted.
- pytest, the test.sh/CTRF pipeline and Harbor oracle/nop checks have not been executed in this working environment. Direct function checks are not a substitute for those package gates.
- Narrative grading has not been run through the platform rubric judge.
- Model sweeps and the decision-changing crux remain unvalidated.
- The supplied SQLite, PDF and address data do not contribute to the revised script's selection. Their roles, the multi-format complexity requirement and the distractor limit must be reassessed for this revision.
- Package-wide personal-information removal, licensing verification and archive cleanup remain separate outstanding work. This revision must not be described as submission-ready.
