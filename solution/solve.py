#!/usr/bin/env python3
"""Reference solution for the revised recurrence-priority instruction.md.

Requires pandas. Run: python solution/solve.py [--data-dir PATH]
Outputs default to $OUTPUT_DIR or /workspace/output.
No weighted risk score, minimum-hours filter, or hard-coded selected mine.
"""
from pathlib import Path
import argparse
import json
import os
import pandas as pd

YEARS = {'2023', '2024', '2025'}
KEYS = ['MINE_ID', 'EVENT_NO']
SERIOUS_CODES = {'01', '02', '03', '04', '05'}
DECISION = ['SS_INSPECTION_EVENTS', 'SS_EVENT_YEARS', 'QUALIFYING_SS_VIOLATIONS']
SUMMARY = ['MINE_ID', 'CURRENT_MINE_NAME', 'PRIORITY_RANK', 'TOTAL_HOURS',
           'HOURS_YEARS_REPORTED', 'SERIOUS_RECORDS', 'INJURY_RATE',
           'TOTAL_VIOLATIONS', 'SS_VIOLATIONS', 'TOTAL_INSPECTIONS', *DECISION]


def read_csv(path, columns, separator=',', encoding='utf-8', year=None):
    frames = []
    for frame in pd.read_csv(path, usecols=columns, dtype='string', sep=separator,
                             encoding=encoding, chunksize=100000):
        for column in columns:
            frame[column] = frame[column].str.strip()
        if year:
            frame = frame[frame[year].isin(YEARS)]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)


def unique_records(frame, key, source, findings):
    before = len(frame)
    frame = frame.drop_duplicates().copy()
    findings.append({'source': source, 'exact_duplicate_rows_removed': before - len(frame)})
    if frame[key].isna().any().any():
        raise ValueError(f'{source}: missing record identifiers require resolution')
    if frame.duplicated(key).any():
        raise ValueError(f'{source}: conflicting duplicate record identifiers require resolution')
    return frame


def table(frame):
    def cell(value):
        if pd.isna(value):
            return 'Unavailable'
        if isinstance(value, float):
            return f'{value:.6f}'
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines = ['| ' + ' | '.join(frame.columns) + ' |',
             '|' + '|'.join(['---'] * len(frame.columns)) + '|']
    lines += ['| ' + ' | '.join(cell(x) for x in row) + ' |'
              for row in frame.itertuples(index=False, name=None)]
    return '\n'.join(lines)


def inspection_lookup(inspections, year_column, strict=False):
    """Reduce a mine-event to one year without multiplying violation rows.

    Default: latest reported year within the requested window. Strict scenario:
    remove events with more than one year value or missing year values.
    This treatment is disclosed; alternatives are tested, never hidden.
    """
    source = inspections[KEYS + [year_column]].rename(columns={year_column: 'EVENT_YEAR'})
    if strict:
        variations = source.groupby(KEYS)['EVENT_YEAR'].nunique(dropna=False)
        allowed = variations[variations.eq(1)].reset_index()[KEYS]
        source = source.merge(allowed, on=KEYS, validate='many_to_one')
    source = source[source.EVENT_YEAR.isin(YEARS)].drop_duplicates()
    return source.sort_values('EVENT_YEAR').drop_duplicates(KEYS, keep='last')


