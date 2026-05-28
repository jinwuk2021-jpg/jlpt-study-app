# JLPT official exams (markdown)

Đề thi thật dùng cho chế độ thi mô phỏng JLPT. App đọc qua `app/exam_loader.py` và đồng bộ DB bằng `app/exam_sync.py`.

## Cấu trúc

```
data/exam/
├── n1/
│   └── JLPT_N1_YYYY_MM.md          # Đề đầy đủ (hoặc *_listening.md nếu chỉ nghe)
└── n2/
    └── JLPT_N2_YYYY_MM.md
```

- **Tên file**: `JLPT_{N1|N2}_{năm}_{tháng}.md` (tháng `07` hoặc `12`)
- **META**: khối YAML trong file (ngày thi, audio, danh sách section)
- **Câu hỏi**: `#### Q1` … `Q70`, `#### L1` … (nghe; số câu có thể khác theo kỳ)

## Không commit

- `**/_pdf_*/` — ảnh render từ PDF khi OCR (tạo bằng `scripts/extract_jlpt_pdf.py`, xóa sau khi xong)

## Nhập hàng loạt (2014+)

Danh sách đề cần nhập từ `~/Downloads/N1` … `N5`: `scripts/exam_import_manifest.yaml` (bỏ qua đề trước 2014).

```bash
python scripts/extract_docx_text.py /path/to/exam.docx /tmp/exam.txt
python scripts/build_n1_exam_from_docx.py /path/to/exam.docx --year 2015 --month 12
python scripts/extract_jlpt_pdf.py /path/to/真题.pdf --out data/exam/n2/_pdf_pages
python scripts/sync_exams.py
```

## Thêm đề mới

1. `python scripts/extract_jlpt_pdf.py /path/to/真题.pdf --out data/exam/n2/_pdf_…_pages`
2. Soạn / chỉnh `JLPT_*.md` theo mẫu `JLPT_N2_2019_12.md`
3. `python scripts/sync_exams.py` (hoặc khởi động lại app)
