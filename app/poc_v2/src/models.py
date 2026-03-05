"""v2 POC: パズルエンジン - データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Descriptor:
    id: str
    label: str
    formation_conditions: list[list[str]] | None = None  # None = 基礎記述素
    rejection_conditions: list[list[str]] | None = None  # confirmed により棄却される条件


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
    topic_category: str = ""  # トピックカテゴリ（UI 用分類）


@dataclass
class GameState:
    confirmed: set[str] = field(default_factory=set)  # 観測で確定した記述素
    derived: set[str] = field(default_factory=set)  # 仮説導出された記述素
    discovered_pieces: set[str] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)
    history: list[str] = field(default_factory=list)

    @property
    def known(self) -> set[str]:
        """confirmed ∪ derived: 想起やピース判定に使用"""
        return self.confirmed | self.derived
