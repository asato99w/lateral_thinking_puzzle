"""仮説連鎖の整合性チェック

_trigger / _kind / _piece メタ情報の整合性を検証する。
data_src.json 専用（_ プレフィックスフィールドが必要）。
"""

import json
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_trigger_exists(data: dict) -> list[str]:
    """各ピースの _trigger が descriptors に存在するか"""
    errors = []
    descriptor_ids = {d["id"] for d in data.get("descriptors", [])}

    for piece in data.get("pieces", []):
        pid = piece["id"]
        trigger = piece.get("_trigger")
        if trigger is None:
            continue
        if trigger not in descriptor_ids:
            errors.append(f"piece '{pid}' の _trigger '{trigger}' が descriptors に存在しない")

    return errors


def check_trigger_has_formation(data: dict) -> list[str]:
    """trigger 記述素が formation_conditions を持つか"""
    errors = []
    descriptor_map = {d["id"]: d for d in data.get("descriptors", [])}

    for piece in data.get("pieces", []):
        pid = piece["id"]
        trigger = piece.get("_trigger")
        if trigger is None:
            continue
        d = descriptor_map.get(trigger)
        if d is None:
            continue  # check_trigger_exists で検出済み
        if "formation_conditions" not in d:
            errors.append(f"piece '{pid}' の _trigger '{trigger}' が formation_conditions を持たない（基礎記述素）")

    return errors


def check_descriptor_piece_ref(data: dict) -> list[str]:
    """記述素の _piece が正しいピースを指しているか"""
    errors = []
    piece_ids = {p["id"] for p in data.get("pieces", [])}

    # ピースの members から descriptor → piece の正しいマッピングを作る
    descriptor_to_piece: dict[str, str] = {}
    for piece in data.get("pieces", []):
        for mid in piece.get("members", []):
            descriptor_to_piece[mid] = piece["id"]

    for d in data.get("descriptors", []):
        did = d["id"]
        declared_piece = d.get("_piece")
        if declared_piece is None:
            continue
        if declared_piece not in piece_ids:
            errors.append(f"descriptor '{did}' の _piece '{declared_piece}' が pieces に存在しない")
            continue
        actual_piece = descriptor_to_piece.get(did)
        if actual_piece is not None and actual_piece != declared_piece:
            errors.append(
                f"descriptor '{did}' の _piece が '{declared_piece}' だが、"
                f"実際は piece '{actual_piece}' の member"
            )

    return errors


def check_dependency_trigger_formation(data: dict) -> list[str]:
    """依存ピースのトリガーの formation_conditions が依存先の記述素を含むか"""
    errors = []
    descriptor_map = {d["id"]: d for d in data.get("descriptors", [])}
    piece_map = {p["id"]: p for p in data.get("pieces", [])}

    for piece in data.get("pieces", []):
        pid = piece["id"]
        trigger = piece.get("_trigger")
        deps = piece.get("depends_on", [])
        if trigger is None or not deps:
            continue

        trigger_d = descriptor_map.get(trigger)
        if trigger_d is None or "formation_conditions" not in trigger_d:
            continue

        # 依存先ピースの members を集める
        dep_members: set[str] = set()
        for dep_pid in deps:
            dep_piece = piece_map.get(dep_pid)
            if dep_piece:
                dep_members.update(dep_piece.get("members", []))

        # formation_conditions のいずれかのグループが依存先の記述素を含むか
        has_dep_ref = False
        for cond_group in trigger_d["formation_conditions"]:
            if any(ref in dep_members for ref in cond_group):
                has_dep_ref = True
                break

        if not has_dep_ref and dep_members:
            errors.append(
                f"piece '{pid}' の _trigger '{trigger}' の formation_conditions が "
                f"依存先ピース {deps} の記述素を含まない"
            )

    return errors


def run(path: str) -> tuple[bool, list[str]]:
    data = load_data(path)

    # メタ情報の存在チェック
    has_meta = any("_trigger" in p for p in data.get("pieces", []))
    has_meta = has_meta or any("_piece" in d for d in data.get("descriptors", []))
    if not has_meta:
        print("  SKIP: 仮説連鎖メタ情報なし")
        return True, []

    checks = [
        ("_trigger の存在", check_trigger_exists),
        ("trigger の formation_conditions 保有", check_trigger_has_formation),
        ("_piece の参照整合", check_descriptor_piece_ref),
        ("依存ピースの trigger 整合", check_dependency_trigger_formation),
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
        print("Usage: python check_hypothesis_chain.py <data_src.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: {path} が見つかりません", file=sys.stderr)
        sys.exit(2)

    print("[check_hypothesis_chain]")
    ok, _ = run(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
