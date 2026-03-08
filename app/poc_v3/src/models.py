"""v3 POC: パズルエンジン - データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Proposition:
    id: str
    label: str
    formation_conditions: list[list[str]] | None = None  # 仮説導出: confirmed → derived（1回パス）
    entailment_conditions: list[list[str]] | None = None  # 論理的導出: confirmed → confirmed（不動点計算）
    rejection_conditions: list[list[str]] | None = None  # confirmed により棄却される条件


@dataclass
class Piece:
    """逆算連鎖から抽出されたパズルのピース"""

    id: str
    label: str
    members: list[str]  # 構成命題の ID 群
    depends_on: list[str]  # 依存ピースの ID 群（空なら独立ピース）


@dataclass
class Question:
    """質問。想起条件は命題の族（OR of AND）"""

    id: str
    text: str
    answer: str
    recall_conditions: list[list[str]]  # OR of AND: 想起条件（reveals される命題の導出条件）
    reveals: list[str]  # 回答で明らかになる命題 ID 群
    mechanism: str  # ラベル: "observation" | "link" | "anomaly"
    prerequisites: list[str] = field(default_factory=list)  # 質問文の言語的前提（confirmed のみで判定）
    topic_category: str = ""  # トピックカテゴリ（UI 用分類）


@dataclass
class GameState:
    confirmed: set[str] = field(default_factory=set)  # 観測 + 論理的導出で確定した命題
    derived: set[str] = field(default_factory=set)  # 仮説導出された命題
    discovered_pieces: set[str] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)
    history: list[str] = field(default_factory=list)

    @property
    def known(self) -> set[str]:
        """confirmed ∪ derived: 想起やピース判定に使用"""
        return self.confirmed | self.derived
