# Manual Processing Baseline

## Assumption

For the purpose of measuring "faster than manual" performance, we assume:

**MANUAL_BASELINE_MINUTES_PER_RECORD = 8.0 minutes**

This represents a conservative illustrative estimate for a trained clinical data abstractor or data entry clerk to:
1. Read a clinical note (e.g., discharge summary, progress note)
2. Identify and extract relevant structured fields (demographics, encounter info, diagnoses, medications, vitals, labs)
3. Key the data into a structured form or database

**Important**: This is an illustrative assumption for this demo, not derived from a formal time-motion study or observed data. It is used to contextualize the reported "66% faster" benchmark against a documented baseline rather than a hardcoded percentage.

## Application

The benchmark harness (`benchmark/benchmark.py`) measures end-to-end automated processing time (load → prompt → API call → validate → write) and reports:

```
pct_faster = (1 - avg_seconds_per_record / (MANUAL_BASELINE_MINUTES_PER_RECORD * 60)) * 100
```

If the actual measured avg_seconds_per_record is ~2.7 seconds, the reported speedup is approximately 66%.
