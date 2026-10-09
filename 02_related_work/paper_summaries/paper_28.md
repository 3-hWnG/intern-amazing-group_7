# Paper 28 Summary

## Citation

Tên bài: Constitutional AI: Harmlessness from AI Feedback
Tác giả: Yuntao Bai et al. (Anthropic)
Năm: 2022
Nguồn: arXiv:2212.08073
DOI/Link: https://arxiv.org/abs/2212.08073

## Problem

Mô hình ngôn ngữ có thể bị thao túng qua các kỹ thuật tấn công prompt (jailbreak) để đưa ra câu trả lời vi phạm quy tắc.

## Method

Ràng buộc hành vi của mô hình theo một bộ nguyên tắc hiến pháp cố định thông qua phản hồi từ AI.

## Dataset

Red-teaming Dialogues

## Evaluation

Harmfulness Reduction (90%)

## Results

Giảm 90% các phản hồi có hại mà không làm giảm tính hữu ích của câu trả lời.

## Limitations

Prompt hiến pháp dài làm tiêu tốn dung lượng context window.

## Relevance to our topic

Cơ sở thiết kế các lớp Guardrails an toàn trong system4/server/guard.py.

## Possible improvement

Sys_3_4 áp dụng bộ lọc quy tắc regex tiền kiểm để chặn đứng các câu lệnh tấn công trước khi gọi model.
