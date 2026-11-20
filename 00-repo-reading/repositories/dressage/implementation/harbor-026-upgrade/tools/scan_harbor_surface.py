"""Index Harbor contact sites in two pinned Git trees, independently of the installed packages."""

import argparse
import ast
import subprocess
from pathlib import Path

DRESSAGE = "3e3142fe8ea07e4504c3b20a936a4c201a3de44c"
HARBOR = "3cb627394b95d3ae605f31e0d694edf508cf4b7b"
BASE = "src/harbor/environments/base.py"
BACKEND = "dressage/integrations/harbor/environment.py"
URL = f"https://github.com/Accio-Lab/Dressage/blob/{DRESSAGE}/"
UPSTREAM = f"https://github.com/harbor-framework/harbor/blob/{HARBOR}/"

# Reviewed receivers at the integration boundary. These names locate candidate reads and
# writes, including getattr on Any. A hit still needs the surrounding function for meaning.
RECEIVERS = {
    "compat": set("job Job job_config config agent entry.config".split()),
    "data_source": set("self.job_config self.eval_job_config job_config job_config_type source".split()),
    "plugin": set(("job item trial_config original_agent candidate_agent agent task_reference "
                   "task_config environment phase step event job_result result config").split()),
    "rollout": set(("Job job job_config source_job_config source_environment result final_result "
                    "task package item.trial_name agent").split()),
    "artifacts": set("trial_result job_result result verifier_result step step_verifier info".split()),
    "environment": set("self.task_env_config self.network_policy policy self.environment_dir".split()),
}
ACCESSORS = {"getattr", "hasattr", "setattr", "_string_attr", "_nested_string_attr", "_datetime_attr"}
INDIRECT = {
    "compat": {"resolver"},
    "data_source": {"job_config_type.model_validate", "_deepcopy_model", "_dump_model"},
    "plugin": {"getter", "_stable_dump", "_deep_copy_model", "TaskConfig.model_validate_toml"},
    "rollout": {"_CREATE_JOB", "_copy_model", "_validated_model_update", "plugin.on_job_start",
                "plugin.on_job_end", "plugin.get_result", "_bundle_samples", "_eval_output",
                "RolloutFnTrainOutput", "RolloutFnEvalOutput"},
    "environment": {"super().__init__", "super().validate_network_policy_support", "self._resolve_user",
                    "self._merge_env", "self._output_callback", "ExecResult", "EnvironmentCapabilities"},
}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def method_lines(tree, class_name):
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name: node.lineno for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def file_role(path):
    if path.startswith("tests/"):
        return "测试或夹具"
    if path.endswith(".md"):
        return "文档"
    if path == "dressage/proxy/__init__.py":
        return "源码注释提及 Harbor"
    if path == "dressage/rollout/log_rollout.py":
        return "消费已转换 Sample 的奖励元数据"
    if path.startswith("examples/"):
        return "配置、启动脚本或任务生成工具"
    if path == "pyproject.toml":
        return "包依赖及插件登记"
    return "集成实现"