def decision_table(mines, violations, lookup):
    ss = violations[violations.SIG_SUB.eq('Y')]
    linked = ss.merge(lookup, on=KEYS, how='inner', validate='many_to_one')
    counts = linked.groupby('MINE_ID').agg(
        SS_INSPECTION_EVENTS=('EVENT_NO', 'nunique'),
        SS_EVENT_YEARS=('EVENT_YEAR', 'nunique'),
        QUALIFYING_SS_VIOLATIONS=('VIOLATION_NO', 'nunique'))
    ranked = mines[['MINE_ID', 'CURRENT_MINE_NAME']].merge(counts, on='MINE_ID', how='left')
    ranked[DECISION] = ranked[DECISION].fillna(0).astype('int64')
    ranked = ranked.sort_values(DECISION + ['MINE_ID'], ascending=[False]*3 + [True])
    # Standard competition ranks; mine ID only orders tied rows for display.
    ranks, previous, current = [], None, 0
    for position, values in enumerate(ranked[DECISION].itertuples(index=False, name=None), 1):
        if values != previous:
            current, previous = position, values
        ranks.append(current)
    ranked['PRIORITY_RANK'] = ranks
    return ranked, linked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--output-dir', type=Path,
                        default=Path(os.environ.get('OUTPUT_DIR', '/workspace/output')))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    candidates = [root/'environment'/'data', root/'data', Path('/workspace/data')]
    data = args.data_dir or next((p for p in candidates if (p/'Mines.csv').is_file()), None)
    if data is None:
        raise FileNotFoundError('Cannot locate input data; pass --data-dir')
    out = args.output_dir
    analysis = out/'analysis'
    analysis.mkdir(parents=True, exist_ok=True)
    reconciliation, exclusions, unresolved, coverage = [], [], [], []

    print('Loading mines and exposure...', flush=True)
    mine_columns = ['MINE_ID', 'CURRENT_MINE_NAME', 'CURRENT_MINE_STATUS',
                    'CURRENT_MINE_TYPE', 'COAL_METAL_IND', 'PRIMARY_SIC', 'CURRENT_STATUS_DT']
    mines_all = unique_records(read_csv(data/'Mines.csv', mine_columns), ['MINE_ID'],
                               'Mines.csv', reconciliation)
    mines = mines_all[mines_all.CURRENT_MINE_STATUS.eq('Active') &
                      mines_all.CURRENT_MINE_TYPE.eq('Surface') &
                      mines_all.COAL_METAL_IND.eq('M') &
                      mines_all.PRIMARY_SIC.eq('Crushed, Broken Limestone NEC')].copy()
    if mines.empty:
        raise ValueError('No eligible mines')
    ids = set(mines.MINE_ID)
    exclusions.append({'source': 'Mines.csv', 'reason': 'Outside activity/type/commodity scope',
                       'records': len(mines_all)-len(mines)})
    coverage.append({'source': 'Mines.csv', 'eligible_operations': len(mines),
                     'status_basis': 'CURRENT_MINE_STATUS and CURRENT_STATUS_DT in supplied file',
                     'limitation': 'Status date is not an independently established extract date.'})

    prod = read_csv(data/'MinesProdYearly.csv',
                    ['MINE_ID', 'CALENDAR_YR', 'SUBUNIT_CD', 'ANNUAL_HRS'], year='CALENDAR_YR')
    prod = unique_records(prod, ['MINE_ID','CALENDAR_YR','SUBUNIT_CD'],
                          'MinesProdYearly.csv', reconciliation)
    prod = prod[prod.MINE_ID.isin(ids)].copy()
    prod['HOURS'] = pd.to_numeric(prod.ANNUAL_HRS, errors='coerce')
    invalid_hours = prod.HOURS.isna() | prod.HOURS.lt(0)
    prod.loc[invalid_hours, 'HOURS'] = float('nan')
    # Do not make a partly invalid annual total appear complete.
    annual = prod.groupby(['MINE_ID','CALENDAR_YR']).HOURS.agg(
        lambda x: x.sum() if x.notna().all() else float('nan')).reset_index()
    hours = annual.groupby('MINE_ID').HOURS.sum(min_count=1).rename('TOTAL_HOURS')
    n_years = annual[annual.HOURS.notna()].groupby('MINE_ID').size().rename('HOURS_YEARS_REPORTED')
    exclusions.append({'source': 'MinesProdYearly.csv', 'reason': 'Invalid or negative hours',
                       'records': int(invalid_hours.sum()), 'treatment': 'Affected annual totals unavailable'})

    print('Loading accident and violation records...', flush=True)
    acols = ['MINE_ID','DOCUMENT_NO','CAL_YR','DEGREE_INJURY_CD']
    if (data/'Accidents.txt').is_file():
        accidents = read_csv(data/'Accidents.txt', acols, '|', 'latin1', 'CAL_YR')
    else:
        accidents = read_csv(data/'Accidents.csv', acols, year='CAL_YR')
    accidents = unique_records(accidents, ['DOCUMENT_NO'], 'Accidents', reconciliation)
    accidents = accidents[accidents.MINE_ID.isin(ids)]
    accidents = accidents[accidents.DEGREE_INJURY_CD.isin(SERIOUS_CODES)]
    injury = accidents.groupby('MINE_ID').size().rename('SERIOUS_RECORDS')

    vcols = ['MINE_ID','EVENT_NO','VIOLATION_NO','CAL_YR','SIG_SUB']
    files = sorted(data.glob('Violations_part*.csv'))
    if not files:
        files = [data/'Violations.csv']
    violations = pd.concat([read_csv(p, vcols, year='CAL_YR') for p in files], ignore_index=True)
    violations = unique_records(violations, ['VIOLATION_NO'], 'Violations', reconciliation)
    violations = violations[violations.MINE_ID.isin(ids)].copy()
    missing_event = violations.EVENT_NO.isna() | violations.EVENT_NO.eq('')
    exclusions.append({'source': 'Violations', 'reason': 'Missing event ID; excluded from event linkage',
                       'records': int(missing_event.sum())})
    valid_v = violations[~missing_event].copy()
    coverage.append({'source': 'Violations', 'period': '2023–2025 by CAL_YR',
                     'files': [p.name for p in files],
                     'limitation': 'S&S is the supplied SIG_SUB classification; no independent legal reclassification.'})

    print('Reconciling inspection events...', flush=True)
    icols = KEYS + ['CAL_YR','INSPECTION_BEGIN_DT','INSPECTION_END_DT']
    inspections = read_csv(data/'Inspections.csv', icols)
    inspections = inspections[inspections.MINE_ID.isin(ids)].copy()
    missing_i = inspections[KEYS].isna().any(axis=1) | inspections.EVENT_NO.eq('')
    exclusions.append({'source': 'Inspections.csv', 'reason': 'Missing mine/event key',
                       'records': int(missing_i.sum())})
    inspections = inspections[~missing_i]
    exact_duplicates = int(inspections.duplicated().sum())
    inspections = inspections.drop_duplicates()
    variation = inspections.groupby(KEYS).CAL_YR.nunique(dropna=False)
    conflicting = variation[variation.gt(1)].reset_index()[KEYS]
    for column, label in [('INSPECTION_BEGIN_DT','BEGIN_YEAR'),('INSPECTION_END_DT','END_YEAR')]:
        inspections[label] = pd.to_datetime(inspections[column], format='%m/%d/%Y', errors='coerce').dt.strftime('%Y').astype('string')
    mismatch = inspections.CAL_YR.ne(inspections.BEGIN_YEAR).fillna(False)
    reconciliation.append({'source': 'Inspections.csv', 'exact_duplicate_rows_removed': exact_duplicates,
                           'conflicting_calendar_year_keys': len(conflicting),
                           'calendar_year_differs_from_start_year_rows': int(mismatch.sum()),
                           'treatment': 'Baseline uses reported CAL_YR; one mine-event counted once; latest in-window year for multi-year keys. Date alternatives tested.'})
    lookup = inspection_lookup(inspections, 'CAL_YR')
    ranking, linked = decision_table(mines, valid_v, lookup)
    top_ids = set(ranking.loc[ranking.PRIORITY_RANK.eq(1), 'MINE_ID'])
    counts = violations.groupby('MINE_ID').size().rename('TOTAL_VIOLATIONS')
    ss_counts = violations[violations.SIG_SUB.eq('Y')].groupby('MINE_ID').size().rename('SS_VIOLATIONS')
    inspection_counts = lookup.groupby('MINE_ID').size().rename('TOTAL_INSPECTIONS')
    summary = ranking.copy()
    for series in [hours, n_years, injury, counts, ss_counts, inspection_counts]:
        summary = summary.merge(series, on='MINE_ID', how='left', validate='one_to_one')
    count_columns = ['HOURS_YEARS_REPORTED','SERIOUS_RECORDS','TOTAL_VIOLATIONS','SS_VIOLATIONS','TOTAL_INSPECTIONS']
    summary[count_columns] = summary[count_columns].fillna(0).astype('int64')
    summary['INJURY_RATE'] = float('nan')
    aligned = summary.HOURS_YEARS_REPORTED.eq(3) & summary.TOTAL_HOURS.gt(0)
    summary.loc[aligned,'INJURY_RATE'] = summary.loc[aligned,'SERIOUS_RECORDS'] / summary.loc[aligned,'TOTAL_HOURS'] * 200000
    summary[SUMMARY].to_csv(analysis/'summary.csv', index=False, float_format='%.6f', na_rep='')
    coverage.append({'source': 'MinesProdYearly.csv / Accidents', 'period': '2023–2025',
                     'mines_with_complete_hours': int(aligned.sum()),
                     'mines_without_calculable_rate': int((~aligned).sum()),
                     'limitation': 'Rates describe selected records, not an official MSHA incidence rate. Operator/contractor and subunit population alignment is not independently verified.'})

    all_lookup = inspections[KEYS].drop_duplicates()
    event_check = valid_v.merge(all_lookup.assign(HISTORICAL=True), on=KEYS, how='left', validate='many_to_one')
    no_history = int(event_check.HISTORICAL.isna().sum())
    recent_check = valid_v.merge(lookup, on=KEYS, how='left', validate='many_to_one')
    no_recent = int(recent_check.EVENT_YEAR.isna().sum())
    exclusions.append({'source': 'Violations', 'reason': 'No qualifying review-period inspection record',
                       'records': no_recent, 'without_any_historical_inspection': no_history,
                       'treatment': 'Retained in violation totals, excluded from qualifying-event counts'})
    coverage.append({'source': 'Inspections.csv', 'period': 'All supplied years searched; 2023–2025 decision window',
                     'limitation': 'Event linkage demonstrates record association, not uniform inspection intensity or complete reporting.'})

    scenarios = [
        ('baseline', 'Reported inspection CAL_YR', lookup, valid_v, 'Reporting year governs the baseline decision.'),
        ('strict_year', 'Exclude inspection keys with conflicting or missing calendar years',
         inspection_lookup(inspections,'CAL_YR',True), valid_v, 'Tests ambiguity in historical year assignments.'),
        ('inspection_start', 'Use inspection start year instead of reported calendar year',
         inspection_lookup(inspections,'BEGIN_YEAR'), valid_v, 'Missing/unparseable start dates excluded; cross-year events may move.'),
        ('inspection_end', 'Use inspection end year instead of reported calendar year',
         inspection_lookup(inspections,'END_YEAR'), valid_v, 'Missing/unparseable end dates excluded; cross-year events may move.'),
    ]
    # Deliberately labeled coverage stress case; does not silently relax baseline eligibility.
    ss_only = valid_v[valid_v.SIG_SUB.eq('Y')][KEYS+['CAL_YR']].rename(columns={'CAL_YR':'EVENT_YEAR'})
    ss_only = ss_only.sort_values('EVENT_YEAR').drop_duplicates(KEYS,keep='last')
    scenarios.append(('unmatched_stress', 'Assume S&S events lacking qualifying inspection records belong in-window',
                      ss_only, valid_v, 'Coverage stress bound only; does not satisfy the baseline requirement for an inspection record.'))
    rows = []
    for sid, description, look, source, limitation in scenarios:
        ranks, _ = decision_table(mines, source, look)
        winners = ranks[ranks.PRIORITY_RANK.eq(1)]
        changed = set(winners.MINE_ID) != top_ids
        for row in winners.itertuples():
            rows.append({'SCENARIO_ID':sid,'ASSUMPTION_CHANGE':description,
                         'SELECTED_MINE_ID':row.MINE_ID,'SELECTED_MINE_NAME':row.CURRENT_MINE_NAME,
                         'SS_INSPECTION_EVENTS':row.SS_INSPECTION_EVENTS,
                         'SELECTION_CHANGED':str(changed).lower(),
                         'LIMITATION':limitation+(' Unresolved top tie.' if len(winners)>1 else '')})
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv(analysis/'sensitivity.csv',index=False)
    unresolved.extend([
        {'issue':'No independently verified dataset extraction date', 'effect':'Active status refers to the supplied snapshot only.'},
        {'issue':'Unequal inspection intensity and incomplete source coverage', 'effect':'Observed recurrence does not estimate underlying safety risk.'},
        {'issue':'Injury numerator/exposure population alignment', 'effect':'Injury rates are contextual screening measures only and do not determine selection.'},
    ])
    if len(conflicting):
        unresolved.append({'issue':'Inspection keys have conflicting calendar years','count':len(conflicting),
                           'effect':'Alternative year handling is tested in sensitivity.csv.'})
    if sensitivity.SELECTION_CHANGED.eq('true').any():
        unresolved.append({'issue':'Selection changes in a tested scenario','effect':'Recommendation is conditional on the documented baseline reconciliation.'})
    if len(top_ids)!=1:
        unresolved.append({'issue':'Unresolved first-place tie','effect':'A unique recommendation cannot be justified by the stated policy.'})
    quality = {'source_coverage':coverage,'reconciliation_findings':reconciliation,
               'excluded_records':exclusions,'unresolved_issues':unresolved}
    (analysis/'data_quality.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

    # All decision evidence and competitor values are derived from this run.
    winners = summary[summary.PRIORITY_RANK.eq(1)]
    if len(winners)==1:
        winner = winners.iloc[0]
        name, mid = winner.CURRENT_MINE_NAME, winner.MINE_ID
        recommendation = f'Prioritize **{name}**, MSHA Mine ID **{mid}**, for the funded independent review of recurring S&S enforcement concerns.'
        status = mines.set_index('MINE_ID').loc[mid,'CURRENT_STATUS_DT']
        status_text = str(status) if pd.notna(status) else 'not supplied'
        annual_evidence = linked[linked.MINE_ID.eq(mid)].groupby('EVENT_YEAR').agg(
            SS_INSPECTION_EVENTS=('EVENT_NO','nunique'), QUALIFYING_SS_VIOLATIONS=('VIOLATION_NO','nunique')).reset_index()
        selected_text = f'The selected operation has {int(winner.SS_INSPECTION_EVENTS)} qualifying events across {int(winner.SS_EVENT_YEARS)} inspection years, associated with {int(winner.QUALIFYING_SS_VIOLATIONS)} S&S violations. Its supplied current status is Active, with status date {status_text}. That date does not establish the extraction date.'
        annual_text = table(annual_evidence)
    else:
        recommendation = 'The stated priorities leave an unresolved first-place tie. No unique recommendation is justified.'
        selected_text = table(winners[['MINE_ID','CURRENT_MINE_NAME']+DECISION])
        annual_text = 'No unique selected operation.'
    competitors = summary.head(6)[['MINE_ID','CURRENT_MINE_NAME']+DECISION+['TOTAL_INSPECTIONS']]
    injury_alternatives = summary[summary.INJURY_RATE.notna() & ~summary.MINE_ID.isin(top_ids)].nlargest(3,'INJURY_RATE')
    stable = sensitivity.SELECTION_CHANGED.eq('false').all()
    memo = f'''# Mining Safety: Recurring Enforcement Review

## Recommendation

{recommendation}

This decision implements the funding committee's recurrence priority. It is not a finding of current unsafe conditions, regulatory noncompliance, or the highest underlying safety risk.

## Scope and status

All {len(mines)} active surface metal/nonmetal operations classified as Crushed, Broken Limestone NEC in the supplied mine master are included. No work-hour threshold or three-year exposure requirement determines eligibility. The review covers 2023–2025. Status refers to the supplied snapshot, whose extraction date is not independently established.

{selected_text}

## Decision evidence

{table(competitors)}

The priority order is qualifying distinct inspection events, then distinct inspection years containing those events, then associated S&S violations. Tied rows share a rank. Mine ID only provides reproducible display order and never breaks a policy tie. Multiple citations within one event are counted as one recurrence occasion; separate events are not assumed statistically independent.

### Selected operation by inspection year

{annual_text}

## Injury-based alternatives

{table(injury_alternatives[['MINE_ID','CURRENT_MINE_NAME','TOTAL_HOURS','SERIOUS_RECORDS','INJURY_RATE','SS_INSPECTION_EVENTS']])}

These alternatives warrant attention under an injury-focused objective. Injury rates are selected accident records per 200,000 reported work hours. They inform review scope but do not override this fund's recurrence criterion. Small exposure denominators can produce unstable rates. The comparison does not infer that lower injury counts indicate safer working conditions.

## Definitions and reconciliation

- Eligibility uses current master status, surface mine type, metal/nonmetal classification, and the stated commodity.
- Baseline violations and inspections use their reported CAL_YR for the 2023–2025 window. Cross-source matching uses the mine ID and event ID together.
- A qualifying event has at least one in-window SIG_SUB=Y violation and a corresponding in-window inspection record. S&S classification is accepted as recorded, not independently reassessed.
- Exact duplicates are removed. Conflicting violation, accident, production, or master record identifiers halt the run for review. Multiple historical inspection rows collapse to one event; if multiple inspection years remain, the latest in-window year supplies the annual attribution. Strict exclusion and date-based alternatives are tested.
- SS_VIOLATIONS includes all recorded S&S violations in scope. QUALIFYING_SS_VIOLATIONS includes only those linked to qualifying events. TOTAL_INSPECTIONS counts all distinct in-window inspection events for each eligible mine.
- TOTAL_HOURS sums available valid annual exposure; HOURS_YEARS_REPORTED discloses its coverage. Missing annual exposure is not zero. Invalid subunit hours make that annual total unavailable.
- SERIOUS_RECORDS counts supplied accident records with DEGREE_INJURY_CD in 01–05. This operational selection follows the earlier analysis convention; it is not labeled an official MSHA incidence measure or independently validated injury classification.
- INJURY_RATE is reported only with valid work-hour data in all three years and positive total hours. Operator/contractor population alignment remains unverified. These contextual values do not determine selection.
- Zero event or violation counts mean zero qualifying records found in the supplied files; they do not establish absence of actual concerns or complete source reporting.

## Sensitivity and uncertainty

{table(sensitivity[['SCENARIO_ID','SELECTED_MINE_ID','SS_INSPECTION_EVENTS','SELECTION_CHANGED']])}

{'The selected set is unchanged in the tested scenarios.' if stable else 'The selected set changes in at least one scenario; the baseline conclusion is conditional on its stated reconciliation.'} This does not prove robustness to every possible missing record or alternative source interpretation. The unmatched-event scenario is an explicit coverage stress bound, not a valid replacement for the required baseline evidence.

## Data quality

{no_recent} in-scope violation records lack a matching in-window inspection event; {no_history} lack any historical inspection match. {len(conflicting)} inspection keys have conflicting reported calendar years. The eligible inspection extract contains {exact_duplicates} exact duplicate rows. {int((~aligned).sum())} operations lack a calculable full-period injury rate. Detailed coverage, exclusions and unresolved issues are recorded in analysis/data_quality.json.

## Proposed independent review

Examine original records for the qualifying events, the hazards cited, corrective actions and evidence of closure. Determine whether repeated findings concern the same hazards or distinct conditions, and consider changes in operation or management. Review inspection intensity and scope, work-hour exposure, reporting completeness, and injury records before drawing conclusions about safety controls. The historical recurrence count alone does not prove failed corrective action.

## Reproducibility and limits

The accompanying reference script generates all figures and tables from the supplied mine, production, accident, violation and inspection records. No external data or manually entered competitor figures are used. Operator-history and address records are not used in the selection. The supplied citation handbook is not parsed by this script; no legal interpretation is claimed. The output is a review priority under a defined funding policy, not a comprehensive risk model.
'''
    (out/'recommendation.md').write_text(memo,encoding='utf-8')
    print(json.dumps({'eligible_mines':len(mines),'selected_mine_ids':sorted(top_ids),
                      'selection_stable_in_tested_scenarios':bool(stable),'output':str(out)},indent=2))
    if len(top_ids)!=1:
        raise SystemExit('Outputs written, but benchmark requires redesign: unresolved top tie.')


if __name__ == '__main__':
    main()
