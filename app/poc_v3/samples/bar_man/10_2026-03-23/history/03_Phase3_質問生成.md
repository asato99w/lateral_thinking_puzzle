# Phase 3: 質問生成

## 生成した質問（19問、全て「はい」回答）

| ID | 対象 | 質問概要 | mechanism |
|---|---|---|---|
| QT1 | IM1 | 銃は男にとって良い結果？ | anomaly |
| QT2 | IM2 | 水は喉の渇き以外の理由？ | observation |
| QT3 | KRB1 | 困りごとを抱えていた？ | observation |
| QT4 | IM3 | 水と困りごとは関係？ | link |
| QT5 | KRB2 | 水で困りごと解消と思った？ | link |
| QT6 | IM4 | 助けるつもりで銃？ | observation |
| QT7 | IM5 | 男の様子から助けが必要と判断？ | link |
| QT8 | KRA1 | 身体的な異変？ | observation |
| QT9 | IM6 | 異変は周りが気づけるもの？ | observation |
| QT10 | KRA2 | バーテンダーは異変に気づいた？ | observation |
| QT11 | IM7 | 目的は異変の解消？ | link |
| QT12 | KRA3 | 銃で異変に対処？ | link |
| QT13 | IM8 | 対処は成功？ | observation |
| QT14 | KRB3 | 困りごとは解消？ | observation |
| QT15 | IM9 | ありがとうは困りごと解消への感謝？ | link |
| QT16 | KRB4 | 銃の理由を理解していた？ | observation |
| QT17 | FPC1 | 要素Aのまとめ確認 | link |
| QT18 | FPC2 | 要素Bのまとめ確認 | link |
| QT19 | FP | 全体のまとめ確認 | link |

## 探索パス（3パス検証済み）
1. B軸優先: 水の理由 → 困りごと → バーテンダー側
2. A軸優先: バーテンダーの意図 → 異変 → 水の理由
3. 交互: B軸とA軸を交互に進行
