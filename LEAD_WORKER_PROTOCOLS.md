# Quy chuẩn Phối hợp Lead–Worker (Lead–Worker Operating Protocols)

Tài liệu này xác định nguyên tắc vận hành, ranh giới trách nhiệm và cơ chế tương tác 2 chiều giữa **Hermes (Lead Orchestrator)** và các **Dedicated Coding Workers** (`muse-code`, `deepseek-code`, `glm-code`, `agy-code`, `codex`).

---

## 1. Nguyên Tắc Cốt Lõi: Tách Biệt Tuyệt Đối Vai Trò

```text
┌──────────────────────────────────────────────────────────────────┐
│                   HERMES (LEAD ORCHESTRATOR)                     │
│                                                                  │
│  1. Khảo sát bối cảnh & Phân tích nguyên nhân gốc (Recon & Root) │
│  2. Lập Kế hoạch Thi công (Implementation Plan & Numbered Brief)  │
│  3. Giám sát lộ trình (Watchdog: Chống treo, kẹt loop, đứt quota) │
│  4. Nghiệm thu độc lập đầu ra (Independent Verification)         │
│  ❌ CẤM TỰ GÕ CODE, RSYNC, DOCKER BUILD, LÀM THAY VIỆC CỦA DEV   │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                   1. Giao Plan   │   2. Review & Phản biện
                   thi công       │      (Technical Debate)
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DEDICATED CODING WORKER                        │
│                                                                  │
│  1. Review phản biện kế hoạch với Lead trước khi đụng code      │
│  2. 100% Thi công: Sửa code, refactor, tái cấu trúc              │
│  3. 100% Test Ownership: Tự viết testcase, tự chạy test         │
│  4. Chu trình RED ➔ GREEN ➔ REFACTOR (Đỏ trước khi sửa)          │
│  5. Tự build, lint, sửa lỗi biên dịch trong workspace            │
└──────────────────────────────────────────────────────────────────┘
```

- **Hermes là LEAD, không phải Dev thứ hai**: Người dùng thuê năng lực điều phối, quản trị và kiểm định chất lượng. Việc Hermes tự sửa file, tự patch tay là hành vi vi phạm vai trò, dễ sinh lỗi hồi quy (regression) và biến buổi làm việc thành bãi thử nghiệm chắp vá.
- **Worker chịu trách nhiệm 100% thi công**: Bất kỳ sửa đổi nào trong codebase, từ viết logic đến viết testcase và chạy test đều thuộc quyền và nghĩa vụ của Worker.

---

## 2. Ma Trận Trách Nhiệm Chi Tiết (RACI Matrix)

| Hạng mục công việc | Hermes (Lead) | Worker (Dev) | Tiêu chí & Yêu cầu bắt buộc |
| :--- | :---: | :---: | :--- |
| **Khảo sát yêu cầu & Recon bối cảnh** | **A / R** | C | Hermes đọc hiểu repo, trích xuất token/Figma specs, đo số liệu ban đầu |
| **Lập Kế hoạch thi công (Brief/Plan)** | **A / R** | C | Hermes soạn kế hoạch đánh số, working directory, whitelist file, acceptance checks |
| **Review & Phản biện Kế hoạch** | **A** | **R** | **Bắt buộc**: Worker phản biện kiến trúc, rủi ro, phương án test trước khi code |
| **Viết code tính năng / Bugfix** | I | **A / R** | 100% do Worker thực hiện trong repo workspace |
| **Viết Testcase (Unit & Regression)** | C | **A / R** | 100% do Worker viết; spec phải đo số thật (pixel, vị trí, z-index), cấm chỉ đo biến cờ |
| **Chạy Test & Vòng lặp RED ➔ GREEN** | I | **A / R** | Worker tự chạy test: phải ĐỎ trước khi sửa và XANH sau khi sửa hoàn tất |
| **Giám sát lộ trình (Watchdog)** | **A / R** | I | Hermes kiểm tra mtime file (~5 phút), bắt kẹt loop, phát hiện 429 quota để xoay acc |
| **Nghiệm thu độc lập đầu ra** | **A / R** | I | Hermes tự chạy bộ test độc lập, đo lại số thật, đối chiếu baseline, cấm tin self-report |

*(R = Responsible/Thực hiện, A = Accountable/Chịu trách nhiệm chính, C = Consulted/Trao đổi phản biện, I = Informed/Theo dõi)*

---

## 3. Quy Trình Vận Hành 5 Bước

### Bước 1: Khảo sát & Lập Kế Hoạch (Hermes Lead)
- Đo đạc chính xác nguyên nhân gốc rễ (root cause recon).
- Soạn một bản kế hoạch thi công (Numbered Implementation Plan / Brief) duy nhất chứa:
  1. **Working directory**: Đường dẫn tuyệt đối của repo làm việc.
  2. **Whitelist file**: Danh sách file được phép chỉnh sửa (nghiêm cấm sửa lan ngoài phạm vi).
  3. **Acceptance Criteria**: Bộ tiêu chí nghiệm thu định lượng bằng số đo thật.
  4. **Prohibitions**: Cấm sửa nới lỏng spec cũ, cấm đo FPS đa viewport trên host không GPU, cấm pkill bừa bãi.

