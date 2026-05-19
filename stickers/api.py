from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator

from inventory import (
    BASE_DIR,
    COUNTRY_INVENTORY_DIR,
    GLOBAL_INVENTORY_FILE,
    apply_stickers,
    get_types_by_scope,
    load_country_inventory_by_code,
    load_countries,
    load_groups,
    load_types,
    load_global_inventory,
    save_country_inventory,
    save_global_inventory,
    summarize_duplicates,
    summarize_missing,
)

app = FastAPI(
    title="Panini World Cup Sticker Tracker",
    description="API for updating country sticker inventory and reporting missing stickers.",
)

STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class StickerUpdate(BaseModel):
    stickers: list[str] | str

    @validator("stickers", pre=True)
    def parse_stickers(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @validator("stickers")
    def validate_stickers(cls, stickers: list[str]) -> list[str]:
        if not stickers:
            raise ValueError("stickers list must not be empty")
        return sorted(stickers)


def normalize_country_code(country_code: str) -> str:
    return country_code.strip().upper()


def get_inventory_path_for_country(country_code: str) -> Path:
    return COUNTRY_INVENTORY_DIR / f"{country_code}.json"


def get_global_types() -> list[str]:
    types = load_types()
    global_types_config = get_types_by_scope(types, "global")
    # Explicitly define the order for FWC and CC
    ordered_global_types = []
    if "FWC" in global_types_config:
        ordered_global_types.append("FWC")
    if "CC" in global_types_config:
        ordered_global_types.append("CC")
    return ordered_global_types


def ensure_country_exists(country_code: str) -> None:
    country_code = normalize_country_code(country_code)
    if country_code in [t.upper() for t in get_global_types()]:
        return
    if country_code not in load_countries():
        raise HTTPException(status_code=404, detail=f"Country {country_code} not found")


def build_inventory_report(name: str, inventory: dict[str, Any], target_section: str | None = None) -> dict[str, Any]:
    found = []
    missing = []
    duplicates = {}
    total_count = 0
    found_count = 0

    for type_name, stickers in inventory.items():
        if not isinstance(stickers, dict) or type_name in ("country", "inventory"):
            continue
        
        if target_section and type_name != target_section:
            continue

        for key, value in stickers.items():
            count = int(value)
            total_count += 1
            if count > 0:
                found.append(key)
                found_count += 1
                if count > 1:
                    duplicates[key] = count
            else:
                missing.append(key)

    percentage = (found_count / total_count * 100) if total_count > 0 else 0

    return {
        "country": name,
        "found": found,
        "missing": missing,
        "duplicates": duplicates,
        "completion_percentage": round(percentage, 2),
        "counts": {
            "found": found_count,
            "missing": len(missing),
            "total": total_count,
        },
    }


@app.get("/countries")
def list_countries() -> dict[str, Any]:
    ordered_list = []
    
    global_types = get_global_types() # Returns ['FWC', 'CC']
    all_country_codes = load_countries() # All 48 country codes
    wc_groups = load_groups() # Group A, B, C... with their countries

    # 1. Add FWC
    if "FWC" in global_types:
        ordered_list.append("FWC")

    # 2. Add countries by World Cup group order (A, B, C...)
    for group_letter in sorted(wc_groups.keys()): # Ensures A, B, C order
        for country_code_in_group in wc_groups[group_letter]:
            if country_code_in_group in all_country_codes: # Only add if it's a valid country code we track
                ordered_list.append(country_code_in_group)
    
    # 3. Add CC
    if "CC" in global_types:
        ordered_list.append("CC")

    return {"countries": ordered_list}


@app.get("/inventory/{country_code}")
def read_country_inventory(country_code: str) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    
    global_map = {t.upper(): t for t in get_global_types()}
    if normalized_code in global_map:
        try:
            inventory = load_global_inventory(GLOBAL_INVENTORY_FILE)
            section_name = global_map[normalized_code]
            return build_inventory_report(section_name, inventory, target_section=section_name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Global inventory file not found")

    ensure_country_exists(normalized_code)
    try:
        inventory = load_country_inventory_by_code(normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    return build_inventory_report(normalized_code, inventory)


@app.post("/inventory/{country_code}")
def add_country_stickers(country_code: str, payload: StickerUpdate) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    
    global_map = {t.upper(): t for t in get_global_types()}
    if normalized_code in global_map:
        try:
            inventory = load_global_inventory(GLOBAL_INVENTORY_FILE)
            section_name = global_map[normalized_code]
            apply_stickers(inventory, payload.stickers)
            save_global_inventory(inventory)
            return build_inventory_report(section_name, inventory, target_section=section_name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Global inventory file not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    ensure_country_exists(normalized_code)
    try:
        inventory = load_country_inventory_by_code(normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    try:
        apply_stickers(inventory, payload.stickers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    save_country_inventory(normalized_code, inventory)
    return build_inventory_report(normalized_code, inventory)


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Static UI not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
