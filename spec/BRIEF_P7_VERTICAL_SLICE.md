# ĐẶC TẢ GIAI ĐOẠN P7 — VERTICAL SLICE: AI ART & CHARACTER ANIMATION FACTORY

**Phiên bản:** 1.0 (Chính thức)  
**Trọng tâm:** Thử nghiệm dây chuyền sản xuất hoạt họa 2D Anime Chibi bằng AI trên 01 Vertical Slice hoàn chỉnh trước khi mở rộng sản xuất hàng loạt.  
**Mục tiêu cốt lõi:** Chứng minh hệ thống AI tự tạo nhân vật Anime 2D, các bộ action chuyển động, tách VFX, căn chỉnh tọa độ chống trượt chân, đóng gói Sprite Atlas và nạp mượt mà vào PixiJS 8 Runtime.

---

## 1. Ba Ràng Buộc Kỹ Thuật Bất Khả Xâm Phạm
1. **Môi trường hạ tầng:** Ubuntu VPS (CPU-first), không yêu cầu GPU rời cho các tác vụ xử lý ảnh, căn chỉnh và điều phối.
2. **Động cơ sinh ảnh:** Google Image API (Imagen 3 / Gemini Image) sinh ảnh từ xa; ComfyUI đóng vai trò API-only workflow engine (không cài node AI local nặng CUDA).
3. **Hình thức hoạt họa:** Frame-by-frame 2D animation truyền thống kết hợp variable frame duration; chưa dùng Spine/Skeletal animation.

---

## 2. Phạm Vi Gói Mẫu Vertical Slice (Giai đoạn Mở màn P7)
Tuyệt đối không sinh hàng loạt toàn bộ 11 quái vật và 3 đại boss ngay từ đầu. Dây chuyền P7 bắt buộc phải vượt qua bài kiểm tra nghiệm thu trên **01 Gói Mẫu duy nhất**:

### A. 01 Nhân vật Tiên Hiệp: "Thanh Vân Kiếm Sĩ"
* **Định danh:** `character_id: "player_swordsman"`
* **Master Reference:** 01 ảnh chuẩn độ phân giải cao toàn thân (chính diện và góc nghiêng 3/4) mang phong cách Anime Chibi: tóc đen búi trâm ngọc, đạo bào thanh lam viền vàng kim, tay cầm thanh đoản phi kiếm.

### B. 04 Bộ Actions Chuyển Động (Tổng 26 frames):
1. **`idle` (Nghỉ / Thở):**
   * *Số lượng:* 8 frames (loop liên tục, ~10 FPS).
   * *Nội dung:* Chân trụ bám đất, lồng ngực nhấp nhô nhẹ, tà áo và dải trâm đung đưa tự nhiên theo chu kỳ.
2. **`attack1` (Trảm Kích Kiếm Khí — Variable Frame Duration):**
   * *Số lượng:* 6 frames (không loop, tổng thời gian 500ms).
   * *Timeline phân rã:*
     - Frame 1 (150ms): Tụ lực lùi nhẹ trọng tâm (Wind-up).
     - Frame 2 (70ms): Chân bước tới, vung kiếm về phía trước.
     - Frame 3 (40ms): Vung chém cực đại (Smear slash motion) — **Hit Event kích hoạt tại 220ms**.
     - Frame 4 (40ms): Kéo dài xung lực chém (Impact follow-through).
     - Frame 5 (100ms): Khựng thế thu kiếm (Recovery hold).
     - Frame 6 (100ms): Thu chân trở về tư thế thủ (Return to stance).
3. **`hurt` (Trúng Đòn / Bị Thương):**
   * *Số lượng:* 4 frames (không loop, 10 FPS).
   * *Nội dung:* Khựng người, ngửa ra sau, chớp nháy viền đỏ cảnh báo sát thương.
4. **`die` (Tử Trận / Đạo Tiêu):**
   * *Số lượng:* 8 frames (không loop, 12 FPS).
   * *Nội dung:* Kiếm rơi khỏi tay, ngã quỵ xuống đất, cơ thể hóa thành luồng linh quang xanh nhạt tan biến vào hư không.

### C. 01 Hiệu Ứng VFX Độc Lập: "Thanh Quang Trảm" (Slash FX)
* **Quy tắc vàng:** VFX chém kiếm **tuyệt đối không được vẽ dính liền vào người nhân vật**.
* P7 xuất riêng bộ texture vệt chém kiếm hình bán nguyệt (Arc Slash) và các hạt đốm sáng (Sparks).
* Engine P6 sẽ lắng nghe event `vfx_trigger: 180ms` để render vệt chém đè lên trên `vfxContainer`, gắn `GlowFilter` bloom phát sáng thật.