### Bước 2: Review & Phản Biện 2 Chiều (Worker ↔ Lead Debate)
- **Quy tắc bất di bất dịch**: Worker sau khi nhận plan KHÔNG ĐƯỢC cắm đầu vào code ngay.
- Worker phải phân tích phản biện lại kế hoạch:
  - *"Đoạn logic này có mâu thuẫn với module X trong repo không?"*
  - *"Tiêu chí testcase Lead đưa ra có đo đúng triệu chứng người dùng thấy hay chỉ đo biến trạng thái nội bộ?"*
  - *"Có giải pháp nào tối ưu hơn về kiến trúc và tránh nợ kỹ thuật không?"*
- Nếu có điểm bất hợp lý, Worker gửi ý kiến phản biện lại cho Lead. Hai bên thống nhất giải pháp cuối cùng (**Final Consensus**) rồi mới chuyển sang thi công.

### Bước 3: Thi Công 100% & Chu Trình Testcase (Worker)
- Worker thực hiện toàn bộ việc code và refactor.
- **Quy ước Testcase bắt buộc**:
  - Với mỗi lỗi/tính năng, Worker **PHẢI tự viết testcase/spec hồi quy riêng**. Thiếu spec = Chưa xong.
  - Testcase phải đo số thật (pixel, mã màu, toạ độ tuyệt đối, số node DOM, status code, payload thực).
  - Tuân thủ chu trình **RED ➔ GREEN**: Chạy test thấy ĐỎ (chứng minh lỗi tồn tại) ➔ Sửa code ➔ Chạy test lại thấy XANH (chứng minh lỗi đã được giải quyết).

---

## 4. Quy Tắc Cổng Kiểm Thử 2 Lần Bắt Buộc (Two-Stage Testing Gate)

Tuyệt đối KHÔNG ĐƯỢC tin vào một lần test duy nhất. Mọi task code/sửa lỗi bắt buộc phải vượt qua **2 CỔNG TEST ĐỘC LẬP**:

```text
┌──────────────────────────────────────────────────────────────┐
│  CỔNG 1: PRE-DEPLOY LOCAL GATE (Tại Repo / Workspace Cục Bộ)  │
│                                                              │
│  - Worker chạy toàn bộ testcase trên bản local.              │
│  - Điều kiện: XANH 100% (Pass toàn bộ test, 0 compile error, │
│    không gây lỗi hồi quy / regression).                      │
│  - ⛔ NẾU LOCAL ĐỎ ➔ CẤM TUYỆT ĐỐI KHÔNG ĐƯỢC DEPLOY.         │
└──────────────────────────────┬───────────────────────────────┘
                               │ Local pass 100%
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               TIẾN HÀNH BUILD & DEPLOY LÊN HOST              │
│  (Rsync đủ cây, build container, reload service)              │
└──────────────────────────────┬───────────────────────────────┘
                               │ Deploy thành công
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  CỔNG 2: POST-DEPLOY LIVE GATE (Trên Môi Trường Đã Deploy)   │
│                                                              │
│  - Chạy lại TOÀN BỘ bộ testcase trực tiếp trên runtime thật: │
│    live container, live URL, đúng account đối chứng.         │
│  - Đo số thật trên production/staging (pixel, layout,        │
│    status code, socket response).                            │
│  - Loại bỏ hoàn toàn rủi ro: rsync thiếu file, bundle Next.js│
│    bị cache cũ, sai lệch env giữa local và container.        │
│  - ⛔ NẾU LIVE ĐỎ ➔ BỊ COI LÀ FALSE-DONE, PHẢI SỬA LẠI NGAY.  │
└──────────────────────────────────────────────────────────────┘
```

1. **Lần 1 — Pre-Deploy Local Gate**:
   - Chạy trên workspace của worker. Phải pass 100% các spec trước khi cho phép tiến hành khâu deploy.
   - Nếu testcase local còn trượt hoặc vỡ build mà đem deploy là vi phạm quy trình nghiêm trọng.
2. **Lần 2 — Post-Deploy Live Gate**:
   - Sau khi deploy xong (ví dụ rsync đủ 4 cây thư mục, Next.js build bundle mới, docker container up), BẮT BUỘC phải kích hoạt test suite chạy lại lần thứ hai nhắm thẳng vào live URL / runtime thật.
   - Chỉ khi bản live trả về kết quả XANH và đo đúng số thật thì task mới chính thức được đóng.

---

