"""v2 POC: パズルエンジン - データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Fact:
    id: str
    label: str


@dataclass
class Piece:
    """逆算連鎖から抽出されたパズルのピース"""

    id: str
    label: str
    facts: list[str]  # 構成事実の ID 群
    depends_on: list[str]  # 依存ピースの ID 群（空なら独立ピース）


@dataclass
class Hypothesis:
    """仮説。形成条件は事実/仮説の族（OR of AND）"""

    id: str
    label: str
    formation_conditions: list[list[str]]  # OR of AND: 各内側リストは事実/仮説IDの集合


@dataclass
class Question:
    """質問。想起条件は事実/仮説の族（OR of AND）"""

    id: str
    text: str
    answer: str
    recall_conditions: list[list[str]]  # OR of AND: 想起条件
    reveals: list[str]  # 回答で明らかになる事実 ID 群
    mechanism: str  # ラベル: "observation" | "link" | "anomaly"


@dataclass
class GameState:
    observed_facts: set[str] = field(default_factory=set)
    formed_hypotheses: set[str] = field(default_factory=set)
    discovered_pieces: set[str] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)
    history: list[str] = field(default_factory=list)
