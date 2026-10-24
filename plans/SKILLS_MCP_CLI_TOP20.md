# Danh sách 20 Skills / MCP / CLI nên trang bị cho Hermes + Workers

Đúng, 20 công cụ nằm trong danh sách đề xuất, nhưng không có nghĩa là nên cài cả 20 ngay. :V

Tao chia thành 3 mức ưu tiên:

| Mức ưu tiên          | Số lượng | Khuyến nghị                      |
| -------------------- | -------- | -------------------------------- |
| P0 — Cốt lõi         | 7        | Cài trước                        |
| P1 — UI, Art, Sprite | 5        | 4 công cụ nên cài + 1 thử nghiệm |
| P2 — Bổ sung         | 8        | Cài khi có nhu cầu               |
| Tổng                 | 20       | Không cần bật đồng thời          |

Stars là số tham khảo từ các lượt đối chiếu trước, làm tròn và chưa được xác minh live lại trong câu trả lời này. Điểm /10 là mức phù hợp với hệ thống của m, không phải benchmark độc lập.

## P0 — 7 công cụ cốt lõi: Cài trước

| # | Tên / GitHub                                                                                                          | Stars ⭐ | Tác dụng thực tế                                  | Điểm | Cài vào đâu?                |
| - | --------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------- | ---- | --------------------------- |
| 1 | [Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp?utm_source=chatgpt.com)                         | \~47k   | Graph codebase, tìm dependency, impact analysis   | 9.7  | Hermes Lead + Coding Worker |
| 2 | [Beads](https://github.com/steveyegge/beads?utm_source=chatgpt.com)                                                   | \~28k   | Quản lý task, dependency, trạng thái agent        | 9.4  | Hermes Lead + Workers       |
| 3 | [Serena](https://github.com/oraios/serena?utm_source=chatgpt.com)                                                     | \~29k   | Tìm symbol, references, chỉnh sửa code chính xác  | 9.5  | Coding Worker               |
| 4 | [Context7](https://github.com/upstash/context7?utm_source=chatgpt.com)                                                | \~63k   | Tra API theo phiên bản, hạn chế dùng API cũ       | 9.7  | Coding Worker               |
| 5 | [PixiJS Skills](https://github.com/pixijs/pixijs-skills?utm_source=chatgpt.com)                                       | \~350   | PixiJS v8, sprite, shader, rendering, performance | 9.8  | Game Worker                 |
| 6 | [Awesome Gamedev Agent Skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills?utm_source=chatgpt.com) | \~3.9k  | Gameplay, RPG, combat, VFX, game feel             | 9.6  | Game Worker                 |
| 7 | [Playwright MCP](https://github.com/microsoft/playwright-mcp?utm_source=chatgpt.com)                                  | \~38k   | Browser automation, screenshot, UI testing        | 9.5  | QA Worker                   |

Nhóm P0 giúp hệ thống làm đúng việc: Hermes hiểu codebase và chia task; worker có kiến thức API, engine và công cụ kiểm thử.

## P1 — 5 công cụ UI, Art, Sprite: Nên trang bị

| #  | Tên / GitHub                                                                                    | Stars ⭐  | Tác dụng thực tế                               | Điểm | Cài vào đâu?     | Khuyến nghị  |
| -- | ----------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------- | ---- | ---------------- | ------------ |
| 8  | [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill?utm_source=chatgpt.com) | \~125k   | Design system, bố cục, màu sắc, typography     | 9.5  | UI Worker        | Cài          |
| 9  | [Taste Skill](https://github.com/Leonxlnx/taste-skill?utm_source=chatgpt.com)                   | \~101.8k | Art direction, visual density, motion, thẩm mỹ | 9.3  | UI Worker        | Cài          |
| 10 | [Impeccable](https://github.com/pbakaus/impeccable?utm_source=chatgpt.com)                      | \~86k    | Audit UI, phát hiện vấn đề thiết kế, polish    | 9.5  | UI + QA Worker   | Cài          |
| 11 | [MengTo Skills](https://github.com/MengTo/Skills?utm_source=chatgpt.com)                        | \~7k     | Animation, game design, VFX, UI workflow       | 9.2  | UI + Game Worker | Cài chọn lọc |
| 12 | [Agent Sprite Forge](https://github.com/0x0funky/agent-sprite-forge?utm_source=chatgpt.com)     | \~4.6k   | Video → sprite, chroma, frame alignment, atlas | 9.6  | Art Worker       | Thử trước    |

Đối với game Anime/Chibi, đây là nhóm rất đáng đầu tư. Tuy nhiên, Taste + UI UX Pro Max + Impeccable không nên cùng điều khiển một tác vụ thiết kế. Nên phân vai: UI UX Pro Max dựng design system, Taste định hướng thẩm mỹ, Impeccable audit kết quả.

## P2 — 8 công cụ bổ sung: Cài khi cần

| #  | Tên / GitHub                                                                                        | Stars ⭐ | Tác dụng thực tế                      | Điểm | Cài vào đâu?         | Khi nào cần?          |
| -- | --------------------------------------------------------------------------------------------------- | ------- | ------------------------------------- | ---- | -------------------- | --------------------- |
| 13 | [Superpowers](https://github.com/obra/superpowers?utm_source=chatgpt.com)                           | \~284k  | Planning, TDD, debugging, review      | 9.6  | Coding Worker        | Task phức tạp         |
| 14 | [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp?utm_source=chatgpt.com) | \~54k   | Console, network, memory, performance | 9.1  | QA Worker            | Debug sâu             |
| 15 | [Unity MCP](https://github.com/CoplayDev/unity-mcp?utm_source=chatgpt.com)                          | —       | Điều khiển Unity Editor từ agent      | 9.0  | Unity Worker         | Dự án Unity           |
| 16 | [Repomix](https://github.com/yamadashy/repomix?utm_source=chatgpt.com)                              | \~29k   | Đóng gói repository cho AI phân tích  | 8.7  | Coding Worker        | Phân tích repo lớn    |
| 17 | [GitHub MCP Server](https://github.com/github/github-mcp-server?utm_source=chatgpt.com)             | \~33k   | Issues, PR, repository automation     | 8.8  | Lead + Coding Worker | Quản lý GitHub        |
| 18 | [Trail of Bits Skills](https://github.com/trailofbits/skills?utm_source=chatgpt.com)                | \~7.8k  | Security audit, static analysis       | 8.5  | QA Worker            | Kiểm tra bảo mật      |
| 19 | [Anthropic Skills](https://github.com/anthropics/skills?utm_source=chatgpt.com)                     | \~174k  | Bộ Skills đa lĩnh vực                 | 9.0  | Worker phù hợp       | Cần Skill chuyên biệt |
| 20 | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills?utm_source=chatgpt.com)           | \~32k   | React, frontend, web performance      | 8.5  | UI + Coding Worker   | Dùng React/web UI     |

Superpowers nằm P2 không phải vì yếu, mà vì workflow TDD, planning và review của nó có thể trùng với quy trình `wkctl` và các gate m đã thiết kế. Nên thử trước trên một Coding Worker thay vì bật cho toàn hệ thống.

## Tổng hợp phân bổ theo Agent

&#x20;Hermes Lead

Orchestrator

Codebase Memory MCP · Beads

Đọc, phân tích, chia task, xác minh. Không sửa code hoặc deploy.

&#x20;Coding / Game Worker

Serena · Context7 · PixiJS Skills · Awesome Gamedev Skills

Thêm Superpowers, Repomix, Anthropic Skills khi task cần.

&#x20;UI Worker

UI UX Pro Max · Taste Skill · Impeccable · MengTo Skills

Phụ trách UI 1440×720, bố cục, animation và polish.

&#x20;Art / Sprite Worker

Agent Sprite Forge

Thử nghiệm xử lý video, chroma, frame, alpha và atlas trước khi đưa vào production.

&#x20;QA Worker

Playwright MCP · Impeccable

Chrome DevTools MCP bổ sung khi cần debug sâu.

## Chốt số lượng

# 11

Nên cài trước

# 1

Thử Sprite Forge

# 8

Dự phòng P2

Vậy là 12 công cụ ưu tiên triển khai hoặc thử nghiệm, 8 công cụ còn lại cài khi cần.

Quan trọng nhất: cài đặt phân tách theo worker, bật Skills theo nhiệm vụ, và tiếp tục cưỡng chế quyền thực thi qua `wkctl`. Không cấp cho Hermes Lead quyền ghi repository, chạy deploy hoặc sử dụng các MCP có chức năng sửa code.