## 5. Watchdog — Giám Sát Tiến Trình Chống Treo/Chết (Hermes Lead)
- Hermes theo dõi tiến trình nền qua PID được cấp phát:
  - **Kiểm tra mtime**: Sau ~5 phút mà các file mục tiêu không có mtime mới ➔ Worker đang lý thuyết suông (theorizing/looping), cần can thiệp kéo về thực tế.
  - **Bắt vòng lặp vô tận (Looping watchdog)**: Phát hiện hành vi chạy test liên tục 10 lần mà không sửa code, hoặc đo đạc vô nghĩa.
  - **Xử lý sự cố chết/treo & Hết Quota**: Bắt lỗi HTTP 429 / `RESOURCE_EXHAUSTED` để kích hoạt cơ chế xoay profile (ví dụ `agy-runner` tự nhảy sang `acc2`, `acc3`), không để chết tác vụ giữa chừng hoặc đốt sạch ngân sách vô ích.

### 5b. Cron watchdog đi kèm mỗi worker (BẮT BUỘC)
- Mỗi lần spawn worker (muse/mini/glm/codex/agy) **phải tạo kèm 1 cron job** theo dõi tiến độ liên tục và báo cáo về chat — user không phải hỏi "xong chưa".
- Tạo cron **kèm `--model` + `--provider` ngay lúc tạo** (không tạo trước set sau):
```bash
hermes cron create --model thtung-muse --provider custom:THTUNG \
  --name "watch-<TÊN-WORKER>" --deliver origin "every 1m" \
  "<prompt watchdog: pgrep worker/Unity, tail log brief, check artifact + curl endpoint, báo tiến độ ≤10 dòng; worker xong hoặc treo >10 phút thì báo ngay>"
```
- ⚠️ Bẫy đã gặp thật (2026-10-02): tạo cron **không** kèm model/provider rồi `edit` thêm sau → job chạy với config cũ, fail liên tiếp `No LLM provider configured`. Luôn tạo kèm từ đầu.
- Khi worker xong (REPORT tồn tại) hoặc chết: báo kết quả cuối 1 lần rồi **xóa cron** (`hermes cron remove <job_id>`) để khỏi spam.
- Tên cron theo quy ước `watch-<TÊN-BRIEF>` để dễ truy vết worker nào.

## 6. Nghiệm Thu Độc Lập Đầu Ra (Hermes Lead)
- Báo cáo tóm tắt của worker chỉ là tài liệu tự thuật (self-report), không phải sự thật đã kiểm chứng.
- Hermes độc lập đo đạc lại:
  - Soát `git diff` xem worker có làm đúng whitelist và không nới lỏng spec cũ hay không.
  - Kiểm tra cả 2 lần test: Cổng 1 (Local) đã xanh chưa, Cổng 2 (Live deploy) đã xanh chưa.
  - Đo lại số thật trên artifact đã deploy/build bằng đúng tài khoản và URL chuẩn.
- Báo cáo kết quả về Discord: Báo cáo ngắn gọn, tập trung vào số đo thực tế, nêu rõ cái gì ĐÃ XONG và cái gì CHƯA XONG. Tuyệt đối không kể lể lại hành trình.

---

## 7. Tiêu Chí Lựa Chọn Worker & So Sánh Thực Tế (Worker Routing Matrix)

Dựa trên kết quả benchmark đối đầu thực tế qua 5 giai đoạn (P1–P5) xây dựng engine và hoàn thiện game:

| Tiêu chí so sánh | Worker A: `@deepseek-ai/dsh` | Worker B: `mini-swe-agent` |
|---|---|---|
| **Số bước thực thi (Steps)** | 826 steps (kỹ tính, kiểm tra lặp lại nhiều lần) | **564 steps (tiết kiệm hơn ~32% chi phí)** |
| **Tốc độ Unit test (Vitest)** | **1.02s / 146 tests (mock sạch, chạy siêu tốc)** | 19.30s / 102 tests (chậm hơn x18.9 lần) |
| **Kích thước Bundle JS** | 500 kB (chạm ngưỡng warning của Vite) | **434 kB (nhẹ hơn ~13%)** |
| **Đỉnh RAM Browser (Heap Peak)** | 95.70 MB | **88.40 MB (tiết kiệm bộ nhớ hơn)** |
| **Khả năng tự sửa lỗi (Self-healing)** | **Rất cao: tự viết script `.dbg.mjs`, vá tận gốc core engine & API** | Trung bình: cần Lead can thiệp runner script khóa workspace |
| **Độ hoàn thiện UI/UX** | **Không lỗi layout, Bestiary Master-Detail, stats đầy đủ** | Sáng tạo thư pháp chữ Hán, nhưng sót lỗi tràn thanh cuộn |

### Quy tắc điều phối của Lead:
* **Chọn Worker A (`dsh`):** Khi cần xây dựng logic phức tạp, hệ thống engine lõi đòi hỏi test suite đồ sộ, chạy CI/CD tốc độ cao và cần UI hoàn chỉnh thương mại.
* **Chọn Worker B (`mini-swe-agent`):** Khi cần triển khai tính năng nhanh gọn, tiết kiệm chi phí gọi mô hình LLM, và tối ưu dung lượng cho web/mobile nhẹ nhàng.

