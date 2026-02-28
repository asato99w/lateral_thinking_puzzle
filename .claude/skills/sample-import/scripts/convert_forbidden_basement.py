"""25_形式化.md (禁じられた地下室フォーマット) を JSON に変換するスクリプト。

使い方:
  python convert_forbidden_basement.py --input <形式化.md> --output <出力.json> --title <タイトル> --statement <問題文>
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).parent.parent.parent.parent  # .claude/skills/sample-import/scripts/ → repo root
DATA_DIR = PROJ_ROOT / "app" / "poc" / "data"

DEFAULT_INPUT = PROJ_ROOT / "samples" / "005_禁じられた地下室" / "01_20260227_統合アルゴリズム適用" / "25_形式化.md"
DEFAULT_OUTPUT = DATA_DIR / "forbidden_basement.json"
DEFAULT_TITLE = "禁じられた地下室"
DEFAULT_STATEMENT = "絶対に開けてはいけないと言われていた地下室のドアを開けた女性。中に入って見たものに驚き、すぐに警察に駆け込んだ。しかし地下室の中には何も異常なものはなかった。"


def parse_descriptors(text: str) -> list[dict]:
    """記述素一覧セクションから全記述素を抽出する。"""
    descriptors = []
    # セクション1の全テーブル行をスキャン
    section_match = re.search(r"## 1\. 記述素一覧(.*?)## 2\.", text, re.DOTALL)
    if not section_match:
        raise ValueError("記述素一覧セクションが見つかりません")
    section = section_match.group(1)
    for line in section.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 2:
            did, label = parts
            # ヘッダー行・区切り行をスキップ
            if did in ("ID", "id") or did.startswith("-"):
                continue
            if re.match(r"[A-Z][a-z]?-\d+", did):
                descriptors.append({"id": did, "label": label})
    return descriptors


def parse_paradigms(text: str) -> list[dict]:
    """パラダイムセクションから全パラダイムを抽出する。"""
    paradigms = []
    # パラダイムごとに分割（### P で始まるセクション）
    # 「## 2. パラダイム」の後、「## 3.」の前まで
    section_match = re.search(r"## 2\. パラダイム(.*?)## 3\.", text, re.DOTALL)
    if not section_match:
        raise ValueError("パラダイムセクションが見つかりません")
    section = section_match.group(1)
    paradigm_sections = re.split(r"(?=### P\d+:)", section)

    for ps in paradigm_sections:
        # ヘッダー行を解析
        header = re.match(r"### (P\d+):\s*(.+)", ps)
        if not header:
            continue
        pid = header.group(1)
        pname = header.group(2).strip()

        # depth
        depth_match = re.search(r"\*\*depth\*\*:\s*(\d+|null)", ps)
        depth = int(depth_match.group(1)) if depth_match and depth_match.group(1) != "null" else None

        # shift_threshold
        st_match = re.search(r"\*\*shift_threshold\*\*:\s*(\d+|null)", ps)
        shift_threshold = int(st_match.group(1)) if st_match and st_match.group(1) != "null" else None

        # neighbors
        nb_match = re.search(r"\*\*neighbors\*\*:\s*\{([^}]*)\}", ps)
        neighbors = []
        if nb_match:
            neighbors = [x.strip() for x in nb_match.group(1).split(",") if x.strip()]

        # p_pred(d)=1
        pred_1_ids = []
        pred_1_match = re.search(r"#### p_pred\(d\)=1\s*\n\s*\n(.+?)(?:\n\s*\n|\n####|\n---)", ps, re.DOTALL)
        if pred_1_match:
            id_text = pred_1_match.group(1).strip()
            pred_1_ids = [x.strip() for x in id_text.split(",") if x.strip()]

        # p_pred(d)=0
        pred_0_ids = []
        pred_0_match = re.search(r"#### p_pred\(d\)=0\s*\n\s*\n(.+?)(?:\n\s*\n|\n####|\n---)", ps, re.DOTALL)
        if pred_0_match:
            id_text = pred_0_match.group(1).strip()
            pred_0_ids = [x.strip() for x in id_text.split(",") if x.strip()]

        # p_pred をリスト形式に組み立て
        p_pred = []
        for did in pred_1_ids:
            p_pred.append([did, 1])
        for did in pred_0_ids:
            p_pred.append([did, 0])

        # relations
        relations = []
        rel_match = re.search(r"#### R\(P\d+\)\s*\n(.*?)(?:\n---|\Z)", ps, re.DOTALL)
        if rel_match:
            rel_section = rel_match.group(1)
            for line in rel_section.split("\n"):
                line = line.strip()
                if not line.startswith("|"):
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 3 and not parts[0].startswith("-") and parts[0] not in ("source",):
                    try:
                        relations.append([parts[0], parts[1], float(parts[2])])
                    except ValueError:
                        continue

        paradigm = {
            "id": pid,
            "name": pname,
            "p_pred": p_pred,
            "relations": relations,
        }
        if shift_threshold is not None:
            paradigm["shift_threshold"] = shift_threshold

        paradigms.append(paradigm)

    return paradigms


def parse_questions(text: str) -> list[dict]:
    """質問一覧セクションから全質問を抽出する。"""
    questions = []
    # セクション3以降を取得
    section_match = re.search(r"## 3\. 質問一覧(.*)", text, re.DOTALL)
    if not section_match:
        raise ValueError("質問一覧セクションが見つかりません")
    section = section_match.group(1)

    # q-XX ごとに分割
    q_sections = re.split(r"(?=### q-\d+)", section)
    for qs in q_sections:
        header = re.match(r"### (q-\d+)", qs)
        if not header:
            continue

        # テーブルから項目→値のマッピングを構築
        fields = {}
        for line in qs.split("\n"):
            line = line.strip()
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 2 and parts[0] not in ("項目", "---"):
                if not parts[0].startswith("-"):
                    fields[parts[0]] = parts[1]

        qid = fields.get("id", header.group(1))

        # ans_yes: [(Fs-54, 1), (Fs-60, 1)] → [["Fs-54", 1], ["Fs-60", 1]]
        ans_yes = parse_tuple_list(fields.get("ans_yes", "[]"))
        ans_no = parse_tuple_list(fields.get("ans_no", "[]"))
        ans_irrelevant = parse_simple_list(fields.get("ans_irrelevant", "[]"))
        prerequisites = parse_simple_list(fields.get("prerequisites", "[]"))
        related_descriptors = parse_simple_list(fields.get("related_descriptors", "[]"))
        paradigms_list = parse_simple_list(fields.get("paradigms", "[]"))

        q = {
            "id": qid,
            "text": fields.get("text", ""),
            "correct_answer": fields.get("correct_answer", ""),
            "ans_yes": ans_yes,
            "ans_no": ans_no,
            "ans_irrelevant": ans_irrelevant,
            "is_clear": fields.get("is_clear", "false").lower() == "true",
            "prerequisites": prerequisites,
            "related_descriptors": related_descriptors,
            "topic_category": fields.get("topic_category", ""),
            "paradigms": paradigms_list,
        }
        questions.append(q)

    return questions


def parse_tuple_list(s: str) -> list:
    """[(Fs-54, 1), (Fs-60, 0)] → [["Fs-54", 1], ["Fs-60", 0]]"""
    s = s.strip()
    if s == "[]":
        return []
    result = []
    pairs = re.findall(r"\(([A-Za-z][\w-]+),\s*(\d+)\)", s)
    for did, val in pairs:
        result.append([did, int(val)])
    return result


def parse_simple_list(s: str) -> list:
    """[Fs-54:0, M-1:1] → ["Fs-54:0", "M-1:1"] or [Fs-1, Fs-2] → ["Fs-1", "Fs-2"] or [] → []"""
    s = s.strip()
    if s == "[]":
        return []
    # prerequisites format: Fs-54:0 or simple IDs
    items = re.findall(r"[A-Za-z][\w-]+(?::\d+)?", s)
    return items


def main():
    parser = argparse.ArgumentParser(description="禁じられた地下室の形式化ファイルを JSON に変換する")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title", type=str, default=DEFAULT_TITLE)
    parser.add_argument("--statement", type=str, default=DEFAULT_STATEMENT)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")

    # 1. 記述素の解析
    descriptors = parse_descriptors(text)
    all_descriptor_ids = [d["id"] for d in descriptors]
    print(f"all_descriptor_ids: {len(all_descriptor_ids)} 件")

    # Ps の値を抽出（全て 1 = 問題文に記述された事実）
    ps_values = [[d["id"], 1] for d in descriptors if d["id"].startswith("Ps-")]
    print(f"ps_values: {len(ps_values)} 件")

    # 2. パラダイムの解析
    paradigms = parse_paradigms(text)
    print(f"paradigms: {len(paradigms)} 件")
    for p in paradigms:
        pred_1 = sum(1 for x in p["p_pred"] if x[1] == 1)
        pred_0 = sum(1 for x in p["p_pred"] if x[1] == 0)
        unknown = len(all_descriptor_ids) - pred_1 - pred_0
        print(f"  {p['id']}: p_pred=1:{pred_1} 0:{pred_0} unknown:{unknown}, relations={len(p['relations'])}")

    # 3. 質問の解析
    questions = parse_questions(text)
    print(f"questions: {len(questions)} 件")

    yes_count = sum(1 for q in questions if q["correct_answer"] == "yes")
    no_count = sum(1 for q in questions if q["correct_answer"] == "no")
    irr_count = sum(1 for q in questions if q["correct_answer"] == "irrelevant")
    print(f"  yes={yes_count}, no={no_count}, irrelevant={irr_count}")

    clear_qs = [q["id"] for q in questions if q.get("is_clear")]
    print(f"  clear questions: {clear_qs}")

    # init_question_ids: prerequisites が空の質問
    init_question_ids = [q["id"] for q in questions if not q.get("prerequisites")]
    print(f"  init_question_ids ({len(init_question_ids)}): {init_question_ids}")

    # topic_categories
    topic_categories = {}
    for q in questions:
        if q.get("topic_category"):
            topic_categories[q["id"]] = q["topic_category"]
    print(f"topic_categories: {len(topic_categories)} 件")

    # Q(P) の自動計算: 質問の effect がパラダイムのアノマリーを含む場合、その質問を Q(P) に追加
    # 加えて、safe 質問（effect が P の予測と矛盾しない）も P に割り当てる
    # → 結果として全質問が全パラダイムに割り当てられる。prerequisites が実質的なゲーティングを担う。
    paradigm_ids = [p["id"] for p in paradigms]
    for q in questions:
        if not q.get("paradigms") or q["paradigms"] == []:
            q["paradigms"] = paradigm_ids[:]
    print(f"Q(P) 自動計算: 全質問を全パラダイムに割当（prerequisites によるゲーティング）")

    # JSON 構築
    result = {
        "title": args.title,
        "statement": args.statement,
        "init_paradigm": "P1",
        "truth_paradigm": paradigm_ids[-1],  # 最終パラダイム = T
        "ps_values": ps_values,
        "all_descriptor_ids": all_descriptor_ids,
        "paradigms": paradigms,
        "topic_categories": topic_categories,
        "questions": questions,
        "init_question_ids": init_question_ids,
    }

    # 検証: 各パラダイムの p_pred に含まれる ID が all_descriptor_ids に存在するか
    all_ids_set = set(all_descriptor_ids)
    errors = []
    for p in paradigms:
        for did, val in p["p_pred"]:
            if did not in all_ids_set:
                errors.append(f"  {p['id']}: p_pred に不明な ID '{did}'")
        for src, tgt, w in p["relations"]:
            if src not in all_ids_set:
                errors.append(f"  {p['id']}: relation source に不明な ID '{src}'")
            if tgt not in all_ids_set:
                errors.append(f"  {p['id']}: relation target に不明な ID '{tgt}'")

    # 検証: 各質問の effect に含まれる ID が all_descriptor_ids に存在するか
    for q in questions:
        for did, val in q["ans_yes"]:
            if did not in all_ids_set:
                errors.append(f"  {q['id']}: ans_yes に不明な ID '{did}'")
        for did, val in q["ans_no"]:
            if did not in all_ids_set:
                errors.append(f"  {q['id']}: ans_no に不明な ID '{did}'")

    if errors:
        print(f"\n検証エラー ({len(errors)} 件):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("\n検証: OK（不明な ID なし）")

    # 出力
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n出力: {args.output}")


if __name__ == "__main__":
    main()
