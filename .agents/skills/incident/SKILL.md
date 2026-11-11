---
name: incident-triage
description: Triage lỗi agent/release, lưu bằng chứng và đề xuất đường khôi phục.
---
# Skill: Failure / Incident Triage
**Trigger:** retries exhausted, contract drift, deployment rollback hoặc security finding.
**Inputs:** task/run ID, error log, SHA, changes, current environment, incident owner.
**Steps:** ngừng hành động nguy hiểm → phân loại code/tool/policy/infra → ghi last good state → lấy evidence tối thiểu → nêu recovery options và human decision.
**Outputs:** Decision Record/Incident link, owner, next action, revalidation gates.
**Boundary:** không tự thao tác destructive/production nếu không được ủy quyền.
