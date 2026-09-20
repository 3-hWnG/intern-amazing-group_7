# Ban do ma nguon / Codebase index

*Sinh tu dong ngay 2026-09-20 bang `Utility\scripts\make_index.py`. Dung sua tay - chay lai script.*

**Cach doc / How to read** — moi dong: `duong/dan (so_dong) - mo ta`, dong duoi la cac ky hieu chinh:
`f:ten@dong` = ham / function · `c:Ten@dong` = lop / class · `.ten@dong` = method cua lop ngay tren.

Mo dung cho: `Read file_path offset=<dong>`.


---

## Backend/

May chu: API, pipeline tra loi, CSDL, MCP search


**`Backend/api/`**

- `__init__.py` (1d)
- `auth_routes.py` (65d) - Đăng ký / đăng nhập / đăng xuất.
  `f:login_page@19  f:register@24  f:login@39  f:logout@53  f:me@63`
- `chat_routes.py` (269d) - Hội thoại nhiều cửa sổ + gửi câu hỏi qua hàng đợi.
  `f:list_conversations@56  f:create_conversation@61  f:get_conversation@66`
  `f:rename_conversation@91  f:delete_conversation@99  f:export_conversation@110`
  `f:export_all_conversations@124  f:message_evidence@138  f:get_profile@148`
  `f:clear_profile@153  f:chat@199  f:feedback@251  f:queue_status@262`
- `deps.py` (36d) - Phụ thuộc dùng chung cho các endpoint: lấy người dùng đang đăng nhập.
  `f:current_user@21  f:optional_user@31`
- `dev_routes.py` (120d) - Công cụ phát triển. CHỈ được đăng ký khi DEV_TOOLS_ENABLED = True.
  `f:dev_status@24  f:dev_toggle@30  f:dev_trace@37  f:dev_trace_clear@44`
  `f:dev_websearch@49  f:stats@55  f:reset@66  f:dev_export_conversation@96`
  `f:dev_export_all@109`
- `file_routes.py` (115d) - Tệp đính kèm theo cuộc trò chuyện.
  `f:supported@52  f:list_files@61  f:upload_file@68  f:delete_file@109`
- `routes.py` (61d) - Route chung: giao diện, cấu hình cho frontend, kiểm tra sức khoẻ.
  `f:render_page@21  f:get_ui@28  f:public_config@33  f:health@48`
- `schemas.py` (40d)
  `c:Credentials@4  c:ConversationCreate@10  c:ConversationRename@14  c:ChatRequest@18`
  `c:FeedbackRequest@23  c:ResetRequest@29  c:DevToggle@34  c:WebSearchTest@38`

**`Backend/core/`**

- `__init__.py` (1d)
- `answer.py` (26d) - Soạn câu trả lời từ Evidence Pack (và lời đáp xã giao).
  `f:generate@12  f:chitchat@24`
- `auth.py` (97d) - Xác thực: băm mật khẩu + phiên đăng nhập bằng cookie.
  `c:AuthError@22  f:hash_password@26  f:verify_password@30  f:validate_credentials@37`
  `f:register@44  f:login@51  f:logout@66  f:user_for_token@70  f:public@77`
  `f:set_cookie@87  f:clear_cookie@95`
- `chunk_index.py` (63d) - Tra cứu trong TỆP ĐÍNH KÈM của một cuộc trò chuyện.
  `f:invalidate@20  f:add_chunks@28  f:delete_document@35  f:search@51`
- `eval_export.py` (199d) - Xuất toàn bộ dữ liệu cuộc hội thoại thành file .txt chuẩn hoá dùng cho Chatbot (ChatGPT / Claude / ...) đánh giá.
  `f:build_conversation_export@22  f:build_all_conversations_export@179`
- `evidence.py` (75d) - Lấy bằng chứng: MCP search (+ tệp đính kèm của hội thoại) -> Evidence Pack.
  `f:gather@19  f:merge@48  f:public_sources@66`
