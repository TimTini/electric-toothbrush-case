# Công cụ bản đầy đủ

Source chính: `../../hop-ban-chai-dien.scad`.
Đầu ra: `../../exports/ban-day-du/`.

Chạy từ thư mục gốc của project:

```powershell
python reference/electric-toothbrush-case-bottom19/build.py --previews --check-variants
python reference/electric-toothbrush-case-bottom19/audit_model.py
python reference/electric-toothbrush-case-bottom19/verify_straight_bore.py
```

OpenSCAD cần có trong PATH, hoặc truyền `--openscad` với đường dẫn executable. `verify_straight_bore.py` cần STL của cả bản đầy đủ và bản thử. Xem README ở thư mục gốc để cài dependency và chạy đủ bộ kiểm tra.
