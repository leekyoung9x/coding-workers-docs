# Công cụ đã trang bị và quy tắc sử dụng — Hermes Lead / Claude Code

## Phạm vi và trạng thái

Worker thử nghiệm: **Claude Code CLI**. Chưa triển khai đồng loạt sang Muse/Codex/worker khác. Đây là snapshot trong lúc nghiệm thu, không phải tuyên bố 22/22 hoàn tất.

- Nhóm 1–16: ledger AB17 ghi đã cài/cấu hình và smoke PASS từ installation worker; chưa hoàn tất nghiệm thu độc lập tổng thể.
- Mục 17 Unity: CLI + cấu hình có, live smoke BLOCKED vì chưa có Editor/Pipeline instance phù hợp. Không cài Coplay thay thế.
- Mục 18–22: đã tích hợp skill; kiểm nghiệm chức năng cuối đang tiếp tục. Browser Use/Agent Browser đã qua workflow mẫu ở staging. Không dùng ledger AB22 đang khởi tạo NOT_RUN để suy ra các gói cũ bị gỡ.
- Không có thay đổi game hoặc deploy trong đợt trang bị này. MCP/skill mới trên Hermes có thể cần phiên mới; không tuyên bố phiên chat hiện tại đã nạp đủ tool.

## Danh sách 22 mục

| ID | Bộ công cụ | Vai trò / trạng thái thực tế |
|---|---|---|
| 1 | Codebase Memory MCP | AB17: installed/configured, worker smoke PASS |
| 2 | Beads | AB17: installed/configured, worker smoke PASS |
| 3 | Context7 | AB17: installed/configured, worker smoke PASS |
| 4 | PixiJS Skills | AB17: installed/configured, worker smoke PASS |
| 5 | Playwright MCP | AB17: installed/configured, worker smoke PASS |
| 6 | Chrome DevTools MCP | AB17: installed/configured, worker smoke PASS |
| 7 | Anthropic Skills | AB17: installed/configured, worker smoke PASS |
| 8 | Vercel Agent Skills | AB17: installed/configured, worker smoke PASS |
| 9 | Serena | AB17: installed/configured, worker smoke PASS |
| 10 | Gamedev Skills Catalog | AB17: installed/configured, worker smoke PASS |
| 11 | UI UX Pro Max | AB17: installed/configured, worker smoke PASS |
| 12 | Taste | AB17: installed/configured, worker smoke PASS |
| 13 | Impeccable | AB17: installed/configured, worker smoke PASS |
| 14 | MengTo Skills | AB17: installed/configured, worker smoke PASS |
| 15 | Superpowers | AB17: installed/configured, worker smoke PASS |
| 16 | Trail of Bits Skills | AB17: installed/configured, worker smoke PASS |
| 17 | Existing Unity CLI + Pipeline/MCP | AB17: installed/configured, worker smoke BLOCKED |
| 18 | Matt Pocock Skills | Lead + Claude: to-spec, to-tickets, implement-spec, handoff đã tích hợp; đang thử tracker Beads trong fixture riêng |
| 19 | Context Engineering | Lead: context-fundamentals, context-optimization, context-compression, evaluation, advanced-evaluation, long-horizon-prompting đã xuất hiện enabled; không thay runtime compaction |
| 20 | Karpathy Guidelines | Claude: skill đã tích hợp; upstream khai báo MIT nhưng không có LICENSE riêng, cần giữ ghi chú provenance |
| 21 | Browser Use | Claude browser role: skill đã tích hợp, binary tái sử dụng; workflow local staging PASS, kiểm nghiệm tích hợp đang tiếp tục |
| 22 | Agent Browser | Claude browser role: skill đã tích hợp, CLI ở isolated prefix; workflow local staging PASS, kiểm nghiệm tích hợp đang tiếp tục |

## Quy định bắt buộc: dùng theo nhiệm vụ, không dùng cho đủ số

**Bắt buộc sử dụng năng lực phù hợp, không bắt buộc bật mọi công cụ trên mọi task.** Brief phải chọn tool/skill và lý do; kết quả có bằng chứng. Không thưởng tỷ lệ skill utilization. N/A phải có lý do cụ thể, không được âm thầm bỏ qua yêu cầu.

### Hermes Lead

1. Với yêu cầu nhiều mục, dùng spec/tickets/handoff của Matt Pocock phù hợp để tạo checklist đánh số: từng yêu cầu gốc -> task -> acceptance criteria -> owner -> evidence. Tác vụ nhỏ không cần tạo spec dài.
2. Dùng Beads làm task ledger khi workspace đã được cấu hình hợp lệ; task có dependency và owner. Hiện thử nghiệm trên fixture; **chưa chuyển task thật /poki sang Beads**. Trước khi migration phải chốt store và chuyển các việc còn mở, không giữ hai nguồn trạng thái mâu thuẫn.
3. Dùng Codebase Memory đọc-only để truy vết/impact khi index của repo đã có và đủ mới. /poki chưa được index toàn bộ; không báo kết luận graph nếu chưa có dữ liệu. Lead không gọi tool sửa code/index write ngoài quyền.
4. Dùng Context Engineering cho brief dài, bàn giao và context gần đầy: giữ quyết định, nguồn, việc chưa xong, blocker, bằng chứng và bước kế tiếp. Không thay lời nhắc bằng claim đã sửa compaction runtime.
5. Lead không sửa code ứng dụng hoặc deploy. Chỉ brief/report/docs được user cho phép. Quyền cần cưỡng chế ở runtime/OS; skill không phải sandbox.
6. Khi worker exit, kiểm artifact/test độc lập. Không đóng task chỉ vì exit0, PID sống, cron chạy hoặc self-report PASS. Báo phần còn thiếu thay vì đưa ETA không có căn cứ.

