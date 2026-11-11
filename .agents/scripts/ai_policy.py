#!/usr/bin/env python3
"""Jobbod AI rules v2: lightweight, stdlib-only DECLARATIVE policy validator.

This is not a sandbox, permission engine, or Git hosting approval verifier.
Use trusted copies of policy/validator in CI; do not run PR-modified security scripts
with sensitive credentials. Exit 0 means configuration/manifest consistency only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys

AI_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPANY = AI_ROOT / "policies" / "company.policy.json"
DEFAULT_PROJECT = AI_ROOT / "project" / "project.policy.json"
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
FILL_TOKEN = "__REQUIRED__"
RANK = {"FAST": 0, "STANDARD": 1, "CRITICAL": 2}


class PolicyError(Exception):
    pass


def read_json(path: Path) -> dict:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PolicyError(f"Không đọc được JSON {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise PolicyError(f"Root JSON phải là object: {path}")
    return content


def check_str(value, label: str, errors: list[str]):
    if not isinstance(value, str) or not value.strip() or FILL_TOKEN in value:
        errors.append(f"{label}: cần giá trị thực, không dùng placeholder")


def safe_patterns(patterns, label, errors):
    if not isinstance(patterns, list) or not patterns:
        errors.append(f"{label}: cần ít nhất một allowed path")
        return
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern.strip():
            errors.append(f"{label}: glob không hợp lệ {pattern!r}")
            continue
        parts = pattern.split("/")
        if (pattern.startswith("/") or "\\" in pattern or ".." in parts
                or pattern in ("*", "**", "./**") or FILL_TOKEN in pattern
                or "//" in pattern or pattern.startswith("-/")):
            errors.append(f"{label}: glob quá rộng/không an toàn {pattern!r}")


def validate_company(company: dict) -> list[str]:
    errors = []
    if company.get("schema_version") != "2.0":
        errors.append("company: schema_version phải là 2.0")
    risk = company.get("risk", {})
    if not isinstance(risk, dict) or risk.get("tiers") != ["FAST", "STANDARD", "CRITICAL"]:
        errors.append("company: cấu hình risk tiers không hợp lệ")
    quality = company.get("quality", {})
    if not isinstance(quality, dict):
        errors.append("company: quality phải là object")
        return errors
    ci = quality.get("tier_ci_baseline", {})
    changes = quality.get("change_ci_checks", {})
    if not isinstance(ci, dict) or any(t not in ci or not isinstance(ci[t], list) for t in RANK):
        errors.append("company: thiếu tier_ci_baseline")
    if not isinstance(changes, dict) or not changes:
        errors.append("company: thiếu change_ci_checks")
    if not isinstance(risk, dict) or any(not isinstance(risk.get(k), list) for k in ("critical_signals", "critical_change_types", "fast_change_types")):
        errors.append("company: thiếu risk signal/type maps")
    execution = company.get("execution", {})
    if not isinstance(execution, dict):
        errors.append("company: execution phải là object")
    scope = company.get("scope", {})
    if not isinstance(scope, dict) or not isinstance(scope.get("governance_protected_globs"), list):
        errors.append("company: thiếu protected path globs")
    return errors


def validate_project(project: dict) -> list[str]:
    errors = []
    if project.get("schema_version") != "2.0":
        errors.append("project: schema_version phải là 2.0")
    for field in ("project_id", "repository", "default_branch", "approved_by", "approved_exception_process", "task_contract_directory", "approved_at"):
        check_str(project.get(field), f"project.{field}", errors)
    owners = project.get("owners")
    if not isinstance(owners, dict):
        errors.append("project.owners phải là object")
    else:
        for field in ("tech_lead", "security_owner", "release_owner"):
            check_str(owners.get(field), f"project.owners.{field}", errors)
    bindings = project.get("ci_check_bindings")
    if not isinstance(bindings, dict) or not bindings:
        errors.append("project.ci_check_bindings chưa map check_id → CI status thực tế")
    else:
        for name, ci_job in bindings.items():
            check_str(name, "project.ci_check_bindings key", errors)
            check_str(ci_job, f"project.ci_check_bindings.{name}", errors)
    additional = project.get("additional_required_checks", [])
    if not isinstance(additional, list) or any(not isinstance(x, str) or not x for x in additional):
        errors.append("project.additional_required_checks phải là list check IDs")
    max_agents = project.get("max_parallel_agents")
    if type(max_agents) is not int or max_agents < 1:
        errors.append("project.max_parallel_agents phải là int >= 1")
    if project.get("production_releases_default_to_human_approval") is not True:
        errors.append("project phải giữ production release mặc định cần human approval")
    return errors


def classify(task: dict, company: dict) -> str:
    risk_cfg = company["risk"]
    signals = set(task.get("risk_signals", []))
    changes = set(task.get("change_types", []))
    if signals & set(risk_cfg["critical_signals"]) or changes & set(risk_cfg["critical_change_types"]):
        return "CRITICAL"
    if changes and changes.issubset(set(risk_cfg["fast_change_types"])) and not signals:
        return "FAST"
    return "STANDARD"


def mandatory_checks(task: dict, company: dict, project: dict | None = None):
    tier = task.get("risk_tier", "STANDARD")
    derived = classify(task, company)
    # A human decision may downgrade routing but never remove original gates.
    effective = max([tier, derived], key=lambda t: RANK[t])
    quality = company["quality"]
    required = set(quality["tier_ci_baseline"][effective])
    for typ in task["change_types"]:
        required.update(quality["change_ci_checks"][typ])
    if len(task.get("impacted_services", [])) > 1:
        required.add("cross_service_integration")
    if project:
        required.update(project.get("additional_required_checks", []))
    return effective, sorted(required)


def validate_task(task: dict, company: dict, project: dict | None = None) -> tuple[list[str], str | None, list[str]]:
    errors = []
    for field in ("task_id", "title", "source_requirement", "base_sha"):
        check_str(task.get(field), f"task.{field}", errors)
    if not SHA_RE.fullmatch(str(task.get("base_sha", ""))):
        errors.append("task.base_sha cần một commit SHA 7–40 ký tự hex (được xác minh trong repo khi chạy scope)")
    tier = task.get("risk_tier")
    if tier not in RANK:
        errors.append("task.risk_tier phải là FAST | STANDARD | CRITICAL")
    types = task.get("change_types")
    known_types = company["quality"]["change_ci_checks"]
    if not isinstance(types, list) or not types or any(not isinstance(t, str) or t not in known_types for t in types):
        errors.append("task.change_types không hợp lệ hoặc không thuộc quality matrix")
    signals = task.get("risk_signals")
    if not isinstance(signals, list) or any(not isinstance(s, str) or not re.fullmatch(r"[a-z_]+", s) for s in signals):
        errors.append("task.risk_signals phải là list snake_case")
    assessment = task.get("risk_assessment", {})
    if not isinstance(assessment, dict):
        errors.append("task.risk_assessment phải là object")
        assessment = {}
    check_str(assessment.get("classification_reason"), "task.risk_assessment.classification_reason", errors)
    unresolved = assessment.get("unresolved_unknowns")
    if not isinstance(unresolved, list):
        errors.append("task.risk_assessment.unresolved_unknowns phải là list")
    elif unresolved:
        errors.append("task còn unresolved_unknowns: BLOCKED trước khi thực thi")
    scope = task.get("scope", {})
    if not isinstance(scope, dict):
        errors.append("task.scope phải là object")
        scope = {}
    safe_patterns(scope.get("allowed_paths"), "task.scope.allowed_paths", errors)
    out_of_scope = scope.get("out_of_scope")
    if out_of_scope is not None and out_of_scope != []:
        if not isinstance(out_of_scope, list):
            errors.append("task.scope.out_of_scope: phải là list mô tả giới hạn")
        else:
            for item in out_of_scope:
                check_str(item, "task.scope.out_of_scope[]", errors)
    services = task.get("impacted_services")
    if not isinstance(services, list) or not services:
        errors.append("task.impacted_services: cần ít nhất một service/module")
    else:
        for svc in services:
            check_str(svc, "task.impacted_services[]", errors)
    if not isinstance(task.get("dependencies"), list):
        errors.append("task.dependencies phải là list")
    owners = task.get("owners", {})
    if not isinstance(owners, dict):
        errors.append("task.owners phải là object")
        owners = {}
    for field in ("accountable_human", "executor"):
        check_str(owners.get(field), f"task.owners.{field}", errors)
    reviewer = owners.get("independent_reviewer")
    if reviewer:
        check_str(reviewer, "task.owners.independent_reviewer", errors)
    ac = task.get("acceptance_criteria")
    if not isinstance(ac, list) or not ac:
        errors.append("task.acceptance_criteria phải có ít nhất một AC")
    else:
        for i, item in enumerate(ac):
            if isinstance(item, str):
                check_str(item, f"task.acceptance_criteria[{i}]", errors)
            elif isinstance(item, dict):
                check_str(item.get("id"), f"task.acceptance_criteria[{i}].id", errors)
                desc = item.get("then") or item.get("description") or item.get("summary")
                if desc:
                    check_str(desc, f"task.acceptance_criteria[{i}].description/then", errors)
                else:
                    for key in ("given", "when", "then"):
                        check_str(item.get(key), f"task.acceptance_criteria[{i}].{key}", errors)
            else:
                errors.append(f"AC[{i}] phải là object hoặc string mô tả tiêu chí")
    execution = task.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            errors.append("task.execution phải là object")
            execution = {}
    else:
        execution = {}
    if "resource_isolation_note" in execution:
        check_str(execution.get("resource_isolation_note"), "task.execution.resource_isolation_note", errors)
    for key in ("fix_attempts_used", "transient_tool_retries_used", "token_spent"):
        val = execution.get(key)
        if val is not None and (type(val) is not int or val < 0):
            errors.append(f"task.execution.{key} phải là nonnegative integer")
    maxfix = company.get("execution", {}).get("maximum_code_fix_attempts_per_gate_failure", 0)
    maxretry = company.get("execution", {}).get("maximum_transient_tool_retries", 0)
    if maxfix and maxfix > 0 and isinstance(execution.get("fix_attempts_used"), int) and execution["fix_attempts_used"] > maxfix:
        errors.append(f"task: exceeded code-fix budget {maxfix}")
    if maxretry and maxretry > 0 and isinstance(execution.get("transient_tool_retries_used"), int) and execution["transient_tool_retries_used"] > maxretry:
        errors.append(f"task: exceeded transient-tool budget {maxretry}")
    quota = execution.get("token_quota")
    spent = execution.get("token_spent")
    if quota is not None:
        if type(quota) is not int or quota <= 0:
            errors.append("task.execution.token_quota phải là positive integer")
        elif type(spent) is int and spent > quota:
            errors.append("task: exceeded token quota")
        elif type(spent) is int and spent >= quota * company["execution"]["budget_warning_fraction"]:
            print(f"WARN: token usage đạt >= {company['execution']['budget_warning_fraction']:.0%} quota", file=sys.stderr)
    for used_key, limit_key in (("time_spent_minutes", "time_limit_minutes"), ("cost_spent", "cost_limit")):
        used, limit = execution.get(used_key), execution.get(limit_key)
        if limit is not None:
            if (used is not None and type(used) not in (int, float)) or type(limit) not in (int, float) or limit <= 0:
                errors.append(f"task.execution.{used_key}/{limit_key}: cần numeric budget hợp lệ")
            elif used is not None and used > limit:
                errors.append(f"task: exceeded {limit_key}")
            elif used is not None and used >= limit * company["execution"]["budget_warning_fraction"]:
                print(f"WARN: {used_key} đạt >= {company['execution']['budget_warning_fraction']:.0%} quota", file=sys.stderr)
    checks = task.get("required_checks")
    if not isinstance(checks, list) or any(not isinstance(x, str) or not x for x in checks):
        errors.append("task.required_checks phải là list check IDs")
        checks = []
    review = task.get("review", {})
    approval = task.get("approval", {})
    release = task.get("release", {})
    for section, label in ((review, "review"), (approval, "approval"), (release, "release")):
        if not isinstance(section, dict):
            errors.append(f"task.{label} phải là object")
    effective = None
    mandatory = []
    if tier in RANK and isinstance(types, list) and types and all(isinstance(x, str) and x in known_types for x in types) and isinstance(signals, list) and isinstance(task.get("impacted_services"), list):
        derived = classify(task, company)
        if RANK[tier] < RANK[derived]:
            downgraded = (
                derived == "CRITICAL" and isinstance(approval, dict)
                and isinstance(approval.get("risk_downgrade_decision_reference"), str)
                and bool(approval.get("risk_downgrade_decision_reference", "").strip())
                and bool(approval.get("risk_downgrade_approved_by", "").strip())
            )
            if not downgraded:
                errors.append(f"task.risk_tier={tier} thấp hơn classification={derived}; cần nâng tier hoặc Decision Record + human approver")
            else:
                print("WARN: routing downgraded by declared human decision; CRITICAL gates still apply; authorization must be verified externally", file=sys.stderr)
        effective, mandatory = mandatory_checks(task, company, project)
        missing = sorted(set(mandatory) - set(checks))
        if missing:
            errors.append("task.required_checks thiếu blocking checks: " + ", ".join(missing))
        known_checks = set().union(*company["quality"]["tier_ci_baseline"].values(), *known_types.values())
        if project:
            known_checks.update(project.get("additional_required_checks", []))
        unknown_checks = sorted(set(checks) - known_checks)
        if unknown_checks:
            errors.append("task.required_checks chứa unknown check ID: " + ", ".join(unknown_checks))
        if project:
            unmapped = sorted(set(mandatory) - set(project.get("ci_check_bindings", {})))
            if unmapped:
                errors.append("project.ci_check_bindings chưa map required CI checks: " + ", ".join(unmapped))
        if effective in company["quality"]["required_plan_review_tiers"]:
            if not isinstance(review, dict):
                errors.append("task.review thiếu plan review")
            else:
                check_str(review.get("plan_review_reference"), "task.review.plan_review_reference", errors)
        if effective == "CRITICAL":
            evidence_fields = {
                "security_review": (review, "review.security_review_reference"),
                "human_change_approval": (approval, "approval.human_change_approval_reference"),
                "rollback_or_restore_plan": (release, "release.rollback_or_restore_plan"),
            }
            for evidence_key in company["quality"].get("critical_evidence", []):
                if evidence_key not in evidence_fields:
                    errors.append(f"company quality: unknown critical evidence key {evidence_key}")
                    continue
                section, full_field = evidence_fields[evidence_key]
                if isinstance(section, dict):
                    check_str(section.get(full_field.split(".")[-1]), f"task.{full_field}", errors)
    if isinstance(release, dict) and "target_environment" in release:
        check_str(release.get("target_environment"), "task.release.target_environment", errors)
    na = task.get("na_exceptions", {})
    if not isinstance(na, dict):
        errors.append("task.na_exceptions phải là object")
    else:
        for check_id, record in na.items():
            if not isinstance(record, dict):
                errors.append(f"N/A {check_id}: cần reason/owner/approval_reference")
                continue
            for key in ("reason", "owner", "approval_reference"):
                check_str(record.get(key), f"N/A {check_id}.{key}", errors)
            if effective == "CRITICAL" and check_id in ("sast", "sca", "secrets_scan", "security_review_check", "rollback_readiness", "restore_drill"):
                if not record.get("approval_reference") or FILL_TOKEN in str(record.get("approval_reference")):
                    errors.append(f"N/A Critical gate {check_id} không được tự bỏ qua nếu thiếu approval_reference của tech lead")
    return errors, effective, mandatory


def path_matches(filepath: str, glob: str) -> bool:
    # fnmatch may match '/' for '*'; only vetted repository-relative patterns are accepted.
    return fnmatch.fnmatchcase(filepath, glob)


def validate_paths(changed_paths: list[str], task: dict, company: dict) -> list[str]:
    errors = []
    allowed = task["scope"]["allowed_paths"]
    blocked = company["scope"]["governance_protected_globs"] + company["scope"].get("deny_globs", [])
    for path in changed_paths:
        if not path or path.startswith("/") or "\\" in path or ".." in path.split("/"):
            errors.append(f"Invalid changed path: {path!r}")
        elif any(path_matches(path, pattern) for pattern in blocked):
            errors.append(f"Protected/secret path changed: {path}")
        elif not any(path_matches(path, pattern) for pattern in allowed):
            errors.append(f"Outside allowed paths: {path}")
    return errors


def git_changed_files(repo: Path, base: str, head: str) -> list[str]:
    for sha, name in ((base, "base"), (head, "head")):
        if not SHA_RE.fullmatch(sha):
            raise PolicyError(f"{name} SHA invalid; cần 7–40 hex chars")
        ret = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"], capture_output=True, text=True, check=False)
        if ret.returncode:
            raise PolicyError(f"{name} commit {sha} không có trong local git history")
    ret = subprocess.run(["git", "-C", str(repo), "diff", "--no-renames", "--name-only", "-z", base, head, "--"], capture_output=True, check=False)
    if ret.returncode:
        raise PolicyError(f"git diff lỗi: {ret.stderr.decode(errors='replace').strip()}")
    return [x.decode("utf-8", errors="replace") for x in ret.stdout.split(b"\0") if x]


def run(argv=None) -> int:
    p = argparse.ArgumentParser(description="Jobbod v2 declarative risk/check/scope validator")
    p.add_argument("--company", type=Path, default=DEFAULT_COMPANY)
    p.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("config")
    t = commands.add_parser("task")
    t.add_argument("--file", type=Path, required=True)
    t.add_argument("--allow-example", action="store_true")
    s = commands.add_parser("scope")
    s.add_argument("--file", type=Path, required=True)
    s.add_argument("--base", required=True)
    s.add_argument("--head", required=True)
    s.add_argument("--repo", type=Path, default=Path.cwd())
    args = p.parse_args(argv)
    try:
        company = read_json(args.company)
        errors = validate_company(company)
        if errors:
            raise PolicyError("\n".join(errors))
        project = None
        example = args.command == "task" and args.allow_example
        if example:
            if os.environ.get("CI", "").lower() not in ("", "0", "false"):
                raise PolicyError("--allow-example bị cấm trong CI")
            if args.file.name != "task.standard.example.json" or args.file.parent.name != "examples":
                raise PolicyError("--allow-example chỉ dùng cho sample ở .agents/examples")
        else:
            project = read_json(args.project)
            errors = validate_project(project)
            if errors:
                raise PolicyError("\n".join(errors))
        if args.command == "config":
            print("PASS: company+project policy structurally valid (not runtime enforcement)")
            return 0
        task = read_json(args.file)
        errors, tier, checks = validate_task(task, company, project)
        if errors:
            raise PolicyError("\n".join(errors))
        if args.command == "scope":
            if task["base_sha"].lower() != args.base.lower():
                # Short/long SHAs may differ while referring to the same commit;
                # require exact correspondence for predictable audit records.
                raise PolicyError("scope --base phải trùng task.base_sha; không tự đổi baseline")
            files = git_changed_files(args.repo.resolve(), args.base, args.head)
            errors = validate_paths(files, task, company)
            if errors:
                raise PolicyError("\n".join(errors))
            print(f"PASS: {len(files)} changed file(s) within declared scope and protected path policy")
        print(f"PASS: manifest consistent (NOT test/CI pass) | {task['task_id']} | effective_tier={tier} | required_checks={','.join(checks)}")
        return 0
    except PolicyError as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
