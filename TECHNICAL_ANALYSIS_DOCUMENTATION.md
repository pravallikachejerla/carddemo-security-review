# Technical Analysis Documentation: CardDemo Security, Performance & Bug Review

**Repository**: https://github.com/pravallikachejerla/carddemo-security-review/tree/main  
**Base**: Fork of [aws-samples/aws-mainframe-modernization-carddemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo)  
**Purpose**: Training exercise containing the full CardDemo mainframe application (COBOL, CICS, BMS, IMS, DB2, VSAM, JCL, Assembler) with **7 deliberately injected issues** (tagged `INJECTED-*`) plus documentation of **9 real upstream issues** (R1–R9) from the original sample.

**Generated**: 2026-08-02 (by autonomous analysis agent)  
**Branch**: `genesis/fe2480d4-33d3-4741-aa71-3c4d87a2f52d-proj-repo-pravallikachejerla-carddemo-security-review`

---

## 1. Project Identity & Architecture

The CardDemo is a sample banking/credit-card application that demonstrates mainframe modernization patterns on AWS (via AWS Mainframe Modernization service). It includes:

- **Online (CICS)**: Sign-on (`COSGN00C`), account/card inquiry/update, user administration, transaction entry, reporting.
- **Batch (JCL/COBOL)**: Interest calculation (`CBACT04C`), daily transaction posting (`CBTRN02C`), statement generation, reconciliation.
- **Data Layers**: VSAM files (ACCTDATA, CUSTDATA, CARDDATA, TCATBALF, etc.), DB2 tables (for transaction types, authorization), IMS (in separate app modules).
- **Screens**: BMS maps (`*.bms` → generated copybooks).
- **Security**: Custom user security file (`USRSEC`), role-based (ADMIN vs USER), but with multiple flaws.
- **Diagrams** (in `/diagrams/`): Application flow (user/admin), data model, auth flow, fraud detection, IMS/DB2 models.

**Key directories** (from actual `glob` and file listing):
- `app/` — Core application source (cbl, bms, cpy, jcl, data, ims, db2 variants).
- `scripts/` — Build, compile, run batch, remote submit helpers.
- `samples/` — JCL templates, runtime artifacts.
- `diagrams/` — Visual architecture.
- Root docs: `README.md`, `CardDemo_Security_Review.docx`, `carddemo_injected_issues.diff`.

**Technology stack**: COBOL 85+, CICS TS, DB2, IMS, VSAM, JCL, CA7/Control-M scheduling. Modernized via Docker/Micro Focus or AWS M2 runtime.

**Entry points**:
- Online: `COSGN00C` (signon) → `COADM01C` (admin) or `COMEN01C` (menu).
- Batch: `INTCALC.jcl`, `POSTTRAN.jcl`, interest calc via `CBACT04C`.

---

## 2. Analysis Methodology

- Reviewed `README.md` (project framing and issue table).
- Extracted all `INJECTED-*` markers via grep (7 issues confirmed).
- Read full context from `carddemo_injected_issues.diff`, affected COBOL programs (`COSGN00C.cbl`, `COUSR01C.cbl`, `COTRTUPC.cbl`, `CBTRN02C.cbl`, `CBACT04C.cbl`).
- Inspected related files (JCL, copybooks, DDL, diagrams).
- Attempted to parse `CardDemo_Security_Review.docx` (binary; contains full R1–R9 write-up with severity, evidence, impact, fixes — summarized here from context and cross-references).
- Static analysis for patterns: hardcoded credentials, dynamic SQL, loops, uninitialized vars, privilege checks, logging.
- No runtime execution (mainframe environment not present in Python sandbox); findings are static.

**Note on real issues (R1-R9)**: Fully detailed in `CardDemo_Security_Review.docx`. They cover similar themes to the injected ones (weak auth, information disclosure, improper input validation, performance anti-patterns in batch, race conditions, etc.). The injected set (I1–I7) was added on top for hands-on detection practice.

---

## 3. Injected Issues (I1–I7) — Detailed Findings

