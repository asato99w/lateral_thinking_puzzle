"""クリアに至る最小質問集合の列挙

クリア条件から逆算し、必要な質問の最小集合を全て求める。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_indices(data: dict) -> tuple:
    """逆算に必要なインデックスを構築"""
    # descriptor_id → それを reveals する質問のリスト
    descriptor_to_questions: dict[str, list[dict]] = {}
    for q in data.get("questions", []):
        for did in q.get("reveals", []):
            descriptor_to_questions.setdefault(did, []).append(q)

    # 導出記述素の formation_conditions
    derived_conditions: dict[str, list[list[str]]] = {}
    for d in data.get("descriptors", []):
        if "formation_conditions" in d:
            derived_conditions[d["id"]] = d["formation_conditions"]

    # 棄却条件
    rejection_conditions: dict[str, list[list[str]]] = {}
    for d in data.get("descriptors", []):
        rc = d.get("rejection_conditions")
        if rc is not None:
            rejection_conditions[d["id"]] = rc

    initial_confirmed: set[str] = set(data.get("initial_confirmed", []))

    return descriptor_to_questions, derived_conditions, initial_confirmed, rejection_conditions


def find_question_sets_for_descriptor(
    descriptor_id: str,
    descriptor_to_questions: dict[str, list[dict]],
    derived_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
    initial_confirmed: set[str],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> list[frozenset[str]]:
    """ある記述素を confirmed にするために必要な質問集合の候補を全て返す。

    戻り値: frozenset[質問ID] のリスト（OR: いずれかの集合があれば十分）
    """
    if descriptor_id in memo:
        return memo[descriptor_id]

    # 循環防止用にまず空を入れる
    memo[descriptor_id] = []

    questions = descriptor_to_questions.get(descriptor_id, [])
    if not questions:
        # どの質問でも reveals されない（initial_confirmed なら不要、そうでなければ到達不能）
        memo[descriptor_id] = []
        return []

    results: list[frozenset[str]] = []
    for q in questions:
        # この質問を使う場合、質問自体 + recall_conditions を満たすための質問集合が必要
        qid = q["id"]
        recall_conds = q.get("recall_conditions", [])

        # recall の各グループ（OR）について、必要な質問集合を求める
        recall_options = find_question_sets_for_recall(
            recall_conds, descriptor_to_questions, derived_conditions, memo,
            initial_confirmed, rejection_conditions,
        )

        # 各 recall オプションに自身の質問を追加
        for option in recall_options:
            results.append(option | frozenset([qid]))

    results = minimize(list(set(results)))
    memo[descriptor_id] = results
    return results


def find_question_sets_for_recall(
    recall_conditions: list[list[str]],
    descriptor_to_questions: dict[str, list[dict]],
    derived_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
    initial_confirmed: set[str],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> list[frozenset[str]]:
    """recall_conditions（OR of AND）を満たすための質問集合候補を返す"""
    if not recall_conditions:
        # recall_conditions = [] → 条件なし（利用不可）
        return []

    results: list[frozenset[str]] = []
    for cond_group in recall_conditions:
        if not cond_group:
            # 空グループ [[]] → 無条件で利用可能
            results.append(frozenset())
            continue

        # AND: グループ内の全記述素を形成する必要がある
        group_options = find_question_sets_for_derived_group(
            cond_group, descriptor_to_questions, derived_conditions, memo,
            initial_confirmed, rejection_conditions,
        )
        results.extend(group_options)

    return results


def find_question_sets_for_derived_group(
    descriptor_ids: list[str],
    descriptor_to_questions: dict[str, list[dict]],
    derived_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
    initial_confirmed: set[str],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> list[frozenset[str]]:
    """記述素グループ（AND）を全て形成するための質問集合候補を返す"""
    # 各記述素について必要な質問集合を求め、直積を取る
    per_descriptor_options: list[list[frozenset[str]]] = []
    for did in descriptor_ids:
        options = find_question_sets_for_derived(
            did, descriptor_to_questions, derived_conditions, memo,
            initial_confirmed, rejection_conditions,
        )
        if not options:
            return []  # 1つでも到達不能なら全体が不可能
        per_descriptor_options.append(options)

    # 直積: 各記述素から1つずつ選んで和集合を取る
    return cartesian_union(per_descriptor_options)


def find_question_sets_for_derived(
    descriptor_id: str,
    descriptor_to_questions: dict[str, list[dict]],
    derived_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
    initial_confirmed: set[str],
    rejection_conditions: dict[str, list[list[str]]] | None = None,
) -> list[frozenset[str]]:
    """ある導出記述素を形成するための質問集合候補を返す。

    記述素は3つの方法で形成される:
    0. initial_confirmed: 初期確認済み（質問不要）
    1. reveals match: descriptor_id を reveals する質問経由で直接 confirmed
    2. formation_conditions: 条件記述素が全て confirmed/形成済み
    """
    # 初期確認済みの記述素は質問不要
    if descriptor_id in initial_confirmed:
        return [frozenset()]

    cache_key = f"derived:{descriptor_id}"
    if cache_key in memo:
        return memo[cache_key]

    memo[cache_key] = []  # 循環防止

    results: list[frozenset[str]] = []

    # 方法1: reveals match（記述素を reveals する質問経由）
    descriptor_options = find_question_sets_for_descriptor(
        descriptor_id, descriptor_to_questions, derived_conditions, memo,
        initial_confirmed, rejection_conditions,
    )
    results.extend(descriptor_options)

    # 方法2: formation_conditions 経由
    conditions = derived_conditions.get(descriptor_id, [])
    for cond_group in conditions:
        group_options = find_question_sets_for_derived_group(
            cond_group, descriptor_to_questions, derived_conditions, memo,
            initial_confirmed, rejection_conditions,
        )
        results.extend(group_options)

    results = minimize(list(set(results)))
    memo[cache_key] = results
    return results


def cartesian_union(
    options_list: list[list[frozenset[str]]],
) -> list[frozenset[str]]:
    """複数の選択肢リストの直積を取り、各組の和集合を返す。
    各ステップで重複排除と極小化を行い、組み合わせ爆発を抑制する。"""
    if not options_list:
        return [frozenset()]

    result = minimize(list(set(options_list[0])))
    for next_options in options_list[1:]:
        next_min = minimize(list(set(next_options)))
        new_result: set[frozenset[str]] = set()
        for existing in result:
            for addition in next_min:
                new_result.add(existing | addition)
        result = minimize(list(new_result))

    return result


def minimize(sets: list[frozenset[str]]) -> list[frozenset[str]]:
    """包含関係で冗長な集合を除去し、極小集合のみ残す"""
    # サイズ順にソート
    sorted_sets = sorted(set(sets), key=len)
    minimal: list[frozenset[str]] = []
    for s in sorted_sets:
        if not any(m <= s for m in minimal):
            minimal.append(s)
    return minimal


def _would_reject(
    descriptor_id: str,
    question_set: frozenset[str],
    questions_by_id: dict[str, dict],
    initial_confirmed: set[str],
    rejection_conditions: dict[str, list[list[str]]],
) -> bool:
    """質問集合の reveals の和集合が descriptor_id の rejection_conditions を満たすか判定"""
    if descriptor_id not in rejection_conditions:
        return False
    # 質問集合が confirms する記述素の和集合
    all_confirmed = set(initial_confirmed)
    for qid in question_set:
        q = questions_by_id.get(qid)
        if q:
            all_confirmed.update(q.get("reveals", []))
    # rejection_conditions の OR of AND 判定（confirmed のみ参照）
    return any(
        all(c in all_confirmed for c in group)
        for group in rejection_conditions[descriptor_id]
    )


def run(path: str) -> list[frozenset[str]]:
    data = load_data(path)
    descriptor_to_questions, derived_conditions, initial_confirmed, rejection_conditions = build_indices(data)
    clear_conditions = data.get("clear_conditions", [])

    if not clear_conditions:
        print("clear_conditions が未定義")
        return []

    memo: dict[str, list[frozenset[str]]] = {}
    all_options: list[frozenset[str]] = []

    # 各クリア条件グループ（OR）
    for cond_group in clear_conditions:
        # AND: グループ内の全記述素を confirmed にする
        per_descriptor_options: list[list[frozenset[str]]] = []
        for descriptor_id in cond_group:
            options = find_question_sets_for_derived(
                descriptor_id, descriptor_to_questions, derived_conditions, memo,
                initial_confirmed, rejection_conditions or None,
            )
            if not options:
                break  # この記述素が到達不能ならこのグループは不可能
            per_descriptor_options.append(options)
        else:
            # 全記述素について選択肢がある場合、直積を取る
            group_options = cartesian_union(per_descriptor_options)
            all_options.extend(group_options)

    # 棄却ポストフィルタ: 質問集合の reveals が rejection_conditions を満たし、
    # formation_conditions 経由で導出される記述素を棄却してしまう場合は除外
    if rejection_conditions:
        questions_by_id = {q["id"]: q for q in data.get("questions", [])}
        filtered: list[frozenset[str]] = []
        for qset in all_options:
            # この質問集合で棄却される記述素を計算
            all_confirmed = set(initial_confirmed)
            for qid in qset:
                q = questions_by_id.get(qid)
                if q:
                    all_confirmed.update(q.get("reveals", []))
            rejected_ids = set()
            for did, conds in rejection_conditions.items():
                if any(all(c in all_confirmed for c in group) for group in conds):
                    rejected_ids.add(did)
            # クリア条件の記述素が棄却されないか確認
            clear_blocked = False
            for cg in clear_conditions:
                if any(did in rejected_ids for did in cg):
                    # このクリア条件グループ内の記述素が棄却される
                    continue
                # 棄却されないグループがあれば OK
                break
            else:
                # 全クリア条件グループが棄却の影響を受ける場合は除外
                if rejected_ids:
                    clear_blocked = True
            if not clear_blocked:
                filtered.append(qset)
        all_options = filtered

    # 極小化
    minimal = minimize(all_options)
    return minimal


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_clear_chains.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    minimal = run(path)

    print(f"[find_clear_chains] クリアに至る最小質問集合: {len(minimal)} 通り\n")
    # サイズ順 → 辞書順
    for i, qset in enumerate(sorted(minimal, key=lambda s: (len(s), sorted(s))), 1):
        ids = sorted(qset)
        print(f"  #{i} ({len(ids)}問): {ids}")

    # 質問ラベルも表示
    data = load_data(path)
    q_labels = {q["id"]: q["text"] for q in data.get("questions", [])}
    print()
    for i, qset in enumerate(sorted(minimal, key=lambda s: (len(s), sorted(s))), 1):
        print(f"  --- #{i} ---")
        for qid in sorted(qset):
            print(f"    {qid}: {q_labels.get(qid, '?')}")


if __name__ == "__main__":
    main()
