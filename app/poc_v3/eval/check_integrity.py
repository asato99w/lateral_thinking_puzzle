"""データ整合性チェック

data.json の構造的な整合性を検証する。
v2（descriptors, pieces, clear_conditions）と v3（propositions）の両形式に対応。
"""

import json
import sys
from pathlib import Path


REQUIRED_KEYS_V2_DATA = ["id", "title", "statement", "truth", "descriptors", "initial_confirmed", "clear_conditions", "pieces", "questions"]
REQUIRED_KEYS_V2_SRC = ["title", "descriptors", "initial_confirmed", "clear_conditions", "pieces", "questions"]
REQUIRED_KEYS_V3_DATA = ["id", "title", "statement", "truth", "propositions", "initial_confirmed", "questions"]
REQUIRED_KEYS_V3_SRC = ["title", "propositions", "initial_confirmed", "questions"]
VALID_MECHANISMS = {"observation", "link", "anomaly", "rejection"}


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_v3(data: dict) -> bool:
    """v3 形式かどうかを propositions キーの有無で判定"""
    return "propositions" in data


def _is_src(data: dict) -> bool:
    """data_src.json かどうかを _ プレフィックス付きフィールドの有無で判定"""
    for key in data:
        if key.startswith("_"):
            return True
    collection = "propositions" if _is_v3(data) else "descriptors"
    for d in data.get(collection, []):
        for key in d:
            if key.startswith("_"):
                return True
    for q in data.get("questions", []):
        for key in q:
            if key.startswith("_"):
                return True
    return False


def _get_descriptors(data: dict) -> list[dict]:
    """v2/v3 互換で命題コレクションを取得"""
    return data.get("propositions", data.get("descriptors", []))


def check_required_keys(data: dict) -> list[str]:
    errors = []
    is_v3 = _is_v3(data)
    is_src = _is_src(data)

    if is_v3:
        required = REQUIRED_KEYS_V3_SRC if is_src else REQUIRED_KEYS_V3_DATA
    else:
        required = REQUIRED_KEYS_V2_SRC if is_src else REQUIRED_KEYS_V2_DATA

    for key in required:
        if key not in data:
            errors.append(f"必須キー '{key}' が存在しない")

    if is_src:
        has_st = "S" in data and "T" in data
        has_full = "statement" in data and "truth" in data
        if not has_st and not has_full:
            errors.append("問題文/真相キーが不足: (S, T) または (statement, truth) が必要")
    return errors


def check_unique_ids(data: dict) -> list[str]:
    errors = []
    is_v3 = _is_v3(data)
    collections = ["questions"]
    if is_v3:
        collections.insert(0, "propositions")
    else:
        collections = ["descriptors", "pieces", "questions"]

    for collection_name in collections:
        items = data.get(collection_name, [])
        ids = [item["id"] for item in items]
        seen = set()
        for id_ in ids:
            if id_ in seen:
                errors.append(f"{collection_name} 内で ID '{id_}' が重複")
            seen.add(id_)
    return errors


def check_initial_confirmed(data: dict) -> list[str]:
    errors = []
    descriptor_ids = {d["id"] for d in _get_descriptors(data)}
    for ref in data.get("initial_confirmed", []):
        if ref not in descriptor_ids:
            # v3: S命題は initial_confirmed に含まれるが propositions には含まれないことがある
            # propositions には分割命題・中間命題のみが含まれる場合がある
            if not _is_v3(data):
                errors.append(f"initial_confirmed の '{ref}' が descriptors に存在しない")
    return errors


def check_clear_conditions(data: dict) -> list[str]:
    if _is_v3(data):
        return []  # v3 では clear_conditions を使用しない
    errors = []
    descriptor_ids = {d["id"] for d in _get_descriptors(data)}
    clear_conds = data.get("clear_conditions", [])
    if not clear_conds:
        errors.append("clear_conditions が空（クリア不可能）")
        return errors
    for i, cond_group in enumerate(clear_conds):
        if not cond_group:
            errors.append(f"clear_conditions[{i}] が空グループ")
        for ref in cond_group:
            if ref not in descriptor_ids:
                errors.append(f"clear_conditions[{i}] の参照 '{ref}' が descriptors に存在しない")
    return errors


def check_piece_refs(data: dict) -> list[str]:
    if _is_v3(data):
        return []  # v3 では pieces を使用しない
    errors = []
    descriptor_ids = {d["id"] for d in _get_descriptors(data)}
    piece_ids = {p["id"] for p in data.get("pieces", [])}
    for piece in data.get("pieces", []):
        pid = piece["id"]
        for mref in piece.get("members", []):
            if mref not in descriptor_ids:
                errors.append(f"piece '{pid}' の members 参照 '{mref}' が descriptors に存在しない")
        for trigger_group in piece.get("trigger", []):
            for tref in trigger_group:
                if tref not in descriptor_ids:
                    errors.append(f"piece '{pid}' の trigger 参照 '{tref}' が descriptors に存在しない")
        for dep in piece.get("depends_on", []):
            if dep not in piece_ids:
                errors.append(f"piece '{pid}' の depends_on 参照 '{dep}' が pieces に存在しない")
    return errors


def check_formation_refs(data: dict) -> list[str]:
    errors = []
    descriptors = _get_descriptors(data)
    descriptor_ids = {d["id"] for d in descriptors}
    # v3: initial_confirmed の S 命題も有効な参照先
    all_valid_ids = descriptor_ids | set(data.get("initial_confirmed", []))
    for d in descriptors:
        did = d["id"]
        for cond_group in d.get("formation_conditions", []):
            for ref in cond_group:
                if ref not in all_valid_ids:
                    errors.append(f"命題 '{did}' の formation_conditions 参照 '{ref}' が存在しない")
    return errors


