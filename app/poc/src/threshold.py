"""パラダイムの近傍・閾値・深度を O* から導出する。"""
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


def _anomaly_set(paradigm: Paradigm, o_star: dict[str, int]) -> set[str]:
    """Anomaly(P, O*): P_pred(d) ≠ O*(d) の記述素集合。"""
    return {
        d for d, pred in paradigm.p_pred.items()
        if d in o_star and pred != o_star[d]
    }


def _tension(paradigm: Paradigm, o_star: dict[str, int]) -> int:
    """tension(O*, P) = |Anomaly(P, O*)|。"""
    return len(_anomaly_set(paradigm, o_star))


def compute_neighborhoods(
    paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> None:
    """各パラダイムの近傍集合を O* ベースの射影で計算する。

    P' が P_current の近傍 ⟺
      1. tension(O*, P') < tension(O*, P_current)（strict <）
      2. Remaining(P', P_current) ⊂ Anomaly(P_current)（真部分集合）
      3. Hasse 図で直接後続（中間がない）
      4. Explained 包含で冗長でない（Explained(A) ⊂ Explained(B) なら B を除外）

    Remaining(P', P_current) = Anomaly(P_current, O*) ∩ Anomaly(P', O*)
    """
    pids = list(paradigms.keys())
    anomaly_sets: dict[str, set[str]] = {
        pid: _anomaly_set(paradigms[pid], o_star) for pid in pids
    }
    tensions: dict[str, int] = {
        pid: len(anomaly_sets[pid]) for pid in pids
    }
    # Explained(P) = {d | P_pred(d) == O*(d)}
    explained: dict[str, set[str]] = {}
    for pid in pids:
        explained[pid] = {
            d for d, pred in paradigms[pid].p_pred.items()
            if d in o_star and pred == o_star[d]
        }

    for pid_cur in pids:
        anom_cur = anomaly_sets[pid_cur]
        if not anom_cur:
            paradigms[pid_cur].neighbors = set()
            continue

        # 候補: tension strict < かつ Remaining が真部分集合
        remaining_map: dict[str, frozenset[str]] = {}
        for pid_cand in pids:
            if pid_cand == pid_cur:
                continue
            if tensions[pid_cand] >= tensions[pid_cur]:
                continue
            remaining = anom_cur & anomaly_sets[pid_cand]
            if remaining < anom_cur:  # 真部分集合
                remaining_map[pid_cand] = frozenset(remaining)

        # Hasse 図: 直接後続のみ（中間がない）
        # P_a が P_b を覆う ⟺ Remaining(P_a) ⊃ Remaining(P_b) かつ中間なし
        # 近傍 = Remaining が極大（他の候補の Remaining に真に含まれない）
        neighbors: set[str] = set()
        cand_pids = list(remaining_map.keys())
        for i, pid_a in enumerate(cand_pids):
            rem_a = remaining_map[pid_a]
            is_covered = False
            for j, pid_b in enumerate(cand_pids):
                if i == j:
                    continue
                rem_b = remaining_map[pid_b]
                if rem_a < rem_b:  # rem_a ⊂ rem_b（rem_b のほうが大きい = 中間）
                    is_covered = True
                    break
            if not is_covered:
                neighbors.add(pid_a)

        # Explained 包含フィルタ:
        # Explained(A) ⊂ Explained(B) のとき B を除外し、より近い A のみ残す。
        # （Explained が大きいパラダイムは、小さいパラダイムを経由して到達すべき）
        filtered = set(neighbors)
        for pid_a in neighbors:
            for pid_b in neighbors:
                if pid_a == pid_b:
                    continue
                if explained[pid_a] < explained[pid_b]:  # Explained(A) ⊂ Explained(B)
                    filtered.discard(pid_b)
        paradigms[pid_cur].neighbors = filtered


def _resolve(
    o_star: dict[str, int],
    p_source: Paradigm,
    p_target: Paradigm,
) -> int:
    """P_source のアノマリーのうち P_target が正しく予測する数。"""
    count = 0
    for d, pred_src in p_source.p_pred.items():
        if d not in o_star:
            continue
        if pred_src == o_star[d]:
            continue
        # d は P_source のアノマリー
        pred_tgt = p_target.prediction(d)
        if pred_tgt is not None and pred_tgt == o_star[d]:
            count += 1
    return count


def compute_shift_thresholds(
    paradigms: dict[str, Paradigm],
    o_star: dict[str, int],
) -> None:
    """各パラダイムの shift_threshold N(P_target) を計算する。

    N(P_target) = min over { P_source | P_target ∈ neighbors(P_source) }
                  of resolve(O*, P_source, P_target)

    P_target を近傍に持つ全 P_source からの resolve の最小値。
    """
    # 逆引き: 各 P_target について、それを近傍に持つ P_source の一覧
    for pid_target, p_target in paradigms.items():
        min_resolve = None
        for pid_source, p_source in paradigms.items():
            if pid_source == pid_target:
                continue
            if pid_target not in p_source.neighbors:
                continue
            res = _resolve(o_star, p_source, p_target)
            if min_resolve is None or res < min_resolve:
                min_resolve = res

        p_target.shift_threshold = min_resolve


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
