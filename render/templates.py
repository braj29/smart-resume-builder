from __future__ import annotations

import pathlib
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"


def list_templates() -> Dict[str, pathlib.Path]:
    return {p.stem: p for p in TEMPLATE_DIR.glob("*.tex")}


def render_template(template_name: str, context: dict) -> str:
    templates = list_templates()
    if template_name not in templates:
        raise ValueError(f"Template {template_name} not found. Available: {list(templates)}")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=("tex",)),
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="{{",
        variable_end_string="}}",
        comment_start_string="\\#",
        comment_end_string="}",
    )
    template = env.get_template(f"{template_name}.tex")
    return template.render(**context)
