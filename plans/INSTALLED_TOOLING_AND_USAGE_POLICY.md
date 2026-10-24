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

## Tác dụng cụ thể và khi nào phải dùng từng mục

Các ví dụ dưới đây là mục đích sử dụng trong Poki, **không phải tuyên bố các lỗi ví dụ đã được công cụ sửa xong**. Skill hướng dẫn cách làm; MCP/CLI cung cấp thao tác; hiệu quả vẫn cần đo trên task thật.

1. **Codebase Memory MCP — hiểu quan hệ code và phạm vi ảnh hưởng.** Lead (read-only) và Coding Worker dùng khi cần biết một handler/service được gọi ở đâu, luồng nào bị tác động. Ví dụ: truy từ endpoint nâng sao tới validation và trừ vật phẩm. Đầu ra: symbol/flow/caller có đường dẫn kiểm chứng; cần index mới và đúng repo.
2. **Beads — lưu đầu việc và quan hệ phụ thuộc bền vững.** Lead/Worker dùng cho task nhiều mục, nhiều phiên: tạo task, owner, dependency, blocker và evidence. Ví dụ: tách sửa backend, sync client và QA thành các việc có thứ tự. Đầu ra: task IDs và acceptance đầy đủ. Không tự launch hay giám sát process, không thay supervisor; chưa migration task Poki thật.
3. **Context7 — tra tài liệu thư viện đúng phiên bản.** Coding/Game/UI dùng khi chưa chắc API PixiJS8, React/Next hoặc thư viện đang cài. Đầu ra: tài liệu/API và version phù hợp lockfile, tránh code dựa trên API cũ. Không chứng minh implementation đúng chỉ vì có trích docs.
4. **PixiJS Skills — sử dụng renderer Pixi đúng cách.** Game Worker dùng cho Assets, texture/atlas, scene graph, input, ticker, cleanup, batching và filters. Ví dụ: điều tra sprite mờ hoặc layering trong GameCanvas. Đầu ra: implementation và visual/performance evidence, không phải tăng số API được gọi.
5. **Playwright MCP — để Claude trực tiếp thao tác trình duyệt.** QA dùng mở trang, click, lấy trạng thái và screenshot nhằm tái hiện lỗi. Ví dụ: mở popup, đổi tab, kiểm click không bị scrim chặn. Đầu ra: steps và evidence; regression lâu dài phải chuyển thành test runner assertions.
6. **Chrome DevTools MCP — tìm nguyên nhân lỗi và nghẽn trên browser.** QA dùng console, network, trace/performance/memory khi lỗi render, API hoặc leak. Ví dụ: kiểm texture request404, long task hoặc frame-time tăng sau mở/đóng panel. Đầu ra: trace/request/error cụ thể, không kết luận chỉ từ FPS.
7. **Anthropic Skills — bộ hướng dẫn tác vụ cho Claude Code.** Chọn frontend-design/canvas-design/webapp-testing/mcp-builder và các skill tài liệu phù hợp đã cài. Ví dụ: dựng prototype UI, viết quy trình test web hoặc tích hợp MCP. Đầu ra tùy skill; bộ này không phải một engine hay một chương trình tự chạy.
8. **Vercel Agent Skills — cải thiện phần React/web UI.** Worker Next/React dùng react-best-practices, composition-patterns, react-view-transitions, web-design-guidelines đã chọn. Ví dụ: giảm render không cần thiết, tổ chức component panel và kiểm accessibility. Không đồng nghĩa phải deploy Vercel; không áp quy tắc DOM vào sprite gameplay.
9. **Serena — tra và chỉnh sửa code theo symbol.** Coding Worker dùng symbol overview, references và editing được server hỗ trợ thay vì đọc/sửa mò nguyên file. Ví dụ: lần caller của hàm đổi pet rồi sửa đúng method. Đầu ra: references và diff đúng scope. TS đã có smoke; không suy rộng sang C# khi chưa thử LSP.
10. **Gamedev Skills — kiến thức gameplay bên ngoài renderer.** Game Worker chọn puzzle, game-feel, game-ui-ux và skill engine phù hợp đã tuyển từ catalog. Ví dụ: input lock trong cascade match3, feedback khi trúng đòn và tính đọc được của UI. Đầu ra: logic/timing/test theo spec; tuyệt đối không tự invent economy/reward.
11. **UI UX Pro Max — hệ thống hóa bố cục và design tokens.** UI Worker dùng khi thiết kế màn hình mới hoặc phần Figma chưa đặc tả: hierarchy, màu, font, spacing, states. Đầu ra: spec/token/layout có lý do và được duyệt, không tự thay phong cách dự án.
12. **Taste — định hướng chất lượng thị giác.** UI Worker dùng skill design-taste-frontend để xem density, hierarchy, composition, motion và tránh giao diện generic. Ví dụ: đề xuất cách phân cấp card và CTA khi user cho phép polish. Đầu ra: phương án/diff thị giác; reference đã chốt vẫn ưu tiên.
13. **Impeccable — audit và tinh chỉnh UI.** UI/QA dùng tìm lỗi contrast, spacing, typography, consistency, responsive và thiết kế rập khuôn. Ví dụ: audit modal có text dài, button disabled khó đọc. Đầu ra: danh sách lỗi có mức độ + ảnh trước/sau; audit DOM không tự hiểu toàn bộ pixels canvas.
14. **MengTo Skills — hướng dẫn chọn lọc về UI, action và VFX.** Các skill đã chọn gồm game-dev-combat-animation, game-dev-combat-skill-polish, design-action-combat, create-game-vfx, audit-ai-design-slop, no-ai-design-slop. Game/UI dùng để lập nhịp anticipation/impact/recovery và polish hình ảnh. Không tự sinh chuỗi sprite hay bảo đảm mượt; phải nộp clip thực tế.
15. **Superpowers — quy trình giải quyết việc có kiểm chứng.** Coding dùng brainstorming/planning khi cần, TDD, systematic-debugging, review và verification-before-completion. Ví dụ: tái hiện bug reward hai lần, viết test đỏ rồi sửa và kiểm xanh. Đầu ra: reproduction, tests, diff và review; không thêm tầng quy trình cho một sửa đổi nhỏ không cần thiết.
16. **Trail of Bits Skills — hỗ trợ audit bảo mật.** QA/security chọn sharp-edges, differential-review, variant-analysis, semgrep/codeql… theo ngôn ngữ và dependency sẵn có. Ví dụ: review trust boundary, tìm các endpoint cùng mẫu lỗi authorization. Đầu ra: finding có source/sink/reproduction. Cài skill không đồng nghĩa đã cài và chạy mọi scanner phụ thuộc.
17. **Unity CLI + Pipeline/MCP — điều khiển môi trường và Editor Unity.** Unity Worker dùng install/module/build/test cùng tool Editor mà Pipeline cung cấp để kiểm scene/component/prefab. Đầu ra: log, test XML, screenshot hoặc build đúng project/version. CLI đã có; live MCP cần Editor reachable, không thay bằng Coplay ở đợt này.
18. **Matt Pocock Skills — biến yêu cầu thành spec, tickets và handoff.** Lead/Claude dùng to-spec, to-tickets, implement-spec, handoff. Ví dụ: yêu cầu nhiều hạng mục được tách thành ticket có dependency, acceptance và phần việc chưa xong. Đầu ra: spec/task IDs/handoff nối tracker; fixture Beads chạy được không có nghĩa tracker repo Poki đã migrate.
19. **Context Engineering — giữ context hữu ích trong nhiệm vụ dài.** Lead dùng context-fundamentals/optimization/compression, long-horizon-prompting và evaluation để chọn thông tin, tóm tắt checkpoint và bàn giao. Đầu ra: brief/handoff giữ đủ constraints, decisions, pending và evidence. Không tự nâng context window hay sửa memory/compaction runtime.
20. **Karpathy Guidelines — kỷ luật tối giản và giữ phạm vi.** Claude dùng khi nhận task và review diff: nêu giả định, hỏi khi mơ hồ, thay đổi tối thiểu và đo điều kiện thành công. Ví dụ: sửa mapping item thay vì rewrite cả inventory. Đầu ra: diff tập trung, không thêm content/tính năng ngoài yêu cầu. Đây là hướng dẫn, không phải quyền chặn shell.
21. **Browser Use — thao tác workflow web nhiều bước.** Claude browser role dùng CLI/helper và browser session cô lập để điều hướng, đọc trang, điền dữ liệu không nhạy cảm và kiểm kết quả. Đầu ra: trạng thái thực tế/screenshot và lỗi từng bước. Bản CLI tái sử dụng đã thử form local; chưa chứng minh full autonomous LLM workflow trên Poki.
22. **Agent Browser — browser automation bằng CLI và snapshot/ref.** Claude browser/QA dùng snapshot accessibility, ref như @e2, fill/click/screenshot. Ví dụ: tìm ô form/nút theo snapshot thay vì đoán pixel. Đầu ra: steps và assertion/evidence trên cùng fixture với Browser Use; không mặc định ref DOM giải quyết UI Unity/Pixi canvas.

