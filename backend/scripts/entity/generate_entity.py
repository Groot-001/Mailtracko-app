import re
from pathlib import Path

from jinja2 import Template

TYPE_MAP = {
    "str": "str",
    "string": "str",
    "int": "int",
    "bool": "bool",
    "float": "float",
    "datetime": "datetime",
    "dict": "dict",
    "list": "list",
}

DEFAULT_BY_TYPE = {
    "str": '""',
    "int": "0",
    "bool": "False",
    "float": "0.0",
}


def to_snake_case(text: str) -> str:
    normalized = re.sub(r"(?<!^)(?=[A-Z])", "_", text).replace("-", "_")
    return re.sub(r"_+", "_", normalized).strip("_").lower()


def build_assignment(
    default_value: str | None, metadata_expr: str | None
) -> str | None:
    if default_value is None and metadata_expr is None:
        return None
    if default_value is None and metadata_expr is not None:
        return f"field(metadata={metadata_expr})"
    if default_value is not None and metadata_expr is not None:
        return f"field(default={default_value}, metadata={metadata_expr})"
    return default_value


def prompt_fields() -> list[dict]:
    fields = []

    print("\nEnter fields (empty name to finish)\n")

    while True:
        name = input("\nField name: ").strip()
        if not name:
            break

        raw_type = (
            input("Type (str/int/bool/float/datetime/dict/list): ").strip().lower()
        )
        field_type = TYPE_MAP.get(raw_type, raw_type or "str")

        unique = input("Unique? (y/n): ").strip().lower() == "y"
        index = input("Index? (y/n): ").strip().lower() == "y"
        required = input("Required? (y/n): ").strip().lower() == "y"

        default_value: str | None = None
        if not required:
            suggested_default = DEFAULT_BY_TYPE.get(field_type, "None")
            default_input = input(
                f"Default value (press enter for {suggested_default}): "
            ).strip()
            default_value = default_input or suggested_default

            if default_value == "None" and "| None" not in field_type:
                field_type = f"{field_type} | None"

        metadata_parts: list[str] = []
        if unique:
            metadata_parts.append('"unique": True')
        if index:
            metadata_parts.append('"index": True')
        metadata_expr = (
            "{" + ", ".join(metadata_parts) + "}" if metadata_parts else None
        )

        assignment = build_assignment(
            default_value=default_value,
            metadata_expr=metadata_expr,
        )

        fields.append(
            {
                "name": name,
                "type": field_type,
                "unique": unique,
                "index": index,
                "required": required,
                "assignment": assignment,
            }
        )

    return fields


def generate(class_name: str, fields: list[dict]) -> str:
    template_path = Path(__file__).parent / "templates" / "entity.py.jinja"
    template = Template(template_path.read_text())
    needs_field_import = any(
        isinstance(field.get("assignment"), str)
        and field["assignment"].startswith("field(")
        for field in fields
    )
    entity_label = class_name.removesuffix("Entity") or class_name

    return template.render(
        class_name=class_name,
        fields=fields,
        needs_field_import=needs_field_import,
        entity_label=entity_label.lower(),
    )


def write_file(output_dir: str, file_name: str, content: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    normalized_file_name = file_name if file_name.endswith(".py") else f"{file_name}.py"
    file_path = output_path / normalized_file_name
    file_path.write_text(content)

    print(f"\nGenerated: {file_path}")


def main():
    class_name = input("Entity class name (e.g. UserEntity): ").strip()
    if not class_name:
        print("No entity class name provided. Exiting.")
        return

    fields = prompt_fields()
    if not fields:
        print("No fields provided. Exiting.")
        return

    default_output_dir = "src/modules/auth/domain"
    output_dir = (
        input(
            f"Directory path to create file (default: {default_output_dir}): "
        ).strip()
        or default_output_dir
    )

    default_file_name = f"{to_snake_case(class_name)}.py"
    file_name = (
        input(f"File name (default: {default_file_name}): ").strip()
        or default_file_name
    )

    output = generate(class_name, fields)
    write_file(output_dir=output_dir, file_name=file_name, content=output)


if __name__ == "__main__":
    main()
