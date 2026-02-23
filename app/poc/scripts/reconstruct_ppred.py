#!/usr/bin/env python3
"""
Reconstruct p_pred for turtle_soup.json paradigms.

Extends p_pred with predictions outside Conceivable to ensure:
  explained_o(P1) < explained_o(P2) < ... < explained_o(P5)

Design principles:
  1. Conceivable is NOT modified (tension preserved)
  2. Only ADD new p_pred entries (never modify existing)
  3. New entries are outside Conceivable (logical predictions)
  4. Deeper paradigms get more correct predictions
"""

import json
import sys
from pathlib import Path


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Saved to {path}")


def build_o_star(data):
    """Build O* (ground truth) from ps_values + all questions' correct effects."""
    o_star = {}
    for d_id, val in data["ps_values"]:
        o_star[d_id] = val
    for q in data["questions"]:
        ca = q["correct_answer"]
        if ca == "yes":
            effects = q["ans_yes"]
        elif ca == "no":
            effects = q["ans_no"]
        else:
            continue
        for d_id, val in effects:
            o_star[d_id] = val
    return o_star


def get_paradigm_ppred(paradigm_data):
    """d_plus/d_minus 形式から p_pred dict を構築。"""
    ppred = {}
    for d_id in paradigm_data["d_plus"]:
        ppred[d_id] = 1
    for d_id in paradigm_data["d_minus"]:
        ppred[d_id] = 0
    return ppred


def get_conceivable(paradigm_data):
    """d_plus ∪ d_minus = Conceivable."""
    return set(paradigm_data["d_plus"]) | set(paradigm_data["d_minus"])


def compute_explained_o(p_pred, o_star):
    count = 0
    for d_id, pred_val in p_pred.items():
        if d_id in o_star and o_star[d_id] == pred_val:
            count += 1
    return count


def compute_tension(p_pred, conceivable, o_star):
    tension = 0
    for d_id in conceivable:
        if d_id in p_pred and d_id in o_star:
            if p_pred[d_id] != o_star[d_id]:
                tension += 1
    return tension


