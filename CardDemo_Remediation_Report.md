# CardDemo Security Review — Remediation Report

Repository: pravallikachejerla/carddemo-security-review
Branch: genesis/2cb8c0b5-ecfd-4dcb-91e5-5fc3a8fc5f00-carddemo-security-review-analysis
Pull Request: #1
Prepared: 2026-07-30

# 1. Executive Summary

This report documents an automated security and code-quality remediation pass against the CardDemo mainframe application (COBOL/CICS/BMS/JCL, with DB2/IMS/MQ extension modules), performed via SOMA's genesis agentic delivery pipeline. The repository is explicitly a security-review training exercise: it contains 7 deliberately-injected vulnerabilities/bugs (I1-I7) on top of the pristine upstream AWS CardDemo sample, and a prior manual security review documented 9 additional real, pre-existing findings (R1-R9) in the underlying upstream code itself.

All 7 injected issues were fixed and verified. Of the 9 real findings, 7 were fixed, 1 was partially fixed (see Known Issues), and 2 (R1, R9) were documented in-source rather than code-fixed, since both require platform/infrastructure changes (a RACF/ICSF security exit; a verified SFTP/FTPS endpoint) that cannot be safely fabricated from a code-only change.

Every fix in this report was verified against the actual pushed diff via the GitHub API — not by trusting the delivery pipeline's own self-reported status — before being included here.

# 2. Repository Analysis

## 2.1 Purpose and Scope

CardDemo is AWS's reference mainframe modernization sample application. This fork wraps the original COBOL/CICS/VSAM application with a security/performance review exercise: the full source tree is present, with training defects injected and tagged in-source (grep -rn "INJECTED-" to locate them), plus a companion Word document (CardDemo_Security_Review.docx) covering both the injected findings and 9 real findings from a manual review of the pristine upstream code.

## 2.2 Architecture and Folder Structure



| Path | Contents |

|---|---|

| app/cbl/ | Core COBOL programs — CICS online transactions and batch jobs |

| app/cpy/ | Business/data copybooks — record layouts, COMMAREA, constants |

| app/bms/, app/cpy-bms/ | BMS map source and generated map copybooks (terminal screens) |

| app/csd/ | CICS resource definitions (CARDDEMO.CSD) |

| app/jcl/ | Operational JCL — file define/load, posting, reporting, open/close |

| app/ctl/ | IDCAMS/utility control cards |

| app/data/ASCII, app/data/EBCDIC | Seed/reference data in distributed and host formats |

| app/asm/, app/maclib/ | Assembler support modules/macros |

| app/scheduler/ | Scheduler exports (CA7, Control-M) |

| app/app-transaction-type-db2/ | DB2 extension — transaction-type reference data maintenance |

| app/app-authorization-ims-db2-mq/ | Card authorization processing — MQ ingress/egress, IMS persistence, DB2 fraud reporting |

| app/app-vsam-mq/ | MQ request/response examples over VSAM-backed data |

| scripts/ | Local/remote compile/submit orchestrators (tnftp tunnel to an Ensono-hosted mainframe) |

| samples/ | Sample compile JCL and procs |



## 2.3 Technologies Used

Core: COBOL, CICS (transactions, BMS maps, VSAM file API, XCTL/RETURN flows), VSAM (KSDS + AIX/PATH patterns), JCL + IDCAMS/SDSF utilities, BMS terminal screens.
Extensions: DB2 embedded SQL (SQLCA, DCLGEN-style copybooks, static SQL), IMS DB (HIDAM DBD/PSB, EXEC DLI), IBM MQ (CMQ* copybooks, MQOPEN/MQGET/MQPUT/MQCLOSE).
Supporting: z/OS assembler + macro, shell scripting (compile/submit orchestration over an FTP tunnel).

## 2.4 Workflows and Dependencies

This is a mainframe application with no local build/runtime; it depends on a full z/OS ecosystem (Enterprise COBOL compiler, CICS TS runtime, DFSMS/IDCAMS, and optionally DB2/IMS/MQ). The existing deployment workflow (scripts/remote_compile.sh, upld_module.sh, remote_submit.sh, remote_refresh.sh) submits JCL and transfers modules over a tnftp connection through a local tunnel to an Ensono-hosted mainframe environment. See the new DEPLOYMENT.md (added in this remediation) for the full mechanism.

# 3. Findings and Remediation

## 3.1 Injected Training Issues (I1–I7) — All Fixed



| ID | File | Category | Severity | Status |

|---|---|---|---|---|

| I1 | app/cbl/COSGN00C.cbl | Hardcoded backdoor admin credential (CWE-798/288) | Critical | Fixed |

| I2 | app/cbl/COSGN00C.cbl | Cleartext credential logging (CWE-532) | High | Fixed |

| I3 | app/cbl/COUSR01C.cbl | Privilege-escalation backdoor (CWE-269) | Critical | Fixed |

