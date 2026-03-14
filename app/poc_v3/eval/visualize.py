"""data_src.json の構造を可視化する HTML を生成する"""

import json
import re
import sys
import html
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_html(data: dict) -> str:
    title = data.get("title", "Puzzle")

    # --- Extract structures ---
    propositions = {p["id"]: p for p in data.get("propositions", [])}
    questions = {q["id"]: q for q in data.get("questions", [])}
    s_props = {s["id"]: s for s in data.get("_phase3", {}).get("s_propositions", [])}
    tactical_chains = data.get("_phase3", {}).get("tactical_chains", [])
    division_props = data.get("_phase2", {}).get("division_propositions", [])
    division_hierarchy = data.get("_phase2", {}).get("division_hierarchy", [])
    models = data.get("_phase1", {}).get("models", [])
    tensions = data.get("_phase1", {}).get("tensions", [])
    chain_branches = data.get("_phase9", {}).get("chain_branches", [])
    chain_mapping = data.get("_phase4", {}).get("chain_mapping", {})
    exploration_paths = data.get("_phase4", {}).get("exploration_paths", [])
    chain_extensions = data.get("_phase5", {}).get("chain_extensions", [])
    chain_designs = data.get("_phase6", {}).get("chain_designs", [])
    generated = data.get("_phase9", {}).get("generated", {})

    # --- Build Mermaid diagrams ---

    # Diagram 1: Proposition Derivation Flow (NF excluded)
    derivation_lines = _build_derivation_diagram(propositions, s_props)

    # Diagram 2: Question → Proposition Mapping
    q_lines = _build_question_diagram(questions, propositions)

    # Diagram 3: Model Division Hierarchy
    div_lines = _build_division_diagram(models, division_props, division_hierarchy)

    # Diagram 4: Chain Flow (parse description for intermediate steps)
    chain_lines = _build_chain_diagram(tactical_chains, chain_extensions, chain_designs)

    # Diagram 5: Chain Branches (Rejection Analysis)
    branch_lines = _build_branch_diagram(chain_branches, generated)

    # Diagram 6: Exploration Paths
    path_lines = _build_path_diagram(exploration_paths)

    # --- Integrity Summary ---
    integrity = _check_integrity(data, propositions, questions, s_props)

    # --- Build HTML ---
    return _render_html(
        title=title,
        derivation_diagram="\n".join(derivation_lines),
        question_diagram="\n".join(q_lines),
        division_diagram="\n".join(div_lines),
        chain_diagram="\n".join(chain_lines),
        branch_diagram="\n".join(branch_lines),
        path_diagram="\n".join(path_lines),
        integrity=integrity,
        data=data,
    )


def _build_derivation_diagram(propositions, s_props):
    lines = [
        "graph TD",
        "  classDef sNode fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
        "  classDef nNode fill:#fff3e0,stroke:#e65100,color:#bf360c",
        "  classDef pNode fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20",
        "  classDef tNode fill:#fce4ec,stroke:#c62828,color:#b71c1c",
        "  classDef uNode fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c",
        "  classDef fNode fill:#f5f5f5,stroke:#757575,color:#424242",
    ]

    # Pass 1: define all nodes
    for sp in s_props.values():
        sid = sp["id"]
        lines.append(f'  {sid}["{sid}: {_esc(sp["label"])}"]:::sNode')

    for pid, prop in propositions.items():
        lines.append(f'  {pid}["{pid}: {_esc(prop["label"])}"]:::{_node_class(pid)}')

    # Pass 2: define all edges
    for sp in s_props.values():
        sid = sp["id"]
        for parent in sp.get("derived_from", []):
            lines.append(f"  {parent} -.-> {sid}")

    for pid, prop in propositions.items():
        for fc_group in prop.get("formation_conditions") or []:
            if len(fc_group) == 1:
                lines.append(f"  {fc_group[0]} --> {pid}")
            else:
                jid = f"j_{pid}_{'_'.join(fc_group)}"
                lines.append(f"  {jid}(( ))")
                for src in fc_group:
                    lines.append(f"  {src} --> {jid}")
                lines.append(f"  {jid} --> {pid}")
    return lines


