# Quy chuẩn QA tự động Pokiwar (tài liệu mang từ project /poki)

Nguồn thực thi: `/poki/docs/QUY-CHUAN-TEST-POKIWORLD.md` (quy chuẩn),
`/poki/docs/qa/petdetail-regression-matrix.md` (ma trận hồi quy mẫu),
`/poki/tools/webgl-qa/` (runner `qa.sh` + specs).

Repo này chỉ giữ TÀI LIỆU (không mang bộ test vào).

## 0. Chia vùng 4 project (đừng lẫn)

| Project | Vị trí | Số lượng | Chạy gì |
|---|---|---|---|
| Web Next.js | `pokiwar-web-test/e2e/*.spec.ts` | 141 spec | Trang web + API Server Action (túi đồ, event, shop) |
| Client Vite | `pokiwar-client/e2e/*.spec.ts` | 16 spec | UI client battle, home, login, chat |
| Game server | `colyseus-server/tests/**/*.test.ts` | 25 file Jest | Logic phòng, sách skill, luật game |
| WebGL QA | `tools/webgl-qa/specs/*.py` | 5 spec Python | Client Unity qua CDP: smoke, match, evo, skills, petdetail |

Test quét pixel NẰM Ở WebGL QA (`specs/pet_detail.py` + `src/frame_capture.py`):
đo pixel vùng ROI trước/sau click để chứng minh nút bấm phản ứng thật
(ngưỡng đổi > 0.3%), kèm check pixel variance chống ảnh đen/rỗng.
Không thuộc 141 spec web.

## 1. Stack kiểm thử

- Web Next.js 15: Playwright `@playwright/test`, workers 1 chống xung đột DB,
  Chromium headless thật trên Linux.
- Unity WebGL: Playwright + CDP (`InputController`), tọa độ logic 1920x1080,
  `SyncWaiter` (console oracle) thay `time.sleep`.
- Backend harness: MySQL trực tiếp (`mysql2/promise`) vào DB test `poki_test`,
  mint JWT HS256 (`jose`) ra cookie `poki_session`, gọi Next.js Server Action
  qua header `Next-Action` (manifest `server-reference-manifest.json`).
- Môi trường tách biệt: container web test riêng (`:3007`), DB test riêng,
  tắt captcha trên web test, CẤM ghi DB prod.

## 2. Năm quy tắc cốt lõi

1. **Đo số thật, cấm biến nội bộ.** Assert trên DOM render thật
   (`innerText`, `count`, `boundingBox`, `scrollWidth`), DB thật
   (`balance`, `quantity`), ms thật, HTTP thật. Cấm assert state
   React/biến window tự chế/chuỗi format client.
2. **Đỏ trước, xanh sau.** Spec phải FAILED trên code chưa có tính năng,
   PASSED sau khi xong. Cấm nới assertion để pass giả.
3. **Bảo vệ production.** Mọi spec có guard `DB_NAME === "poki_test"`,
   cleanup seed qua `afterAll`/helper reset.
4. **AI viết spec, Runner làm trọng tài.** Kết luận theo log Playwright,
   không theo suy đoán.
5. **Mỗi bug = 1 regression test** trước khi sửa.

## 3. Suite 8 nhóm (mọi tính năng mới phải phủ đủ)

1. Chức năng & luồng game (happy + unhappy path).
2. Bảo mật & chống gian lận (auth, race/double-click + `lockUser`,
   ledger invariant `SUM(delta) == balance`, anti-negative, dirty input).
3. Phân quyền UI (user `is_admin=0` không thấy nút dev/panel debug;
   admin thấy đủ; screenshot đối chứng).
4. Cross-platform 3 viewport (1440x900, 768x1024, 390x844), chống tràn
   ngang, nút có bounding box thật, ảnh CDN fallback emoji khi 404.
5. Console & network zero-error sau mỗi tương tác (whitelist có kiểm soát).
6. Kinh tế game (sinks/sources, EV gacha, giá shop, mốc khả thi).
7. Hiệu năng (DCL < 2000ms, full load < 3500ms, action avg < 1200ms,
   batch 10 song song < 7000ms, DOM <= 1500 nodes, tab-loop growth <= 15%).
8. Biên & tương thích ngược (zero state, deep link F5, cộng dồn nguồn cũ).

## 4. Checklist thi công (RED → GREEN → tsc → screenshot → sync → web-test → docs/commit)

1. Viết spec đỏ phủ 8 nhóm. 2. Thi công code. 3. Chạy xanh 100%.
4. `tsc --noEmit` sạch. 5. Screenshot đa nền tảng + Admin/User.
6. Sync mã nguồn các cây. 7. Rebuild web-test, check `/api/healthz`.
8. Cập nhật plan + commit/push.

## 5. Quy tắc seed (M94)

Seed đi qua đúng đường người chơi / hàm sản xuất (action UI gọi),
CẤM `INSERT` thẳng bảng đích. Ngoại lệ tăng tốc nhiều ngày chơi:
dùng đúng nút dev (`devCompleteQuest`, `devGrant`, phiên admin),
nhận/tiêu vẫn qua producer thật với acc người chơi (`is_admin=0`).
CẤM dùng admin thật 46 trong test.

## 6. Unity WebGL input (InputController)

- CẤM DOM click/dispatchEvent tổng hợp; BẮT BUỘC CDP mouse/keyboard.
- Tọa độ logic 1920x1080, quy đổi qua bounding box canvas động.
- `click`, `double_click`, `click_and_type`/`type_text` (clear trước),
  `fill_login_form`, `drag` (steps >= 6, hold >= 150ms),
  `dismiss_announcement_popups`, `navigate_sequence` + break condition.
- Đồng bộ bằng `SyncWaiter` (đợi console/backend), chụp `FrameCapture`
  xác nhận visual; không `time.sleep`.

## 7. Luật no-fake-green (ma trận hồi quy)

- Lỗi user đã báo mà chưa sửa = FAIL, không phải BLOCKED.
- Tổng suite FAIL (exit != 0) khi còn bất kỳ R nào FAIL.
- Ảnh đen/rỗng KHÔNG tính PASS; thiếu tiên quyết → BLOCKED.
- Mỗi lỗi user báo >= 1 test assert thật (console oracle / HTTP /
  pixel có ngưỡng / EditMode trên prefab thật).
- Gate mẫu (màn pet detail): `qa.sh test petdetail` + EditMode
  `ScreenPetDetailSkillPopupTests` xanh 100% trước mọi bàn giao.