- `intent.py` (679d) - Hiểu câu hỏi và quyết định đi đường nào: tra cứu / hỏi lại / trò chuyện / ngoài phạm vi.
  `c:Understanding@29    .as_dict@42  f:understand@259  f:gate@357`
  `f:generate_prompt_choices@445  f:analyze@584  f:profile_update@669`
- `llm.py` (136d) - Cổng Ollama — MỘT mô hình nhỏ (mục tiêu 3–4B, thử nghiệm 1.5B) đóng nhiều vai.
  `c:LLMError@34  f:client@41  f:model_for@48  f:chat@70  f:chat_json@74  f:warm_up@95`
  `f:model_info@103  f:status@124`
- `mcp_client.py` (236d) - Client MCP — giữ MỘT phiên kết nối lâu dài tới MCP search server.
  `c:MCPUnavailable@29  c:MCPTimeout@33  c:_Bridge@45    .ensure_started@57    .submit@127`
  `  .stop@137  f:call_tool@186  f:search_evidence@198  f:connect@212  f:status@227`
  `f:shutdown@234`
- `orchestrator.py` (184d) - Bộ điều phối — đúng pipeline của kiến trúc (Documentation/ARCHITECTURE.md):
  `c:TurnInput@32  c:TurnResult@42  f:run_turn@55`
- `parsers.py` (202d) - Tệp thô -> danh sách chunk tìm kiếm được.
  `c:UnsupportedFile@23  c:MissingDependency@27  f:supported_extensions@31  f:split_text@70`
  `f:parse@178  f:describe@192`
- `queue.py` (124d) - Hàng đợi xử lý tuần tự, VẪN giữ được hiệu ứng gõ chữ.
  `c:QueueFull@23  c:Job@28  c:QueueManager@38    .start@50    .stop@57    .depth@64`
  `  .submit@68    .stream@77`
- `resources.py` (87d) - Tệp đính kèm theo cuộc trò chuyện: nạp, liệt kê, xoá.
  `f:has_attachments@19  c:UploadError@26  f:ingest_upload@30  f:delete_document@75`
- `summarizer.py` (57d) - Đo độ dài ngữ cảnh và nhờ AI tóm tắt khi vượt ngưỡng.
  `f:estimate_tokens@18  f:build_context@30`
- `verifier.py` (343d) - Kiểm chứng bản nháp TRƯỚC khi trả lời người dùng.
  `c:Verification@30    .fix_notes@49    .as_dict@73  f:rule_check@93  f:verify@244`
  `f:says_not_found@271  f:detail_lines@279  f:has_substance@292  f:is_not_found_answer@296`
  `f:apply_fail_policy@313`

**`Backend/db/`**

- `__init__.py` (1d)
- `connection.py` (86d) - Kết nối SQLite. Đây là nơi DUY NHẤT mở database.
  `f:init_db@34  f:get_conn@62  f:run@72  f:reset_database@77`
- `repositories.py` (430d) - TOÀN BỘ câu SQL của hệ thống nằm ở đây.
  `c:Users@28    .create@30    .by_email@40    .by_id@45    .count@50  c:AuthSessions@55`
  `  .create@57    .user_for@67    .touch@76    .delete@83    .purge_expired@89`
  `c:LoginAttempts@95    .record@97    .recent_count@104    .clear@111  c:UserProfiles@118`
  `  .get@122    .update@129    .clear@151  c:Conversations@158    .create@160`
  `  .by_id@169    .owned_by@174    .list_for@181    .rename@190    .touch@198`
  `  .delete@204    .set_summary@210    .count@217  c:Messages@222    .add@224`
  `  .list_for@240    .owned_by@250    .count@257  c:Evidence@262    .add@264`
  `  .for_message@272  c:Feedback@288    .add@290    .count@297    .stats@301  c:JobLog@314`
  `  .add@316    .stats@326  f:purge_old@334  c:Documents@345    .create@347    .by_id@362`
  `  .owned_by@367    .list_for_conversation@373    .set_details@380    .mark@387`
  `  .delete@394    .count_for_conversation@400  c:DocumentChunks@406    .add_many@408`
  `  .list_for_conversation@423`