---

## 3. Các Giải Pháp Kỹ Thuật Chống Lỗi Cốt Lõi

### A. Chiến Lược Hai Chế Độ Sinh Keyframe (T33)
* **Ưu tiên 1 — `Grid Mode` (Tiết kiệm API):** Ra lệnh cho Google Image API sinh 1 ảnh duy nhất chứa bảng Sprite Sheet lưới (4x2 hoặc 3x3) trên nền đồng nhất. Nếu bộ QA (T35) xác nhận 8 frame đủ, không bị cụt kiếm và tỷ lệ nhân vật đồng nhất $\rightarrow$ chấp nhận.
* **Fallback 2 — `Sequential Mode` (Bảo toàn Consistency):** Nếu Grid Mode bị biến dạng hoặc thiếu frame, tự động chuyển sang sinh tuần tự: gửi kèm `master_reference.png` + `frame_{n-1}.png` làm tham chiếu thị giác để Google giữ nguyên khuôn mặt, nếp áo và vũ khí.

### B. Hệ Thống Tọa Độ 3 Lớp & Root Motion (T32 — Chống Trượt Chân)
* Khóa cố định 3 thông số:
  - `floorY`: Cao độ đường sàn chung.
  - `rootX / rootY`: Vị trí logic của nhân vật trong gameplay.
  - `anchorX / anchorY`: Điểm neo theo từng frame.
* **Foot Contact Tracking:** Ghi nhận chân tiếp đất. Khi nhân vật bước tới ở frame 2 và 3 của `attack1`, cơ thể dịch chuyển có chủ đích theo Root Motion chứ không ép cứng chân tại một điểm gây giật hình.

### C. Timeline Events Độc Lập Render Loop
* P7 xuất file `timeline.json` quy định rõ mốc thời gian tuyệt đối (mili-giây):
  ```json
  {
    "action": "attack1",
    "totalDurationMs": 500,
    "frames": [
      { "frame": 1, "durationMs": 150 },
      { "frame": 2, "durationMs": 70 },
      { "frame": 3, "durationMs": 40 },
      { "frame": 4, "durationMs": 40 },
      { "frame": 5, "durationMs": 100 },
      { "frame": 6, "durationMs": 100 }
    ],
    "events": [
      { "name": "vfx_trigger", "timeMs": 180 },
      { "name": "hit", "timeMs": 220, "damageMultiplier": 1.0 },
      { "name": "recovery", "timeMs": 400 }
    ]
  }
  ```
* Simulation Engine của P6 sẽ chạy đồng hồ mô phỏng riêng. Đến đúng **220ms**, quái vật trong hitbox bị trừ máu ngay lập tức, bất kể máy người chơi đang render ở 60 FPS hay tụt xuống 20 FPS.

### D. Asset Acceptance Gate (Quy Trình 5 Bước Chống Đè Asset Lỗi)
$$\text{GENERATED} \longrightarrow \text{PROCESSED} \longrightarrow \text{QA\_PASSED} \longrightarrow \text{PREVIEW\_APPROVED} \longrightarrow \text{PUBLISHED}$$
* Game runtime luôn tải asset từ thư mục `PUBLISHED`.
* Bất kỳ asset mới nào bị lỗi viền alpha, lệch chân hoặc biến dạng khuôn mặt sẽ bị giữ lại ở vùng Staging để sửa lỗi hoặc sinh lại, không bao giờ làm hỏng bản game đang chơi.

---

## 4. Nghiệm Thu Qua Preview Studio Độc Lập (T36)
Một trang web preview riêng biệt chạy bằng PixiJS v8 với đầy đủ các công cụ:
- [x] **Frame Scrubber:** Thanh tua chậm từng frame, xem chi tiết từng mili-giây.
- [x] **Pivot Inspector:** Hiển thị tâm `[0.5, 0.9]` và đường sàn `floorY`.
- [x] **Action Transition Test:** Bấm chuyển đổi tức thì `idle → attack1 → idle`, `idle → hurt → idle`, `idle → die` mượt mà, không bị khựng chân.
- [x] **Hit Timing Visualizer:** Thanh hiển thị thời điểm nổ vệt chém kiếm (180ms) và nổ sát thương (220ms) khớp 100% với frame chém.
- [x] **Automated Playwright QA:** Script tự động chạy kiểm thử 100% các tiêu chí trên và xuất báo cáo ảnh/video.
