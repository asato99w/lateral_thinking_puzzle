"""データ整合性チェック

data.json の構造的な整合性を検証する。
"""

import json
import sys
from pathlib import Path


REQUIRED_KEYS = ["id", "title", "statement", "truth", "descriptors", "initial_confirmed", "clear_conditions", "pieces", "questions"]
VALID_MECHANISMS = {"observation", "link", "anomaly"}


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_required_keys(data: dict) -> list[str]:
    errors = []
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"必須キー '{key}' が存在しない")
    return errors


def check_unique_ids(data: dict) -> list[str]:
    errors = []
    for collection_name in ("descriptors", "pieces", "questions"):
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
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}
    for ref in data.get("initial_confirmed", []):
        if ref not in descriptor_ids:
            errors.append(f"initial_confirmed の '{ref}' が descriptors に存在しない")
    return errors


def check_clear_conditions(data: dict) -> list[str]:
    errors = []
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}
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
    errors = []
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}
    piece_ids = {p["id"] for p in data.get("pieces", [])}
    for piece in data.get("pieces", []):
        pid = piece["id"]
        for mref in piece.get("members", []):
            if mref not in descriptor_ids:
                errors.append(f"piece '{pid}' の members 参照 '{mref}' が descriptors に存在しない")
        for dep in piece.get("depends_on", []):
            if dep not in piece_ids:
                errors.append(f"piece '{pid}' の depends_on 参照 '{dep}' が pieces に存在しない")
    return errors


def check_formation_refs(data: dict) -> list[str]:
    errors = []
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}
    for d in data.get("descriptors", []):
        did = d["id"]
        for cond_group in d.get("formation_conditions", []):
            for ref in cond_group:
                if ref not in descriptor_ids:
                    errors.append(f"descriptor '{did}' の formation_conditions 参照 '{ref}' が descriptors に存在しない")
    return errors


def check_question_refs(data: dict) -> list[str]:
    errors = []
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}
    # formation_conditions を持つ記述素のID集合（導出記述素 = 仮説的なもの）
    derivable_ids = {d["id"] for d in data.get("descriptors", []) if "formation_conditions" in d}
    # recall_conditions で使われるのは導出可能な記述素のみ（基礎記述素は reveals で直接確認される）
    for q in data.get("questions", []):
        qid = q["id"]
        for cond_group in q.get("recall_conditions", []):
            for ref in cond_group:
                if ref not in descriptor_ids:
                    errors.append(f"question '{qid}' の recall_conditions 参照 '{ref}' が descriptors に存在しない")
        for ref in q.get("reveals", []):
            if ref not in descriptor_ids:
                errors.append(f"question '{qid}' の reveals 参照 '{ref}' が descriptors に存在しない")
    return errors


def check_mechanism_values(data: dict) -> list[str]:
    errors = []
    for q in data.get("questions", []):
        qid = q["id"]
        mech = q.get("mechanism")
        if mech not in VALID_MECHANISMS:
            errors.append(f"question '{qid}' の mechanism '{mech}' が不正（有効値: {VALID_MECHANISMS}）")
    return errors


def check_piece_dag(data: dict) -> list[str]:
    errors = []
    pieces = {p["id"]: p.get("depends_on", []) for p in data.get("pieces", [])}

    # 独立ピース = depends_on が空（他のどのピースにも依存しない）
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
    checks = [
        ("必須キーの存在", check_required_keys),
        ("ID の一意性", check_unique_ids),
        ("initial_confirmed の妥当性", check_initial_confirmed),
        ("clear_conditions の妥当性", check_clear_conditions),
        ("pieces の参照整合", check_piece_refs),
        ("formation_conditions の参照整合", check_formation_refs),
        ("questions の参照整合", check_question_refs),
        ("mechanism の値域", check_mechanism_values),
        ("ピース依存の非循環", check_piece_dag),
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