def _build_question_diagram(questions, propositions):
    lines = [
        "graph LR",
        "  classDef qNode fill:#e8eaf6,stroke:#283593,color:#1a237e",
        "  classDef nNode fill:#fff3e0,stroke:#e65100,color:#bf360c",
        "  classDef pNode fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20",
        "  classDef tNode fill:#fce4ec,stroke:#c62828,color:#b71c1c",
        "  classDef uNode fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c",
        "  classDef fNode fill:#f5f5f5,stroke:#757575,color:#424242",
    ]

    # Pass 1: define all nodes
    for qid, q in sorted(questions.items()):
        ans_mark = "O" if q["answer"] in ("はい", "yes") else "X"
        lines.append(f'  {qid}["{qid} {ans_mark}<br/>{_esc(q["text"])}"]:::qNode')
        for rev in q.get("reveals", []):
            prop = propositions.get(rev, {})
            rev_label = prop.get("label", rev)
            lines.append(f'  {rev}_q["{rev}: {_esc(rev_label)}"]:::{_node_class(rev)}')

    # Pass 2: define all edges
    for qid, q in sorted(questions.items()):
        for rev in q.get("reveals", []):
            lines.append(f"  {qid} -->|reveals| {rev}_q")
    return lines


def _build_division_diagram(models, division_props, division_hierarchy):
    lines = [
        "graph TD",
        "  classDef trueSet fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef falseSet fill:#ffcdd2,stroke:#c62828,color:#b71c1c",
        "  classDef propNode fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20",
    ]

    all_models_str = ", ".join(m["id"] for m in models)
    lines.append(f'  ALL["{_esc(all_models_str)}"]')

    dp_map = {dp["id"]: dp["label"] for dp in division_props}

    def render(nodes, parent_id):
        for node in nodes:
            pid = node["proposition_id"]
            ts = ", ".join(node["true_set"])
            fs = ", ".join(node["false_set"])
            label = dp_map.get(pid, pid)
            lines.append(f'  {pid}_div["{pid}: {_esc(label)}"]:::propNode')
            lines.append(f'  {pid}_true["T: {ts}"]:::trueSet')
            lines.append(f'  {pid}_false["F: {fs}"]:::falseSet')
            lines.append(f"  {parent_id} --> {pid}_div")
            lines.append(f"  {pid}_div -->|TRUE| {pid}_true")
            lines.append(f"  {pid}_div -->|FALSE| {pid}_false")
            if node.get("children"):
                render(node["children"], f"{pid}_true")

    render(division_hierarchy, "ALL")
    return lines


