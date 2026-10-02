# Cơ chế Frame-to-Frame (clips.json) — Burning pipeline từ HTML/Spine → sprite frame trong game

> Folder này dành riêng cho tài liệu cơ chế **frame-to-frame** (hoạt hình tua ảnh theo frame).
> Áp dụng cho game auto-battler (`autobattler-game`, cổng8080) — xương sống render **41/41 tướng** hiện tại.
> Nguồn case-study thực tế: file `stickman-game.html` ("Kiếm Khách Que") được người dùng upload, port vào game (TASK CF).

---

##1. Tổng quan — frame-to-frame là gì?

Hoạt hình **vẽ sẵn từng hình rời** rồi tua theo thứ tự (giống flipbook/hoạt họa truyền thống), **không** dùng khung xương (skeleton) hay runtime tính toán bone như Spine.

```text
idle_0.png → idle_1.png → … → idle_13.png   (đổi ảnh theo thời lượng clip → mắt thấy chuyển động)
```

So sánh với Spine:

| | Frame-to-frame (clips.json) | Spine (skeletal) |
|---|---|---|
| Asset | PNG thường + manifest `clips.json` | `.atlas` + `.json` skeleton + runtime riêng |
| Runtime | Đổi ảnh (blit texture) | Tính bone/IK/mesh nội suy mỗi frame |
| CPU / mobile | **Rất rẻ** | Nặng hơn (runtime + tính toán) |
| Uốn dẻo pose | Không (pose đã vẽ cứng theo frame) | Có (nội suy trơn giữa pose) |
| Vị trí trong hệ thống | **Chạy thật trong game** | Chỉ dùng ở tool **preview** (`ark-spine-previewer`), game **không** cài spine runtime |

Kiến trúc hiện tại: **game chạy100% frame-to-frame**; Spine tồn tại như tool xem/preview; kho asset GitHub `Tiddybub/2d-assets` (CC0,50k PNG/GIF…) là nguồn frame thường, **không phải Spine**.

---

##2. Nguồn case-study: `stickman-game.html`

File HTML tự chứa (single-file), vẽ nhân vật bằng **canvas2D procedural** — tức hình ảnh sinh ra từ code, không có file ảnh sẵn:

###2.1 Khung xương + pose (rig)
- **14 kênh pose** trên1 thân: `lean, head, uaF, faF, uaB, faB, thF, shF, thB, shB, sword, gun, ham, can` (góc tính theo phương thẳng xuống, dương = hướng nhìn).
- Hàm `rig(pose, x, y, facing, scale)` biến pose → toạ độ khớp: hip → neck → sh → head, tứ chi `dn(o, angle, len)` (sin/cos), thanh `armIK` hai xương cho tay sau (cắm đúng grip súng/búa).
- **4 nhân vật dùng chung1 rig**: Kiếm khách (kiếm + khăn verlet), Xạ thủ (sạc plasma), Titan (robot plate + búa neon), Phi Ưng (cánh + cannon).

###2.2 Pose + keyframe tấn công
- Pose mẫu: `poseIdle(t)`, `poseRun(phase)`, `poseAir(vy)`, `poseEGuard`, …
- Mảng keyframe tấn công (mỗi entry = `[thời gian (0..1), easing 'e'|'s', pose]`):
  - `ATK` (kiếm khách,3 chiêu), `ATKT` (Titan, có slam), có trường `dur, a0, a1, step, dmg, reach`.
  - `sampleAtk(A, t)` nội suy giữa2 keyframe (`smooth` = `t²(3−2t)`, `outCubic` cho nhịp chém nhanh).
- Toàn bộ số liệu pose/keyframe này là **nguyên liệu để bake frame** (xem §3).

###2.3 Vẽ nhân vật
`drawFigure(J, col, back, opt)` vẽ các đoạn thẳng (lineCap round) theo khớp đã rig; vũ khí có hàm riêng `drawSword / drawGun / drawCannon / drawWing / drawHammer`, robot có `drawRobot` (plate, joint neon, ngực phát sáng), khăn có hệ **verlet rope** (`initScarf/updScarf`).

---

##3. Bake pipeline: HTML/pose → PNG frame + `clips.json`

Công cụ (trong repo game): `tools/stickman/bake.mjs` + `tools/stickman/harness.html`

```text
stickman-source.html (nguồn, copy vào vendor/)
        │  đọc chính các hàm rig()/pose*/draw* CỦA FILE GỐC
        ▼
harness.html  — trang nạp code nguồn, set pose theo timeline clip,
                vẽ lên offscreen canvas (mỗi frame1 lần)
        ▼
bake.mjs (chạy headless) — xuất PNG cho từng frame
        │
        ├─► assets/units/stickman_sword/idle_0.png … idle_13.png
        ├─► assets/units/stickman_sword/walk_*.png  (24)
        ├─► assets/units/stickman_sword/attack_*.png (30)
        ├─► assets/units/stickman_sword/death_*.png  (8)
        └─► assets/units/stickman_sword/clips.json    ← manifest
        (lặp lại cho stickman_gun / stickman_titan / stickman_fly)
```

