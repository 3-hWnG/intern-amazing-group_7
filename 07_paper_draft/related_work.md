> Sinh tự động từ `latex/sections/related.tex` ngày 28/10/2026 để đọc trên GitHub. Bản chuẩn là LaTeX; muốn sửa thì sửa tệp `.tex`.

## 2. Related Work

**Vietnamese public-service and legal question answering.** Pham Duy and Le Thanh retrieve legal passages for public-service questions from the portal's pages of frequently asked questions with BM25+, a contrastive PhoBERT encoder and a cross-encoder, reporting retrieval metrics[7]. ViGPTQA trains Vietnamese instruction-following LLMs for question answering, including law[9], and Hien *et al.* combine vector retrieval over 45,000 legal documents with an LLM[10]; their system routes out-of-scope questions to experts, but this step is not evaluated. None measures refusal on real citizen questions.

**Abstention and out-of-scope detection.** Selective classification trades coverage for risk[11]; unanswerable questions caused a large drop for strong SQuAD readers[12]; a trained calibrator helps a reader abstain under domain shift[5]; on CLINC150, intent classifiers that do well in scope struggle to flag out-of-scope queries[6]. A survey covers abstention in LLMs[4], and clarifying questions are a third option between answering and refusing[13].

**Who decides.** In retrieval-augmented generation (RAG)[14], Self-RAG and corrective RAG, the model or a retrieval evaluator decides what to do[15,16]; programmable guardrails let developer-written rails decide instead[17]. In e-government, a governance pipeline escalates to humans[2], and a benchmark finds that answering correctly does not imply acknowledging what one does not know[3]. LLMs can outperform crowd workers at text annotation[18].
