"""v6 data_src.json の構造を可視化する HTML を生成する

v6 固有の構造（descriptors, entailment_conditions, _phase1.derivation_graph 等）に対応。
"""

import json
import html as html_mod
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_s_prop(pid: str) -> bool:
    """S命題かどうか判定（D-S*, S* 両形式対応）"""
    return pid.startswith("D-S") or (pid.startswith("S") and len(pid) > 1 and pid[1:].isdigit())


def _reveals_list(q: dict) -> list:
    """reveals を常にリストとして返す（str/list 両対応）"""
    r = q.get("reveals", [])
    if isinstance(r, str):
        return [r] if r else []
    return r


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _short(text: str, n: int = 40) -> str:
    return text[:n] + "..." if len(text) > n else text


def build_html(data: dict) -> str:
    title = data.get("title", "Puzzle")
    descriptors = {d["id"]: d for d in data.get("descriptors", data.get("propositions", []))}
    questions = {q["id"]: q for q in data.get("questions", [])}
    initial_confirmed = set(data.get("initial_confirmed", []))
    phase1 = data.get("_phase1", {})
    phase2 = data.get("_phase2", {})

    # --- Stats ---
    n_desc = len(descriptors)
    n_q = len(questions)
    n_ic = len(initial_confirmed)
    n_ec = sum(1 for d in descriptors.values() if d.get("entailment_conditions"))
    n_fc = sum(1 for d in descriptors.values() if d.get("formation_conditions"))
    n_neg = sum(1 for d in descriptors.values() if d.get("negation_of"))

    # --- Diagram 1: EC/FC flow ---
    ec_fc_diagram = _build_ec_fc_diagram(descriptors, initial_confirmed)

    # --- Diagram 2: Phase 1 derivation graph ---
    deriv_diagram = _build_phase1_derivation_diagram(phase1)

    # --- Diagram 3: Questions ---
    q_diagram = _build_question_diagram(questions, descriptors)

    # --- Diagram 4: Competing models ---
    models_diagram = _build_models_diagram(phase1)

    # --- Diagram 5: Chains ---
    chains_diagram = _build_chains_diagram(phase2)

    # --- Game simulation ---
    game_html = _build_game_simulation(data)

    # --- Descriptor table ---
    desc_table = _build_descriptor_table(descriptors, initial_confirmed, questions)

    return _render_html(
        title=title,
        n_desc=n_desc, n_q=n_q, n_ic=n_ic, n_ec=n_ec, n_fc=n_fc, n_neg=n_neg,
        ec_fc_diagram=ec_fc_diagram,
        deriv_diagram=deriv_diagram,
        q_diagram=q_diagram,
        models_diagram=models_diagram,
        chains_diagram=chains_diagram,
        game_html=game_html,
        desc_table=desc_table,
    )


