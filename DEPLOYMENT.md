# Deployment Considerations for Security Remediation Branch

This repository is deployed as a **mainframe COBOL/CICS/DB2/IMS/MQ application**. The deployment flow in this branch uses JCL submission and source/module transfer over the existing **tnftp tunnel to the Ensono-hosted environment** (as implemented by the scripts in `scripts/`).

## 1) Summary of the 15 remediation changes in this pass

1. `app/cbl/COSGN00C.cbl` — failed sign-on now increments `SEC-USR-FAILED-COUNT` and rewrites the `USRSEC` record on bad password attempts.
2. `app/cbl/COSGN00C.cbl` — lockout behavior is enforced after repeated failures (`SEC-USR-FAILED-COUNT >= 5`) with generic invalid-credential messaging.
3. `app/cbl/COSGN00C.cbl` — missing-user path returns the same generic invalid-credential response to reduce user-ID enumeration exposure.
4. `app/cbl/COUSR01C.cbl` — add-user transaction now explicitly blocks non-admin callers using `CDEMO-USRTYP-ADMIN` authorization logic.
5. `app/cbl/COUSR01C.cbl` — add-user validation enforces baseline password policy checks (minimum length and password not equal to User ID).
6. `app/cpy/CSUSR01Y.cpy` — `SEC-USER-DATA` record layout was extended with trailing field `SEC-USR-FAILED-COUNT` for lockout tracking.
7. `app/cbl/CBTRN02C.cbl` — posting job output handling was corrected to append behavior (`OPEN EXTEND TRANSACT-FILE`) for transaction writes.
8. `app/cbl/CBTRN02C.cbl` — credit-limit validation now consistently rejects over-limit activity (no special-source bypass).
9. `app/cbl/CBTRN02C.cbl` — transaction validation path avoids unnecessary full-file browse logic and preserves keyed-access behavior for performance.
10. `app/cbl/CBACT04C.cbl` — account-level accumulator handling was corrected (per-account `WS-TOTAL-INT` reset) to prevent cross-account carry-over.
11. `app/cbl/CBACT04C.cbl` — interest computation uses financial rounding (`ROUNDED`) and fee-skip behavior is surfaced with explicit operational warning output.
12. `app/app-transaction-type-db2/cbl/COTRTUPC.cbl` — DB2 update processing uses host-variable static `EXEC SQL` (parameterized) instead of concatenated dynamic SQL execution.
13. `scripts/remote_compile.sh` — R9 note added documenting tnftp plaintext hop over local tunnel and required transport hardening review.
14. `scripts/remote_submit.sh` — same R9 transport-risk note added for JES job submission path.
15. `scripts/remote_refresh.sh` and `scripts/upld_module.sh` — same R9 transport-risk note added for refresh-job submission and module upload paths.

## 2) Actual deployment mechanism used by this repo today

### Compile and link of COBOL modules
- `scripts/remote_compile.sh` is the compile entry point for `.cbl` changes.
- It renders and submits `scripts/compile_batch.jcl.template` (member substitution via `ZZZZZZZZ`) to JES.
- The submitted JCL compiles and link-edits into `AWS.M2.CARDDEMO.LOADLIB`.

### Module/source upload
- `scripts/upld_module.sh` uploads source/members to target PDS datasets (for example `AWS.M2.CARDDEMO.CBL(...)`, `CPY(...)`, etc.).
- The script pads source records to 80-byte mainframe format before transfer.

### JCL submission and operational jobs
- `scripts/remote_submit.sh` submits `.jcl` members to JES (`quote site filetype=JES`).
- `scripts/remote_refresh.sh` submits the environment refresh sequence (`CLOSEFIL`, file refresh jobs, then `OPENFIL`).
- Operational JCL content lives under `app/jcl/` (batch cycles such as posting, interest, backup/index, file refresh/open-close).

### CICS resource deployment context
- CICS resource definitions are maintained in `app/csd/CARDDEMO.CSD` (programs, mapsets, files, transactions/group definitions).
- Any production promotion must ensure the target CICS region has compatible CSD definitions and enabled resources for the promoted modules.

### Transport channel currently used
- All of the above scripts currently use `tnftp localhost 2121`, i.e., FTP over the local tunnel endpoint to the Ensono-hosted target.
- As documented in the scripts, the deploying team must verify tunnel/security posture (TLS/SSH termination and migration plan to SFTP/FTPS where available) before production use.

## 3) Test-region verification checklist before production promotion

Run these checks in a **real CICS/DB2 test region** with representative files/tables and operations data.

### Security/sign-on and user administration
- [ ] **`COSGN00C.cbl`**: execute full CICS sign-on transaction tests for valid credentials, invalid credentials, repeated failures, lockout threshold behavior, and post-lockout messaging.
- [ ] **`COSGN00C.cbl` + `CSUSR01Y.cpy`**: verify `SEC-USR-FAILED-COUNT` increments/rewrite behavior in `USRSEC` and does not corrupt existing user records.
- [ ] **`COUSR01C.cbl`**: verify only admin users can run add-user successfully; non-admin path is denied with expected screen/message behavior.
- [ ] **`COUSR01C.cbl`**: validate password-policy edits on add-user screen (minimum length and disallowing password equal to User ID).

### DB2 transaction-type maintenance
- [ ] **`COTRTUPC.cbl`**: run update flows against DB2 test tables in `CARDDEMO.TRANSACTION_TYPE` and confirm expected update/insert/SQLCODE handling.
- [ ] **`COTRTUPC.cbl`**: test special-character input in transaction description/type to confirm SQL remains safe and functionally correct under host-variable binding.

### Batch posting and interest cycles
- [ ] **`CBTRN02C.cbl`**: execute posting batch cycle with representative `DALYTRAN`, `XREFFILE`, `ACCTFILE`, and `TCATBALF` data; verify throughput and elapsed time against baseline.
- [ ] **`CBTRN02C.cbl`**: verify over-limit transactions are consistently rejected and routed to reject output with correct reason codes.
- [ ] **`CBTRN02C.cbl`**: verify transaction output appends correctly without truncation/replacement side effects.
- [ ] **`CBACT04C.cbl`**: execute interest cycle using representative `TCATBAL/account` data and confirm per-account totals do not bleed across accounts.
- [ ] **`CBACT04C.cbl`**: validate rounded interest values against expected financial calculations and reconcile generated transactions.
- [ ] **`CBACT04C.cbl`**: verify fee-processing operational warning output is captured/monitored by batch operations.

### Deployment transport/process controls
- [ ] Confirm tunnel to Ensono is active and approved before using `remote_compile.sh`, `upld_module.sh`, or `remote_submit.sh`.
- [ ] Confirm JES submissions from `app/jcl` complete with expected return codes and no unexpected dataset/member routing changes.
- [ ] Confirm required CICS resources in `app/csd/CARDDEMO.CSD` are present/enabled in the target test region before module cutover.

## 4) Copybook layout compatibility note (`CSUSR01Y.cpy`)

`CSUSR01Y.cpy` now includes a **new trailing field** (`SEC-USR-FAILED-COUNT`). Existing fields were preserved at their original offsets.

Before deployment, re-check any **other** program that reads/writes `SEC-USER-DATA` (in addition to `COSGN00C.cbl` and `COUSR01C.cbl`) to confirm record-length handling, REWRITE/WRITE behavior, and copybook-consistency in compile/link artifacts.