**`Backend/`**

- `developer_mode.py` (157d) - Chế độ nhà phát triển — một chỗ duy nhất cho mọi công cụ soi hệ thống.
  `f:enabled@32  f:set_enabled@36  f:toggle@43  c:Turn@50    .event@62    .set@72`
  `  .finish@76  f:turn@93  f:traces@97  f:clear_traces@102  f:snapshot@112`
  `f:websearch_check@134`

**`Backend/domain/`**

- `__init__.py` (1d)
- `text.py` (164d) - Tiện ích xử lý chuỗi tiếng Việt dùng chung.
  `f:fold@18  f:tokenize@28  f:terms@33  f:clean@43  f:truncate@53  f:tidy_answer@97`
  `c:BM25@132    .scores@146`

**`Backend/`**

- `main.py` (108d) - Backend/ cho các gói (api, core, db...) và GỐC dự án cho config.py.
  `f:lifespan@32  f:create_app@85`

**`Backend/mcp_search/`**

- `__init__.py` (1d)
- `engine.py` (507d) - Máy tìm kiếm phía sau MCP server — dựng Evidence Pack.
  `f:host_of@74  f:trust_of@85  f:warm_up@122  f:clean_snippet@146  f:plausible_date@180`
  `f:web_search@235  f:fetch_page@276  f:build_evidence_pack@407`
- `server.py` (88d) - MCP server "tthc-search" — công cụ tìm kiếm cho Evidence Pack.
  `f:search_evidence@40  f:web_search@47  f:fetch_page@55  f:main@60`

**`Backend/prompts/`**

- `__init__.py` (1d)
- `templates.py` (432d) - TẤT CẢ prompt của hệ thống + hàm dựng nội dung đưa vào prompt.
  `f:understand_system@67  f:understand_user@96  f:understand_examples@117`
  `f:understand_example_messages@155  f:gate_user@185  f:gate_example_messages@190`
  `f:answer_system@221  f:answer_user@246  f:format_evidence@264  f:verify_system@303`
  `f:verify_user@315  f:strip_citations@374  f:profile_line@380  f:history_digest@391`
  `f:history_messages@407`

---

## Frontend/

Giao dien: HTML + CSS + JS thuan, khong framework


**`Frontend/static/css/`**

- `styles.css` (354d) - Trợ lý Thủ tục hành chính. Tối mặc định, sáng khi body.light

**`Frontend/static/js/`**

- `api.js` (78d) - Lớp gọi API dùng chung. Mọi fetch đi qua đây để xử lý lỗi và 401 một chỗ.
  `f:request@3`
- `app.js` (137d) - Ráp các module lại và xử lý sự kiện trang chính.
  `f:showMemory@6  f:boot@27`
- `auth.js` (48d) - Trang đăng nhập / đăng ký.
  `f:setMode@13`
