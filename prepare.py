"""Prepare HDB data without deleting records. Usage: python prepare.py --input raw.csv --out prepared_v1"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    source, dest = args.input.resolve(), args.out.resolve()
    if source.parent == dest or (dest.exists() and any(dest.iterdir())):
        raise ValueError('Use a separate, empty output directory.')
    raw = pd.read_csv(source, dtype=str, keep_default_na=False)
    expected = ['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','flat_model','lease_commence_date','remaining_lease','resale_price']
    if list(raw.columns) != expected:
        raise ValueError('Unexpected schema; inspect source before proceeding.')
    blanks = raw.apply(lambda s: s.str.strip().eq('').sum()).astype(int)
    if blanks.any():
        raise ValueError(f'Blank fields require review: {blanks.to_dict()}')
    df = raw.copy()
    # This identifies a CSV record, not a real-world transaction or flat.
    df.insert(0, 'source_row', np.arange(2,len(df)+2))
    for c in ['town','flat_type','block','street_name','flat_model']:
        df[c] = df[c].str.strip().str.replace(r'\s+', ' ', regex=True)
    df['address_key'] = df['block'].str.upper()+' '+df['street_name'].str.upper()
    date = pd.to_datetime(df['month'], format='%Y-%m', errors='raise')
    df['transaction_year'], df['transaction_month_number'] = date.dt.year, date.dt.month
    for c in ['floor_area_sqm','resale_price','lease_commence_date']:
        df[c] = pd.to_numeric(df[c], errors='raise')
        if not np.isfinite(df[c]).all() or df[c].le(0).any():
            raise ValueError(f'Invalid or nonpositive values in {c}')
    if df['lease_commence_date'].gt(df['transaction_year']).any():
        raise ValueError('Lease commencement after transaction year requires review.')
    lease = df['remaining_lease'].str.extract(r'^(\d+) years?(?: (\d+) months?)?$')
    if lease[0].isna().any():
        raise ValueError('Unrecognised remaining lease format.')
    years = pd.to_numeric(lease[0], errors='raise')
    months = pd.to_numeric(lease[1].fillna('0'), errors='raise')
    if months.ge(12).any():
        raise ValueError('Invalid remaining lease month component.')
    df['remaining_lease_months'] = years*12+months
    df['remaining_lease_years'] = df['remaining_lease_months']/12
    storey = df['storey_range'].str.extract(r'^(\d+) TO (\d+)$')
    if storey.isna().any().any():
        raise ValueError('Unrecognised storey range.')
    df['storey_lower'] = pd.to_numeric(storey[0],errors='raise')
    df['storey_upper'] = pd.to_numeric(storey[1],errors='raise')
    if df['storey_lower'].gt(df['storey_upper']).any():
        raise ValueError('Reversed storey range.')
    # No CPI data was supplied. This is explicitly nominal, not real price.
    df['log_nominal_resale_price'] = np.log(df['resale_price'])
    df['same_public_fields_flag'] = raw.duplicated(keep=False)
    if df.groupby('address_key')['town'].nunique().gt(1).any():
        raise ValueError('An address maps to multiple towns; review first.')
    addresses = df.groupby('address_key',sort=True).agg(
        block=('block','first'),street_name=('street_name','first'),town=('town','first'),
        transaction_count=('source_row','size'),first_month=('month','min'),last_month=('month','max')).reset_index()
    addresses['search_query'] = addresses['address_key']+' SINGAPORE'
    audit = {
        'source_filename':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'raw_rows':len(raw),'prepared_rows':len(df),'rows_dropped':0,'source_columns':expected,
        'blank_counts':blanks.to_dict(),'first_month':raw['month'].min(),'last_month':raw['month'].max(),
        'monthly_counts':raw['month'].value_counts().sort_index().to_dict(),
        'unique_addresses':len(addresses),'exact_duplicate_excess_rows_if_deduplicated':int(raw.duplicated().sum()),
        'rows_flagged_for_identical_public_fields':int(df['same_public_fields_flag'].sum()),
        'duplicates_policy':'All retained; source has no unit number or transaction identifier.',
        'inflation_adjustment':'Not performed. Log price is nominal.',
        'geocoding':'Not performed. Address queue is not verified coordinates.',
        'mrt_distance':'Not computed. Coordinates and historical coverage policy are needed.'}
    dest.mkdir(parents=True,exist_ok=True)
    df.to_csv(dest/'hdb.csv',index=False,encoding='utf-8-sig')
    addresses.to_csv(dest/'addresses.csv',index=False,encoding='utf-8-sig')
    raw.loc[raw.duplicated(keep=False)].to_csv(dest/'duplicates.csv',index=False,encoding='utf-8-sig')
    (dest/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    # Reopen outputs to verify row preservation, block identifiers, and join coverage.
    saved = pd.read_csv(dest/'hdb.csv',dtype={'block':str})
    queue = pd.read_csv(dest/'addresses.csv',dtype={'block':str})
    assert len(saved)==len(raw)
    assert saved['block'].tolist()==df['block'].tolist()
    assert saved['source_row'].is_unique and queue['address_key'].is_unique
    assert int(queue['transaction_count'].sum())==len(raw)
    assert len(saved.merge(queue[['address_key']],on='address_key',validate='many_to_one'))==len(raw)
    print(json.dumps({k:audit[k] for k in ['raw_rows','prepared_rows','rows_dropped','unique_addresses','first_month','last_month']}))


if __name__=='__main__':
    main()
