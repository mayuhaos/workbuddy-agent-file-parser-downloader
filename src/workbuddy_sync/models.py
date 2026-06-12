from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


EXPERT_TYPE_LABELS = {
    "agent": "专家",
    "team": "专家团",
}


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")


def safe_filename_part(value: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("-", value.strip())
    cleaned = WHITESPACE.sub(" ", cleaned)
    cleaned = cleaned.strip(" .")
    return cleaned or "未分类"


@dataclass(frozen=True)
class Category:
    id: str
    name_zh: str
    name_en: str


@dataclass(frozen=True)
class ExpertEntry:
    id: str
    plugin: str
    agent_name: str
    expert_type: str
    category_id: str
    category_name: str
    display_name_zh: str
    display_name_en: str
    profession_zh: str
    profession_en: str

    @property
    def type_label(self) -> str:
        return EXPERT_TYPE_LABELS.get(self.expert_type, self.expert_type or "未知")

    @property
    def output_filename(self) -> str:
        category = safe_filename_part(self.category_name)
        plugin = safe_filename_part(self.plugin)
        return f"{self.type_label}-{category}-{plugin}.tar.gz"

    def output_path(self, out_dir: Path) -> Path:
        return out_dir / self.type_label / self.output_filename


@dataclass
class DownloadResult:
    entry: ExpertEntry
    url: str
    path: Path
    status: str
    file_size: int = 0
    error: str = ""
    retries: int = 0

    @property
    def success(self) -> bool:
        return self.status in {"success", "skipped"}