| I4 | app/app-transaction-type-db2/cbl/COTRTUPC.cbl | SQL injection via dynamic SQL (CWE-89) | Critical | Fixed |

| I5 | app/cbl/CBTRN02C.cbl | O(n²) batch performance regression | High | Fixed |

| I6 | app/cbl/CBTRN02C.cbl | Credit-limit / fraud-control bypass | Critical | Fixed |

| I7 | app/cbl/CBACT04C.cbl | Uninitialized accumulator / balance corruption | Critical | Fixed |



## 3.2 Real, Pre-Existing Findings (R1–R9)



| ID | File | Category | Severity | Status |

|---|---|---|---|---|

| R1 | app/cpy/CSUSR01Y.cpy, COSGN00C.cbl | Plaintext password storage/comparison | High | Documented only |

| R2 | app/cbl/COSGN00C.cbl | User-ID enumeration via differentiated errors | Medium | Fixed |

| R3 | app/cbl/COSGN00C.cbl, CSUSR01Y.cpy | No account lockout/throttling | High | Partially fixed |

| R4 | app/cbl/COUSR01C.cbl | Missing authorization check on Add-User | High | Fixed (incidental, via I3 fix) |

| R5 | app/cbl/COUSR01C.cbl | No password complexity/reuse policy | Medium | Fixed |

| R6 | app/cbl/CBACT04C.cbl | Interest calculation truncates instead of rounding | Medium | Fixed |

| R7 | app/cbl/CBACT04C.cbl | Fee calculation was left incomplete (no-op placeholder) | Medium | Fixed (gap now logged, not fabricated) |

| R8 | app/cbl/CBTRN02C.cbl | Daily transaction file opened OUTPUT not EXTEND | High | Fixed |

