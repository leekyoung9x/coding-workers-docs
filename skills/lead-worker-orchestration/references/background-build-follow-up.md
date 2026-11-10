# Chạy build/test dài ở nền: phải theo dõi tới khi có kết quả

Lead nói "build xong báo" mà không có gì kéo nó dậy khi build chết thì phiên đứng im vô thời hạn.
Sự cố thật (Unity WebGL): build thoát ngay `EXIT:1` vì sai user/giấy phép; lead đã trả lời "chờ 10-15 phút"
rồi kết thúc lượt; không ai biết build đã chết hơn một tiếng.

## Vì sao không có tiếng báo nào (3 lỗi chồng nhau)

1. `> /tmp/build.log 2>&1; echo "EXIT:$?" >> /tmp/build.log`: toàn bộ output vào file, stdout của process
   rỗng. `watch_patterns` chỉ soi stdout nên KHÔNG BAO GIỜ khớp, kể cả khi log có chữ `error`.
2. `notify_on_complete` để mặc định `False`: process kết thúc không gửi thông báo.
3. Lệnh kết thúc bằng `echo`, nên process luôn thoát mã 0 dù Unity thoát mã 1. Mã thoát của process
   không phản ánh kết quả build.

## Cách chạy đúng

- Chạy với `background=true, notify_on_complete=true`; KHÔNG chuyển hướng stdout vào file rồi mới `echo EXIT`.
  Dùng mã thoát thật của lệnh build (`set -o pipefail`, `tee` ra log) để thoát khác 0 khi build hỏng:

  ```bash
  set -o pipefail; <lệnh build> 2>&1 | tee /tmp/build.log; exit ${PIPESTATUS[0]}
  ```

- Sau khi khởi chạy, ĐỌC LẠI sau 20-30 giây, trước khi báo "đang build": process còn sống không,
  log có thêm dòng không. Build thoát trong vài giây là lỗi môi trường (user, quyền thư mục, giấy phép), không phải
  build chạy lâu.

  ```bash
  sleep 25; ps -p <pid> >/dev/null && echo ALIVE || echo DEAD; tail -5 /tmp/build.log
  ```

- Không kết thúc lượt bằng lời hứa "xong t báo" nếu không có gì chắc chắn đánh thức lượt sau (thông báo process
  hoặc cron). Nếu chỉ có `watch_patterns`, mẫu phải gồm cả dấu hiệu THẤT BẠI (`EXIT:[1-9]`, `error CS`, `Aborting`,
  `No valid ... license`) và output phải đi qua stdout.
- Báo cho owner mốc cụ thể: giờ bắt đầu, log ở đâu, kiểm tra lúc nào. Không dùng "ăn cơm đi" như một cách chờ.
- Khi nhận thông báo kết thúc: mở log, đọc dòng cuối và mã thoát thật; nói build xong hay chết kèm lý do. Build chết
  mà không nói gì là báo cáo sai.

## Unity trên VPS này (nguyên nhân sự cố)

Giấy phép Unity nằm ở tài khoản `linuxuser`. Chạy Unity bằng root cho `No valid Unity Editor license found`
(mã 198). Build phải chạy bằng `linuxuser`, và `linuxuser` phải đi qua được thư mục chứa project
(`/root` mặc định `dr-xr-x---`, cần ACL `x` cho `linuxuser` hoặc đặt project ngoài `/root`).
