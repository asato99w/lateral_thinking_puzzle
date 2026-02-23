"""パラダイムの閾値と深度を Conceivable と O* から導出する。"""
from __future__ import annotations

from models import Paradigm, Question


def build_o_star(
    questions: list[Question],
    ps_values: dict[str, int],
) -> dict[str, int]:
    """完全確定 O* を構築する。全質問の正解と Ps から観測状態を集約。"""
    o_star: dict[str, int] = {}
    for d_id, val in ps_values.items():
        o_star[d_id] = val
    for q in questions:
        if q.correct_answer == "irrelevant":
            continue
        for d_id, v in q.effect:
            o_star[d_id] = v
    return o_star


def _exclusive_conceivable_anomalies(
    paradigm: Paradigm,
    all_paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> int:
    """固有想起アノマリー: Conceivable(P) 固有の記述素のうち P_pred(d) ≠ O*(d) の数。"""
    # 他の全パラダイムの conceivable の和集合
    other_conceivable = set()
    for pid, p in all_paradigms.items():
        if pid != paradigm.id:
            other_conceivable |= p.conceivable

    exclusive = paradigm.conceivable - other_conceivable
    count = 0
    for d in exclusive:
        pred = paradigm.prediction(d)
        if pred is not None and d in o_star and pred != o_star[d]:
            count += 1
    return count


def _shared_conceivable_anomalies(
    paradigm: Paradigm,
    other: Paradigm,
    o_star: dict[str, int],
) -> int:
    """共有想起アノマリー(P, P'): Conceivable(P) ∩ Conceivable(P') 内で P_pred(d) ≠ O*(d) の数。"""
    shared = paradigm.conceivable & other.conceivable
    count = 0
    for d in shared:
        pred = paradigm.prediction(d)
        if pred is not None and d in o_star and pred != o_star[d]:
            count += 1
    return count


def compute_thresholds(
    paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> None:
    """各パラダイムの threshold を固有想起アノマリー + min共有想起アノマリーから導出。

    threshold(P) = |固有想起アノマリー(P)| + min_{P'} |共有想起アノマリー(P, P')|
    """
    for pid, p in paradigms.items():
        exclusive = _exclusive_conceivable_anomalies(p, paradigms, o_star)

        # 共有アノマリーが最小のパラダイムとの値を採用
        min_shared = None
        for pid2, p2 in paradigms.items():
            if pid2 == pid:
                continue
            shared_anomalies = _shared_conceivable_anomalies(p, p2, o_star)
            if min_shared is None or shared_anomalies < min_shared:
                min_shared = shared_anomalies

        if min_shared is not None:
            p.threshold = exclusive + min_shared
        else:
            # 他のパラダイムが存在しない場合
            p.threshold = None


def compute_depths(
    paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> None:
    """Explained(P) の包含関係から depth を導出する。

    Explained(P) = {d | P_pred(d) == O*(d)} （符号込みの正しい予測集合）
    Explained(P) ⊂ Explained(P') ならば depth(P) < depth(P')

    包含関係による半順序をトポロジカルソートして depth を割り当てる。
    """
    # 各パラダイムの Explained 集合を計算
    explained: dict[str, set[str]] = {}
    for pid, p in paradigms.items():
        exp = set()
        for d, pred_val in p.p_pred.items():
            if d in o_star and pred_val == o_star[d]:
                exp.add(d)
        explained[pid] = exp

    # 包含関係 DAG を構築: pid1 → pid2 means Explained(pid1) ⊂ Explained(pid2)
    # (pid1 のほうが浅い)
    pids = list(paradigms.keys())
    # strictly_contained[a] = set of b where Explained(a) ⊂ Explained(b)
    strictly_contained: dict[str, set[str]] = {pid: set() for pid in pids}

    for i, a in enumerate(pids):
        for j, b in enumerate(pids):
            if i == j:
                continue
            if explained[a] < explained[b]:  # proper subset
                strictly_contained[a].add(b)

    # トポロジカルソートで depth 割り当て
    # depth = 最長到達パスの長さ（比較不能なものは同じ depth になりうる）
    depth_map: dict[str, int] = {}

    def compute_depth(pid: str, visited: set[str]) -> int:
        if pid in depth_map:
            return depth_map[pid]
        if pid in visited:
            return 0  # 循環（あってはならないが安全策）
        visited.add(pid)

        # このパラダイムを含むものが存在しなければ depth は最大
        # depth は「自分より小さい Explained を持つものの最大 depth + 1」
        # ただし、自分が最小なら depth = 0
        parents = [
            p for p in pids
            if pid in strictly_contained[p]  # p ⊂ pid → p は pid より浅い
        ]
        if not parents:
            depth_map[pid] = 0
        else:
            max_parent_depth = max(compute_depth(p, visited) for p in parents)
            depth_map[pid] = max_parent_depth + 1
        return depth_map[pid]

    for pid in pids:
        compute_depth(pid, set())

    for pid, p in paradigms.items():
        p.depth = depth_map.get(pid, 0)
