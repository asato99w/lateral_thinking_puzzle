"""12_形式化_v2.md の差分を forbidden_basement.json に適用するスクリプト。

一時的なパッチスクリプト。v2 の変更点:
1. 全パラダイムの relations 更新（ゲート辺追加）
2. P3, P4 の p_pred 追加（Fs-96, Fs-14）
3. P5 の Fs-14 p_pred 変更（0→1）
4. 全パラダイムに neighbors 追加
5. q24, q27 の paradigms を全パラダイムに変更
6. init_question_ids 更新
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
INPUT = DATA_DIR / "forbidden_basement.json"
OUTPUT = DATA_DIR / "forbidden_basement.json"

def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    paradigms = {p["id"]: p for p in data["paradigms"]}

    # === 1. Relations 更新 ===

    # P1: 追加 7本
    paradigms["P1"]["relations"] = [
        ["Fs-31", "Fs-71", 0.8],
        ["Fs-31", "Fs-34", 0.7],
        ["Fs-19", "Ps-1", 0.6],
        ["Fs-71", "Ps-5", 0.8],
        ["Fs-31", "Ps-6", 0.8],
        ["Fs-31", "Fs-83", 0.7],
        ["Fs-31", "M-3", 0.8],
        # 追加（ゲート辺）
        ["Fs-31", "Fs-60", 0.7],
        ["Fs-31", "Fs-61", 0.7],
        ["Fs-31", "M-4", 0.7],
        ["Fs-19", "M-1", 0.7],
        # 追加（横辺）
        ["Fs-23", "Fs-24", 0.7],
        ["Fs-14", "Fs-3", 0.6],
        ["Fs-71", "Fs-75", 0.8],
    ]

    # P2: 追加 6本
    paradigms["P2"]["relations"] = [
        ["Fs-31", "Fs-71", 0.8],
        ["Fs-31", "Fs-34", 0.7],
        ["Fs-19", "Ps-1", 0.6],
        ["Fs-71", "Ps-5", 0.8],
        ["Fs-87", "Ps-6", 0.8],
        ["Fs-87", "Fs-82", 0.7],
        ["Fs-87", "Fs-83", 0.7],
        # 追加
        ["Fs-31", "Fs-60", 0.7],
        ["Fs-31", "Fs-61", 0.7],
        ["Fs-31", "M-4", 0.7],
        ["Fs-19", "M-1", 0.7],
        ["Fs-82", "Fs-87", 0.7],
        ["Fs-71", "Fs-75", 0.8],
    ]

    # P3: 全面更新（既存5本 + 追加9本）
    paradigms["P3"]["relations"] = [
        ["Fs-83", "Fs-84", 0.8],
        ["Fs-84", "Fs-86", 0.7],
        ["Fs-56", "Ps-4", 0.7],
        ["Fs-83", "Fs-31", 0.8],
        ["Fs-83", "Fs-87", 0.7],
        # 追加
        ["Fs-31", "Fs-83", 0.8],
        ["Fs-60", "Fs-61", 0.7],
        ["Fs-60", "Fs-62", 0.7],
        ["Fs-96", "Fs-100", 0.7],
        ["Fs-84", "M-4", 0.6],
        ["Fs-84", "Ft-20", 0.7],
        ["Fs-83", "Fs-56", 0.7],
        ["Fs-84", "D-4", 0.7],
        ["Fs-56", "Fs-98", 0.7],
    ]

    # P4: 追加 6本
    paradigms["P4"]["relations"] = [
        ["Fs-83", "Fs-84", 0.8],
        ["Fs-84", "Fs-86", 0.7],
        ["Fs-56", "Ps-4", 0.7],
        ["Fs-83", "Fs-31", 0.8],
        ["Fs-83", "Fs-87", 0.7],
        ["M-4", "D-3", 0.8],
        ["M-4", "D-7", 0.8],
        ["D-3", "Fs-84", 0.8],
        ["D-7", "B-6", 0.7],
        ["M-4", "Fs-34", 0.8],
        ["D-3", "Fs-88", 0.8],
        # 追加
        ["Fs-31", "Fs-83", 0.8],
        ["Fs-60", "Fs-61", 0.7],
        ["Fs-14", "M-4", 0.7],
        ["Fs-14", "M-1", 0.7],
        ["Fs-96", "D-1", 0.7],
        ["D-3", "D-6", 0.7],
    ]

    # P5: 追加 2本
    paradigms["P5"]["relations"] = [
        ["Pt-1", "Ft-15", 0.9],
        ["Pt-1", "Ft-22", 0.9],
        ["Pt-2", "Ft-16", 0.9],
        ["Pt-3", "Pt-4", 0.9],
        ["Pt-3", "Ft-29", 0.8],
        ["Ft-28", "Pt-5", 0.9],
        ["Pt-1", "Fs-14", 0.8],
        ["Ft-15", "Fs-34", 0.9],
        ["Pt-3", "Fs-60", 0.9],
        ["Pt-3", "Fs-61", 0.9],
        ["Pt-3", "Fs-62", 0.9],
        ["Pt-3", "Fs-63", 0.9],
        ["M-4", "D-3", 0.8],
        ["M-4", "D-7", 0.8],
        ["D-3", "Fs-84", 0.8],
        # 追加
        ["Fs-14", "Ft-17", 0.7],
        ["D-3", "Ft-22", 0.8],
    ]

    # S1: 追加 5本
    paradigms["S1"]["relations"] = [
        ["Fs-31", "Fs-35", 0.7],
        ["Fs-19", "Ps-1", 0.6],
        ["Fs-31", "Ps-6", 0.8],
        ["Fs-31", "Fs-83", 0.7],
        ["Fs-31", "M-3", 0.8],
        # 追加
        ["Fs-31", "Fs-60", 0.7],
        ["Fs-31", "Fs-61", 0.7],
        ["Fs-35", "M-4", 0.7],
        ["Fs-19", "M-1", 0.7],
        ["Fs-35", "Fs-44", 0.6],
    ]

    # S2: 追加 5本
    paradigms["S2"]["relations"] = [
        ["Fs-96", "B-1", 0.7],
        ["Fs-31", "Fs-96", 0.7],
        ["Fs-31", "Ps-6", 0.8],
        ["Fs-31", "Fs-83", 0.7],
        ["Fs-31", "M-3", 0.8],
        # 追加
        ["Fs-31", "Fs-60", 0.7],
        ["Fs-31", "Fs-61", 0.7],
        ["B-1", "M-4", 0.7],
        ["Fs-19", "M-1", 0.7],
        ["B-1", "Fs-84", 0.6],
    ]

    # === 2. Neighbors 追加 ===
    neighbors_map = {
        "P1": ["P2", "S1"],
        "P2": ["P3", "S2"],
        "P3": ["P4"],
        "P4": ["P5"],
        "P5": [],
        "S1": ["P3"],
        "S2": ["P4"],
    }
    for pid, nbrs in neighbors_map.items():
        paradigms[pid]["neighbors"] = nbrs

    # === 3. P_pred 更新 ===

    # P3: Fs-96=0, Fs-14=1 追加
    p3_pred = {d: v for d, v in paradigms["P3"]["p_pred"]}
    p3_pred["Fs-96"] = 0
    p3_pred["Fs-14"] = 1
    paradigms["P3"]["p_pred"] = [[d, v] for d, v in p3_pred.items()]

    # P4: Fs-96=0, Fs-14=0 追加
    p4_pred = {d: v for d, v in paradigms["P4"]["p_pred"]}
    p4_pred["Fs-96"] = 0
    p4_pred["Fs-14"] = 0
    paradigms["P4"]["p_pred"] = [[d, v] for d, v in p4_pred.items()]

    # P5: Fs-14 を 0→1 に変更
    p5_pred = {d: v for d, v in paradigms["P5"]["p_pred"]}
    p5_pred["Fs-14"] = 1
    paradigms["P5"]["p_pred"] = [[d, v] for d, v in p5_pred.items()]

    # === 4. Question paradigms 更新 ===
    all_pids = ["P1", "P2", "P3", "P4", "P5", "S1", "S2"]
    questions = {q["id"]: q for q in data["questions"]}
    questions["q24"]["paradigms"] = all_pids
    questions["q27"]["paradigms"] = all_pids

    # === 5. init_question_ids 更新 ===
    data["init_question_ids"] = [
        "q01", "q02", "q03", "q04", "q05", "q06", "q07",
        "q21", "q23", "q24",
        "q34", "q36", "q37", "q38",
    ]

    # === 書き出し ===
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # サマリ表示
    for p in data["paradigms"]:
        nbrs = p.get("neighbors", [])
        print(f"  {p['id']}: p_pred={len(p['p_pred'])}, "
              f"relations={len(p['relations'])}, neighbors={nbrs}")
    print(f"init_question_ids: {data['init_question_ids']}")
    print(f"\n出力: {OUTPUT}")


if __name__ == "__main__":
    main()