def main():
    path = Path(__file__).resolve().parent.parent / "data" / "turtle_soup.json"
    data = load_data(path)
    o_star = build_o_star(data)

    true_count = sum(1 for v in o_star.values() if v == 1)
    false_count = sum(1 for v in o_star.values() if v == 0)
    print(f"O* size: {len(o_star)} (true: {true_count}, false: {false_count})")
    print()

    paradigms = {p["id"]: p for p in data["paradigms"]}

    # --- Print BEFORE state ---
    print("=== BEFORE ===")
    before_tensions = {}
    for pid in ["P1", "P2", "P3", "P4", "P5"]:
        p = paradigms[pid]
        ppred = get_paradigm_ppred(p)
        conc = get_conceivable(p)
        eo = compute_explained_o(ppred, o_star)
        tn = compute_tension(ppred, conc, o_star)
        before_tensions[pid] = tn
        print(f"  {pid}: |p_pred|={len(ppred)}, |conceivable|={len(conc)}, "
              f"explained_o={eo}, tension={tn}")
    print()

    # =============================================
    # Define addition layers
    # =============================================

    # Category A: Problem statement premises (O*=1)
    ps_additions = {f"Ps-{i}": 1 for i in range(1, 7)}

    # Category B: Red herring descriptors (O*=0)
    red_herring_additions = {f"Fs-{i:02d}": 0 for i in range(46, 61)}
    # Partial RH for P4 (7 of 15, enough for P4 > P3 in O*)
    red_herring_partial = {f"Fs-{i:02d}": 0 for i in range(46, 53)}

    # Category C: Graduated surface facts (O*=1)

    # Layer 1: Basic observable facts from the story
    surface_layer1 = {
        "Fs-01": 1,   # レストランの存在
        "Fs-03": 1,   # 一人で来店
        "Fs-05": 1,   # 特定の目的
        "Fs-07": 1,   # このレストランでなければ
        "Fs-17": 1,   # 味は重要
        "Fs-18": 1,   # 何かに気づいた
        "Fs-20": 1,   # 味に驚いた
        "Fs-21": 1,   # 一口は意図的
        "Fs-23": 1,   # スープの正体に疑問
        "Fs-32": 1,   # 店員は嘘をついていない
        "Fs-33": 1,   # 本物のウミガメのスープ
    }

    # Layer 2: Past experience and taste memory facts
    surface_layer2 = {
        "Fs-12": 1,   # 特別な思い入れ
        "Fs-14": 1,   # ウミガメのスープでなければ
        "Fs-19": 1,   # 味を確認するため
        "Fs-24": 1,   # 判別基準
        "Fs-25": 1,   # 過去の体験と関係
        "Fs-26": 1,   # 以前飲んだことがある
        "Fs-27": 1,   # 別の人が作った
        "Fs-28": 1,   # 不安
        "Fs-61": 1,   # 過去の体験が来店と関係
        "Ft-36": 1,   # 過去の記憶を確かめたかった
        "Ft-38": 1,   # 味覚の記憶
    }

    # Layer 3: Deception, dangerous past, emotional impact
    surface_layer3 = {
        "Ft-03": 1,   # 命の危険
        "Ft-01": 1,   # 船
        "Fs-39": 1,   # 自殺はレストランの出来事と関係
        "Fs-40": 1,   # スープで何かを知った
        "Fs-41": 1,   # 知った事実
        "Fs-42": 1,   # 絶望
        "Fs-43": 1,   # 耐えられない
        "Fs-44": 1,   # スープの一件がなければ
        "Ft-37": 1,   # 味が違った
        "Ft-22": 1,   # 騙された
    }

    # Layer 4: Survival details (starvation, companions, concealment)
    surface_layer4 = {
        "Ft-02": 1,   # 仲間がいた
        "Ft-07": 1,   # 遭難がなければ
        "Ft-09": 1,   # 食料に困った
        "Ft-10": 1,   # 救助が来なかった
        "Ft-11": 1,   # 極限状態
        "Ft-14": 1,   # 飢え
        "Ft-16": 1,   # 飢えで死亡
        "Ft-20": 1,   # 助けようとした
        "Ft-21": 1,   # 善意の嘘
        "Ft-24": 1,   # 本当のことなら飲まなかった
        "Ft-26": 1,   # 罪悪感
        "Ft-28": 1,   # 通常食べないもの
        "Ft-32": 1,   # 苦渋の決断
        "Ft-48": 1,   # 肉
        "Ft-50": 1,   # 危機的状況
        "Ft-51": 1,   # トラウマ
        "Pt-1": 1,    # 事故/遭難
        "Pt-2": 1,    # 食料不足
        "Pt-3": 1,    # 死亡
        "Pt-4": 1,    # スープを飲ませた
    }

    # Layer 5: Truth core (P5 already has these in conceivable)
    surface_layer5 = {
        "Ft-23": 1,   # 知らずに飲んだ
        "Ft-29": 1,   # 人間の肉
        "Ft-30": 1,   # 他に食料なし
        "Ft-31": 1,   # 生き延びるため
        "Ft-40": 1,   # 人肉だと悟った
        "Ft-42": 1,   # 人肉に耐えられなかった
        "Ft-43": 1,   # 騙されていた怒り
        "Pt-6": 1,    # 死んだ仲間の肉
    }

    # Additional correct O*=0 predictions (graduated)
    false_layer1 = {"B-02": 0}

    false_layer2 = {
        "Fs-62": 0,   # 戦争参加
        "Fs-63": 0,   # 犯罪
        "Ft-44": 0,   # 以前のスープはレストランで
    }

    false_layer3 = {
        "Ft-45": 0,   # 男が仲間を殺した
        "Ft-47": 0,   # 動物の肉
        "Ft-49": 0,   # 食用として一般的
    }

    # =============================================
    # Define per-paradigm addition sets
    # =============================================
    # P1: Problem premises only
    # P2: + red herrings + basic surface + some false
    # P3: + deeper surface (past experience) + more false
    # P4: + emotional/deception layer + survival details + all false
    # P5: + truth core (everything)

    # Strategy: Graduated additions ensuring O* monotonicity.
    # Each deeper paradigm gets all previous layers + its own.
    # Alignment (smaller p_pred = higher avg) selects the nearest paradigm.
    # The shift to P5 relies on P5's unique deep predictions becoming
    # observable during P4's phase (via questions opened by P4's conceivable).
    additions = {
        "P1": [ps_additions],
        "P2": [ps_additions, red_herring_additions,
               surface_layer1,
               false_layer1],
        "P3": [ps_additions, red_herring_additions,
               surface_layer1, surface_layer2,
               false_layer1, false_layer2],
        "P4": [ps_additions, red_herring_additions,
               surface_layer1, surface_layer2, surface_layer3, surface_layer4,
               false_layer1, false_layer2, false_layer3],
        "P5": [ps_additions, red_herring_additions,
               surface_layer1, surface_layer2, surface_layer3, surface_layer4,
               surface_layer5,
               false_layer1, false_layer2, false_layer3],
    }

    # =============================================
    # Apply additions
    # =============================================
    all_ids = set(data["all_descriptor_ids"])

    for pid in ["P1", "P2", "P3", "P4", "P5"]:
        p = paradigms[pid]
        ppred = get_paradigm_ppred(p)

        added = 0
        skipped_existing = 0
        skipped_invalid = 0

        for layer in additions[pid]:
            for d_id, val in layer.items():
                if d_id not in all_ids:
                    skipped_invalid += 1
                    continue
                if d_id in ppred:
                    skipped_existing += 1
                    continue
                ppred[d_id] = val
                added += 1

        # Convert to p_pred/conceivable format (engine-compatible)
        # Conceivable = original d_plus ∪ d_minus (NOT modified)
        original_conceivable = sorted(set(p["d_plus"]) | set(p["d_minus"]))
        p["p_pred"] = sorted([[d_id, val] for d_id, val in ppred.items()])
        p["conceivable"] = original_conceivable
        # Remove old format keys
        if "d_plus" in p:
            del p["d_plus"]
        if "d_minus" in p:
            del p["d_minus"]

        print(f"  {pid}: +{added} added, {skipped_existing} skipped(existing), "
              f"{skipped_invalid} skipped(invalid)")

    print()

    # --- Print AFTER state ---
    print("=== AFTER ===")
    results = {}
    for pid in ["P1", "P2", "P3", "P4", "P5"]:
        p = paradigms[pid]
        # Now in p_pred/conceivable format
        ppred = {d_id: val for d_id, val in p["p_pred"]}
        conc = set(p["conceivable"])
        eo = compute_explained_o(ppred, o_star)
        tn = compute_tension(ppred, conc, o_star)
        results[pid] = {"explained_o": eo, "tension": tn}
        print(f"  {pid}: |p_pred|={len(ppred)}, |conceivable|={len(conc)}, "
              f"explained_o={eo}, tension={tn}")
    print()

    # --- Validate ---
    all_ok = True

    # Check monotonicity
    pids = ["P1", "P2", "P3", "P4", "P5"]
    for i in range(len(pids) - 1):
        curr = results[pids[i]]["explained_o"]
        next_ = results[pids[i + 1]]["explained_o"]
        if curr >= next_:
            print(f"  FAIL: explained_o({pids[i]})={curr} >= "
                  f"explained_o({pids[i + 1]})={next_}")
            all_ok = False

    if all_ok:
        print("  OK: explained_o strictly increasing P1 < P2 < P3 < P4 < P5")

    # Check tension unchanged
    tension_ok = True
    for pid in pids:
        before_t = before_tensions[pid]
        after_t = results[pid]["tension"]
        if before_t != after_t:
            print(f"  FAIL: tension({pid}) changed: {before_t} -> {after_t}")
            tension_ok = False
            all_ok = False

    if tension_ok:
        print("  OK: tension unchanged for all paradigms")

    # Check conceivable subset of p_pred keys
    for pid in pids:
        p = paradigms[pid]
        ppred_keys = {d_id for d_id, _ in p["p_pred"]}
        conc = set(p["conceivable"])
        if not conc.issubset(ppred_keys):
            diff = sorted(conc - ppred_keys)
            print(f"  FAIL: {pid} conceivable has items not in p_pred: {diff}")
            all_ok = False

    # Convert S1, S2 to p_pred/conceivable format too
    for sid in ["S1", "S2"]:
        if sid in paradigms:
            s = paradigms[sid]
            if "d_plus" in s:
                s_ppred = {}
                for d_id in s["d_plus"]:
                    s_ppred[d_id] = 1
                for d_id in s["d_minus"]:
                    s_ppred[d_id] = 0
                s["conceivable"] = sorted(set(s["d_plus"]) | set(s["d_minus"]))
                s["p_pred"] = sorted([[d_id, val] for d_id, val in s_ppred.items()])
                del s["d_plus"]
                del s["d_minus"]
            print(f"  OK: {sid} converted to p_pred/conceivable format")

    print()
    if all_ok:
        save_data(data, path)
        print("All validations passed.")
    else:
        print("VALIDATION FAILED - file NOT saved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
