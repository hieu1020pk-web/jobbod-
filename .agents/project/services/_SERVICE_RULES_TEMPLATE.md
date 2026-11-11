# Service Rules — [service-id] / template

> Sao chép thành `[service-id].md` theo từng module/service. Không có service rule nghĩa là dùng company + project rule.

- **Owner / escalation:** [team, Tech Lead, reviewer]
- **Source/tests paths:** [paths; affected API/event/schema locations]
- **Boundaries:** [dependencies, owned database, public contract, consumers/producers]
- **Tech stack + conventions:** [verified version, commands, layering, codegen]
- **Change-specific CI gates:** [extra check IDs + real CI job bindings nếu có]
- **Test routing / cost:** [existing suites và selectors; fast/module/boundary commands, timeout/workers, slow-test owner; không thêm file theo task]
- **Integration test fixtures:** [DB isolation, queue/topic and consumer group, ports, fake secrets]
- **Release:** [rollout order, flags, health checks, SLO, restore/rollback and on-call]
- **Risk rules:** [service-specific critical signals; cannot downgrade company critical criteria]
- **Last updated / approved by:** [date, human reviewer]
