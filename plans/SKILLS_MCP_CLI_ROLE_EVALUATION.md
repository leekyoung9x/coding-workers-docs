# Đánh giá danh mục Skills / MCP / CLI cho Coding Workers Leading

## Trạng thái và phạm vi

- Đây là đánh giá kiến trúc và kế hoạch thử nghiệm, **không phải biên bản đã cài đặt**.
- Bản gốc người dùng gửi được giữ ở phụ lục. Stars, khả năng và URL của từng dự án trong bản gốc **chưa được xác minh trực tiếp ở lượt này**; không dùng stars hay điểm tự chấm làm căn cứ nghiệm thu.
- Không thay đổi cấu hình Hermes, worker, quyền hệ thống hoặc triển khai dịch vụ khi tạo tài liệu này.

## Kết luận

Danh mục chia vai trò hợp lý, nhưng không nên triển khai nguyên khối 18 mục. Hãy chọn theo nhu cầu và đo bằng kết quả trên cùng baseline. Skills là hướng dẫn; MCP là giao diện công cụ; CLI là chương trình thực thi: ba loại này cần cách cài đặt, cấp quyền và kiểm thử khác nhau.

### Các điểm giữ lại

1. Lead lập kế hoạch, giao việc, đọc/phân tích theo quyền và xác minh; không sửa mã ứng dụng hoặc deploy trực tiếp. Worker được cấp quyền mới thực thi.
2. Tách Coding/Game, UI/Art và QA theo trách nhiệm; có thể dùng cùng CLI với cấu hình vai trò riêng, không bắt buộc dựng thêm một dịch vụ cho mỗi vai trò.
3. Một browser chính cho QA; DevTools chỉ bổ sung khi cần trace/network/performance.
4. Không dựa vào prompt để bảo vệ repo hoặc secrets. Cần cưỡng chế quyền và có deploy gate độc lập.

### Các điểm cần sửa

1. **18/18 không phải trạng thái hoàn tất:** bản gốc chỉ liệt kê mong muốn. Có 18 lượt gán theo vai trò (3 Lead + 7 Code + 3 UI + 2 Art + 3 QA), nhưng Codebase Memory xuất hiện hai vai trò nên chỉ có 17 công cụ riêng. Phải tách số công cụ duy nhất, số lượt gán và số nghiệm thu.
2. **Không thưởng tỷ lệ sử dụng skill:** chỉ kích hoạt skill liên quan. Không ép thêm filter/NineSlice/engine API chỉ để tăng điểm; áp dụng không phù hợp phải được ghi là N/A có lý do.
3. **Không quy kết chất lượng cho tên model:** khác biệt quan sát được giữa worker chưa chứng minh model nào tốt hơn hoặc skill nào gây lỗi. Cần cùng brief, baseline, thiết bị, tài nguyên, số lần chạy và review diff.
4. **Không coi DOM hay Pixi là lựa chọn tuyệt đối:** cả hai đều có thể đúng. Sai khi chia một panel qua hai hệ render mà không có contract phân tầng. CSS z-index không thể xen kẽ từng sprite trong một canvas. Quy định ownership của panel/text/VFX, modal và input trước khi triển khai.
5. **Không đánh đồng headless với GPU yếu:** headless có thể dùng GPU thật. Phải ghi renderer/backend thực tế, DPR, kích thước drawing buffer, browser flags và profile chất lượng. Không âm thầm giảm resolution hoặc tắt hiệu ứng để qua test.
6. **Screenshot tĩnh không nghiệm thu animation:** cần clip ở tốc độ thật và chậm, kiểm tra chuyển trạng thái, nhất quán hình thể/trang phục, contact/root motion. 26 file PNG không đồng nghĩa 26 pose được sinh độc lập; xoay/scale vài pose không được báo là animation hoàn chỉnh.
7. **Native RGBA không bảo đảm alpha đúng:** phải kiểm tra histogram, composite trên nền sáng/tối/checkerboard và mask vùng trang phục. Các tuyên bố trước đây “100% nguyên vẹn”, “mượt” hoặc “9-point QA verified” không được kế thừa khi chưa có bằng chứng.
8. **Đọc README trước khi cài:** một awesome-list không nhất thiết là gói skill cài được. Hook của một CLI không mặc nhiên tương thích các CLI còn lại. Công cụ có quyền sửa code không nên đưa nguyên quyền cho Lead.
9. **Tránh trùng chức năng:** Codebase Memory và Serena có phần giao nhau; Beads và task store hiện hành cần một nguồn sự thật; Repomix chỉ dùng khi cần export có lọc secrets, không thay index symbol hằng ngày.

