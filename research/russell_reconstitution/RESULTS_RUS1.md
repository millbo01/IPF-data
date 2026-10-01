# RUS1 results — Russell reconstitution closing-flow test

## Final classification

- Mechanism / closing-volume concentration: **PASS**
- Raw directional closing-pressure indicator: **FAIL**
- Raw post-event reversal indicator: **FAIL**

## Coverage

Frozen sample: first 30 official Russell 3000 additions and first 30 official deletions in each of 2023, 2024 and 2025.

- 2023: 60 frozen, 60 QC-resolved, 59 complete. XXII failed with invalid close data.
- 2024: 60 frozen, 60 QC-resolved, 59 complete. AKTS had no minute history.
- 2025 holdout: 60 frozen, 60 QC-resolved, 60 complete.

## Results

### 2023
- Volume excess: N=59, mean +43.2405 pp, median +49.3222 pp, fraction >0 = 0.949; additions median +32.0019 pp, deletions median +56.3630 pp.
- Pressure excess: N=59, mean -105.3548 bp, median -56.6146 bp, fraction >0 = 0.441; additions median -125.3733 bp, deletions median +33.6346 bp.
- Reversal excess: N=59, mean +295.0644 bp, median +183.4331 bp, fraction >0 = 0.780; additions median +135.7989 bp, deletions median +425.8102 bp.

### 2024
- Volume excess: N=59, mean +39.7187 pp, median +43.9413 pp, fraction >0 = 0.966; additions median +42.4810 pp, deletions median +45.0003 pp.
- Pressure excess: N=59, mean +169.4240 bp, median +99.1368 bp, fraction >0 = 0.695; additions median +15.9251 bp, deletions median +164.8039 bp.
- Reversal excess: N=59, mean +92.4113 bp, median +11.1460 bp, fraction >0 = 0.508; additions median +65.7488 bp, deletions median -137.5913 bp.

### Pooled build (2023–2024)
- Volume excess: N=118, mean +41.4796 pp, median +46.2137 pp, fraction >0 = 0.958; additions median +35.4854 pp, deletions median +53.1758 pp.
- Pressure excess: N=118, mean +32.0346 bp, median +15.9251 bp, fraction >0 = 0.568; additions median -23.1021 bp, deletions median +121.4412 bp.
- Reversal excess: N=118, mean +193.7379 bp, median +114.2444 bp, fraction >0 = 0.644; additions median +97.4844 bp, deletions median +170.5113 bp.

### 2025 holdout
- Volume excess: N=60, mean +46.8106 pp, median +51.3622 pp, fraction >0 = 0.967; additions median +44.1953 pp, deletions median +57.9318 pp.
- Pressure excess: N=60, mean +211.6741 bp, median +208.5546 bp, fraction >0 = 0.783; additions median +35.5176 bp, deletions median +384.9709 bp.
- Reversal excess: N=60, mean +90.6824 bp, median +64.1018 bp, fraction >0 = 0.550; additions median -102.3141 bp, deletions median +231.4060 bp.

## ADV20 descriptor

Median pre-event ADV20:
- 2023: $1.50m
- 2024: $1.12m
- 2025: $0.93m

## Frozen gate verdicts

A. Mechanism / close-volume gate: **PASS**.

B. Directional closing-pressure gate: **FAIL**. Although 2024, pooled build and 2025 were positive, the frozen rule also required the 2023 median to be positive; it was -56.6146 bp.

C. Post-event reversal gate: **FAIL**. Although overall medians were positive, the 2024 deletion median was negative and the 2025 addition median was negative; the frozen rule required both addition and deletion medians in the holdout to be positive.

## Interpretation

RUS1 strongly supports the institutional mechanism that Russell reconstitution concentrates trading into the close. It does **not** support blindly trading membership direction or blindly fading the event close. The natural next test is a separately frozen interaction between forced membership flow and a pre-event absorption-capacity proxy.
