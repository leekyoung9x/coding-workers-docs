# Skill: Gửi ảnh & video qua Discord (Hermes voice-channel)

Voice channel render markdown Discord chuẩn. Muốn user THẤY ảnh/video thì dùng đúng cú pháp dưới. Sai cú pháp = user thấy khung trống.

## Gửi ảnh: dùng MEDIA: (đường dẫn tuyệt đối, bot tự upload thành đính kèm)

```text
MEDIA:/root/stickman/game3/proof_closeup.png
```

- Mỗi ảnh 1 dòng `MEDIA:<absolute path>`.
- File phải tồn tại trên máy chạy Hermes, dung lượng nên < 10MB (resize/thumbnail trước nếu cần).
- CẤM dùng `![alt](file:///...)` hay `![alt](/local/path)` — Discord không load được file local của server, user chỉ thấy khung trống. Đây là lỗi đã gặp thật (phiên stickman 02/10/2026).

## Gửi video demo gameplay: dùng MEDIA: giống ảnh

```text
MEDIA:/root/stickman/game3/demo.mp4
```

- Video quay từ gameplay thật (Playwright record / canvas MediaRecorder → ffmpeg h264 yuv420p), nên < 10MB để gửi nhanh.
- Ảnh URL `http(s)://` render bình thường; chỉ `file://` là hỏng.

## Checklist trước khi báo "đây ảnh/video"

1. File tồn tại (`ls -lh <path>`).
2. Dùng `MEDIA:<absolute path>`, không bọc trong markdown image.
3. Video đã verify play được (`ffprobe` duration/size).
4. Không bao giờ đổ lỗi "bot không gửi được" khi thực chất là mình dùng sai cú pháp — sai thì nhận, sửa, gửi lại.
