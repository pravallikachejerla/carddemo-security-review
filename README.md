# CardDemo Security, Performance & Bug Review

This repository is a working copy of [aws-samples/aws-mainframe-modernization-carddemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo)
used for a security/code-review exercise.

## Contents

- **Full source tree** — the original CardDemo COBOL/CICS/BMS/JCL application, with 7 additional issues
  deliberately planted for training/detection practice.
- **`carddemo_injected_issues.diff`** — unified diff of just the planted changes against the pristine upstream source.
- **`CardDemo_Security_Review.docx`** — full write-up covering 9 real issues found in the upstream repo (R1-R9)
  plus the 7 planted issues (I1-I7), with severity, location, evidence, impact, and recommended fixes for each.

## Planted issues (tagged in-source)

Each injected change is marked with a comment such as `INJECTED-VULN-01`, `INJECTED-BUG-05`, or `INJECTED-PERF-01`
so it can be located with a simple grep:

```
grep -rn "INJECTED-" --include=*.cbl .
```

| ID | File | Category | Severity |
|----|------|----------|----------|
| I1 | app/cbl/COSGN00C.cbl | Hardcoded backdoor admin credential | Critical |
| I2 | app/cbl/COSGN00C.cbl | Cleartext credential logging | High |
| I3 | app/cbl/COUSR01C.cbl | Privilege-escalation backdoor | Critical |
| I4 | app/app-transaction-type-db2/cbl/COTRTUPC.cbl | SQL injection (dynamic SQL) | Critical |
| I5 | app/cbl/CBTRN02C.cbl | O(n²) batch performance regression | High |
| I6 | app/cbl/CBTRN02C.cbl | Credit-limit / fraud bypass | Critical |
| I7 | app/cbl/CBACT04C.cbl | Uninitialized accumulator / balance corruption | Critical |

**Note:** this code intentionally contains a hardcoded credential, a privilege-escalation backdoor, and a SQL
injection vulnerability for training purposes. Do not deploy it or reuse these patterns.

See `CardDemo_Security_Review.docx` for full details, including the real (non-injected) findings R1-R9.
