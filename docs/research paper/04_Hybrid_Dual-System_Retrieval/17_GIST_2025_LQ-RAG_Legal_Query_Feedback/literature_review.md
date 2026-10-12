# Literature Review: Legal Query RAG (LQ-RAG)

- **T├íc giß║ú:** Rahman S. M. Wahidur, Sumin Kim, Haeung Choi, David S. Bhatti, Heung-No Lee (GIST, South Korea)
- **N─âm xuß║Ñt bß║ún:** 2025 (Th├íng 2/2025)
- **Tß║íp ch├¡ / Hß╗Öi nghß╗ï:** *IEEE Access*, Volume 13, pp. 36978ΓÇô36994
- **Ph├ón loß║íi nghi├¬n cß╗⌐u:** Domain-Specific Legal RAG & Multi-Agent Recursive Feedback
- **Link Citation / DOI:** [https://doi.org/10.1109/ACCESS.2025.3542125](https://doi.org/10.1109/ACCESS.2025.3542125)
- **Tß╗çp to├án v─ân (PDF gß╗æc):** [`Legal_Query_RAG_IEEE_Access_2025.pdf`](Legal_Query_RAG_IEEE_Access_2025.pdf)
- **Thuß╗Öc nh├│m chuy├¬n ─æß╗ü:** Nh├│m 4: Truy Xuß║Ñt Lai & Hß╗ç Thß╗æng K├⌐p (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (C├óu hß╗Åi nghi├¬n cß╗⌐u & Vß║Ñn ─æß╗ü giß║úi quyß║┐t)
Hß╗ç thß╗æng hß╗Åi ─æ├íp AI trong l─⌐nh vß╗▒c ph├íp l├╜ th╞░ß╗¥ng gß║╖p tß╗╖ lß╗ç ß║úo gi├íc (hallucination) rß║Ñt cao (tß╗½ 58% ─æß║┐n 82%), dß╗» liß╗çu bß╗ï thi├¬n lß╗çch v├á suy luß║¡n ph├íp l├╜ phß╗⌐c tß║íp khiß║┐n c├íc m├┤ h├¼nh sinh v─ân bß║ún phß╗ò th├┤ng (nh╞░ GPT-4, Llama) dß╗à tr├¡ch dß║½n sai luß║¡t hoß║╖c bß╗ïa ─æß║╖t tiß╗ün lß╗ç.

B├ái b├ío giß║úi quyß║┐t trß╗▒c diß╗çn c├óu hß╗Åi: *L├ám thß║┐ n├áo ─æß╗â kß║┐t hß╗úp kß╗╣ thuß║¡t tinh chß╗ënh chuy├¬n s├óu (Fine-Tuning) v├á kiß║┐n tr├║c ─æa t├íc tß╗¡ phß║ún hß╗ôi ─æß╗ç quy (Recursive Feedback) nhß║▒m giß║úm thiß╗âu ß║úo gi├íc v├á n├óng cao ─æß╗Ö ch├¡nh x├íc cß╗ºa c├óu trß║ú lß╗¥i ph├íp l├╜?*

---

## 2. Methodology & Technical Architecture (Ph╞░╞íng ph├íp luß║¡n & Kiß║┐n tr├║c kß╗╣ thuß║¡t)
LQ-RAG ─æß╗ü xuß║Ñt kiß║┐n tr├║c 2 tß║ºng kß║┐t hß╗úp 4 th├ánh phß║ºn chuy├¬n biß╗çt:
1. **Tß║ºng Fine-Tuning (FT Layer):**
   - Tinh chß╗ënh m├┤ h├¼nh nh├║ng ph├íp l├╜ (**Legal Embedding LLM**) ─æß╗â cß║úi thiß╗çn khß║ú n─âng biß╗âu diß╗àn ngß╗» ngh─⌐a v├á cß║Ñu tr├║c ─æiß╗üu luß║¡t.
   - Tinh chß╗ënh m├┤ h├¼nh sinh (**Hybrid Fine-Tuned Generative LLM - HFM**) chuy├¬n biß╗çt cho v─ân phong v├á t╞░ duy lß║¡p luß║¡n ph├íp l├╜.
2. **Tß║ºng RAG ─æa t├íc tß╗¡ & Phß║ún hß╗ôi ─æß╗ç quy (Recursive Feedback):**
   - **Custom Audit/Evaluation Agent:** ─É├ính gi├í chß║Ñt l╞░ß╗úng c├óu trß║ú lß╗¥i v├á kiß╗âm tra ─æß╗Ö tin cß║¡y cß╗ºa chß╗⌐ng cß╗⌐ truy xuß║Ñt.
   - **Prompt Engineering Agent:** Tß╗▒ ─æß╗Öng ─æiß╗üu chß╗ënh prompt nß║┐u c├óu trß║ú lß╗¥i ch╞░a ─æß║ít chuß║⌐n kiß╗âm ─æß╗ïnh.
   - **V├▓ng lß║╖p ─æß╗ç quy:** Nß║┐u kiß╗âm ─æß╗ïnh ph├ít hiß╗çn thiß║┐u c─ân cß╗⌐ hoß║╖c sinh ß║úo gi├íc, hß╗ç thß╗æng gß╗¡i phß║ún hß╗ôi ─æß╗â tinh chß╗ënh lß║íi truy vß║Ñn v├á t├íi sinh ─æ├íp ├ín.

---

## 3. Empirical Results & Findings (Kß║┐t quß║ú thß╗▒c nghiß╗çm & Ph├ít hiß╗çn ch├¡nh)
- T─âng **23% ─æiß╗âm li├¬n quan** (relevance score) so vß╗¢i cß║Ñu h├¼nh RAG c╞í bß║ún (naive RAG).
- T─âng **14% hiß╗çu n─âng** so vß╗¢i RAG chß╗ë d├╣ng m├┤ h├¼nh LLM tinh chß╗ënh th├┤ng th╞░ß╗¥ng.
- M├┤ h├¼nh nh├║ng ph├íp l├╜ (Fine-Tuned Embedding) ─æß║ít mß╗⌐c cß║úi thiß╗çn **13% vß╗ü Hit Rate** v├á **15% vß╗ü Mean Reciprocal Rank (MRR)**.

---

## 4. Strengths & Limitations (╞»u ─æiß╗âm & Hß║ín chß║┐)
- **╞»u ─æiß╗âm (Strengths):** Kß║┐t hß╗úp chß║╖t chß║╜ giß╗»a Fine-tuning m├┤ h├¼nh nh├║ng v├á c╞í chß║┐ kiß╗âm to├ín tß╗▒ ─æß╗Öng (Audit Agent) vß╗¢i v├▓ng lß║╖p ─æß╗ç quy ─æß╗â chß║╖n ß║úo gi├íc.
- **Hß║ín chß║┐ (Limitations):** Chi ph├¡ t├¡nh to├ín v├á ─æß╗Ö trß╗à cao do c╞í chß║┐ phß║ún hß╗ôi nhiß╗üu v├▓ng lß║╖p; phß╗Ñ thuß╗Öc v├áo dß╗» liß╗çu ph├íp luß║¡t tiß║┐ng Anh/H├án Quß╗æc ─æ├ú g├ín nh├ún ─æß╗â tinh chß╗ënh.

---

## 5. Direct Relevance & Takeaways for V10.6 Project (├ünh xß║í tß╗¢i dß╗▒ ├ín V10.6)
- **─Éiß╗âm t╞░╞íng ─æß╗ông l├╜ thuyß║┐t:** ├¥ t╞░ß╗ƒng vß╗ü **Audit/Evaluation Agent** v├á kiß╗âm tra ch├⌐o t╞░╞íng ─æß╗ông vß╗¢i module **Fact Verifier & Grounding Guard (`verifier.py`)** trong V10.6. C╞í chß║┐ v├▓ng lß║╖p tinh chß╗ënh prompt t╞░╞íng ─æß╗ông vß╗¢i v├▓ng lß║╖p cß╗⌐u tß╗½ kh├│a nhiß╗üu l╞░ß╗út cß╗ºa LLM 1 (`RETRIEVAL_MAX_KEY_ATTEMPTS`).
- **Kh├íc biß╗çt cß╗æt l├╡i trong giß║úi ph├íp thß╗▒c tß║┐:** 
  - LQ-RAG giß║úi quyß║┐t ß║úo gi├íc bß║▒ng c├ích "cho m├┤ h├¼nh sinh ra rß╗ôi d├╣ng agent kh├íc ─æß╗ç quy kiß╗âm tra v├á sß╗¡a lß║íi" $\rightarrow$ dß║½n ─æß║┐n ─æß╗Ö trß╗à cao v├á vß║½n c├│ rß╗ºi ro m├┤ h├¼nh audit bß╗ï ß║úo gi├íc theo.
  - V10.6 ├íp dß╗Ñng giß║úi ph├íp thß╗▒c dß╗Ñng v├á triß╗çt ─æß╗â h╞ín: **UI Formatting Engine (Zero LLM)** ΓÇö to├án bß╗Ö th├┤ng tin lß╗ç ph├¡, th├ánh phß║ºn hß╗ô s╞í v├á thß╗¥i hß║ín ─æ╞░ß╗úc render trß╗▒c tiß║┐p 100% bß║▒ng code tß╗½ CSDL chuß║⌐n h├│a, ─æß║ít mß╗⌐c **0% hallucination** m├á kh├┤ng cß║ºn qua nhiß╗üu v├▓ng lß║╖p ─æß╗ç quy tß╗æn k├⌐m t├ái nguy├¬n.
