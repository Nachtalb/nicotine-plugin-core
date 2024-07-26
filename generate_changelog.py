#!/usr/bin/env python
import ast
import os
import sys
from typing import Any, List, Literal, NamedTuple, Optional, Set

Entry = NamedTuple(
    "Entry",
    [
        ("version", str),
        ("change_type", str),
        ("description", str),
        ("item_name", str),
        ("fully_qualified_name", str),
        ("type", Literal["func", "class", "variable", "method"]),
    ],
)


def get_init_exports(directory: str) -> Set[str]:
    init_path = os.path.join(directory, "__init__.py")
    if not os.path.exists(init_path):
        return set()

    with open(init_path, "r") as f:
        tree = ast.parse(f.read())

    exports = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                exports.add(alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)

    return exports


def get_fully_qualified_name(
    node: ast.AST, module_name: str, class_name: Optional[str] = None, init_exports: Set[str] = set()
) -> str:
    if isinstance(node, ast.FunctionDef):
        name = f"{class_name}.{node.name}" if class_name else node.name
        return f"npc.{name}" if name in init_exports or class_name in init_exports else f"{module_name}.{name}"
    elif isinstance(node, ast.ClassDef):
        return "npc." + node.name if node.name in init_exports else f"{module_name}.{node.name}"
    elif isinstance(node, ast.Assign) and len(node.targets) == 1:
        if isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            return "npc." + name if name in init_exports else f"{module_name}.{name}"
    return module_name


def get_item_type(node: ast.AST, in_class: bool) -> Literal["func", "class", "variable", "method"]:
    if isinstance(node, ast.FunctionDef):
        return "method" if in_class else "func"
    elif isinstance(node, ast.ClassDef):
        return "class"
    elif isinstance(node, ast.Assign):
        return "variable"
    return "func"  # Default to function if unknown


def parse_version_info(node: ast.AST, module_name: str, init_exports: Set[str]) -> List[Entry]:
    version_info = []

    def process_docstring(node: Any, item_name: str, in_class: bool, class_name: Optional[str] = None) -> None:
        docstring = ast.get_docstring(node)
        if docstring:
            fully_qualified_name = get_fully_qualified_name(node, module_name, class_name, init_exports)
            item_type = get_item_type(node, in_class)
            version_info.extend(parse_docstring(docstring, item_name, fully_qualified_name, item_type))

    def visit_node(node: ast.AST, in_class: bool = False, class_name: Optional[str] = None) -> None:
        if isinstance(node, ast.ClassDef):
            process_docstring(node, node.name, in_class)
            for child in ast.iter_child_nodes(node):
                visit_node(child, True, node.name)
        elif isinstance(node, ast.FunctionDef):
            process_docstring(node, node.name, in_class, class_name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper():
                if isinstance(node.value, ast.Str):
                    docstring = node.value.s
                elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    docstring = node.value.value
                else:
                    return
                fully_qualified_name = get_fully_qualified_name(node, module_name, class_name, init_exports)
                item_type = get_item_type(node, in_class)
                version_info.extend(parse_docstring(docstring, node.targets[0].id, fully_qualified_name, item_type))
        else:
            for child in ast.iter_child_nodes(node):
                visit_node(child, in_class, class_name)

    visit_node(node)
    return version_info


def parse_docstring(
    docstring: str,
    item_name: str,
    fully_qualified_name: str,
    item_type: Literal["func", "class", "variable", "method"],
) -> List[Entry]:
    version_info = []
    lines = docstring.split("\n")
    current_version: Optional[str] = None
    current_type: Optional[str] = None
    current_description: List[str] = []
    in_version_block = False

    for line in lines:
        line = line.strip()
        if line.startswith(".. version"):
            if current_version:
                description = (
                    " ".join(current_description).strip() if current_description else "(no description provided)"
                )
                version_info.append(
                    Entry(current_version, current_type or "", description, item_name, fully_qualified_name, item_type)
                )
                current_description = []

            parts = line.split("::")
            if len(parts) == 2:
                current_type = parts[0].split()[-1].lower()
                version_parts = parts[1].strip().split(None, 1)
                current_version = version_parts[0]
                if len(version_parts) > 1:
                    current_description = [version_parts[1]]
                else:
                    current_description = []
            in_version_block = True
        elif in_version_block and line and not line.startswith(".."):
            current_description.append(line)
        elif in_version_block and not line:
            in_version_block = False
        elif not in_version_block:
            continue

    if current_version:
        description = " ".join(current_description).strip() if current_description else "(no description provided)"
        version_info.append(
            Entry(current_version, current_type or "", description, item_name, fully_qualified_name, item_type)
        )

    return version_info


def generate_changelog(directory: str) -> List[Entry]:
    changelog = []
    init_exports = get_init_exports(directory)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                module_name = os.path.splitext(relative_path)[0].replace(os.path.sep, ".")
                print(f"{file_path} Processing file", file=sys.stderr)
                with open(file_path, "r") as f:
                    try:
                        tree = ast.parse(f.read())
                        file_changelog = parse_version_info(tree, module_name, init_exports)
                        changelog.extend(file_changelog)
                        print(f"{file_path} Found {len(file_changelog)} entries", file=sys.stderr)
                    except SyntaxError as e:
                        print(f"{file_path} Error parsing: {e}", file=sys.stderr)
    return changelog


def write_changelog(changelog: List[Entry], output_file: str) -> None:
    sorted_changelog = sorted(changelog, key=lambda x: x.version, reverse=True)

    with open(output_file, "w") as f:
        f.write("Changelog\n=========\n\n")
        current_version = None
        for entry in sorted_changelog:
            if entry.version != current_version:
                if current_version is not None:
                    f.write("\n")  # Add extra newline between versions
                f.write(f"{entry.version}\n{'-' * len(entry.version)}\n\n")
                current_version = entry.version

            fully_qualified_name = entry.fully_qualified_name
            if "npc." not in entry.fully_qualified_name:
                fully_qualified_name = f"npc.{entry.fully_qualified_name}"

            rst_reference = f":{entry.type}:`{fully_qualified_name}`"
            if entry.type == "method":
                class_name, method_name = fully_qualified_name.rsplit(".", 1)
                rst_reference = f":meth:`{class_name}.{method_name}`"

            f.write(f"* {entry.change_type.capitalize()}: [{rst_reference}] {entry.description}\n")


def main(output_file: str) -> None:
    directory = "./npc"

    print(f"Generating changelog for {directory}")
    changelog = generate_changelog(directory)

    if not changelog:
        print("No changelog entries found.")
        sys.exit(1)

    write_changelog(changelog, output_file)
    print(f"Changelog generated successfully. {len(changelog)} entries written to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python generate_changelog.py <output_file>")
    elif len(sys.argv) == 1:
        output_file = "CHANGELOG.rst"
    else:
        output_file = sys.argv[1]

    main(output_file)