## Đánh giá đủ 30 mục

| # | Công cụ | Quyết định đề xuất | Điều kiện / điểm cần xác minh |
|---|---|---|---|
| 1 | Codebase Memory MCP | Pilot Lead read-only + Code | Xác minh repo, license, backend, chi phí index và enforcement quyền đọc; không chỉ dựa vào tool description. |
| 2 | Context7 | Ưu tiên Code | Thử truy vấn đúng phiên bản PixiJS; kiểm tra API key/quota, không gửi secrets. |
| 3 | Superpowers | Chọn lọc Code | Tận dụng TDD/debug/review; đối chiếu skills hiện có, tránh hai workflow mâu thuẫn. |
| 4 | Serena | Pilot Code | Đo chất lượng symbol/references trên TypeScript; so sánh với mục 1 trước khi chạy cả hai. |
| 5 | Beads | Pilot Lead + Worker | Một task store, owner/version/lock rõ; không cho nhiều agent tranh cập nhật trạng thái. |
| 6 | Context Engineering | Chọn lọc Lead | Nạp theo task, đo token/context và chất lượng handoff. |
| 7 | Karpathy Guidelines | Chọn lọc Code | Dùng như nguyên tắc tối giản; không thay tests, spec hoặc review. |
| 8 | TDD Guard | Khi cần | Xác minh hook hỗ trợ từng CLI; test cả đường bypass; không quảng cáo cưỡng chế toàn hệ thống. |
| 9 | Matt Pocock Skills | Pilot Lead + Code | Chọn skill cụ thể phục vụ spec/TypeScript; tránh nạp toàn bộ. |
| 10 | Repomix | Khi cần | Include/exclude và quét secret; không pack toàn repo hoặc credentials vào context. |
| 11 | PixiJS Skills | Ưu tiên Game | Pin đúng v8 và dùng theo vấn đề; fidelity/performance gate quan trọng hơn utilization. |
| 12 | Gamedev Agent Skills | Nguồn tuyển chọn | Kiểm tra đây là catalog hay package; chỉ lấy skill đúng engine, review license. |
| 13 | Agent Sprite Forge | Pilot Art riêng | Xác minh input video, model/dịch vụ, chi phí, GPU, alpha và atlas thực tế. |
| 14 | Open Game Skills | Thử nghiệm Art/Game | Chọn một action nhỏ; đánh giá bằng clip chứ không bằng số file. |
| 15 | Unity MCP | Chỉ dự án Unity | Kiểm tra tích hợp Unity hiện có trước khi thêm server trùng. |
| 16 | Pixel Art Skill | Chưa ưu tiên | Chỉ dùng khi art direction thật sự là pixel art. |
| 17 | UI UX Pro Max | Pilot UI | Ràng buộc design system và reference; không tự thay art direction. |
| 18 | Impeccable | Pilot UI + QA | Audit trước/sau, không biến polish thành redesign ngoài scope. |
| 19 | Playwright MCP | Browser chính đề xuất | Tách exploratory MCP với bộ Playwright tests có thể tái chạy trong CI. |
| 20 | Chrome DevTools MCP | Bổ sung QA | Khi cần trace/console/network; cô lập profile và không lộ cookie. |
| 21 | Taste Skill | Tùy UI | Đối chiếu reference, tránh chồng nguyên tắc thẩm mỹ với mục 17/18. |
| 22 | Agent Browser | Phương án thay thế | Chỉ chọn nếu đo được lợi ích hơn browser chính, không cài chỉ để đủ bộ. |
| 23 | Browser Use | Không bắt buộc | Đã có browser helper ở Lead; kiểm kê trước khi dựng thêm hạ tầng. |
| 24 | Figma Context MCP | Theo nhu cầu | Hiện có Figma MCP; xác minh lợi ích thiếu trước khi thêm server khác. |
| 25 | Anthropic Skills | Chọn lọc | Skill portable không có nghĩa hook/tool proprietary portable; kiểm tra license từng phần. |
| 26 | Vercel Agent Skills | Khi dùng React | Áp dụng cho DOM shell, không ép vào Pixi gameplay. |
| 27 | MengTo Skills | Thử nghiệm | Chọn tài liệu cụ thể; cần benchmark cùng reference. |
| 28 | SecondSky Skills | Chọn lọc Code | Review script/quyền mạng/shell trước khi chạy; tránh nạp cả collection. |
| 29 | Trail of Bits Skills | QA security theo đợt | Chọn đúng ngôn ngữ/threat model; không thay SAST/dependency scan thực thi. |
| 30 | GitHub MCP Server | Tùy nhu cầu | So với gh CLI hiện có; token read-only cho Lead, PR/write riêng cho worker, không cấp admin mặc định. |