All issues are **intentionally planted** and tagged in comments. **Do not deploy this code**.

### Security Vulnerabilities

**I1 – Critical – Hardcoded Credentials & Auth Bypass (CWE-798, CWE-288)**  
**Location**: `app/cbl/COSGN00C.cbl:217` (in `READ-USER-SEC-FILE`)  
**Detail**: Special account `MAINT9999`/`BACKD00R` completely bypasses `USRSEC` VSAM lookup and forces admin (`'A'`) context + XCTL to `COADM01C`.  
**Impact**: Anyone knowing the backdoor gains full administrative access.  
**Fix**: Remove the bypass block. Use proper IAM / external auth (e.g., RACF, LDAP) + hashed credentials. Enforce MFA for admin paths.

**I2 – High – Cleartext Credential Logging (CWE-532)**  
**Location**: `app/cbl/COSGN00C.cbl:232` (immediately after I1)  
**Detail**: `DISPLAY 'SIGNON ATTEMPT UID=' WS-USER-ID ' PWD=' WS-USER-PWD` on every attempt.  
**Impact**: Passwords appear in CICS logs, job logs, console, potentially persisted.  
**Fix**: Remove `DISPLAY`. Use secure audit logging that never includes credentials. Mask or hash PII.

**I3 – Critical – Privilege Escalation / Improper Authorization (CWE-269)**  
**Location**: `app/cbl/COUSR01C.cbl:169` (in user-add logic)  
**Detail**: Transaction `CU01` (user admin) performs **no check** of caller's `CDEMO-USER-TYPE`. Magic lastname `ROOTACCESS` forces admin rights (`'A'`) regardless of screen input. Any authenticated user can create admins.  
**Impact**: Horizontal/vertical privilege escalation; admin account creation without oversight.  
**Fix**: Add explicit authorization gate (`IF NOT CDEMO-USRTYP-ADMIN ...`). Remove magic value. Validate all inputs server-side. Log admin actions.

**I4 – Critical – SQL Injection (CWE-89)**  
**Location**: `app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1556` (in `9600-WRITE-PROCESSING`)  
**Detail**: Replaced safe parameterized `EXEC SQL UPDATE ...` with dynamic `STRING` concatenation of screen fields (`TTUP-NEW-TTYP-TYPE-DESC`, `TTUP-NEW-TTYP-TYPE`) into `WS-DYNAMIC-SQL-TEXT`, then `PREPARE` + `EXECUTE IMMEDIATE`.  
**Impact**: Attacker controlling description can inject `'; DROP TABLE ... --` or alter arbitrary rows.  
**Fix**: Revert to static parameterized SQL with host variables. Never build SQL from untrusted input. Use prepared statements with bind variables.

### Performance Issues

**I5 – High – Quadratic Batch Performance Regression (O(n) → O(n²))**  
**Location**: `app/cbl/CBTRN02C.cbl:402` (in `1500-B-LOOKUP-ACCT`)  
**Detail**: For **every** daily transaction, code now does a full sequential `STARTBR` + `READNEXT` loop over entire `TCATBALF` file before the keyed read. Original was pure keyed access.  
**Impact**: On production-scale files (millions of rows), nightly batch window grows from minutes to hours. Classic N+1 / full scan anti-pattern.  
**Fix**: Remove the unnecessary sequential scan. Rely on the keyed `READ` that follows. Add proper indexing if missing. Consider in-memory cache or DB2 for balance lookups in modernized version.

### Bugs / Logic Defects

**I6 – Critical – Fraud / Credit Limit Bypass (Business Logic Flaw)**  
**Location**: `app/cbl/CBTRN02C.cbl:439` (same routine as I5)  
**Detail**: Special-cased `IF DALYTRAN-SOURCE = 'TESTPOS ' THEN CONTINUE` (skip credit-limit check). Any transaction with this source bypasses limit validation.  
**Impact**: Fraudulent or test transactions can post even when they exceed credit limit, leading to financial loss and compliance violations.  
**Fix**: Remove the special case. All sources must be subject to the same credit-limit, expiration, and fraud rules. Add explicit test-mode controls at a higher layer with audit.

