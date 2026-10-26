# Cấu trúc dự án hop-ban-chai-dien

Điểm bắt đầu: [README](../README.md). Source chính và script chạy giữ ở thư mục gốc. Chuẩn thư mục áp dụng ngày 26/10/2026.

## File và thư mục hiện có

Source: `hop-ban-chai-dien.scad; in-thu.scad`.

- [reference/](../reference/): đầu vào tham chiếu và nguồn hỗ trợ.
- [exports/](../exports/): đầu ra CAD, preview và report theo pipeline.
- [docs/](../docs/): tài liệu project và ảnh minh họa.
- [fusion/](../fusion/): script/manifest, hướng dẫn và test Fusion.
- [tests/](../tests/): kiểm thử project.

reference giữ các bộ source/build hỗ trợ trước đây trong Nguon; cấu trúc con và vai trò từng bộ được bảo toàn.

## Quy ước dùng chung

- `exports/` chứa đầu ra; README/manifest xác định bộ hiện hành và revision nguồn.
- `reference/` chứa input và provenance khi có; `assets/` giữ tài nguyên runtime khi có.
- `docs/` chứa tài liệu, `work/` chứa checkpoint/khảo sát local, `work/tmp/` chứa file thử và `backups/` chứa snapshot khi cần. Thư mục được tạo theo dữ liệu thực tế.
- `archive/` giữ phiên bản lịch sử khi project dùng cơ chế đó. Các thư mục chuyên biệt tiếp tục theo pipeline hiện có.
- Kiểm source/đường dẫn, render, native Fusion, slicer và thử vật lý có trạng thái bằng chứng riêng trong hồ sơ kỹ thuật.

## Tra đường dẫn lịch sử

`Nguon/` được đổi thành `reference/`. Report, snapshot và log cũ giữ thông tin tại thời điểm chạy; áp dụng bản đồ trên khi tra locator cũ. Tài liệu và script đang dùng tham chiếu vị trí hiện hành.