## Thứ tự triển khai đề xuất

### Đợt 0 — Kiểm kê và baseline

- [ ] Kiểm kê skill/MCP/CLI đã có theo từng vai trò; ghi version, nguồn, license và quyền.
- [ ] Chốt repo/nhánh/worktree riêng cho thử nghiệm; giữ baseline P5/P6 có thể so sánh.
- [ ] Xác minh upstream, pin commit/version, đọc script cài đặt; không thực thi nội dung không tin cậy trực tiếp.
- [ ] Xác minh cơ chế quyền hiện có; không coi việc nhắc tên `wkctl` là đã có enforcement.

### Đợt 1 — Bộ cốt lõi nhỏ

- [ ] Game: PixiJS skills chọn lọc + Context7 + workflow TDD/debug/review hiện có.
- [ ] Code intelligence: thử một trong Codebase Memory/Serena; thêm cái còn lại chỉ nếu giải quyết khoảng trống đo được.
- [ ] QA: một browser chính + bộ test CLI tái lập; DevTools khi cần.
- [ ] UI: thử một bộ audit/design trên một màn hình, không nạp đồng loạt ba bộ.
- [ ] Task store: Beads chỉ khi có nhu cầu dependency/đa phiên chưa được công cụ hiện tại đáp ứng.

### Đợt 2 — Art thử nghiệm độc lập

- [ ] Một nhân vật, một action, nguồn tham chiếu cố định; không ghi đè asset đang dùng trước khi duyệt.
- [ ] Lưu prompt/workflow/request ID/model alias thực tế, input/output hash và provenance từng frame.
- [ ] Nộp contact sheet + clip 1x/0.5x + bản composite sáng/tối + atlas/metadata.
- [ ] Người dùng duyệt hình và chuyển động trước khi publish; test kỹ thuật xanh không tự thay thế duyệt thị giác.

## Contract quyền và nghiệm thu

- **Lead:** đọc code theo scope; ghi brief/report trong vùng tài liệu được cho phép; không ghi repo ứng dụng, không giữ deploy credentials. Nghiệm thu chỉ qua runner quyền hạn chế, không qua shell đặc quyền tùy ý.
- **Coding/UI/Art worker:** workspace riêng, quyền ghi theo task, không tự duyệt kết quả của mình và không tự thêm nội dung game.
- **QA worker:** đọc artifact, chạy test cô lập, ghi report; tài khoản test giới hạn, không credential prod.
- **Deploy worker/CI:** nhận artifact đã duyệt, quyền đích riêng, cần approval, audit log và rollback. Lead không deploy trực tiếp.
- Filesystem read-only là chưa đủ nếu Lead vẫn là root/có sudo/Docker socket hoặc shell toàn quyền. Cần user/container isolation, mounts, capability/tool allowlist, egress và credentials tách biệt. Không mount Docker socket cho sandbox.
- Gate tối thiểu: unit/integration/build, baseline screenshot nhiều viewport, kiểm tra panel/modal/input layering, profile render cố định, trace performance và clip animation. Cấm chỉnh test hoặc giảm chất lượng chỉ để đạt số.