def _build_ec_fc_diagram(descriptors, initial_confirmed):
    """EC/FC の導出関係を Mermaid で描画"""
    lines = [
        "graph TD",
        "  classDef ic fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
        "  classDef ec fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef fc fill:#fff3e0,stroke:#e65100,color:#bf360c",
        "  classDef neg fill:#fce4ec,stroke:#c62828,color:#b71c1c",
        "  classDef fp fill:#ffeb3b,stroke:#f57f17,color:#333",
    ]

    # S 命題はまとめて 1 ノード
    s_ids = sorted([d for d in initial_confirmed if _is_s_prop(d)])
    lines.append(f'  S_GROUP["S命題 ({len(s_ids)}個)"]:::ic')

    # 非S命題を描画
    for did, d in sorted(descriptors.items()):
        if _is_s_prop(did):
            continue
        label = _short(d.get("label", did), 35)
        ec = d.get("entailment_conditions")
        fc = d.get("formation_conditions")
        neg = d.get("negation_of")

        if did == "FP":
            cls = "fp"
        elif neg:
            cls = "neg"
        elif ec:
            cls = "ec"
        elif fc:
            cls = "fc"
        elif did in initial_confirmed:
            cls = "ic"
        else:
            cls = "ic"
        lines.append(f'  {_safe_id(did)}["{_esc(did)}: {_esc(label)}"]:::{cls}')

    # EC edges (solid, green)
    for did, d in descriptors.items():
        if _is_s_prop(did):
            continue
        for group in d.get("entailment_conditions") or []:
            sources = []
            for src in group:
                if _is_s_prop(src):
                    sources.append("S_GROUP")
                elif src in descriptors:
                    sources.append(_safe_id(src))
            if len(sources) == 1:
                lines.append(f"  {sources[0]} ==> {_safe_id(did)}")
            elif len(sources) > 1:
                jid = f"j_ec_{_safe_id(did)}"
                lines.append(f"  {jid}(( ))")
                for s in sources:
                    lines.append(f"  {s} ==> {jid}")
                lines.append(f"  {jid} ==> {_safe_id(did)}")

    # FC edges (dashed, orange)
    for did, d in descriptors.items():
        if _is_s_prop(did):
            continue
        if d.get("negation_of"):
            continue  # skip H*/NF* for clarity
        for group in d.get("formation_conditions") or []:
            sources = []
            for src in group:
                if _is_s_prop(src):
                    sources.append("S_GROUP")
                elif src in descriptors:
                    sources.append(_safe_id(src))
            if len(sources) == 1:
                lines.append(f"  {sources[0]} -.-> {_safe_id(did)}")
            elif len(sources) > 1:
                jid = f"j_fc_{_safe_id(did)}"
                lines.append(f"  {jid}(( ))")
                for s in sources:
                    lines.append(f"  {s} -.-> {jid}")
                lines.append(f"  {jid} -.-> {_safe_id(did)}")

    return "\n".join(lines)


def _build_phase1_derivation_diagram(phase1):
    """Phase 1 の導出グラフを描画"""
    dg_raw = phase1.get("derivation_graph", {})
    if not dg_raw:
        return "graph TD\n  empty[No derivation_graph]"

    # Handle both flat dict and {"nodes": {...}} formats
    dg = dg_raw.get("nodes", dg_raw) if isinstance(dg_raw, dict) else dg_raw
    # Filter out non-node keys like "description"
    dg = {k: v for k, v in dg.items() if isinstance(v, dict)}

    lines = [
        "graph TD",
        "  classDef fp fill:#ffeb3b,stroke:#f57f17,color:#333",
        "  classDef fpc fill:#ce93d8,stroke:#6a1b9a,color:#fff",
        "  classDef comp fill:#81d4fa,stroke:#0277bd,color:#000",
        "  classDef ca fill:#a5d6a7,stroke:#2e7d32,color:#000",
    ]

    for nid, node in dg.items():
        label = node.get("label", nid)
        short = _short(label, 40)
        if nid == "FP":
            cls = "fp"
        elif nid.startswith("FPC"):
            cls = "fpc"
        elif node.get("type") == "共通抽象":
            cls = "ca"
        else:
            cls = "comp"
        lines.append(f'  {_safe_id(nid)}["{_esc(nid)}: {_esc(short)}"]:::{cls}')

    for nid, node in dg.items():
        for child in node.get("derives", []):
            if child in dg:
                lines.append(f"  {_safe_id(nid)} --> {_safe_id(child)}")

    return "\n".join(lines)


