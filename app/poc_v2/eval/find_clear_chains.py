"""クリアに至る最小質問集合の列挙

クリア条件から逆算し、必要な質問の最小集合を全て求める。
"""

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_indices(data: dict) -> tuple:
    """逆算に必要なインデックスを構築"""
    # fact_id → それを reveals する質問のリスト
    fact_to_questions: dict[str, list[dict]] = {}
    for q in data.get("questions", []):
        for fid in q.get("reveals", []):
            fact_to_questions.setdefault(fid, []).append(q)

    # hypothesis_id → formation_conditions
    hypo_conditions: dict[str, list[list[str]]] = {}
    for h in data.get("hypotheses", []):
        hypo_conditions[h["id"]] = h.get("formation_conditions", [])

    return fact_to_questions, hypo_conditions


def find_question_sets_for_fact(
    fact_id: str,
    fact_to_questions: dict[str, list[dict]],
    hypo_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
) -> list[frozenset[str]]:
    """ある事実を observed にするために必要な質問集合の候補を全て返す。

    戻り値: frozenset[質問ID] のリスト（OR: いずれかの集合があれば十分）
    """
    if fact_id in memo:
        return memo[fact_id]

    # 循環防止用にまず空を入れる
    memo[fact_id] = []

    questions = fact_to_questions.get(fact_id, [])
    if not questions:
        # どの質問でも reveals されない（initial_facts なら不要、そうでなければ到達不能）
        memo[fact_id] = []
        return []

    results: list[frozenset[str]] = []
    for q in questions:
        # この質問を使う場合、質問自体 + recall_conditions を満たすための質問集合が必要
        qid = q["id"]
        recall_conds = q.get("recall_conditions", [])

        # recall の各グループ（OR）について、必要な質問集合を求める
        recall_options = find_question_sets_for_recall(
            recall_conds, fact_to_questions, hypo_conditions, memo
        )

        # 各 recall オプションに自身の質問を追加
        for option in recall_options:
            results.append(option | frozenset([qid]))

    memo[fact_id] = results
    return results


def find_question_sets_for_recall(
    recall_conditions: list[list[str]],
    fact_to_questions: dict[str, list[dict]],
    hypo_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
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

        # AND: グループ内の全仮説を形成する必要がある
        group_options = find_question_sets_for_hypothesis_group(
            cond_group, fact_to_questions, hypo_conditions, memo
        )
        results.extend(group_options)

    return results


def find_question_sets_for_hypothesis_group(
    hypo_ids: list[str],
    fact_to_questions: dict[str, list[dict]],
    hypo_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
) -> list[frozenset[str]]:
    """仮説グループ（AND）を全て形成するための質問集合候補を返す"""
    # 各仮説について必要な質問集合を求め、直積を取る
    per_hypo_options: list[list[frozenset[str]]] = []
    for hid in hypo_ids:
        options = find_question_sets_for_hypothesis(
            hid, fact_to_questions, hypo_conditions, memo
        )
        if not options:
            return []  # 1つでも到達不能なら全体が不可能
        per_hypo_options.append(options)

    # 直積: 各仮説から1つずつ選んで和集合を取る
    return cartesian_union(per_hypo_options)


def find_question_sets_for_hypothesis(
    hypo_id: str,
    fact_to_questions: dict[str, list[dict]],
    hypo_conditions: dict[str, list[list[str]]],
    memo: dict[str, list[frozenset[str]]],
) -> list[frozenset[str]]:
    """ある仮説を形成するための質問集合候補を返す。

    仮説は2つの方法で形成される:
    1. fact match: hypo_id と同じ ID の事実が observed → 質問で reveals
    2. formation_conditions: 条件仮説が全て形成済み
    """
    cache_key = f"hypo:{hypo_id}"
    if cache_key in memo:
        return memo[cache_key]

    memo[cache_key] = []  # 循環防止

    results: list[frozenset[str]] = []

    # 方法1: fact match（H-* 事実を reveals する質問経由）
    fact_options = find_question_sets_for_fact(
        hypo_id, fact_to_questions, hypo_conditions, memo
    )
    results.extend(fact_options)

    # 方法2: formation_conditions 経由
    conditions = hypo_conditions.get(hypo_id, [])
    for cond_group in conditions:
        group_options = find_question_sets_for_hypothesis_group(
            cond_group, fact_to_questions, hypo_conditions, memo
        )
        results.extend(group_options)

    memo[cache_key] = results
    return results


def cartesian_union(
    options_list: list[list[frozenset[str]]],
) -> list[frozenset[str]]:
    """複数の選択肢リストの直積を取り、各組の和集合を返す"""
    if not options_list:
        return [frozenset()]

    result = options_list[0]
    for next_options in options_list[1:]:
        new_result: list[frozenset[str]] = []
        for existing in result:
            for addition in next_options:
                new_result.append(existing | addition)
        result = new_result

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


def run(path: str) -> list[frozenset[str]]:
    data = load_data(path)
    fact_to_questions, hypo_conditions = build_indices(data)
    clear_conditions = data.get("clear_conditions", [])

    if not clear_conditions:
        print("clear_conditions が未定義")
        return []

    memo: dict[str, list[frozenset[str]]] = {}
    all_options: list[frozenset[str]] = []

    # 各クリア条件グループ（OR）
    for cond_group in clear_conditions:
        # AND: グループ内の全事実を観測する
        per_fact_options: list[list[frozenset[str]]] = []
        for fact_id in cond_group:
            options = find_question_sets_for_fact(
                fact_id, fact_to_questions, hypo_conditions, memo
            )
            if not options:
                break  # この事実が到達不能ならこのグループは不可能
            per_fact_options.append(options)
        else:
            # 全事実について選択肢がある場合、直積を取る
            group_options = cartesian_union(per_fact_options)
            all_options.extend(group_options)

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
