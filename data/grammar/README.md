# Ngữ pháp theo cấp độ JLPT

Danh sách ngữ pháp **đầy đủ** cho JLPT N5 → N1, tự động tạo từ dữ liệu JLPTsensei.

## Số lượng mẫu

| File | Cấp độ | Số mẫu |
|------|--------|--------|
| [n5.md](./n5.md) | N5 | 84 |
| [n4.md](./n4.md) | N4 | 132 |
| [n3.md](./n3.md) | N3 | 182 |
| [n2.md](./n2.md) | N2 | 197 |
| [n1.md](./n1.md) | N1 | 253 |

**Tổng cộng:** 848 mẫu ngữ pháp

## Cấu trúc mỗi mẫu

- **Mẫu (JP)** — cách viết tiếng Nhật
- **Romaji** — phiên âm
- **Nghĩa** — tiếng Việt
- **Cách dùng** — giải thích cách sử dụng
- **Ví dụ** — 3 câu ví dụ kèm dịch

## Tạo lại file

```bash
python scripts/generate_grammar_files.py
```

File JSON backup: `n5.json` … `n1.json`