def _build_chain_diagram(tactical_chains, chain_extensions, chain_designs):
    """戦術連鎖の description から中間ステップを解析して描画する"""
    lines = [
        "graph TD",
        "  classDef srcNode fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
        "  classDef midNode fill:#fff3e0,stroke:#e65100,color:#bf360c",
        "  classDef tgtNode fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef extNode fill:#fce4ec,stroke:#c62828,color:#b71c1c",
        "  classDef uniNode fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c",
    ]

    for tc in tactical_chains:
        cid = tc["id"]
        tactic = tc.get("tactic", "")
        desc = tc.get("description", "")
        sources = tc.get("source", [])
        target = tc.get("target", "")

        lines.append(f'  subgraph {cid}["{cid}: {_esc(tactic)}"]')
        lines.append("    direction LR")

        # Parse description to extract steps: e.g.
        # "S13(水を求めた) →[常識的仮説の排除]→ N1a(喉の渇きではない) →[動機の探索]→ P1(困りごと)"
        # "{S5,S6}(銃+ありがとう) →[矛盾の指摘]→ N2a(銃は恩恵) →[因果の逆転]→ P1(困りごと)"
        step_nodes = _parse_chain_description(desc)

        if step_nodes:
            # Use parsed steps
            prev_nid = None
            for i, (node_id, node_label, edge_label) in enumerate(step_nodes):
                nid = f"{cid}_{node_id}"
                is_target = (node_id == target)
                cls = "tgtNode" if is_target else ("srcNode" if i == 0 else "midNode")
                display = f"{node_id}" if not node_label else f"{node_id}: {_esc(node_label)}"
                lines.append(f'    {nid}["{display}"]:::{cls}')
                if prev_nid:
                    if edge_label:
                        lines.append(f'    {prev_nid} -->|"{_esc(edge_label)}"| {nid}')
                    else:
                        lines.append(f"    {prev_nid} --> {nid}")
                prev_nid = nid
        else:
            # Fallback: show source → target with AND junction if multiple sources
            if len(sources) > 1:
                jid = f"{cid}_and"
                lines.append(f"    {jid}(( ))")
                for src in sources:
                    lines.append(f'    {cid}_{src}["{src}"]:::srcNode')
                    lines.append(f"    {cid}_{src} --> {jid}")
                lines.append(f'    {cid}_{target}["{target}"]:::tgtNode')
                lines.append(f"    {jid} --> {cid}_{target}")
            else:
                for src in sources:
                    lines.append(f'    {cid}_{src}["{src}"]:::srcNode')
                lines.append(f'    {cid}_{target}["{target}"]:::tgtNode')
                if sources:
                    lines.append(f"    {cid}_{sources[0]} --> {cid}_{target}")

        lines.append("  end")

    # Chain extensions (NT1 etc.)
    for ext in chain_extensions:
        props = ext.get("propositions", [])
        src_chain = ext.get("source_chain", "")
        note = ext.get("note", "")
        for p in props:
            lines.append(f'  {p}_ext["{p}: {_esc(note[:30])}"]:::extNode')
            lines.append(f"  {src_chain} --> {p}_ext")

    # Unique element chains (NU1 etc.)
    for cd in chain_designs:
        tgt = cd.get("target", "")
        note = cd.get("note", "")
        for p in cd.get("propositions", []):
            lines.append(f'  {p}_uni["{p}: {_esc(note[:30])}"]:::uniNode')
            # Connect from the extension it depends on
            lines.append(f"  NT1_ext --> {p}_uni")

    return lines


def _parse_chain_description(desc: str):
    """Parse chain description like:
    "S13(水を求めた) →[常識的仮説の排除]→ N1a(喉の渇きではない) →[動機の探索]→ P1(困りごと)"
    "{S5,S6}(銃+ありがとう) →[矛盾の指摘]→ N2a(銃は恩恵) →[因果の逆転]→ P1(困りごと)"

    Returns list of (node_id, short_label, edge_label_to_next)
    """
    if not desc:
        return []

    # Split by →[tactic]→ or just →
    # Pattern: node_part →[tactic]→ node_part → ...
    # First, extract all segments separated by → (with optional [tactic] in between)
    parts = re.split(r'\s*→\s*', desc)
    if len(parts) < 2:
        return []

    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if this is a tactic label [xxx]
        tactic_match = re.match(r'^\[(.+)\]$', part)
        if tactic_match:
            # Attach tactic as edge label to previous node
            if result:
                result[-1] = (result[-1][0], result[-1][1], tactic_match.group(1))
            continue

        # Parse node: "{S5,S6}(label)" or "N1a(label)" or just "P1"
        node_match = re.match(r'^\{?([A-Za-z0-9,\s]+)\}?\s*(?:\((.+?)\))?$', part)
        if node_match:
            node_ids_str = node_match.group(1).strip()
            label = node_match.group(2) or ""
            # For multi-source like "S5,S6", use combined ID
            node_ids = [n.strip() for n in node_ids_str.split(",")]
            if len(node_ids) > 1:
                combined_id = "_".join(node_ids)
                result.append((combined_id, f"{{{','.join(node_ids)}}}: {label}" if label else f"{{{','.join(node_ids)}}}", ""))
            else:
                result.append((node_ids[0], label, ""))

    return result


