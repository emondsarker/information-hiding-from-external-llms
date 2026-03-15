"""Bidirectional mapping store for original ↔ pseudonym pairs (JSON-backed)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class MappingEntry:
    original: str
    pseudonym: str
    label: str
    scale_factor: float | None = None


@dataclass
class MappingStore:
    run_id: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    mappings: list[MappingEntry] = field(default_factory=list)
    _forward: dict[str, str] = field(default_factory=dict, repr=False)
    _reverse: dict[str, str] = field(default_factory=dict, repr=False)
    _scale_factors: dict[str, float] = field(default_factory=dict, repr=False)

    def add(self, original: str, pseudonym: str, label: str, scale_factor: float | None = None) -> None:
        if original in self._forward:
            return
        entry = MappingEntry(original=original, pseudonym=pseudonym, label=label, scale_factor=scale_factor)
        self.mappings.append(entry)
        self._forward[original] = pseudonym
        self._reverse[pseudonym] = original
        if scale_factor is not None:
            self._scale_factors[pseudonym] = scale_factor

    def get_pseudonym(self, original: str) -> str | None:
        return self._forward.get(original)

    def get_original(self, pseudonym: str) -> str | None:
        return self._reverse.get(pseudonym)

    def get_scale_factor(self, pseudonym: str) -> float | None:
        return self._scale_factors.get(pseudonym)

    def save(self, path: Path) -> None:
        data = {
            "run_id": self.run_id,
            "mappings": [asdict(m) for m in self.mappings],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> MappingStore:
        data = json.loads(path.read_text())
        store = cls(run_id=data["run_id"])
        for m in data["mappings"]:
            store.add(
                original=m["original"],
                pseudonym=m["pseudonym"],
                label=m["label"],
                scale_factor=m.get("scale_factor"),
            )
        return store

    @property
    def forward_map(self) -> dict[str, str]:
        return dict(self._forward)

    @property
    def reverse_map(self) -> dict[str, str]:
        return dict(self._reverse)