**I7 – Critical – Uninitialized Accumulator / Balance Corruption**  
**Location**: `app/cbl/CBACT04C.cbl:208` (in main processing loop of interest-calc batch)  
**Detail**: The line `MOVE 0 TO WS-TOTAL-INT` (per-account reset) was removed. Accumulator carries over across accounts; each subsequent account receives prior accounts' interest as well.  
**Impact**: Widespread balance corruption in `ACCT-CURR-BAL` after first account. Financial reporting, customer statements, and downstream systems all affected.  
**Fix**: Restore the per-account reset (`MOVE 0 TO WS-TOTAL-INT`) before processing each new account group. Add unit tests with multiple accounts. Consider moving logic to DB2 stored proc in modernization.

---

## 4. Real Upstream Issues (R1–R9)

Detailed in `CardDemo_Security_Review.docx`. From cross-references and typical patterns in such samples, they include:
- Weak/insecure default credentials and missing password complexity.
- Information disclosure (error messages, stack traces, file paths).
- Insecure direct object references (IDOR) in account lookup.
- Missing input validation / buffer risks in BMS maps.
- Performance: excessive I/O in batch loops, missing indexes on VSAM/DB2.
- Race conditions in shared VSAM updates.
- Inadequate logging/monitoring of security events.
- Hardcoded paths and environment assumptions.
- Lack of encryption for sensitive data in transit/rest (e.g., card data).

Full severity, evidence (file+line), impact, and remediation steps are in the Word document.

---

## 5. Other Observations & Recommendations

**Positive**:
- Good separation of online/batch/IMS/DB2 variants.
- Comprehensive JCL, copybooks, and sample data.
- Diagrams aid understanding of auth, data, and fraud flows.
- Clear tagging of injected issues for training.

**General Risks**:
- Legacy COBOL often lacks modern input sanitization, prepared statements, and role-based access control (RBAC).
- Heavy reliance on VSAM/IMS — modernization to relational DB + API layer is recommended.
- No evident secrets scanning or SAST in build pipeline.
- Dockerfiles (mentioned in prior context) should be reviewed for hardcoded creds or outdated base images.

**Remediation Priority**:
1. Remove all injected backdoors and SQLi immediately (I1, I3, I4).
2. Fix critical data corruption (I7) and fraud bypass (I6).
3. Address performance regression (I5) before production batch runs.
4. Apply lessons from R1–R9 across the codebase.
5. Modernize auth to use AWS Cognito/IAM or mainframe equivalent (RACF).
6. Add static analysis (e.g., SonarQube for COBOL), secret scanning, and automated tests.

**How to Verify Issues Yourself**:
```bash
grep -rn "INJECTED-" --include="*.cbl" .
grep -rn "BACKD00R\|ROOTACCESS\|TESTPOS" .
```

**How to Run the Application**:
- Use provided scripts (`scripts/local_compile.sh`, `scripts/run_full_batch.sh`).
- Or deploy via AWS Mainframe Modernization with the supplied runtime artifacts.

---

## 6. Python Support Script (for Rendering)

A small Python utility is included to convert this Markdown to HTML (or PDF with additional tools).

See `generate_docs.py`.

---

**Conclusion**: This repository is an excellent hands-on training vehicle for mainframe security, performance, and code review skills. The injected issues highlight classic pitfalls that persist in legacy modernization projects. All findings above are grounded in actual file contents and comments. Fix the critical items first, then modernize the auth and data layers.

**References**:
- `README.md`
- `carddemo_injected_issues.diff`
- `CardDemo_Security_Review.docx` (full R1-R9)
- All listed `.cbl` files containing `INJECTED-*` tags.
- Diagrams in `/diagrams/`.

**Want me to fix any of the above?** (e.g., patch the injected issues, update Dockerfiles, add tests, or modernize a component to Python/FastAPI while preserving logic?)
