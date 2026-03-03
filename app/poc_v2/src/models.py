"""v2 POC: パズルエンジン - データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Descriptor:
    id: str
    label: str
    formation_conditions: list[list[str]] | None = None  # None = 基礎記述素


@dataclass
class Piece:
    """逆算連鎖から抽出されたパズルのピース"""

    id: str
    label: str
    members: list[str]  # 構成記述素の ID 群
    depends_on: list[str]  # 依存ピースの ID 群（空なら独立ピース）


@dataclass
class Question:
    """質問。想起条件は記述素の族（OR of AND）"""

    id: str
    text: str
    answer: str
    recall_conditions: list[list[str]]  # OR of AND: 想起条件
    reveals: list[str]  # 回答で明らかになる記述素 ID 群
    mechanism: str  # ラベル: "observation" | "link" | "anomaly"


@dataclass
class GameState:
    confirmed: set[str] = field(default_factory=set)
    discovered_pieces: set[str] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)
    history: list[str] = field(default_factory=list)
