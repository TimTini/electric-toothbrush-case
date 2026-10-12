# Công cụ bản in thử

Source chính: `../../in-thu.scad`.
Đầu ra: `../../exports/in-thu/`.

Chạy từ thư mục gốc của project:

```powershell
python Nguon/electric-toothbrush-case-print-test/build.py --previews
python Nguon/electric-toothbrush-case-print-test/audit_trial.py
```

OpenSCAD cần có trong PATH, hoặc truyền `--openscad` với đường dẫn executable. Audit bản thử so sánh đáy, cổ và ren với STL bản đầy đủ. Xem README ở thư mục gốc để cài dependency và chạy đủ bộ kiểm tra.