### Bổ sung ngoài danh sách22: Claude Code Game Studios

**Mục đích:** cung cấp project template gồm agent roles, slash-command skills, hooks/rules và mẫu tài liệu để tổ chức một workflow game trong Claude Code: thiết kế, lập story, triển khai, review, QA và release checklist. Đây không phải model mới hay49 process tự chạy.

**Trạng thái cập nhật:** bản pilot riêng đã cài/cấu hình và qua smoke test; Lead đã đối chiếu số agent/skill và đọc output smoke thực tế. Có 49 agent definitions, 74 skills; discovery và project-stage-detect hoạt động, hook từ chối đọc nguyên file lớn được chứng minh trong harness. Chưa áp vào game Poki, không thay thế 22 mục. Upstream chỉ có engine enum Godot/Unity/Unreal, không có hỗ trợ Pixi; một số hook event chưa được thử. Xem [báo cáo đầy đủ và giới hạn](CLAUDE_CODE_GAME_STUDIOS_PILOT_RESULT.md).

**Cách dùng dự kiến:** Hermes vẫn là Lead; studio agents là vai trò nội bộ của Claude. Phải nối vào task ledger chung, giữ model/session hiện tại và quyền nội dung game; không tạo hệ task/director thứ hai cạnh tranh. Hooks cần review; không phải OS sandbox. Chỉ chốt launch instructions sau khi pilot có bằng chứng.

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
