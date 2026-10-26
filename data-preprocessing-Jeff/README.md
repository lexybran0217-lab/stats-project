# HDB Resale Analysis Dataset

This dataset supports the group project examining the association between HDB resale prices and MRT proximity, while accounting for structural housing characteristics and other locational factors.

## Dataset overview

- **Analysis file:** `hdb_resale_analysis.csv`
- **Preprocessing notebook:** Jeff's data-preprocessing notebook.
- **Unit of observation:** one published HDB resale transaction record. A block can appear repeatedly across transactions and months. Duplicates were not dropped as they are only a small number and are likely representing different transactions with the same characteristics.
- **Records:** 240,919.
- **Variables:** 14, in the order shown below.
- **Registration period:** January 2017 to September 2026; 2026 is a partial year.
- **Variable of Interests** `dist_mrt`, the main variable of interest, is first; `log_real_resale_price`, the dependent variable, is second.

## Data dictionary

| Variable | Type / unit | Definition |
| --- | --- | --- |
| `dist_mrt` | Numeric; metres | Shortest WGS84 geodesic distance from the HDB block reference point to an eligible MRT exit. Eligibility depends on the station opening month. LRT exits are excluded. |
| `log_real_resale_price` | Numeric; natural logarithm | Natural log of resale price after adjustment using the quarterly HDB Resale Price Index, with 2017 Q1 as the reference period. |
| `town` | Nominal categorical | HDB town in the transaction data. |
| `flat_type` | Nominal categorical | Flat type, such as `3 ROOM` or `4 ROOM`. |
| `storey_range` | Ordered categorical | Reported floor band, such as `01 TO 03` or `10 TO 12`. The exact floor is unavailable. |
| `floor_area_sqm` | Numeric; square metres | Floor area of the flat. |
| `flat_model` | Nominal categorical | HDB flat-model classification, such as `Improved` or `New Generation`. |
| `remaining_lease_years` | Numeric; years | Reported remaining lease converted to years, including the fractional year represented by its month component. |
| `dist_cbd` | Numeric; metres | WGS84 geodesic distance to one fixed reference point at Raffles Place MRT station, used as a proxy for the CBD. |
| `dist_pri_sch` | Numeric; metres | Shortest WGS84 geodesic distance to a primary-school campus reference point in the supplied MOE directory snapshot. |
| `year` | Integer; calendar year | Registration year extracted from the original `YYYY-MM` field. |
| `month` | Integer; 1–12 | Registration month extracted from the original `YYYY-MM` field. |
| `latitude` | Numeric; decimal degrees | Latitude of the HDB block reference point, in WGS84. Repeated for transactions at the same block. |
| `longitude` | Numeric; decimal degrees | Longitude of the HDB block reference point, in WGS84. Repeated for transactions at the same block. |


## Feature construction

### Price adjustment

For a transaction in quarter `t`:

```text
adjusted resale price = nominal resale price × RPI(2017 Q1) / RPI(t)
log_real_resale_price = ln(adjusted resale price)
```

The supplied index value for 2017 Q1 is **133.9**. January 2017 uses 2017 Q1 because the index is quarterly; there is no separate January index in the supplied file. All transactions within the same quarter receive the same adjustment factor.

This adjustment removes aggregate HDB resale-market index movements. It is **not CPI inflation adjustment** and should not be described as a general purchasing-power measure. The outcome is a natural logarithm, not a price in dollars.

### Remaining lease

```text
remaining lease in years = reported years + reported months / 12
```

For example, `61 years 04 months` becomes approximately `61.3333` years. This uses the reported lease rather than estimating it from the lease commencement year.

### Geographic distances

Block numbers and street names identify unique HDB blocks, whose coordinates are obtained using OneMap. Distances are computed once per relevant block or block-month combination and attached to transaction records.

- **MRT:** choose the nearest exit among stations opened in or before the transaction month. A station opening in August 2026 is excluded from July 2026 transactions and included from August 2026. All transactions in the opening month are treated alike because exact transaction days are unavailable.
- **CBD:** use one fixed Raffles Place MRT station coordinate throughout the study period. This measures distance to a CBD proxy point, not to the CBD boundary.
- **Primary school:** select the nearest campus point from the downloaded directory. The same school-location snapshot is used for every transaction year.

All three distances are in **metres**: `1000` means 1 km. They are direct ellipsoidal geographic distances, not walking routes, travel times or official Primary 1 admissions distances.

## Load the shared dataset

The shared CSV is sufficient for analysis; group members do not need to rerun OneMap lookups merely to load it.

```python
import pandas as pd

df_analysis = pd.read_csv("hdb_resale_analysis.csv")

# CSV retains floor-band labels but does not retain categorical ordering.
storey = df_analysis["storey_range"].astype("string").str.strip()
if not storey.str.fullmatch(r"\d+ TO \d+", na=False).all():
    raise ValueError("Missing or unexpected storey-range labels.")

levels = sorted(
    storey.unique(),
    key=lambda label: tuple(int(x) for x in label.split(" TO "))
)

df_analysis["storey_range"] = pd.Categorical(
    storey, categories=levels, ordered=True
)

print(df_analysis.shape)
display(df_analysis.head())
```

## Analysis notes and limitations

- Keep the master CSV unchanged; create working copies for modelling.
- Do not automatically remove identical analysis rows. The public data lack unit numbers and unique transaction identifiers, and the analysis export omits several identifying fields. Different transactions may therefore look identical.
- An ordered `storey_range` preserves band order but does not impose equal price differences between bands.
- The nearest-MRT measure accounts for station opening months, but assumes the supplied exits were available when their station opened.
- School openings, closures, mergers and relocations are not reconstructed. Earlier transactions are matched against the supplied school-directory snapshot on data.gov.
- Interpret regression findings as associations, rather than causal effects. Compare partial-year 2026 results with appropriate care.

## Source datasets

| Source | Role |
| --- | --- |
| [HDB resale transactions](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) | Transaction prices and housing characteristics. |
| [HDB Resale Price Index — SingStat](https://tablebuilder.singstat.gov.sg/table/TS/M212161) | Quarterly HDB-market price adjustment; supplied Excel file. |
| [OneMap](https://www.onemap.gov.sg/apidocs/) | HDB block and school coordinates. |
| [LTA MRT station exits](https://data.gov.sg/datasets/d_b39d3a0871985372d7e1637193335da5/view) | MRT exit coordinates. |
| [Kaggle station directory](https://www.kaggle.com/datasets/lzytim/full-list-of-mrt-and-lrt-stations-in-singapore) | Station opening dates and the fixed CBD reference coordinate. Jeff's notebook adds Hume, Keppel, Cantonment and Prince Edward Road. |
| [MOE general information of schools](https://data.gov.sg/datasets/d_688b934f82c1059ed0a6993d2a829089/view) | Primary-school selection, campus addresses and postal codes. |

For reproducibility, retain the downloaded reference files, Jeff's notebook, `hdb_geocode_cache.json` and `primary_school_geocode_cache.json` with the project. OneMap access tokens should not be included in shared files.