| R9 | scripts/*.sh | Deployment scripts use unencrypted FTP | Medium | Documented only |



## 3.3 Detail: Key Fixes

I1/I2 — COSGN00C.cbl backdoor + credential logging: Removed the hardcoded MAINT9999/BACKD00R bypass that granted unconditional admin access, and the DISPLAY statement that logged plaintext user IDs and passwords to the CICS/job log on every signon attempt. Net change: +0/-24 lines, pure removal.

I3/R4 — COUSR01C.cbl privilege escalation + missing authorization: Removed the ROOTACCESS magic last-name value that silently granted admin rights, and added a real authorization check (WHEN NOT CDEMO-USRTYP-ADMIN) so only an already-admin operator can create new users — fixing both the injected backdoor and the real missing-authorization finding in one change.

I4 — COTRTUPC.cbl SQL injection: Reverted the STRING-concatenated dynamic SQL (built from unvalidated screen input, executed via PREPARE/EXECUTE) back to the original static, parameterized EXEC SQL UPDATE using host variables.

I5/I6 — CBTRN02C.cbl performance and fraud bypass: Removed a redundant full-file STARTBR/READNEXT scan that turned an O(n) batch post into O(n²), and removed a special-cased credit-limit bypass for transactions tagged with a specific source value.

I7 — CBACT04C.cbl uninitialized accumulator: Restored the per-account "MOVE 0 TO WS-TOTAL-INT" reset that had been removed, which was causing interest to accumulate across the entire batch run and corrupt every account's balance from the second account onward.

R2 — COSGN00C.cbl user enumeration: Unified the "User not found" and "Wrong Password" messages into a single generic "Invalid User ID or Password" response so a caller cannot distinguish a nonexistent account from a wrong password.

R3 — COSGN00C.cbl / CSUSR01Y.cpy account lockout: Added a SEC-USR-FAILED-COUNT field to the shared USRSEC copybook (appended at the end of the record to preserve the existing layout and length for any other program reading this file), and wired COSGN00C.cbl to increment it on a wrong-password attempt and reject the signon with a generic message once the count reaches 5. The complementary reset-on-successful-signon logic could not be landed after 3 attempts due to a repeatable patch-application conflict in the delivery pipeline — see Known Issues.

R5 — COUSR01C.cbl password policy: Added a minimum-length check (reject fewer than 4 characters) and a check rejecting a password identical to the user ID, using the program's existing WS-ERR-FLG/WS-MESSAGE error-handling pattern.

R6 — CBACT04C.cbl interest rounding: Added the ROUNDED clause to the interest COMPUTE statement, eliminating the silent truncation of fractional cents that was under-charging interest and compounding across billing cycles.

R7 — CBACT04C.cbl fee-calculation stub: The 1400-COMPUTE-FEES paragraph was left as an incomplete no-op with no visible signal that fees were never assessed. Rather than fabricate an unauthorized fee schedule, the fix adds an explicit DISPLAY warning naming the account and run date, so the gap is visible in the job log instead of silent.

R8 — CBTRN02C.cbl file open mode: Changed OPEN OUTPUT (which creates/overwrites) to OPEN EXTEND (append) for TRANSACT-FILE, so a job restart or reprocessing run no longer silently destroys the prior run's transaction records.

# 4. Testing Summary

This is a COBOL/CICS/DB2/IMS/MQ mainframe application. The automated environment used to perform this remediation has no COBOL compiler, no CICS runtime, and no DB2/IMS/MQ subsystem available — compilation and execution against real data are not possible outside an actual z/OS/CICS test region.

Verification actually performed for every fix in this report:

- Each fix was read back in full from the actual pushed source (via the GitHub compare/diff API) and manually traced against the documented finding to confirm the change matches the described defect and remediation exactly, with no unrelated changes bundled in.

- Every commit's diff was checked for scope: files touched, lines added/removed, and that no stray artifacts (e.g. internal tooling bookkeeping files) were committed alongside the real fix.

- The final branch state was verified against main via the GitHub compare API to confirm a clean, accumulating diff across all 15 commits with no regressions between fixes.

Verification NOT performed (requires real infrastructure): COBOL compilation, CICS transaction testing, DB2 SQL execution, batch job execution against representative datasets, and JCL submission. See DEPLOYMENT.md (added to the repository in this remediation) for the specific test-region checklist a deploying team must run before promoting any of these changes to production.

# 5. Known Issues

R3 lockout reset is incomplete: The failed-attempt counter correctly increments and enforces the lockout threshold, but the complementary reset-on-successful-signon logic could not be landed after 3 attempts: the delivery pipeline's patch-reapplication step repeatably failed with a context mismatch at the exact same source line, despite the underlying edit being logically correct each time. This is not a security regression — if anything it errs toward more lockout, not less — but a user could eventually hit the threshold from historical failed attempts even after a successful login.

R1 (plaintext passwords) requires platform integration: The documented recommendation is a salted one-way hash via a callable security exit or z/OS RACF/ICSF service. No such exit exists in this repository, and hand-rolling a substitute hash function in COBOL would provide false confidence without real cryptographic guarantees. Fixed with an in-source comment documenting the gap and the required production remediation instead.

R9 (unencrypted FTP) requires verified infrastructure: The deployment scripts tunnel through "localhost:2121" to a real external mainframe provider (referenced as Ensono). Blindly swapping the transport protocol without being able to verify the remote endpoint's actual SFTP/FTPS support risked silently breaking a working deployment pipeline. Fixed with an in-source comment documenting the risk and the required verification step instead.

# 6. Recommendations and Future Enhancements

Recommended next steps, in rough priority order:

- Complete R3: land the reset-on-successful-signon logic (a smaller, more targeted change may avoid the patch-application conflict) so the lockout counter clears correctly after a legitimate login.

- R1: integrate a real RACF/ICSF-backed credential hash-and-compare exit rather than continuing with plaintext password storage in production.

- R9: confirm the actual tunnel/endpoint configuration with the Ensono-hosted environment and migrate to SFTP/FTPS if supported.

- Add a lightweight, repository-local vulnerability-pattern guard (a grep-based script checking for the same classes of defect just fixed — hardcoded credential comparisons, DISPLAY of password fields, STRING-built dynamic SQL, magic-value privilege grants) so a future change cannot silently reintroduce them.

- Add a lockout auto-expiry (time-based unlock) as a more robust alternative/complement to a simple reset-on-success, since it avoids the specific location that caused the R3 patch-application issue.

- Add an audit trail for admin actions (e.g., who created which user account and when) to complement the authorization fixes in R4/I3.

- Add an idempotent batch-reconciliation control record so a rerun enabled by the R8 fix (OPEN EXTEND) cannot still double-post a partially-processed transaction file.

- Schedule and execute the full DEPLOYMENT.md test-region checklist in a real CICS/DB2 test region before any production promotion — nothing in this report substitutes for that.

# 7. Modified Files Summary



| File | Status | Lines +/- |

|---|---|---|

| app/cbl/COSGN00C.cbl | Modified | +41 / -55 |

| app/cbl/COUSR01C.cbl | Modified | +18 / -13 |

| app/app-transaction-type-db2/cbl/COTRTUPC.cbl | Modified | +5 / -28 |

| app/cbl/CBTRN02C.cbl | Modified | +7 / -37 |

| app/cbl/CBACT04C.cbl | Modified | +5 / -11 |

| app/cpy/CSUSR01Y.cpy | Modified | +12 / -1 |

| scripts/remote_compile.sh | Modified | +8 / -0 |

| scripts/remote_submit.sh | Modified | +8 / -0 |

| scripts/remote_refresh.sh | Modified | +8 / -0 |

| scripts/upld_module.sh | Modified | +8 / -0 |

| README.md | Modified | Fix-status tables added |

| DEPLOYMENT.md | Added (new) | +78 / -0 |



Note: two 0-byte internal bookkeeping artifacts (app/app-transaction-type-db2/cbl/COTRTUPC.cbl.lock, app/cbl/COSGN00C.cbl.lock) were committed early in this remediation before a genesis pipeline bug (fixed mid-session) was corrected. They are harmless but not cleaned up, since no file-delete capability exists in the current agent toolkit.