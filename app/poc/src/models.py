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
    d_plus: Set[str] = field(default_factory=set)
    d_minus: Set[str] = field(default_factory=set)
    relations: List[Tuple[str, str, float]] = field(default_factory=list)
    threshold: Optional[int] = None  # 近傍と O* から導出

    def __post_init__(self):
        self.validate()

    def validate(self):
        d_all = self.d_plus | self.d_minus
        overlap = self.d_plus & self.d_minus
        if overlap:
            raise ValueError(
                f"Paradigm {self.id}: d_plus と d_minus が重複: {sorted(overlap)}"
            )
        for src, tgt, w in self.relations:
            if src not in d_all:
                raise ValueError(
                    f"Paradigm {self.id}: relation の src '{src}' が D(P) に含まれない"
                )
            if tgt not in d_all:
                raise ValueError(
                    f"Paradigm {self.id}: relation の tgt '{tgt}' が D(P) に含まれない"
                )

    @property
    def d_all(self) -> Set[str]:
        return self.d_plus | self.d_minus

    def prediction(self, d_id: str) -> Optional[int]:
        if d_id in self.d_plus:
            return 1
        if d_id in self.d_minus:
            return 0
        return None


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
