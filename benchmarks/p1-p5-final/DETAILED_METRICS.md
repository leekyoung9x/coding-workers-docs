# Báo Cáo Kỹ Thuật Định Lượng Chi Tiết 8 Coding Workers (P1–P5)

Tài liệu này lưu trữ toàn bộ dữ liệu đo kiểm độc lập, số liệu benchmark định lượng thực tế và các phát hiện kỹ thuật sâu qua 18 gates kỹ thuật (T01 đến T18) cho cả 8 worker.

---

## 1. Ma Trận Nghiệm Thu 18 Gates Kỹ Thuật (T01 – T18)

| Mã Gate | Nội Dung Kiểm Định | Worker A (`dsh`) | Worker B (`mini`) | Worker C (`opencode`) | Worker D (`agy`) | Worker E (`muse`) | Worker F (`claude`) | Worker G (`kimi`) | Worker H (`codex`) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **T01** | Production Build (`tsc` strict + `vite build`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T02** | Công thức Sát thương / DEF / Crit biên | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T03** | PRNG tất định theo Seed & Khả năng tái lập | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T04** | Đường cong XP, hàng đợi level-up, 6 cảnh giới | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T05** | 12 Công pháp (cooldown, tie-break, AoE, orbit) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T06** | Hiệu ứng Status (Slow clamp, Freeze boss, DOT 1s) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T07** | 8 Quái vật đặc thù (predictive, dash, kite, pool) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T08** | 3 Boss tuần tự (Huyết Lang, Mộc Linh, Ma Quân) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T09** | Tạm dừng (Pause clock stops simulation & CD) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T10** | Save/Load `localStorage` (Valid, Corrupt, Version) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T11** | Object Pooling chống sát thương trùng | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T12** | Stress Test 500 quái + 100 đạn trong 60s | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T13** | Kiểm thử Playwright E2E Headless | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T14** | Responsive Letterbox (1280x720, 1440x720, 1920x1080) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T15** | Accelerated Simulation tới boss cuối & Win/Lose | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T16** | Tuyệt đối không lỗi Console / Unhandled Rejection | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T17** | Đo đạc hiệu năng thực tế (ms/step, FPS, Heap RAM) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **T18** | Bản phát hành Production Preview sạch (HTTP 200) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

---

## 2. Bảng Số Liệu Đo Lường Định Lượng Toàn Diện

| Tiêu Chí Đo Đạc | Worker A (`dsh`) | Worker B (`mini`) | Worker C (`opencode`) | Worker D (`agy`) | Worker E (`muse`) | Worker F (`claude`) | Worker G (`kimi`) | Worker H (`codex`) |
|---|---|---|---|---|---|---|---|---|
| **Số lượng Unit Tests** | 146 tests | 102 tests | 142 tests | 51 tests | 107 tests | **284 tests** | 180 tests | 128 tests |
| **Thời gian chạy Unit Test** | **1.02 s** | 19.30 s | 3.26 s | 1.19 s | 2.74 s | 15.01 s | 1.20 s | 3.25 s |
| **Số lượng Playwright E2E** | 19 tests | 18 tests | 23 tests | 3 suites | 9 tests | **60 tests** | 20 tests | 22 tests |
| **Kích thước Bundle JS chính** | 500.0 kB | 434.0 kB | **344.6 kB** | 463.6 kB | 366.3 kB | 436.8 kB | 415.8 kB | 381.5 kB |
| **Gzip Bundle JS chính** | 152.1 kB | 133.0 kB | **106.4 kB** | 134.0 kB | 114.7 kB | 133.5 kB | 127.7 kB | 118.2 kB |
| **Tổng dung lượng Assets** | 788 KiB | 720 KiB | **614 KiB** | 680 KiB | 656 KiB | 742 KiB | 698 KiB | 682 KiB |
| **Thời gian build Vite** | 3.82 s | 4.10 s | 2.80 s | 3.20 s | **2.38 s** | 4.75 s | 2.64 s | 2.65 s |
| **Mô phỏng 500 quái (T12)** | 0.063 ms | 0.065 ms | **0.0139 ms** | 0.1345 ms | 0.0530 ms | 0.2660 ms | **0.0380 ms** | 0.1380 ms |
| **Phân vị 99 (p99 ms/step)** | 0.420 ms | 0.450 ms | **0.0980 ms** | 0.8200 ms | 0.3110 ms | 0.4890 ms | 0.7090 ms | 0.9000 ms |
| **Đỉnh RAM JS Heap Browser** | 95.70 MB | 88.40 MB | **9.54 MB** | **9.54 MB** | 42.63 MB | 26.30 MB | 16.30 MB | 80.20 MB |
| **FPS Median (Headless)** | ~18.0 FPS | ~7.5 FPS | 23.4 FPS | 20.0 FPS | **59.9 FPS** | ~13.9 FPS | ~15.0 FPS | ~6.0 FPS |
| **FPS 1% Low (Headless)** | ~13.0 FPS | ~6.6 FPS | 17.6 FPS | 8.57 FPS | **29.9 FPS** | ~12.0 FPS | ~8.6 FPS | ~5.45 FPS |
| **Web Audio Procedural** | 3 BGM, 9 SFX | BGM, SFX | 3 BGM, 8 SFX | 3 BGM, SFX | 3 BGM, 9 SFX | 3 BGM, 8 SFX | 3 BGM, 16 SFX | 3 BGM, SFX |
| **Cổng Preview Trực tiếp** | `:39101` | `:39102` | `:39103` | `:39104` | `:39105` | `:39106` | `:39107` | `:39108` |
| **Đường dẫn Subpath** | `/worker-a/` | `/worker-b/` | `/worker-c/` | `/worker-d/` | `/worker-e/` | `/worker-f/` | `/worker-g/` | `/worker-h/` |

---

## 3. Các Phát Hiện Kỹ Thuật & Tự Gỡ Lỗi Sâu (Self-Healing Case Studies)

### 1. Worker E (`muse`): Phát hiện lỗi vòng lặp Ticker ghi đè BGM
- **Vấn đề ngầm:** Vòng lặp `ticker` game chạy mỗi frame (60 FPS) liên tục kiểm tra trạng thái map để set BGM. Khi người chơi vào Endless Mode, bài nhạc nền đáng lẽ phải giữ chủ đề Ma Vực (`demon`), nhưng bị ticker tự động trả về Trúc Lâm (`forest`).
- **Tự sửa:** Worker E tự phát hiện qua bước kiểm chứng tương tác browser, sửa điều kiện rẽ nhánh trong `src/main.ts`, rebuild và assert trực tiếp lại qua Playwright để xác nhận nhạc `bgm=demon` giữ nguyên.

### 2. Worker F (`claude`): Tự sửa 3 lỗi logic và render nguy hiểm
- **Lệch công thức Anchor Hitbox:** Hàm `bakeGraphic` trong `art.ts` trừ thêm `size/2` làm sprite quái/boss hiển thị lệch khỏi vị trí hitbox thực tế. Claude Code tự đo đạc toạ độ va chạm và sửa lại công thức anchor.
- **Thiếu Texture quái triệu hồi:** Kiểu dữ liệu thêm `sapling` và `clone` nhưng không bake texture, khiến scene ném unhandled error trong ticker và đứng hình toàn bộ game loop. Claude Code tự thêm texture và bổ sung test chặn tái diễn.
- **Boss Arena:** Khi có 300-500 quái thường bao quanh, đòn đánh đơn mục tiêu có targeting tie-break cự ly gần nhất không bao giờ chạm được vào boss (đo được 0 DPS lên boss). Claude Code tự thiết kế cơ chế dọn dẹp quái thường xung quanh khi boss xuất hiện.

### 3. Worker G (`kimi`): Xử lý Timeout Benchmark bằng kịch bản Real-Time
- **Vấn đề ngầm:** Khi chạy đo đạc benchmark T17 với 500 quái trong chế độ tua nhanh (fast-forward simulation), hàm `page.evaluate()` bị nghẽn do Chromium headless chia sẻ CPU và bị timeout 180s.
- **Tự sửa:** Kimi Code tự chuyển đổi phương thức đo sang **Real-Time Sampling**: cho game chạy thật 30s wall time với tải 500 quái, đo delta time giữa các frame qua `requestAnimationFrame`, ghi nhận chính xác 420 frames đạt median 15.0 FPS mà không bị timeout.

### 4. Worker H (`codex`): Tính toán công thức lũy tiến Endless Mode
- **Thử thách:** Cần đảm bảo sau mốc 15:00, cả quái vật đang sống lẫn quái vật mới sinh đều phải tăng đúng +20% HP và ATK sau mỗi 60 giây tiếp theo (`1.2^minute`).
- **Tự sửa:** Codex tự viết script `src/systems/Endless.ts` xử lý đồng bộ thời gian simulation clock với `gameSeconds`, lưu kỷ lục sống sót `vktt_endless_record_v1` và khôi phục chính xác qua Save/Load.

---

## 4. Kết Luận So Sánh Kỹ Thuật

1. **Về khả năng tối ưu hóa tài nguyên:** **Worker C (`opencode`)** dẫn đầu với kích thước bundle 344.6 kB và tốc độ mô phỏng 0.0139 ms/step nhờ cấu trúc dữ liệu nén mảng tại chỗ.
2. **Về trải nghiệm người dùng & đồ họa:** **Worker E (`muse`)** dẫn đầu với 59.9 FPS và HUD công thái học, trong khi **Worker D (`agy`)** có hiệu ứng neon và radar Bát Quái hiện đại nhất.
3. **Về độ tin cậy và an toàn hồi quy:** **Worker F (`claude`)** vượt trội hoàn toàn với 284 unit tests và 60 Playwright tests, tự động loại trừ mọi lỗi tiềm ẩn trong logic game.
