# Quy trình 7 bước Lead + mapping bộ công cụ tối thiểu (chốt 2026-10-28)

> Lead ĐỌC SKILL để hiểu bản chất → viết spec → worker thi công → audit bằng skill khác.
> Không giao khoán mù. Không dùng tool mà không hiểu. Thiếu tool nào thì ghi rõ BLOCKED + lý do, không bịa.

## B1 — Đọc skill, hiểu bản chất
Superpowers (systematic-debugging, test-driven-development, verification-before-completion),
Context Engineering, Karpathy Guidelines, Matt Pocock (to-spec / to-tickets).
Ra: hiểu đúng vấn đề, không đoán.

## B2 — Đọc code, hiểu project
Codebase Memory MCP (search_graph, trace_path, get_architecture, check_index_coverage),
Serena (find_symbol, find_referencing_symbols).
Ra: biết code hiện tại làm gì, hot path ở đâu.

## B2.5 — QA bản live hiện tại (bắt buộc từ 2026-10-28)
Playwright MCP (snapshot 3 viewport + console + network),
Chrome DevTools MCP (requests, computed styles),
Impeccable (scan anti-patterns), Agent Browser / Browser Use (flow thật),
design-taste + ui-ux-pro-max (audit visual).
Ra: bảng so sánh live vs yêu cầu (đã có / thiếu / thừa) — làm đầu vào B3.

## B3 — Lên kế hoạch rõ ràng
Matt Pocock (to-spec), Context Engineering (long-horizon-prompting),
Gamedev Skills Catalog (nếu game).
Ra: kế hoạch có số đo, không viết trên giấy.

## B4 — Viết spec + tạo beads
Beads (create / claim / link / dep), Matt Pocock (implement-spec), MengTo Skills.
Ra: spec + bead, worker chỉ việc thi công.

## B5 — Worker thi công
Worker chạy theo spec. Lead giám sát watchdog, KHÔNG code trực tiếp.

## B6 — Nghiệm thu audit QA (skill khác lúc làm)
Playwright MCP, Chrome DevTools MCP, Impeccable, design-taste,
ui-ux-pro-max, Agent Browser, Browser Use,
Trail of Bits (security review), Vercel / Anthropic Skills (nếu khớp stack),
Superpowers verification-before-completion.
Mỗi phát hiện phải có bằng chứng (screenshot / log / số đo). Không suy đoán.

## Ghi chú trung thực
- Tool nào không có trên máy (chưa cài / không reachable) thì ghi BLOCKED + log,
  không bỏ qua im lặng, không bịa đã dùng.
- Impeccable chạy root cần xử lý sandbox riêng (không để fail im lặng).
