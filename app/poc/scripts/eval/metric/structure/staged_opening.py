"""段階的オープンの連鎖を検証する。

init_questions が共有質問を含まない場合に、
R(P) の同化を通じて共有質問が段階的にオープンされるかを追跡する。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import load_data, MAIN_PATH  # noqa: E402
from engine import (
    init_game,
    init_questions,
    compute_effect,
    _assimilate_descriptor,
    open_questions,
    tension,
    alignment,
    EPSILON,
)


def classify_question(q, paradigms):
    """質問を P1固有 / 共有 / 他パラダイム に分類する。"""
    eff = compute_effect(q)
    if q.correct_answer == "irrelevant":
        return "irrelevant", set()

    eff_ds = {d for d, v in eff}
    homes = {}
    for pid in MAIN_PATH:
        if pid not in paradigms:
            continue
        p = paradigms[pid]
        overlap = eff_ds & p.conceivable
        if overlap:
            homes[pid] = overlap

    if not homes:
        return "orphan", set()
    if len(homes) == 1:
        pid = list(homes.keys())[0]
        return f"{pid}_exclusive", homes
    return "shared", homes


def main():
    paradigms, questions, all_ids, ps_values, init_pid = load_data()
    p_init = paradigms[init_pid]

    # 現行の init_questions
    init_qs = init_questions(p_init, questions)

    # 分類
    exclusive_qs = []
    shared_qs = []
    for q in init_qs:
        kind, homes = classify_question(q, paradigms)
        if kind == f"{init_pid}_exclusive":
            exclusive_qs.append(q)
        elif kind == "shared":
            shared_qs.append((q, homes))

    print(f"初期オープン {len(init_qs)}問 の内訳:")
    print(f"  {init_pid}固有: {len(exclusive_qs)}問")
    print(f"  共有: {len(shared_qs)}問")
    for q, homes in shared_qs:
        home_str = " & ".join(homes.keys())
        eff = compute_effect(q)
        eff_ds = [d for d, v in eff]
        print(f"    {q.id} [{home_str}] effect={eff_ds}")
    print()

    # --- シミュレーション: 固有質問のみ初期オープン ---
    print("=" * 60)
    print("シミュレーション: 固有質問のみ初期オープン")
    print("=" * 60)
    print()

    state = init_game(ps_values, paradigms, init_pid, all_ids)

    # 共有質問の effect 記述素と必要な H 値を整理
    shared_targets = {}  # d_id -> [(question, v)]
    for q, homes in shared_qs:
        eff = compute_effect(q)
        for d, v in eff:
            shared_targets.setdefault(d, []).append((q, v))

    print("共有質問のオープンに必要な記述素:")
    for d in sorted(shared_targets):
        qs = shared_targets[d]
        print(f"  {d}: H ≈ {qs[0][1]} が必要 ({', '.join(q.id for q, v in qs)})")
    print()

    # 固有質問を逐次回答し、同化による共有記述素の H 変化を追跡
    print("固有質問の逐次回答:")
    print("-" * 60)

    opened_shared = set()

    for q in exclusive_qs:
        eff = compute_effect(q)

        # 直接更新
        for d, v in eff:
            state.h[d] = float(v)
            state.o[d] = v
        state.answered.add(q.id)

        # 同化
        p_cur = paradigms[state.p_current]
        for d, v in eff:
            pred = p_cur.prediction(d)
            if pred is not None and pred == v:
                _assimilate_descriptor(state.h, d, p_cur)

        # 共有記述素の H 変化をチェック
        newly_openable = []
        for d in sorted(shared_targets):
            if d in opened_shared:
                continue
            for sq, v in shared_targets[d]:
                if sq.id in opened_shared:
                    continue
                if abs(state.h[d] - v) < EPSILON:
                    newly_openable.append((sq, d, state.h[d]))
                    opened_shared.add(sq.id)

        eff_str = ", ".join(f"{d}={v}" for d, v in eff)
        line = f"{q.id}({q.correct_answer}) [{eff_str}]"

        if newly_openable:
            print(line)
            for sq, d, h_val in newly_openable:
                print(f"  → H[{d}]={h_val:.3f} → {sq.id} オープン可能")
                print(f"    「{sq.text}」")
        else:
            # 同化が共有記述素に影響したか
            assimilated = []
            for d in sorted(shared_targets):
                if abs(state.h[d] - 0.5) > 0.01 and d not in state.o:
                    assimilated.append((d, state.h[d]))
            if assimilated:
                print(line)
                for d, h_val in assimilated:
                    threshold = EPSILON
                    for sq, v in shared_targets[d]:
                        gap = abs(h_val - v)
                        status = "open" if gap < threshold else f"残り{gap:.3f}"
                        print(f"  同化: H[{d}]={h_val:.3f} ({status})")
                        break
            else:
                print(f"{line}  (共有記述素への同化なし)")

    print()
    print("-" * 60)

    # 結果サマリ
    not_opened = [sq for sq, _ in shared_qs if sq.id not in opened_shared]
    print(f"段階的にオープン可能: {len(opened_shared)}問")
    print(f"オープン不可: {len(not_opened)}問")
    for sq in not_opened:
        eff = compute_effect(sq)
        eff_ds = [(d, state.h.get(d, 0.5)) for d, v in eff]
        print(f"  {sq.id}: {[(d, f'H={h:.3f}') for d, h in eff_ds]}")
        print(f"    「{sq.text}」")

    print()

    # R(P1) の共有記述素への経路を可視化
    print("=" * 60)
    print(f"R({init_pid}) から共有記述素への経路")
    print("=" * 60)

    shared_ds = set()
    for pid in MAIN_PATH:
        if pid == init_pid or pid not in paradigms:
            continue
        shared_ds |= p_init.conceivable & paradigms[pid].conceivable

    print(f"共有記述素: {sorted(shared_ds)}")
    print()

    # R(P1) で共有記述素に到達する経路
    for src, tgt, w in p_init.relations:
        is_src_shared = src in shared_ds
        is_tgt_shared = tgt in shared_ds
        if is_tgt_shared:
            src_type = "共有" if is_src_shared else "固有"
            print(f"  {src}({src_type}) →({w}) {tgt}(共有)")

    # 共有記述素だが R(P1) のターゲットにならないもの
    relation_tgts = {tgt for _, tgt, _ in p_init.relations}
    relation_srcs = {src for src, _, _ in p_init.relations}
    unreachable = shared_ds - relation_tgts - set(state.o.keys())
    if unreachable:
        print()
        print(f"  R({init_pid}) で到達不可能な共有記述素: {sorted(unreachable)}")
        for d in sorted(unreachable):
            is_src = d in relation_srcs
            if is_src:
                targets = [(tgt, w) for src, tgt, w in p_init.relations if src == d]
                print(f"    {d}: src としてのみ存在 → {targets}")
            else:
                print(f"    {d}: R({init_pid}) に未接続")


if __name__ == "__main__":
    main()