### Claude Code — Coding / Game

1. Đọc brief và task ledger; dùng Karpathy Guidelines để làm rõ giả định, giữ scope và tránh overengineering. Không thêm game content nếu chưa được duyệt.
2. Tra symbol/references bằng Serena và impact bằng Codebase Memory khi hỗ trợ/đã index. Serena TS đã thử; C# chưa được kiểm chứng. Nếu công cụ trả trống, không suy ra không có caller.
3. Dùng Context7 khi API/version chưa chắc; đối chiếu package lock. Không gọi tra docs hình thức cho mọi dòng code.
4. Áp dụng Superpowers TDD/debug/review phù hợp hoặc workflow tương đương hiện có; ghi reproduction, test trước/sau và kiểm diff. Không bật hook SessionStart mới toàn cục.
5. Pixi task: PixiJS Skills + gamedev skill con phù hợp. React/Next task: Vercel Agent Skills. Không nhét filter/UI canvas chỉ để đạt checklist, không giảm chất lượng hình âm thầm để cứu FPS.
6. Anthropic Skills dùng theo tác vụ trong Claude Code; không mặc định bộ skill đã có tự động được áp dụng. Report ghi tên skill và đầu ra hữu ích, không chỉ số lượng file.

### Claude Code — UI / Art

- UI UX Pro Max: design system/layout khi cần; Taste: art direction/hierarchy/motion; Impeccable: audit. Một design/reference đã duyệt là chuẩn; không bắt cả ba cùng redesign một màn hình.
- MengTo: chọn skill motion/UI/game phù hợp, report rõ lựa chọn. UI task đối chiếu Figma, kiểm text overflow, modal/input/layering và viewport hỗ trợ.
- Animation nghiệm thu bằng clip1x/0.5x, chuyển trạng thái, alpha composite và contact sheet. Screenshot đẹp hoặc26 PNG không chứng minh animation mượt.
- Không nằm trong đợt này: Sprite Forge chưa được đưa vào pipeline production.

### Claude Code — Browser / QA

- Playwright MCP cho tương tác/exploration; Playwright test runner cho regression tái lập. Canvas cần assert trạng thái/hit target và ảnh thực tế, không chỉ DOM selector.
- Chrome DevTools dùng khi cần console/network/performance/memory, báo renderer/DPR/drawing-buffer thực tế.
- Browser Use hoặc Agent Browser cho workflow web; chọn một công cụ chính mỗi phiên để tránh tranh session. Dùng profile cô lập, không công khai debug port. Smoke staging chỉ chứng minh workflow mẫu, không chứng minh browser nào tốt hơn toàn diện.
- Trail of Bits dùng theo threat model/ngôn ngữ phù hợp; kết hợp test authorization, replay, reward/idempotency. Không scan prod ngoài scope.
- Không đưa password/token vào prompt/log hoặc gõ lại bằng script. Dùng cơ chế nhập bí mật được phê duyệt; thiếu đường nhập an toàn thì ghi blocker.

### Unity

Dùng Unity CLI + Pipeline/MCP hiện có cho Unity task. Xác minh user/license/project/version và single-project lock. Không coi MCP initialize thành công là live Editor smoke PASS; không mở production project chỉ để làm xanh kiểm tra.

## Acceptance gate chung

- Ledger đủ mọi yêu cầu; không mất việc qua handoff.
- Nguồn/version/license và backup cấu hình được ghi nhận.
- installed != configured != smoke PASS != task Poki thực tế đạt chất lượng.
- Chạy suite liên quan và `/poki/qa.sh test all` khi thay đổi Poki; đợt cài tool không phải chứng minh gameplay.
- UI có ảnh/clip từ artifact đúng target; performance so cùng profile, không hạ chất lượng ngầm.
- Blocker phải có nguyên nhân, owner và next action. Không hợp thức hóa test lỗi bằng sửa threshold để có PASS.

## Bằng chứng và giới hạn

Local installation reports (không public credentials/config raw):
- `/poki/docs/reports/ab17/REPORT.md`, `status.json`, `smoke/`, `evidence/`.
- `/poki/docs/reports/ab22-additions/REPORT.md`, `MERGE_INSTRUCTIONS.md`.
- `/poki/docs/reports/ab22/`: kết quả finisher đang xây dựng; chưa có final verdict tại snapshot này.

Các gap đã biết: Unity live Editor; Serena C#; Impeccable URL scan dưới root; Beads project migration; Codebase Memory index /poki; Matt tracker fixture chưa đồng nghĩa project thật đã sẵn sàng. Danh sách này phải cập nhật bằng bằng chứng mới, không tự nâng trạng thái vì đã qua thời gian.