def _build_branch_diagram(chain_branches, generated):
    lines = [
        "graph TD",
        "  classDef trueNode fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef falseNode fill:#ffcdd2,stroke:#c62828,color:#b71c1c",
        "  classDef nfNode fill:#f5f5f5,stroke:#757575,color:#424242",
    ]

    gen_props = {g["id"]: g for g in generated.get("propositions", [])}

    for cb in chain_branches:
        cid = cb["chain_id"]
        lines.append(f'  subgraph {cid}_branch["{cid}: {_esc(cb.get("chain_path", ""))}"]')
        for br in cb.get("branches", []):
            step = br["at_step"]
            true_label = br.get("true_side_label", "")
            lines.append(f'    {cid}_{step}_t["T {step}: {_esc(true_label)}"]:::trueNode')
            for i, par in enumerate(br.get("parallels", [])):
                par_label = par.get("label", "")
                par_models = ", ".join(par.get("models", []))
                par_id = f"{cid}_{step}_f{i}"
                lines.append(f'    {par_id}["F {_esc(par_label)}<br/>({par_models})"]:::falseNode')
                lines.append(f"    {cid}_{step}_t --- {par_id}")

                for gp_id, gp in gen_props.items():
                    if (gp.get("source_chain") == cid
                            and gp.get("source_step") == step
                            and gp.get("parallel_index") == i):
                        lines.append(f'    {gp_id}_nf["{gp_id}"]:::nfNode')
                        lines.append(f"    {par_id} -.-> {gp_id}_nf")
        lines.append("  end")
    return lines


def _build_path_diagram(exploration_paths):
    lines = [
        "graph LR",
        "  classDef pathNode fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
    ]

    for idx, ep in enumerate(exploration_paths):
        name = ep.get("name", f"Path{idx}")
        seq = ep.get("sequence", "")
        # ASCII-safe subgraph ID
        sg_id = f"path_sg_{idx}"
        lines.append(f'  subgraph {sg_id}["{_esc(name)}"]')

        steps = seq.split(" → ")
        prev_nid = None
        for j, step in enumerate(steps):
            # Unique node ID per path per step
            nid = f"p{idx}s{j}"
            lines.append(f'    {nid}["{_esc(step)}"]:::pathNode')
            if prev_nid:
                lines.append(f"    {prev_nid} --> {nid}")
            prev_nid = nid
        lines.append("  end")
    return lines


def _node_class(node_id: str) -> str:
    if node_id.startswith("S"):
        return "sNode"
    if node_id.startswith("NF"):
        return "fNode"
    if node_id.startswith("NT"):
        return "tNode"
    if node_id.startswith("NU"):
        return "uNode"
    if node_id.startswith("N"):
        return "nNode"
    if node_id.startswith("P"):
        return "pNode"
    return "nNode"


def _esc(text: str) -> str:
    """Escape for Mermaid labels"""
    return text.replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;")


def _check_integrity(data, propositions, questions, s_props):
    issues = []
    ok = []

    # 1. All revealed propositions exist
    for qid, q in questions.items():
        for rev in q.get("reveals", []):
            if rev not in propositions:
                issues.append(f"Q {qid} reveals unknown proposition {rev}")
    if not any("reveals unknown" in i for i in issues):
        ok.append("全質問の reveals 先は全て propositions に存在")

    # 2. negation_of の対称性検証
    neg_issues = []
    for pid, prop in propositions.items():
        neg = prop.get("negation_of")
        if neg is not None:
            target = propositions.get(neg)
            if target is None:
                neg_issues.append(f"{pid}: negation_of '{neg}' が propositions に存在しない")
            elif target.get("negation_of") != pid:
                neg_issues.append(f"{pid}.negation_of={neg} だが {neg}.negation_of={target.get('negation_of')}（非対称）")
    if neg_issues:
        for ni in neg_issues:
            issues.append(ni)
    else:
        has_neg = any(prop.get("negation_of") for prop in propositions.values())
        if has_neg:
            ok.append("negation_of の対称性が保たれている")

    # 3. Formation conditions reference valid IDs
    all_ids = set(propositions.keys()) | set(s_props.keys())
    for pid, prop in propositions.items():
        for fc_group in (prop.get("formation_conditions") or []):
            for ref in fc_group:
                if ref not in all_ids:
                    issues.append(f"Proposition {pid}: fc が未知の {ref} を参照")
    if not any("fc が未知" in i for i in issues):
        ok.append("全命題の formation_conditions の参照先が存在")

    # 4. Model coverage completeness
    coverage = data.get("_phase9", {}).get("coverage", {})
    uncovered = coverage.get("uncovered", [])
    if uncovered:
        issues.append(f"カバーされていないモデル: {uncovered}")
    else:
        all_m = coverage.get("all_models", [])
        ok.append(f"全モデル ({len(all_m)}個) がカバー済み")

    # 5. Duplicate initial_confirmed
    top_ic = data.get("initial_confirmed", [])
    phase3_ic = data.get("_phase3", {}).get("initial_confirmed", [])
    if top_ic and phase3_ic:
        if set(top_ic) == set(phase3_ic):
            issues.append("initial_confirmed がトップレベルと _phase3 で重複（実害なし、データ冗長）")
        else:
            issues.append("initial_confirmed がトップレベルと _phase3 で不一致")

    # 6. Clear conditions consistency
    cc = data.get("clear_conditions", [])
    p6_cc = data.get("_phase6", {}).get("clear_conditions", [])
    if cc and p6_cc and cc == p6_cc:
        ok.append("clear_conditions がトップレベルと _phase6 で一致")
    elif cc and p6_cc and cc != p6_cc:
        issues.append("clear_conditions がトップレベルと _phase6 で不一致")

    # 7. reveals single element check
    multi_reveals = []
    for qid, q in questions.items():
        rev = q.get("reveals", [])
        if len(rev) != 1:
            multi_reveals.append(f"{qid}: reveals が {len(rev)} 要素")
    if multi_reveals:
        for m in multi_reveals:
            issues.append(m)
    else:
        ok.append("全質問の reveals が単一要素（1質問1命題）")

    return {"issues": issues, "ok": ok}