- `chat.js` (367d) - Khung chat: trạng thái xử lý, câu trả lời có trích dẫn [S#], nhãn kiểm chứng,
  `f:el@20  f:esc@27  f:scroll@34  f:normSources@40  f:rich@46  f:badge@64  f:sourceList@70`
  `f:evidencePanel@97  f:renderEvidence@117  f:feedback@165  f:choiceBox@182`
  `f:fillAssistant@237  f:render@256  f:clear@267  f:empty@269  f:load@278  f:send@307`
- `conversations.js` (78d) - Quản lý danh sách hội thoại ở thanh bên.
  `f:render@9  f:refresh@47  f:select@54  f:create@64`
- `dev.js` (295d) - Bảng Dev: soi vì sao trợ lý trả lời như vậy.
  `f:esc@13  f:row@15  f:describe@27  f:renderTrace@51  f:refreshTrace@87  f:testWeb@110`
  `f:refreshStatus@136  f:syncToggle@148  f:wireReset@156  f:setOpen@180  f:init@190`
  `f:stats@279  f:afterTurn@291`
- `files.js` (97d) - Tệp đính kèm của cuộc trò chuyện.
  `f:render@14  f:refresh@67  f:attach@80`

**`Frontend/templates/`**

- `index.html` (104d)
- `login.html` (41d) - <h1>Trợ lý Thủ tục hành chính</h1>

---

## Database/

Luoc do + du lieu nguon + CSDL dang chay


**`Database/`**

- `schema.sql` (121d)

---

## Evaluation/

Cham diem pipeline va chat luong truy van


**`Evaluation/`**

- `analyze_queries.py` (57d) - Chấm SƠ BỘ chất lượng truy vấn (không tra web) cho file queries_baseline_*.csv.
  `f:fold@18  f:toks@21  f:has_diac@31  f:cover@33  f:facet_ok@38`
- `build_eval_set.py` (557d) - build_eval_set.py — Nhóm 7 / LLM Pháp lý
  `f:strip_diacritics@345  f:to_abbrev@352  f:add_typo@359  f:keyword_only@393`
  `f:colloquial@399  f:load_rows@407  f:build@425  f:main@544`
- `evaluate.py` (140d) - Chấm điểm pipeline trên bộ câu hỏi TỰ SOẠN (Evaluation/eval_set.jsonl).
  `f:main@45`
- `gen_queries_baseline.py` (230d) - Sinh BASELINE truy vấn tìm kiếm cho bộ 862 câu (Evaluation/eval_questions.csv).
  `f:parse_args@46  f:short_model@90  f:search_queries@98  f:load_items@105  f:done_ids@114`
  `f:run_one@122  f:summarize@150  f:main@188`
- `search_baseline.py` (248d) - Đo TRA CỨU THẬT cho 3 cách tạo truy vấn trên cùng một mẫu câu hỏi.
  `f:parse_args@47  f:fold@59  f:tokens@64  f:is_hit@68  c:Searcher@75    .save@82`
  `  .search@88  f:rank@110  f:question_queries@125  f:sample@130  f:main@145`
  `f:summarize@204`

---

## Utility/

Fine-tune + script van hanh


**`Utility/finetune/`**

- `benchmark_quant.py` (103d) - So sánh mô hình qua Ollama (ví dụ FP16 vs 4-bit): dung lượng, VRAM, tốc độ, độ trễ.
  `f:bench@36  f:main@76`
- `export_dataset.py` (96d) - Xuất dữ liệu fine-tune từ hội thoại THẬT được người dùng chấm "Phù hợp".
  `f:main@35`
- `merge_and_export.py` (90d) - Gộp adapter LoRA -> FP16 -> GGUF -> lượng tử hoá 4-bit -> tạo mô hình Ollama.
  `f:main@42`
- `train_qlora.py` (125d) - QLoRA fine-tune mô hình 3–4B (hoặc 1.5B để thử) trên dữ liệu từ export_dataset.py.
  `f:main@31`

**`Utility/scripts/`**

- `fix_venv.py` (112d) - Sua duong dan tuyet doi ben trong .venv sau khi COPY/DI CHUYEN thu muc.
  `f:old_root_from_cfg@26  f:main@36`
- `make_index.py` (164d) - Sinh Documentation\CODEBASE_INDEX.md - ban do ma nguon.
  `f:iter_files@35  f:first_doc_line@45  f:py_symbols@67  f:js_symbols@87  f:wrap@101`
  `f:main@115`
- `run.ps1` (67d) - Tro ly Thu tuc hanh chinh - V10.3
- `setup.ps1` (196d) - CAI DAT LAN DAU - Tro ly Thu tuc hanh chinh V10.3

---

**Tong / total: 59 tep, 9097 dong.**