**Nguyên tắc pixel-faithful**: bake dùng **đúng code vẽ + pose + easing của file gốc**, nên frame ra giống hệt bản HTML (không phải vẽ lại tay). Kết quả4 tướng = **262 frame PNG** (76+58+70+58).

> Lưu ý: nếu nguồn là **Spine thật** (từ tool preview) thì dùng pipeline capture khác (`scripts/swap-spine-unit.mjs`: chạy Spine runtime headless, bắt frame + heartbeat chống timeout) — cùng đích là PNG + `clips.json`.

---

##4. Định dạng `clips.json` (manifest)

Đặt tại `assets/units/<dir>/clips.json`, khai báo từng clip của đơn vị:

```json
{
  "idle":   { "name": "Idle",    "duration": 3,    "frames": 14 },
  "walk":   { "name": "Move",    "duration": 0.7,  "frames": 24 },
  "attack": { "name": "Attack",  "duration": 1.24, "frames": 30 },
  "death":  { "name": "Death",   "duration": 0.8,  "frames": 8  }
}
```

- **khóa** (`idle/walk/attack/death/…`): tên clip dùng bởi game logic (spawn/idle pool/attack/death trigger).
- **`name`**: tên gốc (Spine track / tên clip nguồn) — truy vết ngược.
- **`duration`**: thời lượng clip (giây) → fps nội suy = `frames / duration`.
- **`frames`**: số frame — file đặt tên `<clip>_0.png … <clip>_{N-1}.png`, **bắt buộc đủ file trên disk** (guard test kiểm tra URL preload khớp file thật).

---

##5. Cách game load & chạy

```text
Units.js (registry)
  unit = { id: 'stickman_kiemkhach', kind: 'stickman_sword', … }
        │  + comment nguồn (vendor/stickman-source.html), active mặc định
        ▼
GameApp preload — đọc clips.json → dựng danh sách URL frame → tải trước (4.003 URL dạng này ở time-of-check)
        ▼
UnitRenderer — nhánh resolve (phân nhánh pipeline, mỗi unit tự khai kind):
   A) clips.json frames  ← 41/41 tướng hiện tại (gồm stickman)
   B) sprite still / avatar (fallback)
   (không có nhánh spine runtime — game không cài package spine)
        ▼
Battle loop — theo state (idle/walk/attack/death) + đồng hồ clip:
   frame_index = floor(elapsed / (duration / frames)) % frames
   → gán texture (đổi ảnh), có crossfade blend nếu hợp đồng yêu cầu
```

Đặc điểm vận hành:
- **0 tính toán xương** mỗi frame → mobile-sound (chính lý do chọn bake thay vì vector runtime cũ).
- Fallback trung thực: unit thiếu frame rơi về procedural **có log lỗi** (`console.error`) + guard test chặn commit khi unit "frameless".
- Có hợp đồng blend/frame-skip riêng (vd `FrameBlendSkips` regenerate khi thêm frame).

---

##6. Workflow thêm tướng mới theo cơ chế này

1. **Có nguồn**: (a) file HTML/canvas procedural → bake bằng harness (như stickman); hoặc (b) model Spine → capture headless (`swap-spine-unit.mjs`, watchdog plan-size + heartbeat120s).
2. Chạy bake/capture → sinh `assets/units/<dir>/*.png` + `clips.json`.
3. **Register** trong `src/data/Units.js` (id, kind, stats, active/inactive).
4. **Test**: đủ frame (guard), clips manifest khớp file, per-clip logic (idle pool/attack/death), preload URL tồn tại, perf.
5. **Evidence**: ảnh card roster + ảnh battle + video (bắt buộc mắt kiểm tra trước khi báo).
6. Service `:8080` là static server — **không restart**, chỉ commit + push.

---

##7. Checklist nghiệm thu (đội Lead kiểm)

- [ ] `clips.json` có đủ4 clip chuẩn (idle/walk/attack/death) trừ khi nguồn thiếu (phải ghi chú trung thực).
- [ ] Số file PNG trên disk == tổng `frames` của manifest (guard test xanh).
- [ ] Frame giống nguồn (soi vision/đối chiếu, không vẽ lại tay).
- [ ] Đơn vị xuất hiện đúng trong roster + battle, effect (`kind` đúng nhánh).
- [ ] Không regression các suite hiện có; full `npx vitest run --maxWorkers=4` xanh.
- [ ] Mobile size không vỡ layout; perf không tăng (frame blit).

---

##8. Tham chiếu nhanh

- Case-study đầy đủ: task `TASK_STICKMAN_PORT.md` (repo `autobattler-game`) —4 tướng + map `hoanghon`, evidence `verify_cf_*.png`, `cf_stickmen.webm`.
- Bảo trì bake: `tools/stickman/bake.mjs`, `tools/stickman/harness.html`.
- Spine capture: `scripts/swap-spine-unit.mjs` (repo `autobattler-game`).
- Tool preview Spine + kho frame CC0: repo `ark-spine-previewer` (port8082), nguồn `github.com/Tiddybub/2d-assets`.
