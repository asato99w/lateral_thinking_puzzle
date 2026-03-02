"""v2 POC: 探索領域ベースのパズルエンジン - データモデル"""

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
class ExplorationDomain:
    """独立ピースが開く探索領域"""

    id: str
    name: str
    root_piece: str  # この領域を開く独立ピースの ID
    reachable_facts: list[str]  # この領域内で発見可能な事実


@dataclass
class Strategy:
    """汎用探索戦略"""

    id: str
    name: str


@dataclass
class Question:
    """観測事実 × 戦略から導かれる質問"""

    id: str
    text: str
    answer: str  # Yes/No 回答テキスト
    strategy: str  # 戦略 ID
    preconditions: list[str]  # この質問が生まれるために必要な観測事実 ID 群
    reveals: list[str]  # 回答で明らかになる事実 ID 群
    mechanism: str  # "observation" | "link" | "anomaly"


@dataclass
class GameState:
    observed_facts: set[str] = field(default_factory=set)
    discovered_pieces: set[str] = field(default_factory=set)
    opened_domains: set[str] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)
    history: list[str] = field(default_factory=list)