## Những gì tài liệu này chưa chứng minh

Chưa xác minh stars, tính năng upstream, chi phí, hỗ trợ từng CLI, trạng thái cài đặt thực tế hoặc hiệu quả của 30 công cụ. Chưa cưỡng chế quyền ở OS/CI và chưa sửa các lỗi P6/P7. Việc đó cần task triển khai riêng có acceptance test.

---

# Phụ lục — Bản gốc người dùng cung cấp

Nội dung dưới đây được giữ nguyên làm nguồn tham chiếu; các số liệu và khuyến nghị không tự động được xác nhận bởi phần đánh giá bên trên.

# Bảng xếp hạng 30 Skills / MCP / CLI cho Hermes Lead & Workers

Tao giữ nguyên danh sách trước, bổ sung cột cài vào Hermes Lead hay Worker, đồng thời phân biệt rõ công cụ nên cài ngay, chỉ dùng khi cần và không cần thiết.

Nguyên tắc hệ thống của m:

- Hermes Lead: Chỉ đọc code, phân tích kiến trúc, lập kế hoạch, giao việc và xác minh kết quả. Không được sửa code hoặc deploy trực tiếp.
- Coding Worker: Thực hiện sửa code, gameplay, engine, refactor và unit test.
- UI/Art Worker: Thiết kế UI, sprite, animation, VFX.
- QA Worker: Chạy browser, chụp screenshot, kiểm thử và báo cáo lỗi.

Stars là số tham khảo từ các lượt tìm trước, chưa xác minh trực tiếp lại ở lượt này. Điểm /10 là mức phù hợp với pipeline của m, không phải benchmark độc lập.

## 1. Code Intelligence & Agent Orchestration