def check_entailment_refs(data: dict) -> list[str]:
    errors = []
    descriptors = _get_descriptors(data)
    descriptor_ids = {d["id"] for d in descriptors}
    all_valid_ids = descriptor_ids | set(data.get("initial_confirmed", []))
    for d in descriptors:
        did = d["id"]
        for cond_group in d.get("entailment_conditions") or []:
            for ref in cond_group:
                if ref not in all_valid_ids:
                    errors.append(f"命題 '{did}' の entailment_conditions 参照 '{ref}' が存在しない")
    return errors


def check_rejection_refs(data: dict) -> list[str]:
    errors = []
    descriptors = _get_descriptors(data)
    descriptor_ids = {d["id"] for d in descriptors}
    all_valid_ids = descriptor_ids | set(data.get("initial_confirmed", []))
    for d in descriptors:
        did = d["id"]
        for cond_group in d.get("rejection_conditions") or []:
            for ref in cond_group:
                if ref not in all_valid_ids:
                    errors.append(f"命題 '{did}' の rejection_conditions 参照 '{ref}' が存在しない")
    return errors


def _get_reveals(q: dict) -> list[str]:
    """reveals を文字列・リスト両対応でリストとして返す"""
    r = q.get("reveals", [])
    if isinstance(r, str):
        return [r] if r else []
    return r


def check_question_refs(data: dict) -> list[str]:
    errors = []
    descriptors = _get_descriptors(data)
    descriptor_ids = {d["id"] for d in descriptors}
    # v3: initial_confirmed の S 命題も有効な参照先
    all_valid_ids = descriptor_ids | set(data.get("initial_confirmed", []))
    for q in data.get("questions", []):
        qid = q["id"]
        # v2 互換: recall_conditions が存在する場合のみチェック
        for cond_group in q.get("recall_conditions", []):
            for ref in cond_group:
                if ref not in all_valid_ids:
                    errors.append(f"question '{qid}' の recall_conditions 参照 '{ref}' が存在しない")
        for ref in _get_reveals(q):
            if ref not in all_valid_ids:
                errors.append(f"question '{qid}' の reveals 参照 '{ref}' が存在しない")
    return errors


def check_mechanism_values(data: dict) -> list[str]:
    if _is_v3(data):
        return []  # v3 では mechanism を使用しない
    errors = []
    for q in data.get("questions", []):
        qid = q["id"]
        mech = q.get("mechanism")
        if mech not in VALID_MECHANISMS:
            errors.append(f"question '{qid}' の mechanism '{mech}' が不正（有効値: {VALID_MECHANISMS}）")
    return errors


def check_prerequisites_grounded(data: dict) -> list[str]:
    """前提条件の命題が対話上で確立可能か検証する。"""
    errors = []
    initial = set(data.get("initial_confirmed", []))
    all_reveals = set()
    for q in data.get("questions", []):
        for ref in _get_reveals(q):
            all_reveals.add(ref)

    grounded = initial | all_reveals

    for q in data.get("questions", []):
        qid = q["id"]
        for ref in q.get("prerequisites", []):
            if ref not in grounded:
                errors.append(
                    f"question '{qid}' の prerequisites '{ref}' が "
                    f"initial_confirmed にも reveals にも含まれない（導出のみでは前提不成立）"
                )
    return errors


def check_piece_dag(data: dict) -> list[str]:
    if _is_v3(data):
        return []  # v3 では pieces を使用しない
    errors = []
    pieces = {p["id"]: p.get("depends_on", []) for p in data.get("pieces", [])}

    independent = [pid for pid, deps in pieces.items() if len(deps) == 0]
    dependent = [pid for pid, deps in pieces.items() if len(deps) > 0]
    print(f"    独立ピース（依存なし）: {independent}")
    print(f"    依存ピース: {[f'{pid} → {pieces[pid]}' for pid in dependent]}")

    def has_cycle(node: str, visiting: set, visited: set) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in pieces.get(node, []):
            if has_cycle(dep, visiting, visited):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    visited: set[str] = set()
    for pid in pieces:
        if pid not in visited:
            if has_cycle(pid, set(), visited):
                errors.append(f"pieces の depends_on に循環が存在する（'{pid}' を含む）")
    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)
    is_v3 = _is_v3(data)
    fmt = "v3" if is_v3 else "v2"
    print(f"  形式: {fmt}")

    checks = [
        ("必須キーの存在", check_required_keys),
        ("ID の一意性", check_unique_ids),
        ("initial_confirmed の妥当性", check_initial_confirmed),
        ("clear_conditions の妥当性", check_clear_conditions),
        ("pieces の参照整合", check_piece_refs),
        ("formation_conditions の参照整合", check_formation_refs),
        ("entailment_conditions の参照整合", check_entailment_refs),
        ("rejection_conditions の参照整合", check_rejection_refs),
        ("questions の参照整合", check_question_refs),
        ("mechanism の値域", check_mechanism_values),
        ("ピース依存の非循環", check_piece_dag),
        ("前提条件の対話上の確立", check_prerequisites_grounded),
    ]

    all_errors: list[str] = []
    for label, fn in checks:
        errors = fn(data)
        if errors:
            print(f"  FAIL: {label}")
            for e in errors:
                print(f"    - {e}")
            all_errors.extend(errors)
        else:
            print(f"  PASS: {label}")

    return len(all_errors) == 0, all_errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_integrity.py <data.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print("[check_integrity]")
    ok, _ = run(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
