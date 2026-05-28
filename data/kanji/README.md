# Kanji theo cấp độ JLPT

Thư mục chứa 5 file kanji từ N5 đến N1 (danh sách JLPT đầy đủ từ nguồn mở).

## Cấu trúc mỗi kanji

```markdown
## [STT]. [Kanji]

- **Từ kanji:** ...
- **Nghĩa:** ...
- **Số nét:** ...
- **Cách đọc âm On:** ...
- **Cách đọc âm Kun:** ...

**10 từ mẫu ghép:**

| STT | Từ ghép | Cách đọc | Nghĩa |
```

## Danh sách file

| File | Cấp độ | Số kanji (ước lượng) | Mô tả |
|------|--------|----------------------|-------|
| [n5.md](./n5.md) | N5 | 80 | Kanji cơ bản nhất |
| [n4.md](./n4.md) | N4 | 170 | Kanji sơ cấp |
| [n3.md](./n3.md) | N3 | 370 | Kanji trung cấp |
| [n2.md](./n2.md) | N2 | 380 | Kanji trung cao |
| [n1.md](./n1.md) | N1 | 1135 | Kanji cao cấp |

**Tổng:** khoảng 2135 kanji (theo [jlpt-kanji-dictionary](https://github.com/AnchorI/jlpt-kanji-dictionary)).

## Tạo lại dữ liệu

```bash
pip install deep-translator
python scripts/generate_kanji_files.py
python scripts/import_content.py --force
```

Nguồn: AnchorI/jlpt-kanji-dictionary, kanjiapi.dev (từ vựng ghép), Smallsan/jlpt_kanji_json_msgpack (cách đọc).

## Ghi chú

- Mỗi kanji có **10 từ mẫu ghép** (ưu tiên từ thông dụng từ JMdict qua kanjiapi.dev)
- Nghĩa tiếng Việt được dịch tự động từ tiếng Anh
- Âm **On** (音読み) và **Kun** (訓読み) lấy từ kanjiapi.dev
