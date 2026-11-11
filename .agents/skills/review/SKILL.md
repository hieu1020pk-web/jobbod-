---
name: review-change
description: Independent review theo AC, diff và evidence thực tế.
---
# Skill: Review Change
**Trigger:** PR ready for review hoặc gate failure triage.
**Inputs:** task contract, spec gốc, diff/sha, CI logs, contract versions.
**Steps:** đối chiếu scope → AC → quality matrix → missing checks/N/A → edge/security/migration → findings → conclusion.
**Outputs:** QA_REPORT + `PASS/FAIL/BLOCKED`, citations đến file/diff/CI evidence và open findings.
**Boundary:** không sửa code đang review hay tắt gates.