def render(dressage_repo, harbor_repo):
    files = []
    submodules = []
    for row in git(dressage_repo, "ls-tree", "-r", DRESSAGE).splitlines():
        meta, path = row.split("\t", 1)
        if meta.split()[1] == "blob":
            files.append(path)
        else:
            submodules.append(path)
    pyfiles = [path for path in files if path.endswith(".py")]
    hits = [line.split(":", 1)[1] for line in
            git(dressage_repo, "grep", "-Iil", "-e", "harbor", DRESSAGE, "--").splitlines()]
    imports, dynamic, versions, fields = [], [], [], {}
    string_entries = []
    entry_markers = ("[project.entry-points.", 'dressage = "dressage.integrations.harbor.plugin',
                     "harbor run", "--plugin dressage", "--data-source-path dressage.integrations.harbor",
                     "--rollout-function-path dressage.integrations.harbor",
                     '"dressage.integrations.harbor.environment:DressageEnvironment"')
    for path in hits:
        if path.startswith(("tests/", "docs/")) or path.endswith(".md"):
            continue
        original = git(dressage_repo, "show", f"{DRESSAGE}:{path}")
        for line, row in enumerate(original.splitlines(), start=1):
            if row.strip().startswith(entry_markers):
                string_entries.append((path, line, row.strip()))
    for path in pyfiles:
        content = git(dressage_repo, "show", f"{DRESSAGE}:{path}")
        tree = ast.parse(content, filename=path)
        lines = content.splitlines()
        module = Path(path).stem if path.startswith("dressage/integrations/harbor/") else ""
        if path == BACKEND:
            overrides = method_lines(tree, "DressageEnvironment")
        relevant = RECEIVERS.get(module, set())
        indirect = INDIRECT.get(module, set())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.level:
                    continue
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(name.split(".")[0] == "harbor" for name in names):
                    imports.append((path, node.lineno, lines[node.lineno - 1].strip()))
            if isinstance(node, ast.Call):
                func = ast.unparse(node.func)
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.split(".")[0] == "harbor":
                    if func.split(".")[-1] in {"import_module", "__import__"}:
                        dynamic.append((path, node.lineno, lines[node.lineno - 1].strip()))
                    if func.split(".")[-1] == "version":
                        versions.append((path, node.lineno, lines[node.lineno - 1].strip()))
                matches = func in indirect or (
                    func in ACCESSORS and arg is not None and ast.unparse(arg) in relevant
                )
            elif isinstance(node, ast.Attribute) and relevant:
                expression = ast.unparse(node)
                matches = ast.unparse(node.value) in relevant or expression in relevant or (
                    path == BACKEND and expression == "self._mounts"
                )
            else:
                matches = False
            if matches:
                fields.setdefault(path, {})[node.lineno] = lines[node.lineno - 1].strip()

    base = ast.parse(git(harbor_repo, "show", f"{HARBOR}:{BASE}"))
    base_methods = method_lines(base, "BaseEnvironment")
    common = [(n, i) for n, i in overrides.items() if n in base_methods]
    out = ["# Dressage 调用 Harbor 的逐处源码索引", "",
           f"固定 Dressage `{DRESSAGE[:7]}` 和 Harbor `{HARBOR[:7]}`。由 [扫描脚本](../tools/scan_harbor_surface.py) 从 Git 对象生成。接手审核时先看[交付物与验收表](../archive/integration-inventory.md#coverage)，在这里回查具体代码。", "",
           f"遍历 {len(files)} 个跟踪文件，其中 {len(pyfiles)} 个 Python 文件，生产包内 {sum(p.startswith('dressage/') for p in pyfiles)} 个。独立子模块 {', '.join(submodules)} 按 Git 引用记录。", "",
           '<a id="imports"></a>', "",
           "## 1. 直接导入、包版本及动态导入", "",
           f"直接导入 {len(imports)} 句，分布在 {len({p for p, _, _ in imports})} 个文件。另有 {len(versions)} 处读取 Harbor 发行包版本，找到 {len(dynamic)} 处以 Harbor 模块名字符串直接调用 import_module 或 __import__。", "",
           "| 文件与行 | 源码原行 |", "| --- | --- |"]
    for path, line, original in sorted(imports + versions + dynamic):
        out.append(f"| [{path}:{line}]({URL}{path}#L{line}) | `{original}` |")
    out.extend(["", "### 通过配置字符串和 CLI 进入的源码原行", "",
                "| 文件与行 | 源码原行 |", "| --- | --- |"])
    for path, line, original in sorted(string_entries):
        out.append(f"| [{path}:{line}]({URL}{path}#L{line}) | `{original}` |")
    out.extend(["", '<a id="overrides"></a>', "", "## 2. Harbor 可调用的后端实现", "",
                f"对两个固定版本的类定义按同名方法逐个比对，得到 {len(common)} 项。打开两边同行能查签名和返回值。", "",
                "| 实现 | Dressage | Harbor 基类 |", "| --- | --- | --- |"])
    for name, line in common:
        base_line = base_methods[name]
        out.append(f"| `{name}` | [实现 {line}]({URL}{BACKEND}#L{line}) | [基类 {base_line}]({UPSTREAM}{BASE}#L{base_line}) |")
    out.extend(["", '<a id="members"></a>', "", "## 3. 配置、回调、对象字段和间接调用的位置", "",
                "按已追踪的接收对象、getattr 等字段访问和已确认的间接入口找候选行。同一行只列一次，行号打开原文。通用变量名可能同时命中本仓库对象，变量别名和动态键还要结合交付物表里的完整函数判断。这部分适合查漏，行数不代表接口数量。", ""])
    for path, selected in sorted(fields.items()):
        out.extend([f"### `{path}`", "", "| 原行 | 位置 |", "| --- | --- |"])
        for line, original in sorted(selected.items()):
            cell = original.replace("|", r"\|")
            out.append(f"| `{cell}` | [第 {line} 行]({URL}{path}#L{line}) |")
        out.append("")
    out.extend(["", '<a id="files"></a>', "", "## 4. 全仓出现 Harbor 字样的文件", "",
                f"按正文大小写无关匹配，共 {len(hits)} 个文件。此处也保留文档、注释、随仓配置和集成测试目录以外的命中，便于复核统计边界。", "",
                "| 用途 | 文件 |", "| --- | --- |"])
    for path in hits:
        out.append(f"| {file_role(path)} | [{path}]({URL}{path}) |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dressage-repo", type=Path, required=True)
    parser.add_argument("--harbor-repo", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Compare output with the archived index")
    args = parser.parse_args()
    index = render(args.dressage_repo, args.harbor_repo)
    if args.check:
        if index != (Path(__file__).resolve().parents[1] / "usage" / "harbor-call-sites.md").read_text():
            raise SystemExit("The archived index differs from the pinned source scan")
        print("Static contact index matches both pinned Git trees")
    else:
        print(index, end="")
