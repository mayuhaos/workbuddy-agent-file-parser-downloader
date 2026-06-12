from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import httpx

from .models import Category, ExpertEntry


DEFAULT_MANIFEST_URL = (
    "https://acc-1258344699.cos.accelerate.myqcloud.com/"
    "workbuddy/expert-marketplace/expert_center.json"
)


def _localized(value: dict[str, Any] | None, key: str, fallback: str = "") -> str:
    if not isinstance(value, dict):
        return fallback
    item = value.get(key)
    if isinstance(item, str) and item.strip():
        return item.strip()
    return fallback


def fetch_manifest(manifest_url: str, output_path: Path, timeout: float = 60.0) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
        response = client.get(manifest_url)
        response.raise_for_status()
        output_path.write_bytes(response.content)
    return json.loads(output_path.read_text(encoding="utf-8"))


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_categories(manifest: dict[str, Any]) -> dict[str, Category]:
    categories: dict[str, Category] = {}
    for raw in manifest.get("categories", []):
        category_id = str(raw.get("id") or "").strip()
        if not category_id:
            continue
        name = raw.get("name") if isinstance(raw.get("name"), dict) else {}
        categories[category_id] = Category(
            id=category_id,
            name_zh=_localized(name, "zh", category_id),
            name_en=_localized(name, "en", category_id),
        )
    return categories


def parse_experts(manifest: dict[str, Any]) -> list[ExpertEntry]:
    categories = parse_categories(manifest)
    entries: list[ExpertEntry] = []
    for raw in manifest.get("experts", []):
        plugin = str(raw.get("plugin") or "").strip()
        if not plugin:
            continue
        category_id = str(raw.get("categoryId") or "").strip()
        category = categories.get(category_id)
        display_name = raw.get("displayName") if isinstance(raw.get("displayName"), dict) else {}
        profession = raw.get("profession") if isinstance(raw.get("profession"), dict) else {}
        entries.append(
            ExpertEntry(
                id=str(raw.get("id") or plugin).strip(),
                plugin=plugin,
                agent_name=str(raw.get("agentName") or "").strip(),
                expert_type=str(raw.get("expertType") or "").strip(),
                category_id=category_id,
                category_name=category.name_zh if category else category_id or "未分类",
                display_name_zh=_localized(display_name, "zh", plugin),
                display_name_en=_localized(display_name, "en", ""),
                profession_zh=_localized(profession, "zh", ""),
                profession_en=_localized(profession, "en", ""),
            )
        )
    return entries
