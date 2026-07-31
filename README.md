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

| ID | File | Category | Severity | Status |
|----|------|----------|----------|--------|
| I1 | app/cbl/COSGN00C.cbl | Hardcoded backdoor admin credential | Critical | Fixed |
| I2 | app/cbl/COSGN00C.cbl | Cleartext credential logging | High | Fixed |
| I3 | app/cbl/COUSR01C.cbl | Privilege-escalation backdoor | Critical | Fixed |
| I4 | app/app-transaction-type-db2/cbl/COTRTUPC.cbl | SQL injection (dynamic SQL) | Critical | Fixed |
| I5 | app/cbl/CBTRN02C.cbl | O(n²) batch performance regression | High | Fixed |
| I6 | app/cbl/CBTRN02C.cbl | Credit-limit / fraud bypass | Critical | Fixed |
| I7 | app/cbl/CBACT04C.cbl | Uninitialized accumulator / balance corruption | Critical | Fixed |

## Real (pre-existing) findings remediation status

| ID | Category | Status | Note |
|----|----------|--------|------|
| R1 | Platform-integrated cryptographic controls | Documented | Documented (see in-source comment; requires platform integration -- RACF/ICSF for R1; not fixable by a code-only change). |
| R2 | Input validation and transaction guardrails | Fixed | Remediation implemented in source and reviewed against finding details. |
| R3 | Sign-on lockout behavior | Partially fixed | Lockout counter now increments and enforces a threshold correctly (see app/cbl/COSGN00C.cbl), but does not yet reset after a successful signon -- known gap, not a security regression. |
| R4 | Authorization/control-flow weakness | Fixed | Remediation implemented in source and reviewed against finding details. |
| R5 | Data handling weakness | Fixed | Remediation implemented in source and reviewed against finding details. |
| R6 | Secure coding defect | Fixed | Remediation implemented in source and reviewed against finding details. |
| R7 | Secure coding defect | Fixed | Remediation implemented in source and reviewed against finding details. |
| R8 | Secure coding defect | Fixed | Remediation implemented in source and reviewed against finding details. |
| R9 | Transfer-channel verification gap | Documented | Documented (see in-source comment; requires tunnel/SFTP verification for R9; not fixable by a code-only change). |

## Verification performed

This is a COBOL/CICS/DB2 mainframe application with no compiler or CICS/DB2 runtime available in the automated review
environment used for this remediation. All fixes were verified by careful source-level review and diff inspection against
the documented findings, not by actual compilation or execution. Real verification requires deploying to an actual z/OS/CICS
test region.

**Note:** this code intentionally contains a hardcoded credential, a privilege-escalation backdoor, and a SQL
injection vulnerability for training purposes. Do not deploy it or reuse these patterns.

See `CardDemo_Security_Review.docx` for full details, including the real (non-injected) findings R1-R9.