def _build_question_diagram(questions, descriptors):
    """質問 → 命題のマッピング"""
    lines = [
        "graph LR",
        "  classDef yes fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef no fill:#ffcdd2,stroke:#c62828,color:#b71c1c",
        "  classDef prop fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
    ]

    for qid, q in sorted(questions.items()):
        ans = q.get("answer", "")
        mark = "O" if ans in ("はい", "yes") else "X"
        cls = "yes" if mark == "O" else "no"
        text = _short(q.get("text", ""), 30)
        prereqs = q.get("prerequisites", [])
        prereq_str = f"<br/>prereqs: {','.join(prereqs)}" if prereqs else ""
        cat = q.get("topic_category", "")
        cat_str = f"<br/>[{_esc(cat)}]" if cat else ""
        lines.append(f'  {qid}["{_esc(qid)} {mark}: {_esc(text)}{cat_str}{prereq_str}"]:::{cls}')

        for rev in _reveals_list(q):
            d = descriptors.get(rev, {})
            rev_label = _short(d.get("label", rev), 25)
            lines.append(f'  {qid}_{rev}["{_esc(rev)}: {_esc(rev_label)}"]:::prop')
            lines.append(f"  {qid} --> {qid}_{rev}")

    return "\n".join(lines)


def _build_models_diagram(phase1):
    """競合モデルを描画"""
    cm = phase1.get("competing_models", {})
    if not cm:
        return "graph TD\n  empty[No competing_models]"

    lines = ["graph TD",
             "  classDef elemA fill:#bbdefb,stroke:#1565c0,color:#000",
             "  classDef elemB fill:#c8e6c9,stroke:#2e7d32,color:#000",
             "  classDef model fill:#fff3e0,stroke:#e65100,color:#000"]

    elements = phase1.get("elements", {})
    for elem_key, elem in elements.items():
        eid = f"elem_{elem_key}"
        cls = "elemA" if elem_key == "A" else "elemB"
        elem_label = _short(elem.get("label", ""), 40)
        lines.append(f'  {eid}["{_esc(elem_key)}: {_esc(elem_label)}"]:::{cls}')

    for elem_key, models in cm.items():
        eid = f"elem_{elem_key}"
        for m in models:
            mid = _safe_id(m["id"])
            lines.append(f'  {mid}["{_esc(m["id"])}: {_esc(m["label"])}"]:::model')
            lines.append(f"  {eid} --> {mid}")

    return "\n".join(lines)


def _build_chains_diagram(phase2):
    """戦術連鎖を描画"""
    chains = phase2.get("chains", phase2.get("chain_mapping", {}))
    if not chains:
        return "graph TD\n  empty[No chains in _phase2]"

    lines = ["graph TD",
             "  classDef src fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
             "  classDef mid fill:#fff3e0,stroke:#e65100,color:#bf360c",
             "  classDef tgt fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20"]

    for cid, chain in chains.items():
        target = chain.get("target", "")
        desc = chain.get("description", cid)
        steps = chain.get("steps", [])
        intermediates = chain.get("intermediates", [s["output"] for s in steps])

        lines.append(f'  subgraph {_safe_id(cid)}["{_esc(cid)}: {_esc(desc)}"]')
        lines.append("    direction LR")

        # Show intermediates → target
        prev = None
        for i, inter in enumerate(intermediates):
            nid = f"{_safe_id(cid)}_{_safe_id(inter)}"
            lines.append(f'    {nid}["{_esc(inter)}"]:::mid')
            if prev:
                lines.append(f"    {prev} --> {nid}")
            prev = nid

        tgt_nid = f"{_safe_id(cid)}_{_safe_id(target)}"
        lines.append(f'    {tgt_nid}["{_esc(target)}"]:::tgt')
        if prev:
            lines.append(f"    {prev} --> {tgt_nid}")

        lines.append("  end")

    return "\n".join(lines)


