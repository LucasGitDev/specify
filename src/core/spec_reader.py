from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_CRITERIA_HEADINGS = re.compile(
    r"^#{1,3}\s+.*(critério|aceite|success|sucesso|acceptance).*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class SpecValidation:
    valid: bool
    title: str | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def read(spec_path: Path) -> str:
    return spec_path.read_text()


def validate(content: str) -> SpecValidation:
    errors: list[str] = []
    warnings: list[str] = []
    title: str | None = None

    if not content.strip():
        return SpecValidation(valid=False, title=None, errors=["spec está vazia"])

    # título obrigatório
    for line in content.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if title is None:
        errors.append("spec não tem título (linha começando com '# ')")

    # seção de critérios obrigatória
    if not _CRITERIA_HEADINGS.search(content):
        errors.append(
            "spec não tem seção de critérios "
            "(heading com 'critério', 'aceite', 'success' ou 'sucesso')"
        )

    # stack recomendada (aviso)
    if not re.search(
        r"(stack|linguagem|language|go|python|typescript)", content, re.IGNORECASE
    ):
        warnings.append("spec não menciona linguagem ou stack")

    return SpecValidation(
        valid=len(errors) == 0,
        title=title,
        errors=errors,
        warnings=warnings,
    )


def extract_criteria(content: str) -> list[str]:
    """Extrai itens de lista sob a primeira seção de critérios encontrada."""
    lines = content.splitlines()
    in_section = False
    criteria: list[str] = []

    for line in lines:
        if re.match(r"^#{1,3}\s+", line):
            if _CRITERIA_HEADINGS.match(line):
                in_section = True
                continue
            elif in_section:
                break  # nova seção — parar
        if in_section and line.strip().startswith("- "):
            criteria.append(line.strip()[2:].strip())

    return criteria
