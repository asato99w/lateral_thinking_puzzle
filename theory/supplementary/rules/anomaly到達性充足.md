# anomaly 到達性充足

## 概要

各パラダイム P_i（シフト元となるもの）について、固有記述素からの同化連鎖によって anomaly を threshold 以上生成できることを保証する規則。

関係構造の構成 Rule 3 の定量的強化として位置づけられる。Rule 3 は「固有→共有の関係が存在すること」を要求するが、本規則は「anomaly 生成に十分な量であること」を要求する。

## 定義

- **E(P_i)**: P_i の固有記述素 = D(P_i) - ∪_{j≠i} D(P_j)
- **reachable(E(P_i), R(P_i))**: E(P_i) から R(P_i) の推移閉包で到達可能な記述素
- **opening_ds(q, P_i)**: 質問 q の effect のうち、到達可能かつ P_i が正しく予測する記述素
- **anomaly_ds(q, P_i)**: 質問 q の effect のうち、P_i の予測と真値が異なる記述素
- **Q_anomaly(P_i)**: opening_ds と anomaly_ds がともに空でない質問の集合
- **anomaly_upper_bound(P_i)**: Q_anomaly の anomaly 記述素の和集合の大きさ

## 形式的定義

```
opening_ds(q, P_i) = {d : (d, v) ∈ effect(q),
                       d ∈ reachable(E(P_i), R(P_i)),
                       prediction_i(d) == v}

anomaly_ds(q, P_i) = {d : (d, v) ∈ effect(q),
                       prediction_i(d) ≠ v,
                       prediction_i(d) ≠ None}

Q_anomaly(P_i) = {q : opening_ds(q, P_i) ≠ ∅ かつ anomaly_ds(q, P_i) ≠ ∅}

anomaly_upper_bound(P_i) = |⋃_{q ∈ Q_anomaly(P_i)} anomaly_ds(q, P_i)|
```

## 検証条件

```
∀ P_i ∈ メインパス（最終パラダイムを除く）:
  threshold(P_i) が定義されている場合:
    anomaly_upper_bound(P_i) >= threshold(P_i)
```

## 不充足時の対処

不充足の原因は以下の3つに分類され、連鎖的に依存する:

1. **固有記述素の不足**: |E(P_i)| が少なく到達の起点がない → 固有記述素の追加
2. **R(P) 接続性の不足**: 固有→共有の関係がなく到達できない → R(P) 関係の追加
3. **質問の不足**: 到達可能記述素はあるが anomaly 生成質問がない → 質問の追加

対処の順序: 1 → 2 → 3（1 が 2 の前提、2 が 3 の前提）

## 備考

- 本規則は opening_reach スクリプトの検証ロジックを理論的規則として定式化したもの
- 関係構造の構成 Rule 3 を包含する（anomaly 到達性が充足されれば、固有→共有の関係の存在は自動的に満たされる）
- S1 アルゴリズムの駆動条件および終了条件として使用される