| #  | GitHub / Công cụ                                                                                                            | Stars ⭐ | Tác dụng                                    | Điểm | Cài vào đâu?       | Có nên cài?  |
| -- | --------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------- | ---- | ------------------ | ------------ |
| 1  | [Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp?utm_source=chatgpt.com)                               | \~47.3k | Graph codebase, dependency, impact analysis | 9.8  | Lead + Code Worker | Có           |
| 2  | [Context7](https://github.com/upstash/context7?utm_source=chatgpt.com)                                                      | \~63.4k | Tài liệu API theo phiên bản                 | 9.7  | Code Worker        | Có           |
| 3  | [Superpowers](https://github.com/obra/superpowers?utm_source=chatgpt.com)                                                   | \~302k  | TDD, lập kế hoạch, debugging, review        | 9.6  | Code Worker        | Có, chọn lọc |
| 4  | [Serena](https://github.com/oraios/serena?utm_source=chatgpt.com)                                                           | \~30.7k | Tìm symbol, references, sửa code            | 9.5  | Code Worker        | Có           |
| 5  | [Beads](https://github.com/steveyegge/beads?utm_source=chatgpt.com)                                                         | \~28k   | Task dependency, tiến độ nhiều agent        | 9.4  | Lead + Worker      | Có           |
| 6  | [Context Engineering Skills](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering?utm_source=chatgpt.com) | —       | Context, memory, multi-agent                | 9.3  | Lead               | Nên thử      |
| 7  | [Karpathy Guidelines](https://github.com/multica-ai/andrej-karpathy-skills?utm_source=chatgpt.com)                          | \~223k  | Giảm code dư, overengineering               | 9.2  | Code Worker        | Nên cài      |
| 8  | [TDD Guard](https://github.com/nizos/tdd-guard?utm_source=chatgpt.com)                                                      | —       | Cưỡng chế quy trình TDD                     | 9.1  | Code Worker        | Tùy dự án    |
| 9  | [Matt Pocock Skills](https://github.com/mattpocock/skills?utm_source=chatgpt.com)                                           | \~302k  | Làm rõ spec trước khi code                  | 9.0  | Lead + Code Worker | Nên thử      |
| 10 | [Repomix](https://github.com/yamadashy/repomix?utm_source=chatgpt.com)                                                      | \~29k   | Đóng gói repo cho AI đọc                    | 8.8  | Lead + Code Worker | Khi cần      |

Lưu ý: Codebase Memory MCP ở Lead phải chỉ có quyền đọc. Nếu Beads được cả Lead và Worker sử dụng, cần phân quyền cập nhật task, tránh nhiều agent cùng sửa trạng thái không kiểm soát.

## 2. Game 2D, Sprite, VFX & Animation

| #  | GitHub / Công cụ                                                                                              | Stars ⭐ | Tác dụng                                       | Điểm | Cài vào đâu?      | Có nên cài?       |
| -- | ------------------------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------- | ---- | ----------------- | ----------------- |
| 11 | [PixiJS Skills](https://github.com/pixijs/pixijs-skills?utm_source=chatgpt.com)                               | \~356   | PixiJS v8, sprite, shader, filter, performance | 10   | Game Worker       | Có ngay           |
| 12 | [Gamedev Agent Skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills?utm_source=chatgpt.com) | —       | Gameplay, shader, animation, nhiều engine      | 9.8  | Game Worker       | Có, chọn lọc      |
| 13 | [Agent Sprite Forge](https://github.com/0x0funky/agent-sprite-forge?utm_source=chatgpt.com)                   | \~4.5k  | Video → sprite, chroma, atlas                  | 9.7  | Art Worker        | Nên thử           |
| 14 | [Open Game Skills](https://github.com/jammyfu/open-game-skills?utm_source=chatgpt.com)                        | —       | Combat, game feel, VFX, animation              | 9.2  | Game + Art Worker | Thử nghiệm        |
| 15 | [Unity MCP](https://github.com/CoplayDev/unity-mcp?utm_source=chatgpt.com)                                    | —       | Điều khiển Unity Editor                        | 9.0  | Unity Worker      | Có nếu dùng Unity |
| 16 | [Pixel Art Skill](https://github.com/ervareza/agent-skill-pixel-art?utm_source=chatgpt.com)                   | \~15    | Pixel sprite, palette, atlas, timing           | 6.5  | Art Worker        | Chưa cần          |

Riêng PixiJS Skills: Tao đánh giá là quan trọng nhất với Game Worker vì giúp agent hiểu đúng cách sử dụng engine, thay vì sinh code Canvas/DOM không phù hợp.

## 3. UI/UX, Browser & Visual QA

| #  | GitHub / Công cụ                                                                                    | Stars ⭐  | Tác dụng                      | Điểm | Cài vào đâu?   | Có nên cài?         |
| -- | --------------------------------------------------------------------------------------------------- | -------- | ----------------------------- | ---- | -------------- | ------------------- |
| 17 | [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill?utm_source=chatgpt.com)     | \~138.7k | Design system, màu, font, UX  | 9.6  | UI Worker      | Có                  |
| 18 | [Impeccable](https://github.com/pbakaus/impeccable?utm_source=chatgpt.com)                          | \~86k    | Audit, critique, polish UI    | 9.5  | UI + QA Worker | Có                  |
| 19 | [Playwright MCP](https://github.com/microsoft/playwright-mcp?utm_source=chatgpt.com)                | \~38.4k  | Browser test, screenshot      | 9.5  | QA Worker      | Có                  |
| 20 | [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp?utm_source=chatgpt.com) | \~54k    | Console, network, performance | 9.3  | QA Worker      | Có                  |
| 21 | [Taste Skill](https://github.com/Leonxlnx/taste-skill?utm_source=chatgpt.com)                       | \~99k    | Art direction, UI đẹp hơn     | 9.0  | UI Worker      | Nên cài             |
| 22 | [Agent Browser](https://github.com/vercel-labs/agent-browser?utm_source=chatgpt.com)                | \~43k    | Browser automation            | 8.9  | QA Worker      | Chọn 1 browser tool |
| 23 | [Browser Use](https://github.com/browser-use/browser-use?utm_source=chatgpt.com)                    | \~119k   | AI tự điều khiển browser      | 8.8  | QA Worker      | Không bắt buộc      |
| 24 | [Figma Context MCP](https://github.com/GLips/Figma-Context-MCP?utm_source=chatgpt.com)              | \~15.6k  | Đọc Figma để code UI          | 8.6  | UI Worker      | Tùy nhu cầu         |

Với m, Playwright MCP nên là công cụ browser chính. Chrome DevTools MCP dùng bổ sung khi cần debug performance, network hoặc console. Không cần chạy cả ba Browser Use, Agent Browser và Playwright MCP cùng lúc.

## 4. Skills tổng hợp, bảo mật & tích hợp

| #  | GitHub / Công cụ                                                                          | Stars ⭐ | Tác dụng                                   | Điểm | Cài vào đâu?       | Có nên cài?     |
| -- | ----------------------------------------------------------------------------------------- | ------- | ------------------------------------------ | ---- | ------------------ | --------------- |
| 25 | [Anthropic Skills](https://github.com/anthropics/skills?utm_source=chatgpt.com)           | \~183k  | Skills chính thức, frontend, MCP, tài liệu | 9.0  | Lead + Worker      | Chọn lọc        |
| 26 | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills?utm_source=chatgpt.com) | \~32k   | React, performance, UX                     | 8.8  | UI + Code Worker   | Nếu dùng React  |
| 27 | [MengTo Skills](https://github.com/MengTo/Skills?utm_source=chatgpt.com)                  | —       | Workflow, thiết kế, game, animation        | 8.5  | UI + Game Worker   | Thử nghiệm      |
| 28 | [SecondSky Skills](https://github.com/secondsky/claude-skills?utm_source=chatgpt.com)     | —       | Engineering, DevOps, automation            | 8.3  | Code Worker        | Chọn lọc        |
| 29 | [Trail of Bits Skills](https://github.com/trailofbits/skills?utm_source=chatgpt.com)      | \~7.8k  | Security audit, static analysis            | 8.2  | QA Worker          | Nên cài         |
| 30 | [GitHub MCP Server](https://github.com/github/github-mcp-server?utm_source=chatgpt.com)   | \~33.8k | PR, issue, repository automation           | 8.1  | Lead + Code Worker | Nếu dùng GitHub |

## 5. Sơ đồ phân bổ công cụ

Hermes Lead

Codebase Memory · Beads · Context Engineering

Read-only code · Giao task · Duyệt kết quả

&#x20;Game Worker

PixiJS Skills, Serena, Context7, Superpowers, Codebase Memory

&#x20;UI Worker

UI UX Pro Max, Taste, Impeccable, Figma

&#x20;Art Worker

Sprite Forge, Open Game Skills, animation pipeline

&#x20;QA Worker

Playwright, Chrome DevTools, Impeccable, security checks

wkctl + Test Gates + Deploy Gate

Chỉ worker được cấp quyền mới có thể sửa code và triển khai

## 6. Checklist cài đặt

## Danh sách triển khai

18/18

Hermes Lead

Codebase Memory MCP

Beads

Context Engineering Skills

Game / Coding Worker

Codebase Memory MCP

Context7

Superpowers

Serena

PixiJS Skills

Gamedev Agent Skills

Karpathy Guidelines

UI Worker

UI UX Pro Max

Impeccable

Taste Skill

Art Worker

Agent Sprite Forge

Open Game Skills

QA Worker

Playwright MCP

Chrome DevTools MCP

Trail of Bits Skills

Chọn tất cả Copy cấu hình

Khuyến nghị cuối: Không cần cài 30 công cụ. Nên triển khai khoảng 12–15 công cụ cốt lõi, phân chia theo vai trò và chỉ kích hoạt đúng lúc.

Đặc biệt, không được dựa vào prompt hoặc Skills để chặn Hermes Lead sửa code. Quyền ghi repository, chạy shell và deploy phải được cưỡng chế ở tầng `wkctl`, filesystem, credentials và CI/CD. Skills chỉ hỗ trợ quy trình, không thay thế cơ chế phân quyền thật.