def _build_game_simulation(data):
    """Python エンジンを使ったゲームシミュレーション（テキスト）"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from engine import load_puzzle, init_game, available_questions, answer_question, check_complete

        # Use data.json alongside data_src.json if available
        src_path = data.get("_src_path", "")
        data_json = Path(src_path).parent / "data.json" if src_path else None
        if data_json and data_json.exists():
            puzzle = load_puzzle(str(data_json))
        else:
            # Fallback: write temp file
            tmp = Path(__file__).resolve().parent / "_tmp_vis.json"
            cleaned = {k: v for k, v in data.items() if not k.startswith("_")}
            if "S" in cleaned and "statement" not in cleaned:
                cleaned["statement"] = cleaned.pop("S")
            if "T" in cleaned and "truth" not in cleaned:
                cleaned["truth"] = cleaned.pop("T")
            if "id" not in cleaned and "title" in cleaned:
                cleaned["id"] = cleaned["title"]
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, ensure_ascii=False)
            puzzle = load_puzzle(str(tmp))
            tmp.unlink(missing_ok=True)

        rows = []
        state = init_game(puzzle)
        rows.append(f"<tr><td>Start</td><td>-</td>"
                     f"<td>confirmed: {len(state.confirmed)}, derived: {len(state.derived)}</td>"
                     f"<td>{', '.join(sorted(state.derived))}</td></tr>")

        step = 0
        while not check_complete(state, puzzle) and step < 20:
            step += 1
            avail = available_questions(state, puzzle)
            if not avail:
                rows.append(f"<tr><td>{step}</td><td colspan='3'>STUCK: no available questions</td></tr>")
                break
            avail_ids = sorted([q.id for q in avail])
            yes_qs = [q for q in avail if q.answer in ("はい", "yes")]
            q = yes_qs[0] if yes_qs else avail[0]
            result = answer_question(state, q, puzzle)
            done = check_complete(state, puzzle)
            status = " COMPLETE" if done else ""
            rows.append(
                f"<tr><td>{step}{status}</td>"
                f"<td>{html_mod.escape(q.id)}: {html_mod.escape(q.text)}<br/>"
                f"<small>avail: {', '.join(avail_ids)}</small></td>"
                f"<td>+confirmed: {', '.join(result.new_confirmed)}</td>"
                f"<td>+derived: {', '.join(result.new_derived)}</td></tr>"
            )

        return "\n".join(rows)
    except Exception as e:
        return f"<tr><td colspan='4'>Simulation error: {html_mod.escape(str(e))}</td></tr>"


def _build_descriptor_table(descriptors, initial_confirmed, questions):
    """全命題の一覧表"""
    # Build reverse map: which question reveals which prop
    reveals_map = {}
    for qid, q in questions.items():
        for rev in _reveals_list(q):
            reveals_map.setdefault(rev, []).append(qid)

    rows = []
    for did in sorted(descriptors.keys()):
        d = descriptors[did]
        label = html_mod.escape(d.get("label", ""))
        ec = d.get("entailment_conditions")
        fc = d.get("formation_conditions")
        neg = d.get("negation_of", "")
        ic = "IC" if did in initial_confirmed else ""
        ec_str = html_mod.escape(str(ec)) if ec else ""
        fc_str = html_mod.escape(str(fc)) if fc else ""
        rev_qs = ", ".join(reveals_map.get(did, []))
        kind = ""
        if _is_s_prop(did):
            kind = "S"
        elif did.startswith("NF"):
            kind = "NF"
        elif did.startswith("H"):
            kind = "H"
        elif did.startswith("FPC"):
            kind = "FPC"
        elif did == "FP":
            kind = "FP"
        elif ec:
            kind = "EC"
        elif fc:
            kind = "FC"

        rows.append(
            f"<tr><td>{html_mod.escape(did)}</td><td>{kind}</td>"
            f"<td>{label}</td><td>{ic}</td>"
            f"<td><small>{ec_str}</small></td><td><small>{fc_str}</small></td>"
            f"<td>{html_mod.escape(neg)}</td><td>{rev_qs}</td></tr>"
        )
    return "\n".join(rows)


def _safe_id(text: str) -> str:
    return text.replace("-", "_").replace(" ", "_")


def _render_html(*, title, n_desc, n_q, n_ic, n_ec, n_fc, n_neg,
                 ec_fc_diagram, deriv_diagram, q_diagram, models_diagram,
                 chains_diagram, game_html, desc_table):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{html_mod.escape(title)} — v6 Visualization</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #fafafa; color: #333; padding: 20px; max-width: 1400px; margin: 0 auto; }}
  h1 {{ font-size: 1.5em; margin-bottom: 12px; }}
  .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }}
  .stat {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 6px;
           padding: 8px 14px; min-width: 90px; text-align: center; }}
  .stat .num {{ font-size: 1.6em; font-weight: bold; color: #1565c0; }}
  .stat .label {{ font-size: 0.8em; color: #666; }}
  .tabs {{ display: flex; gap: 3px; margin: 16px 0 0; border-bottom: 2px solid #e0e0e0; flex-wrap: wrap; }}
  .tab {{ padding: 6px 14px; cursor: pointer; background: #f5f5f5;
          border: 1px solid #e0e0e0; border-bottom: none; border-radius: 6px 6px 0 0;
          font-size: 0.85em; user-select: none; white-space: nowrap; }}
  .tab.active {{ background: #fff; border-bottom: 2px solid #fff; margin-bottom: -2px;
                 font-weight: bold; color: #1565c0; }}
  .panel {{ background: #fff; border: 1px solid #e0e0e0; border-top: none; padding: 16px;
            overflow-x: auto; display: none; }}
  .panel.active {{ display: block; }}
  .mermaid {{ text-align: center; overflow-x: auto; }}
  h2 {{ font-size: 1.1em; margin: 0 0 10px; padding: 6px 10px;
       background: #e3f2fd; border-left: 3px solid #1565c0; border-radius: 2px; }}
  .note {{ font-size: 0.82em; color: #666; margin-bottom: 8px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.82em; }}
  th, td {{ border: 1px solid #e0e0e0; padding: 4px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f5f5f5; font-weight: 600; position: sticky; top: 0; }}
  tr:nth-child(even) {{ background: #fafafa; }}
  .legend {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 8px 0; font-size: 0.8em; }}
  .legend-item {{ display: flex; align-items: center; gap: 3px; }}
  .swatch {{ width: 14px; height: 14px; border-radius: 3px; border: 1px solid #999; }}
  .game-table {{ max-height: 500px; overflow-y: auto; }}
  .game-table td {{ font-size: 0.82em; }}
  small {{ color: #888; }}
</style>
</head>
<body>

<h1>{html_mod.escape(title)} — v6 data_src</h1>

<div class="stats">
  <div class="stat"><div class="num">{n_desc}</div><div class="label">descriptors</div></div>
  <div class="stat"><div class="num">{n_q}</div><div class="label">questions</div></div>
  <div class="stat"><div class="num">{n_ic}</div><div class="label">initial</div></div>
  <div class="stat"><div class="num">{n_ec}</div><div class="label">EC props</div></div>
  <div class="stat"><div class="num">{n_fc}</div><div class="label">FC props</div></div>
  <div class="stat"><div class="num">{n_neg}</div><div class="label">negation</div></div>
</div>

<div class="legend">
  <div class="legend-item"><div class="swatch" style="background:#e3f2fd"></div> Initial/S</div>
  <div class="legend-item"><div class="swatch" style="background:#c8e6c9"></div> EC (confirmed chain)</div>
  <div class="legend-item"><div class="swatch" style="background:#fff3e0"></div> FC (hypothesis)</div>
  <div class="legend-item"><div class="swatch" style="background:#fce4ec"></div> Negation (NF/H)</div>
  <div class="legend-item"><div class="swatch" style="background:#ffeb3b"></div> FP</div>
  <div class="legend-item">━━ EC edge</div>
  <div class="legend-item">╌╌ FC edge</div>
</div>

<div class="tabs">
  <div class="tab active" data-tab="ecfc">EC/FC Flow</div>
  <div class="tab" data-tab="deriv">Phase1 Graph</div>
  <div class="tab" data-tab="questions">Questions</div>
  <div class="tab" data-tab="models">Models</div>
  <div class="tab" data-tab="chains">Chains</div>
  <div class="tab" data-tab="game">Game Sim</div>
  <div class="tab" data-tab="table">All Props</div>
</div>

<div id="ecfc" class="panel active">
  <h2>EC/FC 導出フロー</h2>
  <p class="note">太線(━━) = entailment (confirmed→confirmed, chain可), 破線(╌╌) = formation (confirmed→derived, 1回)</p>
  <pre class="mermaid">
{ec_fc_diagram}
  </pre>
</div>

<div id="deriv" class="panel">
  <h2>Phase 1: 導出グラフ</h2>
  <p class="note">FP → FPC → 構成要素 → 共通抽象。黄=FP, 紫=FPC, 青=構成要素, 緑=共通抽象</p>
  <pre class="mermaid">
{deriv_diagram}
  </pre>
</div>

<div id="questions" class="panel">
  <h2>質問 → 命題マッピング</h2>
  <p class="note">O=はい, X=いいえ. 緑=はい質問, 赤=いいえ質問</p>
  <pre class="mermaid">
{q_diagram}
  </pre>
</div>

<div id="models" class="panel">
  <h2>競合モデル（Phase 1）</h2>
  <pre class="mermaid">
{models_diagram}
  </pre>
</div>

<div id="chains" class="panel">
  <h2>戦術連鎖（Phase 2）</h2>
  <pre class="mermaid">
{chains_diagram}
  </pre>
</div>

<div id="game" class="panel">
  <h2>ゲームシミュレーション（自動プレイ）</h2>
  <p class="note">はい質問優先で自動プレイ</p>
  <div class="game-table">
  <table>
    <tr><th>Step</th><th>Question</th><th>+confirmed</th><th>+derived</th></tr>
    {game_html}
  </table>
  </div>
</div>

<div id="table" class="panel">
  <h2>全命題一覧</h2>
  <div style="max-height:600px; overflow-y:auto;">
  <table>
    <tr><th>ID</th><th>Kind</th><th>Label</th><th>IC</th><th>EC</th><th>FC</th><th>neg_of</th><th>Qs</th></tr>
    {desc_table}
  </table>
  </div>
</div>

<script>
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose',
    flowchart: {{ htmlLabels: true, curve: 'basis', useMaxWidth: false, nodeSpacing: 25, rankSpacing: 50 }},
    themeVariables: {{ fontSize: '13px' }}
  }});

  // Render mermaid in active panel only (on demand)
  async function renderPanel(id) {{
    var panel = document.getElementById(id);
    var elems = panel.querySelectorAll('.mermaid:not([data-processed])');
    for (var el of elems) {{
      el.setAttribute('data-processed', 'true');
      var code = el.textContent.trim();
      try {{
        var {{ svg }} = await mermaid.render('mermaid_' + id + '_' + Math.random().toString(36).slice(2), code);
        el.innerHTML = svg;
      }} catch(e) {{
        el.innerHTML = '<pre style="color:red">Mermaid error: ' + e.message + '</pre><pre>' + code + '</pre>';
      }}
    }}
  }}

  // Initial render
  renderPanel('ecfc');

  // Tab switching
  document.querySelectorAll('.tab').forEach(function(tab) {{
    tab.addEventListener('click', function() {{
      document.querySelectorAll('.panel').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
      var target = tab.getAttribute('data-tab');
      document.getElementById(target).classList.add('active');
      tab.classList.add('active');
      renderPanel(target);
    }});
  }});
</script>

</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_v6.py <data_src.json> [output.html]")
        sys.exit(1)

    src_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else str(
        Path(src_path).parent / "visualization.html"
    )

    data = load_data(src_path)
    data["_src_path"] = str(Path(src_path).resolve())
    html_content = build_html(data)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated: {out_path}")


if __name__ == "__main__":
    main()
