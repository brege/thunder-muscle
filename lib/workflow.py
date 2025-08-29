#!/usr/bin/env python3
"""
YAML workflow runner for Thunder Muscle analysis pipelines
"""
import yaml
import subprocess
import sys
import argparse
from pathlib import Path

# Add lib to path before importing custom modules
sys.path.append("lib")

from config import load_config  # noqa: E402


def run_command(cmd, description=""):
    """Run a command and return success/failure"""
    print(f"Running: {' '.join(cmd)}")
    if description:
        print(f"  → {description}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    else:
        print(f"  ✓ {result.stdout.strip()}")
        return True


def find_tool_script(action):
    """Find the appropriate script for an action"""
    from pathlib import Path

    # Built-in tm.py actions
    tm_actions = ["extract", "filter", "query", "stats"]
    if action in tm_actions:
        return ["python3", "tm.py", action]

    # Check analyzers directory
    analyzer_path = Path("analyzers") / f"{action}.py"
    if analyzer_path.exists():
        return ["python3", str(analyzer_path)]

    # Check plotters directory
    plotter_path = Path("plotters") / f"{action}.py"
    if plotter_path.exists():
        return ["python3", str(plotter_path)]

    # Check tools directory
    tool_path = Path("tools") / f"{action}.py"
    if tool_path.exists():
        return ["python3", str(tool_path)]

    # Check for underscore variants (analyze_temporal -> analyze_temporal.py)
    if action.startswith("analyze_"):
        analyzer_path = Path("analyzers") / f"{action}.py"
        if analyzer_path.exists():
            return ["python3", str(analyzer_path)]

    if action.startswith("plot_"):
        plotter_path = Path("plotters") / f"{action}.py"
        if plotter_path.exists():
            return ["python3", str(plotter_path)]

    if action.startswith("backup_"):
        tool_path = Path("tools") / f"{action}.py"
        if tool_path.exists():
            return ["python3", str(tool_path)]

    return None


def build_command(action, params):
    """Build command dynamically based on action and parameters"""
    base_cmd = find_tool_script(action)
    if not base_cmd:
        return None

    cmd = base_cmd[:]

    # Handle tm.py specific commands
    if base_cmd[1] == "tm.py":
        if action == "filter" and "input" in params and "output" in params:
            cmd.extend([params["input"], params["output"]])

        # Add all other parameters as flags
        for key, value in params.items():
            if key not in ["input", "output"]:
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif not isinstance(value, bool):
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])
    else:
        # For external scripts, add input file first if present
        if "input" in params:
            cmd.append(params["input"])

        # For analyze_domains, add compare_pattern as positional arg
        if action == "analyze_domains" and "compare_pattern" in params:
            cmd.append(params["compare_pattern"])

        # Add all other parameters as flags
        for key, value in params.items():
            if key not in ["input", "compare_pattern"]:
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif not isinstance(value, bool):
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    return cmd


def execute_step(step, config):
    """Execute a single workflow step"""
    action = step.get("action")
    name = step.get("name", "unnamed")
    params = step.get("params", {})

    print(f"\n--- Step: {name} ({action}) ---")

    cmd = build_command(action, params)
    if not cmd:
        print(f"Unknown action or tool not found: {action}")
        return False

    description = f"Running {action}"
    if "output" in params:
        description += f" -> {params['output']}"

    return run_command(cmd, description)


def run_workflow(workflow_file):
    """Execute a complete workflow from YAML file"""
    config = load_config()

    with open(workflow_file, "r") as f:
        workflow = yaml.safe_load(f)

    print(f"Starting workflow: {workflow.get('name', 'Unnamed')}")
    if "description" in workflow:
        print(f"Description: {workflow['description']}")

    steps = workflow.get("steps", [])
    success_count = 0

    for i, step in enumerate(steps, 1):
        print(f"\n{'='*50}")
        print(f"Step {i}/{len(steps)}")

        if execute_step(step, config):
            success_count += 1
        else:
            print(f"Step {i} failed. Stopping workflow.")
            break

    print(f"\n{'='*50}")
    print(f"Workflow completed: {success_count}/{len(steps)} steps successful")

    return success_count == len(steps)


def main():
    parser = argparse.ArgumentParser(description="Run YAML-defined analysis workflows")
    parser.add_argument("workflow_file", help="Path to workflow YAML file")

    args = parser.parse_args()

    if not Path(args.workflow_file).exists():
        print(f"Error: Workflow file '{args.workflow_file}' not found")
        sys.exit(1)

    success = run_workflow(args.workflow_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
