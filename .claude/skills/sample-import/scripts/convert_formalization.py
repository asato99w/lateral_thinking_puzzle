"""08_形式化.md を JSON に変換するスクリプト。

使い方:
  python convert_formalization.py --input <形式化.md> --output <出力.json> --title <タイトル> --statement <問題文>

引数を省略した場合はウミガメのスープのデフォルト値を使用する。
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).parent.parent.parent.parent  # .claude/skills/sample-import/scripts/ → repo root
DATA_DIR = PROJ_ROOT / "app" / "poc" / "data"

# デフォルト値（後方互換性）
DEFAULT_INPUT = PROJ_ROOT / "samples" / "001_ウミガメのスープ" / "09_20260219_統合アルゴリズム適用" / "08_形式化.md"
DEFAULT_OUTPUT = DATA_DIR / "turtle_soup.json"
DEFAULT_TITLE = "ウミガメのスープ"
DEFAULT_STATEMENT = "男がレストランに入り、ウミガメのスープを注文した。一口食べた男は店を出て、自殺した。なぜか？"


def parse_formalization(text: str) -> dict:
    result = {}

    # --- Section 1: ps_values ---
    ps_match = re.search(r"## 1\. 前提事実.*?\n\n((?:\|.*\n)+)", text)
    ps_values = []
    if ps_match:
        for line in ps_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("|") and not line.startswith("|-"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 2 and parts[0].startswith("Ps"):
                    ps_values.append([parts[0], int(parts[1])])
    result["ps_values"] = ps_values

    # --- Section 2: all_descriptor_ids ---
    ids_match = re.search(r"## 2\. 記述素 ID 一覧.*?\n\n(.*?)\n\n", text, re.DOTALL)
    if ids_match:
        ids_text = ids_match.group(1).strip()
        all_ids = [x.strip() for x in ids_text.split(",") if x.strip() and not x.strip().startswith("合計")]
        result["all_descriptor_ids"] = all_ids

    # --- Section 3: init_paradigm ---
    init_match = re.search(r"init_paradigm_id:\s*(\w+)", text)
    if init_match:
        result["init_paradigm"] = init_match.group(1)

    # --- Section 4: paradigms ---
    paradigms = []
    paradigm_pattern = re.compile(
        r"### (\w+)[:：]「(.+?)」\n\n"
        r"- id: (\w+)\n"
        r"- name: (.+?)\n",
        re.MULTILINE,
    )
    # Split by paradigm headers
    paradigm_sections = re.split(r"(?=### [PS]\d+[:：])", text)
    for section in paradigm_sections:
        m = paradigm_pattern.search(section)
        if not m:
            continue
        pid = m.group(3)
        pname = m.group(4)

        # Parse p_pred table
        ppred_match = re.search(r"\*\*p_pred:\*\*\n\n(?:\|.*\n){2}((?:\|.*\n)+)", section)
        p_pred = []
        if ppred_match:
            for line in ppred_match.group(1).strip().split("\n"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 2:
                    p_pred.append([parts[0], int(parts[1])])

        # Parse relations table
        rel_match = re.search(r"\*\*relations:\*\*\n\n(?:\|.*\n){2}((?:\|.*\n)*)", section)
        relations = []
        if rel_match:
            for line in rel_match.group(1).strip().split("\n"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 3:
                    relations.append([parts[0], parts[1], float(parts[2])])

        paradigms.append({
            "id": pid,
            "name": pname,
            "p_pred": p_pred,
            "relations": relations,
        })

    result["paradigms"] = paradigms

    # --- Section 5: topic_categories ---
    tc_match = re.search(r"## 5\. トピックカテゴリ一覧.*?\n\n((?:\|.*\n)+)", text)
    topic_categories = {}
    if tc_match:
        for line in tc_match.group(1).strip().split("\n"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 2 and not parts[0].startswith("-") and parts[0] not in ("ID", "id"):
                topic_categories[parts[0]] = parts[1]
    result["topic_categories"] = topic_categories

    # --- Section 6: questions ---
    questions = []
    q_sections = re.split(r"(?=### q\d+)", text)
    for qs in q_sections:
        qm = re.match(r"### (q\d+)\n", qs)
        if not qm:
            continue
        qid = qm.group(1)
        q = {"id": qid}

        # text
        tm = re.search(r"- text:\s*(.+)", qs)
        q["text"] = tm.group(1).strip() if tm else ""

        # ans_yes
        ay = re.search(r"- ans_yes:\s*(\[.+)", qs)
        q["ans_yes"] = parse_effect_list(ay.group(1)) if ay else []

        # ans_no
        an = re.search(r"- ans_no:\s*(\[.+)", qs)
        q["ans_no"] = parse_effect_list(an.group(1)) if an else []

        # ans_irrelevant
        ai = re.search(r"- ans_irrelevant:\s*(\[.+)", qs)
        q["ans_irrelevant"] = parse_id_list(ai.group(1)) if ai else []

        # correct_answer
        ca = re.search(r"- correct_answer:\s*(\w+)", qs)
        q["correct_answer"] = ca.group(1) if ca else ""

        # is_clear
        ic = re.search(r"- is_clear:\s*(\w+)", qs)
        q["is_clear"] = ic.group(1).lower() == "true" if ic else False

        # prerequisites
        pr = re.search(r"- prerequisites:\s*(\[.*?\])", qs)
        q["prerequisites"] = parse_id_list(pr.group(1)) if pr else []

        # related_descriptors
        rd = re.search(r"- related_descriptors:\s*(\[.+?\])", qs)
        q["related_descriptors"] = parse_id_list(rd.group(1)) if rd else []

        # topic_category
        tc = re.search(r"- topic_category:\s*(\w+)", qs)
        q["topic_category"] = tc.group(1) if tc else ""

        # paradigms
        pm = re.search(r"- paradigms:\s*(\[.*?\])", qs)
        q["paradigms"] = parse_id_list(pm.group(1)) if pm else []

        questions.append(q)

    result["questions"] = questions

    # --- Section 7: init_question_ids ---
    iq_match = re.search(r"init_question_ids:\s*(.+)", text)
    if iq_match:
        ids_text = iq_match.group(1).strip()
        result["init_question_ids"] = [x.strip() for x in ids_text.split(",") if x.strip()]

    return result


def parse_effect_list(s: str) -> list:
    """Parse [[Fs-01, 1], [Fs-02, 0]] into [["Fs-01", 1], ["Fs-02", 0]]"""
    result = []
    # Find all [ID, value] pairs
    pairs = re.findall(r"\[([A-Za-z][\w-]+),\s*(\d+)\]", s)
    for did, val in pairs:
        result.append([did, int(val)])
    return result


def parse_id_list(s: str) -> list:
    """Parse [Fs-01, Fs-02] into ["Fs-01", "Fs-02"], or [] into []"""
    s = s.strip()
    if s == "[]":
        return []
    # Find all descriptor IDs
    ids = re.findall(r"[A-Za-z][\w-]+", s)
    return ids


def main():
    parser = argparse.ArgumentParser(description="形式化ファイルを JSON に変換する")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="形式化ファイルのパス")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="出力 JSON ファイルのパス")
    parser.add_argument("--title", type=str, default=DEFAULT_TITLE,
                        help="パズルのタイトル")
    parser.add_argument("--statement", type=str, default=DEFAULT_STATEMENT,
                        help="問題文")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")
    data = parse_formalization(text)

    # Build result
    result = {
        "title": args.title,
        "statement": args.statement,
        "init_paradigm": data["init_paradigm"],
        "ps_values": data["ps_values"],
        "all_descriptor_ids": data["all_descriptor_ids"],
        "paradigms": data["paradigms"],
        "topic_categories": data["topic_categories"],
        "questions": data["questions"],
    }
    if "init_question_ids" in data:
        result["init_question_ids"] = data["init_question_ids"]

    # Validation summary
    print(f"ps_values: {len(result['ps_values'])} 件")
    print(f"all_descriptor_ids: {len(result['all_descriptor_ids'])} 件")
    print(f"paradigms: {len(result['paradigms'])} 件")
    for p in result["paradigms"]:
        print(f"  {p['id']}: p_pred={len(p['p_pred'])}, relations={len(p['relations'])}")
    print(f"topic_categories: {len(result['topic_categories'])} 件")
    print(f"questions: {len(result['questions'])} 件")

    # Count clear questions
    clear_qs = [q for q in result["questions"] if q.get("is_clear")]
    print(f"  clear questions: {[q['id'] for q in clear_qs]}")

    # Count answers
    yes_count = sum(1 for q in result["questions"] if q["correct_answer"] == "yes")
    no_count = sum(1 for q in result["questions"] if q["correct_answer"] == "no")
    irr_count = sum(1 for q in result["questions"] if q["correct_answer"] == "irrelevant")
    print(f"  yes={yes_count}, no={no_count}, irrelevant={irr_count}")

    if "init_question_ids" in result:
        print(f"  init_question_ids: {result['init_question_ids']}")

    # Write JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n出力: {args.output}")


if __name__ == "__main__":
    main()
