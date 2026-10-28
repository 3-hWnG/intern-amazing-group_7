> Sinh tự động từ `latex/sections/introduction.tex` ngày 28/10/2026 để đọc trên GitHub. Bản chuẩn là LaTeX; muốn sửa thì sửa tệp `.tex`.

## 1. Introduction

Many everyday administrative procedures in Vietnam are handled by commune-level offices: civil status, residence, identity cards, certified copies, social benefits. The National Public Service Portal publishes the record of each procedure[1], but citizens rarely ask in its language. They write letters with a greeting, a family story and abbreviations, often without diacritics, and many ask not how to carry out a procedure but about a file already submitted, a complaint, a fine, or the benefits of police officers. Answering these from procedure records gives confident but wrong guidance, which costs citizens time and trust[2,3].

The task is therefore a three-way decision before it is a retrieval problem: *answer* with one procedure, *clarify* when several fit, or *refuse*. Abstention is a known weak point of language models[4,5] and intent classifiers struggle with out-of-scope queries[6], yet prior work on Vietnamese public-service question answering evaluates only answerable questions[7].

This paper is an evaluation study of that decision on real citizen questions, for an assistant that covers only procedures handled at the commune level (communes, wards and special zones), not all administrative procedures in Vietnam, and that runs on one local machine so that questions need not leave the office[8]. Test sets are locked before the code they evaluate, and every configuration runs once and is reported. We find that:

- our team-written test set overstated performance: 79% of real questions are out of scope (88–92% in random samples), against 11%, and top-1 accuracy falls from 71.9% to 33.9%;

- a transparent rule layer closes much of the gap on two locked test sets, through an out-of-scope gate (refusals) and a citizen lexicon (answers) according to *post hoc* ablations, with no net change on the team-written set;

- a reranker, a local 4-billion-parameter large language model (LLM) and gates learned *post hoc* do not significantly improve balanced or end-to-end accuracy, and letting the model decide over retrieved procedures is no better than always refusing in balanced accuracy;

- a second round of rules that looked better on development ties the first on new questions, and on random traffic no configuration has more correct than wrong answers.
