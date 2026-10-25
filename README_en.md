# Data Cleaning

Basic cleaning of the supplied HDB transaction data is complete. Use `data/hdb_clean.csv` for subsequent analysis and the handover to B. MRT distances and inflation adjustments have not yet been added.

## Dataset Versions

| Dataset | Rows | Columns | Purpose |
| --- | ---: | ---: | --- |
| Original HDB CSV | 240,919 | 11 | Archived source snapshot, January 2017-September 2026 |
| `data/hdb.csv` | 240,919 | 21 | Prepared input used by the notebook |
| `data/hdb_clean.csv` | 240,919 | 20 | Current analysis table, with separate `year` and numeric `month` |

The prepared input contains a combined YYYY-MM period and two date aliases. The cleaned output replaces these with `year` and `month`, reducing the column count from 21 to 20 without removing any records.

## Data Quality and Cleaning Completed

- **Coverage:** January 2017-September 2026, covering 117 consecutive months. The data contains 26 towns, 7 flat types and 21 flat models.
- **Missing values:** No missing or blank values in the cleaned dataset.
- **Text and identifiers:** Whitespace is standardised. `block` remains text, preserving letters and any leading zeros. `source_row` is unique.
- **Date fields:** `year` and `month` are integers and match the source registration period. Month values range from 1 to 12.
- **Numeric checks:** Prices and floor areas are positive and finite. Lease commencement years, remaining-lease conversions, floor-band endpoints and log prices are consistent.
- **Storey bands:** The notebook uses an ordered categorical variable with 17 bands, from `01 TO 03` to `49 TO 51`. The exact floor is unavailable.
- **Identical public records:** 635 records share all original public fields with other records; deduplication would remove 318 rows. All are retained and flagged because unit numbers and unique transaction IDs are unavailable.
- **Address checks:** There are 9,749 distinct addresses. Address keys are unique in `addresses.csv`, each address belongs to one town, and all transaction addresses match this list. A many-to-one join preserves all 240,919 transaction rows.
- **Extreme values:** Observed prices range from S$140,000 to S$1,728,000 and floor areas from 31 to 366.7 square metres. These values match the prepared input and are retained; no automatic outlier removal or winsorisation was applied. The largest-area record is labelled `Terrace` in the source.
- **Annual coverage:** 2017-2025 contains 222,067 records. The 18,852 records for 2026 cover January-September only. The presence of records does not establish that the latest month is complete.

## Cleaned Dataset Field Guide

These are the 20 columns in `data/hdb_clean.csv`. Statistical roles are described below; CSV files do not preserve pandas categorical types or ordering.

| Column | Type or role | Meaning and unit |
| --- | --- | --- |
| `source_row` | Integer identifier | Original CSV row number for tracing records; not a unique transaction or unit ID |
| `year` | Integer date component | Registration year, for example 2017 |
| `month` | Integer date component | Registration month number, 1-12; for example, 2017-01 becomes year 2017 and month 1 |
| `town` | Categorical | HDB town |
| `flat_type` | Categorical | Flat type, for example 4 ROOM |
| `block` | Text identifier | Block number, including any letters |
| `street_name` | Text | Street name |
| `storey_range` | Ordered categorical (ordinal) | Floor band: 01 TO 03 means floor 1, 2 or 3; 10 TO 12 means floor 10, 11 or 12. The exact floor is unknown |
| `floor_area_sqm` | Numeric | Floor area in square metres |
| `flat_model` | Categorical | Flat model |
| `lease_commence_date` | Integer year | Lease commencement year, not a full date |
| `remaining_lease` | Text | Original remaining-lease description, retained for reference |
| `resale_price` | Numeric | Total resale price per flat in Singapore dollars (SGD); 232000 means S$232,000. Prices are nominal |
| `address_key` | Text merge key | Uppercase block number and street name; identifies a block address, not an individual unit |
| `remaining_lease_months` | Numeric, whole months | Remaining lease converted to months |
| `remaining_lease_years` | Numeric | Remaining lease in years, calculated as remaining_lease_months / 12 |
| `storey_lower` | Integer bound | Lowest floor number in the recorded floor band |
| `storey_upper` | Integer bound | Highest floor number in the recorded floor band |
| `log_nominal_resale_price` | Numeric | Natural logarithm of the nominal resale price measured in SGD; not inflation-adjusted |
| `same_public_fields_flag` | Boolean | True when all original public fields match another record; not proof of an erroneous duplicate |

`resale_price (SGD)` is a display label used in notebook tables. The CSV column remains `resale_price`, with numeric values. The notebook restores the order of `storey_range` after reading the CSV.

## Files and Handover

**Share with the team:**
- `data/hdb_clean.csv`: Current analysis table.
- `data/addresses.csv`: Distinct address list for B to geocode.
- `README_en.md`: Dataset definitions, units and handover notes.

**Retain locally for reproducibility:**
- `data/hdb.csv`: Prepared notebook input.
- `data_understanding.ipynb`: Import, quality checks, cleaning, descriptive statistics and cleaned-data preview.
- `prepare.py` and `requirements.txt`: Preparation program and package requirements.
- `data/duplicates.csv`: Review extract of the 635 records with identical public fields; these records also remain in the main table.
- `data/audit.json`: Audit of the preparation stage, including source information and monthly counts; it describes `hdb.csv`, not the final 20-column schema.
- `tasks.txt`: Team responsibilities and deadlines.
- `ai_log.txt`: AI usage record.
- `backup.ipynb`: Earlier notebook copy retained when resolving the editor save conflict; use `data_understanding.ipynb` for current work.

Team members can analyse the shared cleaned CSV directly; they do not each need to rerun the preparation program. The town/flat-type filters in the notebook create views and do not restrict the saved analysis table.

To load the analysis table:

```python
import pandas as pd

df = pd.read_csv("data/hdb_clean.csv", dtype={"block": "string"})
storey_levels = sorted(df["storey_range"].unique(),
                       key=lambda label: int(label.split(" TO ")[0]))
df["storey_range"] = pd.Categorical(df["storey_range"],
                                    categories=storey_levels, ordered=True)
```
## A's Remaining work(need to discuss)
The remaining work is:
- Add and validate MRT coordinates/distances.
- Agree how to handle incomplete 2026 coverage.***
- Add CPI adjustment if using real prices.

## B's Handover Requirements

1. Start from `data/addresses.csv` and return one result row per address, including `address_key`, coordinates and match status.
2. Check returned block and street names. Investigate multiple matches and retain unmatched addresses with their failure reasons.
3. Merge verified results into `data/hdb_clean.csv` using a left, many-to-one join on `address_key`; keep all 240,919 transaction rows visible.
4. Record MRT distances in metres and document whether they are straight-line or walking distances.
5. For cross-year analysis, B and E must verify whether stations and exits were open at the time of registration.
6. After adding external data, check unmatched rates, duplicate merge keys, missing values and row counts again.

## Cleaning Assessment and Next Steps

The checks on the current HDB dataset passed. No further routine row deletion, missing-value imputation or format correction is currently indicated. Retain the flagged records and extreme values unless further evidence establishes an error.

The remaining work belongs to the next preparation and analysis stage:
- Obtain coordinates and MRT distances, and validate the external-data merge.
- Agree on the analysis period and the treatment of incomplete 2026 coverage.
- If the study uses real prices, select a CPI series and base period and add the inflation adjustment. Until then, use the nominal-price label.
- Confirm model specifications with the team after these inputs are ready.

The frozen local source snapshot covers January 2017-September 2026. The [official HDB dataset](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) may contain a newer snapshot; do not silently replace the agreed input during analysis.