def _normalize_conds(conds):
    return sorted([sorted(g) for g in conds])


def _render_html(*, title, derivation_diagram, question_diagram, division_diagram,
                 chain_diagram, branch_diagram, path_diagram, integrity, data):
    issues_html = ""
    for issue in integrity["issues"]:
        issues_html += f'<li class="issue">&#9888; {html.escape(issue)}</li>\n'
    for ok_item in integrity["ok"]:
        issues_html += f'<li class="ok">&#10003; {html.escape(ok_item)}</li>\n'

    n_props = len(data.get("propositions", []))
    n_questions = len(data.get("questions", []))
    n_s = len(data.get("_phase3", {}).get("s_propositions", []))
    n_chains = len(data.get("_phase3", {}).get("tactical_chains", []))
    n_models = len(data.get("_phase1", {}).get("models", []))
    n_tensions = len(data.get("_phase1", {}).get("tensions", []))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{html.escape(title)} data_src</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #fafafa; color: #333; padding: 20px; }}
  h1 {{ font-size: 1.6em; margin-bottom: 10px; }}
  h2 {{ font-size: 1.2em; margin: 20px 0 10px; padding: 8px 12px;
       background: #e3f2fd; border-left: 4px solid #1565c0; border-radius: 2px; }}
  .stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0; }}
  .stat {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 6px;
           padding: 10px 16px; min-width: 120px; }}
  .stat .num {{ font-size: 1.8em; font-weight: bold; color: #1565c0; }}
  .stat .label {{ font-size: 0.85em; color: #666; }}
  .tabs {{ display: flex; gap: 4px; margin: 16px 0 0; border-bottom: 2px solid #e0e0e0; }}
  .tab {{ padding: 8px 16px; cursor: pointer; background: #f5f5f5;
          border: 1px solid #e0e0e0; border-bottom: none; border-radius: 6px 6px 0 0;
          font-size: 0.9em; user-select: none; }}
  .tab.active {{ background: #fff; border-bottom: 2px solid #fff; margin-bottom: -2px;
                 font-weight: bold; color: #1565c0; }}
  .tab-content {{ background: #fff; border: 1px solid #e0e0e0;
                  border-top: none; padding: 16px; overflow-x: auto; }}
  .tab-content.hidden {{ display: none; }}
  .mermaid {{ text-align: center; }}
  ul.checks {{ list-style: none; padding: 8px 0; }}
  ul.checks li {{ padding: 4px 8px; font-size: 0.9em; }}
  li.issue {{ color: #e65100; }}
  li.ok {{ color: #2e7d32; }}
  .legend {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 8px 0; font-size: 0.8em; }}
  .legend-item {{ display: flex; align-items: center; gap: 4px; }}
  .legend-swatch {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid #999; }}
  .note {{ font-size: 0.85em; color: #666; margin-bottom: 8px; }}
</style>
</head>
<body>

<h1>{html.escape(title)} — data_src.json</h1>

<div class="stats">
  <div class="stat"><div class="num">{n_tensions}</div><div class="label">tension</div></div>
  <div class="stat"><div class="num">{n_models}</div><div class="label">model</div></div>
  <div class="stat"><div class="num">{n_s}</div><div class="label">S prop</div></div>
  <div class="stat"><div class="num">{n_props}</div><div class="label">proposition</div></div>
  <div class="stat"><div class="num">{n_questions}</div><div class="label">question</div></div>
  <div class="stat"><div class="num">{n_chains}</div><div class="label">chain</div></div>
</div>

<div class="legend">
  <div class="legend-item"><div class="legend-swatch" style="background:#e3f2fd"></div> S</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#fff3e0"></div> N</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#e8f5e9"></div> P</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#fce4ec"></div> NT</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#f3e5f5"></div> NU</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#f5f5f5"></div> NF</div>
</div>

<div class="tabs">
  <div class="tab active" data-tab="derivation">derivation</div>
  <div class="tab" data-tab="questions">Q -&gt; prop</div>
  <div class="tab" data-tab="division">model split</div>
  <div class="tab" data-tab="chains">chain</div>
  <div class="tab" data-tab="branches">branch / NF</div>
  <div class="tab" data-tab="paths">path</div>
  <div class="tab" data-tab="integrity">integrity</div>
</div>

<div id="derivation" class="tab-content">
<h2>formation_conditions</h2>
<p class="note">
  S -&gt; N -&gt; P -&gt; NT -&gt; NU. Solid = fc, dotted = S derived_from.
  Junction = AND. Multiple arrows to same node = OR.
</p>
<pre class="mermaid">
{derivation_diagram}
</pre>
</div>

<div id="questions" class="tab-content">
<h2>Q -&gt; proposition (reveals)</h2>
<p class="note">O = yes, X = no</p>
<pre class="mermaid">
{question_diagram}
</pre>
</div>

<div id="division" class="tab-content">
<h2>model division hierarchy</h2>
<pre class="mermaid">
{division_diagram}
</pre>
</div>

<div id="chains" class="tab-content">
<h2>tactical chains</h2>
<p class="note">C1-C5 + extensions. Parsed from _phase3 description.</p>
<pre class="mermaid">
{chain_diagram}
</pre>
</div>

<div id="branches" class="tab-content">
<h2>chain branches / rejection (_phase9)</h2>
<p class="note">T = true side, F = false side (parallel). Dotted = generated NF proposition.</p>
<pre class="mermaid">
{branch_diagram}
</pre>
</div>

<div id="paths" class="tab-content">
<h2>exploration paths</h2>
<pre class="mermaid">
{path_diagram}
</pre>
</div>

<div id="integrity" class="tab-content">
<h2>integrity check</h2>
<ul class="checks">
{issues_html}
</ul>
</div>

<script>
  // Initialize mermaid - render all diagrams while all tabs visible
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose',
    flowchart: {{ htmlLabels: true, curve: 'basis' }}
  }});

  // After mermaid renders, hide non-active tabs
  window.addEventListener('load', function() {{
    setTimeout(function() {{
      var tabs = document.querySelectorAll('.tab-content');
      for (var i = 1; i < tabs.length; i++) {{
        tabs[i].classList.add('hidden');
      }}
    }}, 500);
  }});

  // Tab switching
  document.querySelectorAll('.tab').forEach(function(tab) {{
    tab.addEventListener('click', function() {{
      document.querySelectorAll('.tab-content').forEach(function(el) {{
        el.classList.add('hidden');
      }});
      document.querySelectorAll('.tab').forEach(function(el) {{
        el.classList.remove('active');
      }});
      var target = tab.getAttribute('data-tab');
      document.getElementById(target).classList.remove('hidden');
      tab.classList.add('active');
    }});
  }});
</script>

</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize.py <data_src.json> [output.html]")
        sys.exit(1)

    src_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else str(
        Path(src_path).parent / "visualization.html"
    )

    data = load_data(src_path)
    html_content = build_html(data)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated: {out_path}")


if __name__ == "__main__":
    main()
