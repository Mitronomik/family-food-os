"""Hash-pinned Step 5 Russian adult micronutrient reference table."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.db.config import REPOSITORY_ROOT
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.domain.russian_reference_targets import (
    ReviewedRussianReferenceTable,
    RussianReferenceRow,
)


PACKAGE = REPOSITORY_ROOT / "data/curation/ru-reference-step5-runtime"
PUBLICATION_PATH = PACKAGE / "publication.json"
REGISTRY_PATH = REPOSITORY_ROOT / "data/curation/nutrient-registry-v2/registry.json"

PUBLICATION_GIT_BLOB_SHA1 = "1f55158725c338f16715f2c2e2f285d183caf779"
REGISTRY_GIT_BLOB_SHA1 = "db9d4d3b7e913447ff0c0a87b0e28f3085094409"

METHODOLOGY_VERSION = "RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1"
REVIEW_REFERENCE = "STEP5_RU_REFERENCE_TABLE_V1"
SOURCE_ID = "RU-NEEDS-MR-2.3.1.0253-21"
SOURCE_VERSION = "2021-07-22"

EXPECTED_SOURCE = {
    "source_id": SOURCE_ID,
    "document_number": "МР 2.3.1.0253-21",
    "edition_date": SOURCE_VERSION,
    "archive_file": "FamilyFoodOS-corpus-0.3.0-2026-09-20.zip",
    "archive_sha256": "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea",
    "source_pdf_sha256": "cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79",
    "transport": {
        "package_version": "0.3.0",
        "input_sha256": "8e68a6f3450f40c52c44bc422c6ecfad9e8bfa6561041948529c391211df7bdf",
        "qa_sha256": "2404b044cc48ef56abc03653c10d3fc192cb9e6a6ae76a7f869c6c5c51a42445",
        "groups_sha256": "8101fabce928d2033cc831ff4984502b6068b305e0c330b8ff53b3d5d146341e",
        "nutrients_sha256": "bf29e392b548600499de90effa9a46660fa928c6eb867bc8a7bfe35c9f61d031",
        "values_sha256": "ff9b21599797355ca47af6af5db9e920705cfa233cdaecd173d0c0a07cbf4b3f",
        "quality_sha256": "51736ca640e3295fca00fc4011f1cb70fe1c4ef768b320e9c050bf484108d566",
        "validation_sha256": "931e1e4a2e92190b1d4c651d65eaf93dd9b7274fe66ed84658b0bcdbd2677894",
        "manifest_sha256": "cff02f7e5b17ff00bed32ae79d6bc033f9ba83a10cf33170a761a0b623ae4154",
        "source_groups": 147,
        "source_nutrient_definitions": 218,
        "source_claims": 872,
        "scalar_source_group_lookup_ready": 735,
        "withheld": 137,
    },
}
EXPECTED_REGISTRY = {
    "version": REGISTRY_V2,
    "path": "data/curation/nutrient-registry-v2/registry.json",
    "git_blob_sha1": REGISTRY_GIT_BLOB_SHA1,
}
EXPECTED_SELECTION = {
    "source_population_header": "Старше 18 лет",
    "table_numbers": ["11", "12", "16", "17"],
    "age_min_years": 19,
    "age_max_years_exclusive": None,
    "sexes": ["male", "female"],
    "physical_activity_coefficient": None,
    "life_stage": "adult",
    "basis": "group_reference_daily",
    "applicability": "wellness",
    "definition_count": 24,
    "row_count": 48,
}
DEFERRED_CODES = {
    "CALCIUM",
    "FLUORIDE",
    "FOLATE_DFE",
    "FOLATE_TOTAL",
    "VITAMIN_D_D2_D3",
    "VITAMIN_K_PHYLLOQUINONE",
}
CLAIM_ID_RE = re.compile(
    r"^RU-NEEDS-MR-2\.3\.1\.0253-21:"
    r"p(?P<pdf_page>\d+):t(?P<page_table_index>\d+):"
    r"r(?P<row>\d+):c(?P<column>\d+):population$"
)
REFERENCE_MASS_UNITS = {"g/day", "mg/day", "µg/day"}
REGISTRY_MASS_UNITS = {"g", "mg", "µg"}


def _git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_blob_sha1: str) -> Any:
    raw = path.read_bytes()
    if _git_blob_sha1(raw) != expected_blob_sha1:
        raise ValueError(f"Изменён проверенный файл данных: {path.name}.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON в {path.name}.") from exc


def _decimal_source_literal(value: object) -> Decimal:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Source reference value должен быть Decimal-строкой.")
    if "e" in value.lower() or value.startswith(("+", "-")):
        raise ValueError("Source reference value должен быть обычной Decimal-строкой.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Source reference value не является Decimal.") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("Source reference value должен быть конечным и неотрицательным.")
    return result


def _registry_units(registry_path: Path) -> dict[str, str]:
    registry = _checked_json(registry_path, REGISTRY_GIT_BLOB_SHA1)
    if (
        not isinstance(registry, dict)
        or registry.get("registry_version") != REGISTRY_V2
        or not isinstance(registry.get("entries"), list)
    ):
        raise ValueError("Проверенный V2 nutrient registry имеет неверный контракт.")
    result: dict[str, str] = {}
    for entry in registry["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("V2 nutrient registry содержит некорректную definition.")
        code = entry.get("canonical_code")
        unit = entry.get("canonical_unit")
        if not isinstance(code, str) or not isinstance(unit, str) or code in result:
            raise ValueError("V2 nutrient registry содержит неоднозначную definition.")
        result[code] = unit
    return result


def _definition_map(
    publication: dict[str, Any], registry_units: dict[str, str]
) -> dict[str, dict[str, str]]:
    definitions = publication.get("definitions")
    if not isinstance(definitions, list) or len(definitions) != 24:
        raise ValueError("Step 5 должен содержать ровно 24 definition mappings.")
    by_source: dict[str, dict[str, str]] = {}
    codes: set[str] = set()
    for item in definitions:
        if not isinstance(item, dict) or set(item) != {
            "source_definition",
            "canonical_code",
            "source_unit",
            "reference_unit",
            "registry_unit",
            "kind",
        }:
            raise ValueError("Step 5 definition mapping имеет неверную форму.")
        source_definition = item["source_definition"]
        code = item["canonical_code"]
        if (
            not isinstance(source_definition, str)
            or not source_definition
            or not isinstance(code, str)
            or not code
            or source_definition in by_source
            or code in codes
        ):
            raise ValueError("Step 5 definition mapping повторяется.")
        if item["kind"] not in {"vitamin", "mineral"}:
            raise ValueError("Step 5 definition kind не поддерживается.")
        if item["reference_unit"] not in REFERENCE_MASS_UNITS:
            raise ValueError("Step 5 reference unit не является mass/day.")
        if item["registry_unit"] not in REGISTRY_MASS_UNITS:
            raise ValueError("Step 5 registry unit не является mass unit.")
        if registry_units.get(code) != item["registry_unit"]:
            raise ValueError(f"V2 registry definition/unit drift для {code}.")
        if code in DEFERRED_CODES:
            raise ValueError(f"Deferred nutrient попал в Step 5: {code}.")
        by_source[source_definition] = item
        codes.add(code)
    return by_source


def _locator(row: dict[str, Any]) -> str:
    return json.dumps(
        {
            "source_claim_id": row["source_claim_id"],
            **row["locator"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _validate_row(
    row: object,
    definitions: dict[str, dict[str, str]],
) -> RussianReferenceRow:
    if not isinstance(row, dict) or set(row) != {
        "row_id",
        "source_claim_id",
        "source_definition",
        "source_unit",
        "source_value",
        "source_status",
        "locator",
        "sex",
        "canonical_code",
        "reference_unit",
        "registry_unit",
    }:
        raise ValueError("Step 5 row имеет неверную форму.")
    source_definition = row["source_definition"]
    definition = definitions.get(source_definition)
    if definition is None:
        raise ValueError("Step 5 row использует неутверждённую source definition.")
    for key in ("canonical_code", "source_unit", "reference_unit", "registry_unit"):
        if row[key] != definition[key]:
            raise ValueError("Step 5 row расходится с frozen definition mapping.")
    if row["source_status"] != "ready_source_group_lookup":
        raise ValueError("Step 5 row не является ready_source_group_lookup.")
    sex = row["sex"]
    if sex not in {"male", "female"}:
        raise ValueError("Step 5 row имеет неподдерживаемый sex.")
    expected_id = f"{REVIEW_REFERENCE}:{sex}:{row['canonical_code']}"
    if row["row_id"] != expected_id:
        raise ValueError("Step 5 row id расходится с frozen identity.")

    locator = row["locator"]
    if not isinstance(locator, dict) or set(locator) != {
        "pdf_page",
        "page_table_index",
        "table_number",
        "row",
        "column",
    }:
        raise ValueError("Step 5 source locator имеет неверную форму.")
    expected_table = (
        "11"
        if definition["kind"] == "vitamin" and sex == "male"
        else "16"
        if definition["kind"] == "vitamin"
        else "12"
        if sex == "male"
        else "17"
    )
    if locator["table_number"] != expected_table or locator["column"] != 2:
        raise ValueError("Step 5 source table/column расходится с contract.")

    claim_id = row["source_claim_id"]
    match = CLAIM_ID_RE.fullmatch(claim_id) if isinstance(claim_id, str) else None
    if match is None:
        raise ValueError("Step 5 source claim id имеет неверный формат.")
    for field in ("pdf_page", "page_table_index", "row", "column"):
        if int(match.group(field)) != locator[field]:
            raise ValueError("Step 5 source claim id расходится с locator.")

    return RussianReferenceRow(
        id=row["row_id"],
        source_id=SOURCE_ID,
        source_version=SOURCE_VERSION,
        locator=_locator(row),
        review_reference=REVIEW_REFERENCE,
        definition_code=row["canonical_code"],
        unit=row["reference_unit"],
        value=_decimal_source_literal(row["source_value"]),
        sex=sex,
        age_min_years=19,
        age_max_years_exclusive=None,
        physical_activity_coefficient=None,
        life_stage="adult",
    )


def load_reviewed_russian_reference_table(
    package: Path = PACKAGE,
    *,
    registry_path: Path = REGISTRY_PATH,
) -> ReviewedRussianReferenceTable:
    publication = _checked_json(
        package / "publication.json", PUBLICATION_GIT_BLOB_SHA1
    )
    if not isinstance(publication, dict) or publication.get("schema_version") != 1:
        raise ValueError("Неизвестный Step 5 publication payload.")
    if publication.get("methodology_version") != METHODOLOGY_VERSION:
        raise ValueError("Step 5 methodology version изменена.")
    if publication.get("review_reference") != REVIEW_REFERENCE:
        raise ValueError("Step 5 review reference изменён.")
    if publication.get("source") != EXPECTED_SOURCE:
        raise ValueError("Step 5 source transport identity изменена.")
    if publication.get("registry") != EXPECTED_REGISTRY:
        raise ValueError("Step 5 registry pin изменён.")
    if publication.get("selection") != EXPECTED_SELECTION:
        raise ValueError("Step 5 applicability/selection contract изменён.")

    registry_units = _registry_units(registry_path)
    definitions = _definition_map(publication, registry_units)
    rows_raw = publication.get("rows")
    if not isinstance(rows_raw, list) or len(rows_raw) != 48:
        raise ValueError("Step 5 должен содержать ровно 48 rows.")
    rows = tuple(_validate_row(row, definitions) for row in rows_raw)
    if len({row.id for row in rows}) != 48:
        raise ValueError("Step 5 row ids должны быть уникальны.")

    locator_claims = {
        json.loads(row.locator)["source_claim_id"]
        for row in rows
    }
    if len(locator_claims) != 48:
        raise ValueError("Step 5 source claim ids должны быть уникальны.")
    by_sex = {
        sex: tuple(row for row in rows if row.sex == sex)
        for sex in ("male", "female")
    }
    if any(len(values) != 24 for values in by_sex.values()):
        raise ValueError("Step 5 должен содержать 24 rows на каждый sex.")
    expected_codes = {item["canonical_code"] for item in definitions.values()}
    if any({row.definition_code for row in values} != expected_codes for values in by_sex.values()):
        raise ValueError("Step 5 definition coverage расходится между sexes.")

    return ReviewedRussianReferenceTable(
        methodology_version=METHODOLOGY_VERSION,
        review_reference=REVIEW_REFERENCE,
        rows=rows,
    )


def reviewed_russian_reference_table_digest(
    table: ReviewedRussianReferenceTable,
) -> str:
    if not isinstance(table, ReviewedRussianReferenceTable):
        raise TypeError("Требуется проверенная российская таблица норм.")
    payload = [
        {
            "id": row.id,
            "source_id": row.source_id,
            "source_version": row.source_version,
            "locator": row.locator,
            "review_reference": row.review_reference,
            "definition_code": row.definition_code,
            "unit": row.unit,
            "value": format(row.value, "f"),
            "sex": row.sex,
            "age_min_years": row.age_min_years,
            "age_max_years_exclusive": row.age_max_years_exclusive,
            "physical_activity_coefficient": (
                None
                if row.physical_activity_coefficient is None
                else format(row.physical_activity_coefficient, "f")
            ),
            "life_stage": row.life_stage,
            "basis": row.basis,
            "applicability": row.applicability,
        }
        for row in table.rows
    ]
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def _default_table() -> ReviewedRussianReferenceTable:
    return load_reviewed_russian_reference_table()


def russian_reference_table_provider(
    methodology_version: str,
) -> ReviewedRussianReferenceTable:
    if methodology_version != METHODOLOGY_VERSION:
        raise LookupError("Неизвестная версия проверенной российской таблицы норм.")
    return _default_table()
