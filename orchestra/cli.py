"""Orchestra CLI entrypoint and subcommand dispatcher."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import orchestra
from orchestra.adapters.antigravity import AntigravityAdapter
from orchestra.adapters.claude import ClaudeCodeAdapter
from orchestra.adapters.cursor import CursorAdapter
from orchestra.adapters.mock import MockAdapter
from orchestra.adapters.opencode import OpenCodeAdapter
from orchestra.budget.manager import BudgetManager
from orchestra.budget.profiles import BudgetProfileManager
from orchestra.models import RunStatus, Tier, WorkflowDefinition, WorkflowStep
from orchestra.registry import ManifestLoader, RoutingExplainer, SkillDiscovery, SkillResolver
from orchestra.security.policy import SecurityPolicyEngine
from orchestra.validator import SchemaValidator
from orchestra.workflow.engine import WorkflowEngine
from orchestra.workflow.state import RunStateManager


class OrchestraCLI:
    def __init__(self, workspace_root: Optional[Path] = None):
        cwd = Path.cwd().resolve()
        repo_root = Path(__file__).parent.parent.resolve()
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        elif (cwd / "schemas").is_dir() or (cwd / "skills").is_dir() or (cwd / ".agents" / "skills").is_dir():
            self.workspace_root = cwd
        else:
            self.workspace_root = repo_root
        self.discovery = SkillDiscovery()
        self.state_manager = RunStateManager(self.workspace_root)

    def run(self, argv: Optional[List[str]] = None) -> int:
        base_parser = argparse.ArgumentParser(add_help=False)
        base_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

        parser = argparse.ArgumentParser(
            prog="orch",
            description="🎻 Orchestra: Model-Agnostic AI Orchestration Framework",
            parents=[base_parser],
        )
        subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

        # version
        subparsers.add_parser("version", parents=[base_parser], help="Print version information")

        # doctor
        subparsers.add_parser("doctor", parents=[base_parser], help="Check system prerequisites and adapter health")

        # validate
        subparsers.add_parser("validate", parents=[base_parser], help="Validate repository structure, schemas, and links")

        # skills
        skills_parser = subparsers.add_parser("skills", parents=[base_parser], help="Skill management")
        skills_subs = skills_parser.add_subparsers(dest="skills_action")

        skills_subs.add_parser("list", parents=[base_parser], help="List discovered skills")

        inspect_p = skills_subs.add_parser("inspect", parents=[base_parser], help="Inspect skill details")
        inspect_p.add_argument("skill_id", help="Skill ID")

        search_p = skills_subs.add_parser("search", parents=[base_parser], help="Search skills by keyword")
        search_p.add_argument("query", help="Search query")

        skills_subs.add_parser("validate", parents=[base_parser], help="Validate all skill manifests against schema")

        # route
        route_p = subparsers.add_parser("route", parents=[base_parser], help="Deterministically route a task to skills")
        route_p.add_argument("--task", "-t", required=True, help="Task description")
        route_p.add_argument("--explain", "-e", action="store_true", help="Explain routing decision")
        route_p.add_argument("--budget", "-b", type=int, default=4000, help="Context token budget")
        route_p.add_argument("--file", "-f", action="append", help="Target file paths")

        # workflow
        wf_parser = subparsers.add_parser("workflow", parents=[base_parser], help="Workflow operations")
        wf_subs = wf_parser.add_subparsers(dest="wf_action")

        wf_subs.add_parser("list", parents=[base_parser], help="List available declarative workflows")

        wf_val = wf_subs.add_parser("validate", parents=[base_parser], help="Validate workflow JSON file")
        wf_val.add_argument("file", help="Workflow JSON path")

        wf_run = wf_subs.add_parser("run", parents=[base_parser], help="Run workflow file")
        wf_run.add_argument("file", help="Workflow JSON path")
        wf_run.add_argument("--adapter", default="mock", choices=["mock", "opencode", "antigravity", "cursor", "claude"])

        # run
        run_parser = subparsers.add_parser("run", parents=[base_parser], help="Run inspection and recovery")
        run_subs = run_parser.add_subparsers(dest="run_action")

        run_subs.add_parser("list", parents=[base_parser], help="List execution runs")

        run_stat = run_subs.add_parser("status", parents=[base_parser], help="Get run status")
        run_stat.add_argument("run_id", help="Run ID")

        run_insp = run_subs.add_parser("inspect", parents=[base_parser], help="Inspect full run details")
        run_insp.add_argument("run_id", help="Run ID")

        run_canc = run_subs.add_parser("cancel", parents=[base_parser], help="Cancel an active run")
        run_canc.add_argument("run_id", help="Run ID")

        run_query = run_subs.add_parser("query", parents=[base_parser], help="Query runs in SQLite analytics database")
        run_query.add_argument("--status", help="Filter by status (succeeded, failed, cancelled)")
        run_query.add_argument("--tier", help="Filter by tier (Tiny, Normal, Complex, Architectural)")
        run_query.add_argument("--workflow", help="Filter by workflow ID")
        run_query.add_argument("--adapter", help="Filter by adapter")
        run_query.add_argument("--limit", type=int, default=20, help="Max results")

        run_subs.add_parser("stats", parents=[base_parser], help="Display aggregate execution analytics from SQLite")

        run_subs.add_parser("reindex", parents=[base_parser], help="Rebuild SQLite analytics index from on-disk runs")

        # adapters
        adap_parser = subparsers.add_parser("adapters", parents=[base_parser], help="Adapter operations")
        adap_subs = adap_parser.add_subparsers(dest="adap_action")

        adap_subs.add_parser("list", parents=[base_parser], help="List available client adapters")
        adap_subs.add_parser("doctor", parents=[base_parser], help="Check adapter health and environments")

        # install / uninstall
        inst_p = subparsers.add_parser("install", parents=[base_parser], help="Deploy Orchestra to a target environment")
        inst_p.add_argument("target", choices=["opencode", "antigravity", "cursor", "claude", "project"])
        inst_p.add_argument("path", nargs="?", help="Project path (for project target)")
        inst_p.add_argument("--dry-run", action="store_true", help="Simulate installation without changes")

        uninst_p = subparsers.add_parser("uninstall", parents=[base_parser], help="Uninstall Orchestra from target")
        uninst_p.add_argument("target", choices=["opencode", "antigravity", "cursor", "claude"])

        # benchmark
        subparsers.add_parser("benchmark", parents=[base_parser], help="Run token-efficiency benchmarks")

        # learn
        learn_p = subparsers.add_parser(
            "learn",
            parents=[base_parser],
            help="Analyze delegation loop patterns and suggest protocol/rule refinements",
        )
        learn_p.add_argument(
            "--min-occurrences",
            type=int,
            default=1,
            help="Minimum occurrences to generate rule suggestion",
        )

        args = parser.parse_args(argv)
        if not args.subcommand:
            parser.print_help()
            return 0

        # Command Dispatch
        handler = getattr(self, f"cmd_{args.subcommand}", None)
        if handler:
            return handler(args)

        parser.print_help()
        return 1

    def _output(self, data: Any, args: argparse.Namespace) -> None:
        if getattr(args, "json", False):
            print(json.dumps(data, indent=2))
        else:
            if isinstance(data, str):
                print(data)
            else:
                print(json.dumps(data, indent=2))

    # --- Commands ---

    def cmd_version(self, args: argparse.Namespace) -> int:
        info = {
            "orchestra_version": orchestra.__version__,
            "author": orchestra.__author__,
            "license": orchestra.__license__,
            "python_version": sys.version.split()[0],
        }
        if args.json:
            self._output(info, args)
        else:
            print(f"🎻 Orchestra v{info['orchestra_version']} (Python {info['python_version']})")
        return 0

    def cmd_doctor(self, args: argparse.Namespace) -> int:
        results = {
            "schemas": (self.workspace_root / "schemas").is_dir(),
            "skills": (self.workspace_root / "skills").is_dir() or (self.workspace_root / ".agents" / "skills").is_dir(),
            "opencode_adapter": OpenCodeAdapter().validate_environment()[0],
            "antigravity_adapter": AntigravityAdapter().validate_environment()[0],
        }
        if args.json:
            self._output(results, args)
        else:
            print("=== Orchestra Health Check ===")
            print(f"✓ Schemas directory: {'OK' if results['schemas'] else 'MISSING'}")
            print(f"✓ Skills directory:  {'OK' if results['skills'] else 'MISSING'}")
            print(f"{'✓' if results['opencode_adapter'] else '⚠'} OpenCode environment: {'READY' if results['opencode_adapter'] else 'INCOMPLETE'}")
            print(f"{'✓' if results['antigravity_adapter'] else '⚠'} Antigravity environment: {'READY' if results['antigravity_adapter'] else 'INCOMPLETE'}")
        return 0

    def cmd_skills(self, args: argparse.Namespace) -> int:
        skills = self.discovery.discover_workspace(self.workspace_root)
        action = getattr(args, "skills_action", "list") or "list"

        if action == "list":
            if args.json:
                data = [{
                    "id": s.id,
                    "name": s.name,
                    "version": s.version,
                    "kind": s.kind,
                    "summary": s.summary,
                    "tier": s.execution.get("tier", "Normal"),
                } for s in skills.values()]
                self._output(data, args)
            else:
                print(f"Discovered {len(skills)} skills in workspace:")
                for s in skills.values():
                    print(f"  • {s.id:<20} [v{s.version}] ({s.kind}) - {s.summary[:60]}...")
            return 0

        elif action == "inspect":
            s_id = args.skill_id
            skill = self.discovery.get_skill(s_id)
            if not skill:
                print(f"Error: Skill '{s_id}' not found.", file=sys.stderr)
                return 1
            if args.json:
                self._output(skill.__dict__, args)
            else:
                print(f"Skill: {skill.name} ({skill.id})")
                print(f"Version: {skill.version} | Kind: {skill.kind}")
                print(f"Summary: {skill.summary}")
                print(f"Capabilities: {', '.join(skill.capabilities)}")
                print(f"Triggers: {skill.triggers}")
            return 0

        elif action == "search":
            q = args.query.lower()
            matches = [
                s for s in skills.values()
                if q in s.id.lower() or q in s.name.lower() or q in s.summary.lower()
                or any(q in k.lower() for k in s.triggers.get("keywords", []))
            ]
            if args.json:
                self._output([{"id": s.id, "name": s.name, "summary": s.summary} for s in matches], args)
            else:
                print(f"Search results for '{q}' ({len(matches)} matches):")
                for s in matches:
                    print(f"  • {s.id}: {s.summary}")
            return 0

        elif action == "validate":
            schema_file = self.workspace_root / "schemas" / "skill-manifest.json"
            errors_found = 0
            for s_id, s in skills.items():
                m_file = Path(s.path) / "manifest.json"
                with open(m_file, "r") as f:
                    data = json.load(f)
                errs = SchemaValidator.validate(data, schema_file)
                if errs:
                    errors_found += 1
                    print(f"❌ {s_id}: {errs}")
                else:
                    print(f"✓ {s_id} valid")
            return 1 if errors_found else 0

        return 0

    def cmd_route(self, args: argparse.Namespace) -> int:
        skills = self.discovery.discover_workspace(self.workspace_root)
        resolver = SkillResolver(skills)
        res = resolver.resolve(
            args.task,
            context_budget_tokens=args.budget,
            target_files=args.file,
        )

        if args.json:
            self._output(RoutingExplainer.to_dict(res), args)
        elif args.explain:
            print(RoutingExplainer.format_text(res))
        else:
            selected = [s.id for s in res.selected_skills]
            print(f"Task Tier: {res.inferred_tier.value}")
            print(f"Selected Skills: {selected or '(Default Protocols)'}")
            print(f"Estimated Context: ~{res.estimated_context_tokens} tokens")
        return 0

    def cmd_workflow(self, args: argparse.Namespace) -> int:
        action = getattr(args, "wf_action", "list") or "list"

        if action == "list":
            wf_dir = self.workspace_root / "workflows"
            wfs = list(wf_dir.glob("*.json")) if wf_dir.is_dir() else []
            if args.json:
                self._output([f.name for f in wfs], args)
            else:
                print(f"Available workflows ({len(wfs)}):")
                for w in wfs:
                    print(f"  • {w.name}")
            return 0

        elif action == "validate":
            w_file = Path(args.file)
            schema = self.workspace_root / "schemas" / "workflow-definition.json"
            with open(w_file) as f:
                data = json.load(f)
            errs = SchemaValidator.validate(data, schema)
            if errs:
                print(f"❌ Validation failed:\n- " + "\n- ".join(errs), file=sys.stderr)
                return 1
            print("✓ Workflow definition is valid.")
            return 0

        elif action == "run":
            w_file = Path(args.file)
            with open(w_file) as f:
                data = json.load(f)

            steps = [
                WorkflowStep(
                    id=s["id"],
                    name=s["name"],
                    agent_role=s["agent_role"],
                    dependencies=s.get("dependencies", []),
                    target_files=s.get("target_files", []),
                    verification_command=s.get("verification_command"),
                )
                for s in data["steps"]
            ]
            wf = WorkflowDefinition(
                schema_version=data["schema_version"],
                id=data["id"],
                version=data["version"],
                name=data["name"],
                description=data["description"],
                tier=Tier(data["tier"]),
                steps=steps,
                acceptance_criteria=data.get("acceptance_criteria", []),
            )

            adapter = MockAdapter()
            if args.adapter == "opencode":
                adapter = OpenCodeAdapter()
            elif args.adapter == "antigravity":
                adapter = AntigravityAdapter()
            elif args.adapter == "cursor":
                adapter = CursorAdapter()
            elif args.adapter == "claude":
                adapter = ClaudeCodeAdapter()

            profile = BudgetProfileManager.get_profile(wf.tier.value)
            b_mgr = BudgetManager(profile)
            sec = SecurityPolicyEngine(self.workspace_root)
            engine = WorkflowEngine(wf, adapter, self.state_manager, b_mgr, sec)

            record = engine.run(task_description=wf.name)
            if args.json:
                self._output(record.__dict__, args)
            else:
                print(f"✓ Workflow '{wf.name}' executed with status: {record.status.value}")
                print(f"Run ID: {record.run_id}")
            return 0

        return 0

    def cmd_run(self, args: argparse.Namespace) -> int:
        action = getattr(args, "run_action", "list") or "list"

        if action == "list":
            runs = self.state_manager.list_runs()
            if args.json:
                self._output(runs, args)
            else:
                print(f"Recorded runs ({len(runs)}):")
                for r in runs:
                    print(f"  • [{r.get('status')}] {r.get('run_id')} ({r.get('workflow_id')}) at {r.get('created_at')}")
            return 0

        elif action == "status" or action == "inspect":
            run = self.state_manager.load_run(args.run_id)
            if not run:
                print(f"Error: Run '{args.run_id}' not found.", file=sys.stderr)
                return 1
            if args.json:
                self._output(run.__dict__, args)
            else:
                print(f"Run ID: {run.run_id}")
                print(f"Workflow: {run.workflow_id} (Tier: {run.tier})")
                print(f"Status: {run.status.value}")
                print(f"Tokens: {run.total_token_usage}")
                print("Steps:")
                for s in run.step_records:
                    print(f"  - [{s.status.value}] {s.name} ({s.agent_role})")
            return 0

        elif action == "cancel":
            run = self.state_manager.load_run(args.run_id)
            if not run:
                print(f"Error: Run '{args.run_id}' not found.", file=sys.stderr)
                return 1
            self.state_manager.complete_run(args.run_id, RunStatus.CANCELLED)
            if args.json:
                self._output({"run_id": args.run_id, "status": "cancelled"}, args)
            else:
                print(f"✓ Run '{args.run_id}' has been cancelled.")
            return 0

        elif action == "query":
            if not self.state_manager.analytics_db:
                print("Error: Analytics database not initialized.", file=sys.stderr)
                return 1
            results = self.state_manager.analytics_db.query_runs(
                status=getattr(args, "status", None),
                tier=getattr(args, "tier", None),
                workflow_id=getattr(args, "workflow", None),
                adapter=getattr(args, "adapter", None),
                limit=getattr(args, "limit", 20),
            )
            if args.json:
                self._output(results, args)
            else:
                print(f"Queried runs ({len(results)} matching):")
                for r in results:
                    print(f"  • [{r['status']}] {r['run_id']} (WF: {r['workflow_id']}, Tier: {r['tier']}, Adapter: {r['adapter']}) - {r['total_tokens']} tokens")
            return 0

        elif action == "stats":
            if not self.state_manager.analytics_db:
                print("Error: Analytics database not initialized.", file=sys.stderr)
                return 1
            stats = self.state_manager.analytics_db.get_summary_stats()
            if args.json:
                self._output(stats, args)
            else:
                print("=== Orchestra Execution Analytics (SQLite) ===")
                print(f"Total Runs:       {stats['total_runs']} ({stats['succeeded_runs']} succeeded, {stats['failed_runs']} failed, {stats['cancelled_runs']} cancelled)")
                print(f"Success Rate:     {stats['success_rate_percent']}%")
                print(f"Tokens Consumed:  {stats['total_tokens_consumed']} (Cost: ${stats['total_cost_usd']:.4f})")
                print(f"Avg Run Duration: {stats['avg_duration_seconds']}s")
                print("\nRuns by Tier:")
                for t, info in stats["tiers"].items():
                    print(f"  • {t:<14}: {info['count']} runs (avg {info['avg_tokens']} tokens)")
                print("\nSteps by Role:")
                for r, r_info in stats["agent_roles"].items():
                    print(f"  • {r:<14}: {r_info['total_steps']} total steps ({r_info['failed_steps']} failed)")
            return 0

        elif action == "reindex":
            if not self.state_manager.analytics_db:
                print("Error: Analytics database not initialized.", file=sys.stderr)
                return 1
            count = self.state_manager.analytics_db.index_all_existing_runs(self.state_manager.runs_dir)
            print(f"✓ Reindexed {count} runs into SQLite database at {self.state_manager.analytics_db.db_path}.")
            return 0

        return 0

    def cmd_adapters(self, args: argparse.Namespace) -> int:
        action = getattr(args, "adap_action", "list") or "list"
        adapters = [MockAdapter(), OpenCodeAdapter(), AntigravityAdapter(), CursorAdapter(), ClaudeCodeAdapter()]

        if action == "list":
            data = [{
                "name": a.get_name(),
                "capabilities": a.get_capabilities(),
            } for a in adapters]
            if args.json:
                self._output(data, args)
            else:
                print("Available Adapters:")
                for a in adapters:
                    print(f"  • {a.get_name():<12} Capabilities: {len(a.get_capabilities())} registered")
            return 0

        elif action == "doctor":
            results = {}
            for a in adapters:
                ok, issues = a.validate_environment()
                results[a.get_name()] = {"ready": ok, "issues": issues}
            if args.json:
                self._output(results, args)
            else:
                print("Adapter Diagnostics:")
                for name, res in results.items():
                    stat = "✓ READY" if res["ready"] else "⚠ ISSUES"
                    print(f"  {stat} {name}")
                    for iss in res["issues"]:
                        print(f"      - {iss}")
            return 0

        return 0

    def cmd_install(self, args: argparse.Namespace) -> int:
        skills = self.discovery.discover_workspace(self.workspace_root)
        target = args.target

        if args.dry_run:
            print(f"[DRY-RUN] Would install Orchestra ({len(skills)} skills) to {target}")
            return 0

        if target == "opencode":
            adapter = OpenCodeAdapter()
            installed = adapter.install_skills(list(skills.values()))
            # Configure agents
            adapter.configure_agents(self.workspace_root / "agents")
            print(f"✓ Installed {len(installed)} skills and configured Orchestra agents in OpenCode.")
        elif target == "antigravity":
            adapter = AntigravityAdapter(str(self.workspace_root))
            installed = adapter.install_skills(list(skills.values()))
            print(f"✓ Installed {len(installed)} skills in .agents/skills/ for Antigravity.")
        elif target == "cursor":
            adapter = CursorAdapter(str(self.workspace_root))
            installed = adapter.install_skills(list(skills.values()))
            rule_path = adapter.generate_rules()
            print(f"✓ Installed {len(installed)} skills and generated {rule_path} for Cursor.")
        elif target == "claude":
            adapter = ClaudeCodeAdapter(str(self.workspace_root))
            installed = adapter.install_skills(list(skills.values()))
            mem_path = adapter.generate_memory()
            print(f"✓ Installed {len(installed)} skills and generated {mem_path} for Claude Code.")
        elif target == "project":
            if not args.path:
                print("Error: Target path required for project install.", file=sys.stderr)
                return 1
            p = Path(args.path).resolve()
            adapter = AntigravityAdapter(str(p))
            installed = adapter.install_skills(list(skills.values()))
            print(f"✓ Installed Orchestra into project at {p}")

        return 0

    def cmd_uninstall(self, args: argparse.Namespace) -> int:
        target = args.target
        home = Path.home()
        if target == "opencode":
            dest_dir = home / ".config" / "opencode"
            orch_md = dest_dir / "ORCHESTRATOR.md"
            if orch_md.exists():
                orch_md.unlink()
                print(f"✓ Removed {orch_md}")
            backups = sorted(dest_dir.glob("AGENTS.md.bak.*"))
            if backups:
                latest = backups[-1]
                shutil.copy2(latest, dest_dir / "AGENTS.md")
                print(f"✓ Restored original AGENTS.md from {latest.name}")
            print(f"✅ Uninstalled Orchestra configuration from OpenCode.")
            return 0
        elif target == "antigravity":
            rule_file = home / ".gemini" / "antigravity-cli" / "rules" / "ORCHESTRA_AGENTS.md"
            if rule_file.exists():
                rule_file.unlink()
                print(f"✓ Removed {rule_file}")
            print(f"✅ Uninstalled Orchestra configuration from Antigravity.")
            return 0
        elif target == "cursor":
            rule_file = self.workspace_root / ".cursor" / "rules" / "orchestra.mdc"
            if rule_file.exists():
                rule_file.unlink()
                print(f"✓ Removed {rule_file}")
            print(f"✅ Uninstalled Orchestra configuration from Cursor.")
            return 0
        elif target == "claude":
            claude_file = self.workspace_root / "CLAUDE.md"
            if claude_file.exists():
                claude_file.unlink()
                print(f"✓ Removed {claude_file}")
            print(f"✅ Uninstalled Orchestra configuration from Claude Code.")
            return 0
        print(f"Error: Unsupported uninstall target '{target}'.", file=sys.stderr)
        return 1

    def cmd_learn(self, args: argparse.Namespace) -> int:
        if not self.state_manager.analytics_db:
            print("Error: Analytics database is not configured.", file=sys.stderr)
            return 1

        min_occ = getattr(args, "min_occurrences", 1)
        metrics = self.state_manager.analytics_db.get_delegation_metrics()
        suggestions = self.state_manager.analytics_db.suggest_rule_improvements(min_occurrences=min_occ)

        payload = {
            "delegation_metrics": metrics,
            "rule_suggestions": suggestions,
        }

        if args.json:
            self._output(payload, args)
            return 0

        print("=== 🎻 Orchestra AI Delegation Loop Insights ===")
        print(f"Total Dispatched Steps:    {metrics['total_dispatched_steps']}")
        print(f"First-Pass Success:        {metrics['first_pass_success']} ({metrics['first_pass_rate_percent']}%)")
        print(f"Remediated by Loop:        {metrics['remediated_success']}")
        print(f"Failed / Escalated:        {metrics['failed_steps']}")
        print(f"Total Retries Performed:   {metrics['total_retries']}")
        print(f"Loop Repair Efficiency:    {metrics['remediation_efficiency_percent']}%")

        if metrics["roles"]:
            print("\n--- Role-Level Delegation Performance ---")
            for role, data in metrics["roles"].items():
                print(
                    f"  @{role:<12} Steps: {data['total_steps']:<3} | "
                    f"First-Pass: {data['first_pass']:<3} | "
                    f"Remediated: {data['remediated']:<3} | "
                    f"Failed: {data['failed']:<3} | "
                    f"Retries: {data['total_retries']}"
                )

        print("\n=== 💡 Compounding Feedback & Rule Suggestions ===")
        if not suggestions:
            print("  ✓ Zero recurring failure patterns detected. Delegation loops are running cleanly.")
        else:
            for idx, sugg in enumerate(suggestions, 1):
                print(f"\n[{idx}] @{sugg['role']} - {sugg['category']}")
                print(f"    Impact:         {sugg['impact']}")
                print(f"    Recommendation: {sugg['recommendation']}")

        return 0

    def cmd_validate(self, args: argparse.Namespace) -> int:
        # Run repository validation
        res = subprocess.run(["bash", "scripts/validate.sh"], cwd=str(self.workspace_root))
        return res.returncode

    def cmd_benchmark(self, args: argparse.Namespace) -> int:
        from tests.benchmarks.test_benchmarks import BenchmarkRunner
        runner = BenchmarkRunner(self.workspace_root)
        results = runner.run_benchmarks()
        if args.json:
            self._output(results, args)
        else:
            runner.print_summary(results)
        return 0


def main():
    cli = OrchestraCLI()
    sys.exit(cli.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
