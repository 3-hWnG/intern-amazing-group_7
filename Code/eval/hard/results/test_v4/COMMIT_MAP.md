# Đối chiếu hash commit (25/10/2026)

Trưởng nhóm yêu cầu sửa message của 5 commit cuối. Lúc sửa, các commit này mới chỉ nằm ở máy, chưa push.

- Cách sửa: dựng lại từng commit bằng `git commit-tree`. Tree (nội dung tệp), tác giả và ngày giờ của mỗi commit giữ nguyên; chỉ message thay đổi.
- Chuỗi commit cũ vẫn tra được qua tag `archive/2026-10-25-before-message-fix`.
- Trong `stamp.txt` có dòng `commit 9c6051a`. Dòng này được ghi lúc chạy nên giữ nguyên; commit đó ứng với `88cabd6` trong bảng dưới.

| Cũ | Mới | Tree (giống nhau) | Commit |
|---|---|---|---|
| 834cf9d | 65b55af | 1031329d85 | baseline RAG + 4B, chọn prompt v2 trên dev |
| ae1fd25 | a79ec5f | f0f1a7a9ca | khoá nhãn real_v4 |
| 2a5bf40 | dad34b7 | fdeb030e03 | chạy test real_v2 một lần cho baseline RAG |
| 9c6051a | 88cabd6 | e961e32976 | luật vòng 2 sau cờ `S3_R2`, đóng băng trước real_v4 |
| 4f9105c | 536d2be | ca0448366e | chạy real_v4 một lần cho mỗi cấu hình |

Nội dung đã sửa trong message:
- **834cf9d:** bản cũ ghi "ba biến thể prompt khai báo trước mọi lượt chạy". Thực tế v1 được viết và chạy trên dev trước; sau đó v2 và v3 mới được khai báo cùng lúc, trước khi chạy cả hai.
- **2a5bf40:** bỏ đoạn đính chính cho 834cf9d, vì message của 834cf9d đã được sửa.
- **834cf9d, 9c6051a:** sửa thêm ba số bị làm tròn hai lần: độ chính xác cân bằng trên dev của prompt v2 là 0,445 (không phải 0,446), của A+R2+C chỉ dùng tên là 0,9252 (không phải 0,9251), của A là 0,8564 (không phải 0,8563).
- **4f9105c:** bản cũ ghi mức tăng trên dev là "+29/−1". Con số đó là của lượt trung gian; với cấu hình đã chọn, mức tăng là +25/−0 về hành vi.
- Mọi hash nhắc trong message đều đổi sang hash mới.
