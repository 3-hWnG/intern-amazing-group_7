# Khoá bộ real_v2 System 3 (24/10/2026)

Khoá trước mọi thay đổi code của đợt sửa câu khó. Từ đây **không sửa** câu hỏi và nhãn theo kết quả của hệ thống; cần chỉnh thì làm bộ mới. Câu hỏi đã commit riêng trước khi gán nhãn (`a82d970`).

| File | sha256 |
|---|---|
| `eval/real_v2/cases_real_v2.json` (348 câu hỏi, chưa nhãn) | `3f0be29f85343d09aa5ace03cf69c5153e6803f0f15f1ce2115d5db3a005663b` |
| `eval/real_v2/real_v2_labels.json` (nhãn cuối, 348 câu) | `b3f5afa3b5a098f760a8847e330ef271ac7727a85f887d709ae4b041a66ec23e` |
| `eval/real_v2/cases_real_v2_labeled.json` (bộ để chạy, 313 câu) | `2edce334b8a0d6e33fe2bcf741056fd0a909c1708573450970402d7f236cd821` |

Dữ liệu tra khi gán nhãn và để chạy: thủ tục **bản 3** (1.517 thủ tục), `content_sha256` `70c42af175762bb5e91616ecf9f07cdef218ac557b195e7e00898bdafdaa36bd`; `data/snapshot/procedures_v3.jsonl` sha256 `60aea05f28daef36c7fef550d64470f1fc8633b817f3e0e4c5361ab4e0106b30`.

Bộ chạy: 313 câu (`answer` 59, `clarify` 6, `apologize` 248); 35 câu `skip` bị loại. Một lượt gán nhãn (người gán = người sửa hệ thống); xem giới hạn ở `README.md`.
