from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Union


@dataclass
class Descriptor:
    id: str
    label: str


@dataclass
class Paradigm:
    id: str
    name: str
    p_pred: Dict[str, int] = field(default_factory=dict)  # {d_id: 0|1}, unknown=キー不在
    conceivable: Set[str] = field(default_factory=set)  # 想起可能集合
    relations: List[Tuple[str, str, float]] = field(default_factory=list)
    threshold: Optional[int] = None  # 自動計算
    depth: Optional[int] = None  # Explained(P)包含関係から自動導出

    def __post_init__(self):
        self.validate()

    def validate(self):
        # conceivable は p_pred のキーの部分集合でなければならない
        pred_keys = set(self.p_pred.keys())
        if not self.conceivable.issubset(pred_keys):
            invalid = sorted(self.conceivable - pred_keys)
            raise ValueError(
                f"Paradigm {self.id}: conceivable に p_pred に存在しない記述素: {invalid}"
            )
        # relations の src/tgt は conceivable に含まれる必要がある
        for src, tgt, w in self.relations:
            if src not in self.conceivable:
                raise ValueError(
                    f"Paradigm {self.id}: relation の src '{src}' が conceivable に含まれない"
                )
            if tgt not in self.conceivable:
                raise ValueError(
                    f"Paradigm {self.id}: relation の tgt '{tgt}' が conceivable に含まれない"
                )

    def prediction(self, d_id: str) -> Optional[int]:
        return self.p_pred.get(d_id)


@dataclass
class Question:
    id: str
    text: str
    ans_yes: List[Tuple[str, int]]
    ans_no: List[Tuple[str, int]]
    ans_irrelevant: List[str]
    correct_answer: str  # "yes" / "no" / "irrelevant"
    is_clear: bool = False
    prerequisites: List[str] = field(default_factory=list)
    related_descriptors: List[str] = field(default_factory=list)
    topic_category: str = ""

    @property
    def effect(self) -> Union[List[Tuple[str, int]], List[str]]:
        if self.correct_answer == "yes":
            return self.ans_yes
        elif self.correct_answer == "no":
            return self.ans_no
        else:
            return self.ans_irrelevant


@dataclass
class GameState:
    h: Dict[str, float]
    o: Dict[str, int]
    r: Set[str]
    p_current: str
    answered: Set[str] = field(default_factory=set)
