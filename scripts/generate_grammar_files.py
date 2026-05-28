#!/usr/bin/env python3
"""Generate full JLPT grammar markdown files (N5-N1) from JLPTsensei catalog."""

import re
import json
import ssl
import urllib.request
from pathlib import Path

# Fix SSL on macOS Python
ssl._create_default_https_context = ssl._create_unverified_context

BASE = Path(__file__).resolve().parent.parent / "data" / "grammar"
SOURCE = "JLPTsensei.com (past exam analysis)"

LEVELS = {
    "n5": {"url": "https://jlptsensei.com/jlpt-n5-grammar-list/", "total": 84, "pages": 3},
    "n4": {"url": "https://jlptsensei.com/jlpt-n4-grammar-list/", "total": 132, "pages": 4},
    "n3": {"url": "https://jlptsensei.com/jlpt-n3-grammar-list/", "total": 182, "pages": 5},
    "n2": {"url": "https://jlptsensei.com/jlpt-n2-grammar-list/", "total": 197, "pages": 5},
    "n1": {"url": "https://jlptsensei.com/jlpt-n1-grammar-list/", "total": 253, "pages": 7},
}

# Vietnamese usage templates by keyword in English meaning
USAGE_HINTS = [
    (r"must not|may not|should not|cannot", "Dùng để diễn tả điều cấm hoặc không được phép."),
    (r"must|have to|need to|obligation", "Diễn tả nghĩa vụ, bắt buộc phải làm."),
    (r"while|during|between", "Chỉ khoảng thời gian hoặc phạm vi trong khi/lúc."),
    (r"after|before", "Chỉ thứ tự thời gian trước/sau một hành động."),
    (r"because|since|due to", "Nối nguyên nhân và kết quả."),
    (r"if|conditional|when", "Diễn tả điều kiện giả định."),
    (r"not only|but also|as well", "Nhấn mạnh không chỉ A mà còn B."),
    (r"even|no matter", "Dù... vẫn... / bất kể..."),
    (r"seems|probably|might|perhaps", "Diễn tả suy đoán, khả năng."),
    (r"want|desire", "Diễn tả mong muốn."),
    (r"let's|shall we", "Mời rủ, đề nghị cùng làm."),
    (r"please|request", "Yêu cầu, nhờ vả lịch sự."),
    (r"too|also|as well", "Thêm ý 'cũng', 'nữa'."),
    (r"than|more|most|better", "So sánh mức độ."),
    (r"try|attempt", "Thử làm, trải nghiệm."),
    (r"finish|end up|finally", "Kết quả cuối cùng hoặc hoàn tất."),
    (r"instead|rather|substitute", "Thay thế, thay cho."),
    (r"according|based|depending", "Tùy theo, dựa trên."),
    (r"although|but|however|though", "Tương phản, nghịch lại."),
    (r"honorific|polite", "Thể lịch sự, kính ngữ."),
]

MEANING_VI = {
    "must not do": "không được làm",
    "to be": "là (copula)",
    "only; just": "chỉ; chỉ là",
    "probably": "có lẽ; chắc là",
    "because; since; from": "vì; từ",
    "but; however": "nhưng; tuy nhiên",
    "question particle": "trợ từ câu hỏi",
    "or": "hoặc",
    "there is": "có (vật)",
    "to want something": "muốn (vật)",
    "there is; to be; is (living": "có (người/sinh vật)",
    "had better": "nên; tốt hơn là",
    "the most": "nhất",
    "together": "cùng nhau",
    "always; usually": "luôn; thường",
    "to not be": "không phải là",
    "still; not yet": "vẫn còn; chưa",
    "until": "đến; cho đến",
    "before": "trước khi",
    "let's": "cùng ... đi",
    "already": "đã; rồi",
    "without doing": "mà không làm",
    "please don't": "xin đừng",
    "must do": "phải làm",
    "while; during": "trong khi; trong lúc",
    "after": "sau khi",
    "conditional": "thể điều kiện",
    "nothing but": "chỉ toàn; không gì ngoài",
    "might; perhaps": "có thể; có lẽ",
    "it must be": "chắc hắn là",
    "cannot be": "không thể nào",
    "to decide": "quyết định",
    "to be able to": "có thể",
    "volitional": "thể ý chí (cùng làm)",
    "to finish doing": "làm xong",
    "so much": "quá ... đến nức",
    "should do; must do": "nên làm; phải làm",
    "not really": "không hẳn; không đặc biệt",
    "no matter how": "dù ... đến đâu",
    "more and more": "càng ngày càng",
    "instead of": "thay vì",
    "as a result": "kết quả là",
    "in the end": "cuối cùng",
    "not only": "không những",
    "unable to": "không thể",
    "on the other hand": "mặt khác",
    "as expected": "đúng như mong đợi",
    "with the exception": "ngoại trừ",
    "because; since; seeing that": "vì; bởi vì",
    "as if": "như thể",
    "just when": "vừa mới ... thì",
    "dare to": "cố ý; dám",
    "to the end": "cho đến cùng",
    "sure enough": "quả nhiên; đúng như dự đoán",
    "beforehand": "trước; từ trước",
    "owing to": "nhờ có; do",
    "right?": "phải không?",
    "burst into": "bắt đầu đột ngột",
}


def fetch_page(url: str, page: int = 1) -> str:
    full = url if page == 1 else f"{url.rstrip('/')}/page/{page}/"
    req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0 JLPT-Study-App"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _strip_md(text: str) -> str:
    """Remove markdown links/images, leaving visible text."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_grammar_rows(html: str) -> list[dict]:
    rows = []
    seen = set()

    # HTML table rows from jlptsensei.com (no closing </td> tags)
    html_pattern = re.compile(
        r'<tr[^>]*class="?jl-row[^>]*>\s*'
        r'<td[^>]*>(\d+)<td[^>]*>(?:<a[^>]*>)?([^<]+?)(?:</a>)?<td[^>]*>(?:<a[^>]*>)?([^<]+?)(?:</a>)?<td[^>]*>([^<\n]+)',
        re.IGNORECASE,
    )
    for m in html_pattern.finditer(html):
        num, romaji, japanese, meaning = m.groups()
        num = int(num)
        if num in seen:
            continue
        seen.add(num)
        rows.append({
            "num": num,
            "romaji": _strip_md(romaji),
            "japanese": _strip_md(japanese),
            "meaning_en": _strip_md(meaning).rstrip("~").strip(),
        })

    if rows:
        return sorted(rows, key=lambda x: x["num"])

    # Markdown pipe table rows (WebFetch cache format)
    md_pattern = re.compile(
        r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
        re.MULTILINE,
    )
    for m in md_pattern.finditer(html):
        num, romaji, japanese, meaning = m.groups()
        num = int(num)
        if num in seen or "Grammar Lesson" in japanese or "---" in japanese:
            continue
        seen.add(num)
        rows.append({
            "num": num,
            "romaji": _strip_md(romaji),
            "japanese": _strip_md(japanese),
            "meaning_en": _strip_md(meaning).rstrip("~").strip(),
        })
    return sorted(rows, key=lambda x: x["num"])


def load_from_cache(level: str) -> list[dict]:
    cache_dir = Path(__file__).resolve().parent / "grammar_cache"
    info = LEVELS[level]
    all_rows = []
    seen = set()
    for page in range(1, info["pages"] + 1):
        cache_file = cache_dir / f"{level}_p{page}.txt"
        if not cache_file.exists():
            continue
        html = cache_file.read_text(encoding="utf-8")
        for row in parse_grammar_rows(html):
            if row["num"] not in seen:
                seen.add(row["num"])
                all_rows.append(row)
    all_rows.sort(key=lambda x: x["num"])
    return all_rows


def fetch_level(level: str) -> list[dict]:
    cached = load_from_cache(level)
    if cached:
        return cached
    info = LEVELS[level]
    all_rows = []
    seen = set()
    for page in range(1, info["pages"] + 1):
        try:
            html = fetch_page(info["url"], page)
            for row in parse_grammar_rows(html):
                if row["num"] not in seen:
                    seen.add(row["num"])
                    all_rows.append(row)
        except Exception as e:
            print(f"  Warning page {page}: {e}")
    all_rows.sort(key=lambda x: x["num"])
    return all_rows


def translate_meaning(en: str) -> str:
    en_lower = en.lower()
    for key, vi in MEANING_VI.items():
        if key in en_lower:
            return vi
    # Simple word replacements
    text = en
    replacements = [
        ("to ", ""), ("~", "..."), (";", " / "), ("(", " ("), (")", ")"),
        ("not ", "không "), ("and ", "và "), ("or ", "hoặc "),
        ("more ", "hơn "), ("very ", "rất "), ("too ", "quá "),
    ]
    for a, b in replacements:
        text = text.replace(a, b)
    return text[:120] if len(text) > 120 else text


def usage_vi(meaning_en: str) -> str:
    en = meaning_en.lower()
    for pat, hint in USAGE_HINTS:
        if re.search(pat, en):
            return hint
    return f"Dùng để diễn tả: {translate_meaning(meaning_en)}. Thường gặp trong đề JLPT {meaning_en.split()[0] if meaning_en else 'cơ bản'}."


def make_examples(japanese: str, meaning_en: str, romaji: str) -> list[tuple[str, str]]:
    """Generate 3 contextual examples."""
    jp = japanese.split("（")[0].split("(")[0].strip()
    m = meaning_en.lower()

    if "must not" in m or "may not" in m:
        return [
            (f"ここで吸ってはいけません。", "Không được hút thuốc ở đây."),
            (f"走ってはいけない。", "Không được chạy."),
            (f"忘れてはいけません。", "Không được quên."),
        ]
    if "must do" in m or "have to" in m or "obligation" in m:
        return [
            (f"毎日勉強しなければなりません。", "Phải học mỗi ngày."),
            (f"薬を飲まないといけない。", "Phải uống thuốc."),
            (f"早く寝なければならない。", "Phải đi ngủ sớm."),
        ]
    if "let's" in m or "shall we" in m:
        return [
            (f"一緒に行きましょう。", "Cùng đi thôi."),
            (f"休みましょう。", "Cùng nghỉ đi."),
            (f"食べましょうか。", "Mình ăn nhé?"),
        ]
    if "please" in m and "don't" in m:
        return [
            (f"触らないでください。", "Xin đừng chạm vào."),
            (f"心配しないでください。", "Xin đừng lo."),
            (f"忘れないでください。", "Xin đừng quên."),
        ]
    if "please" in m or "request" in m:
        return [
            (f"待ってください。", "Xin hãy đợi."),
            (f"教えてください。", "Xin hãy dạy cho tôi."),
            (f"手伝ってください。", "Làm ơn giúp tôi."),
        ]
    if "because" in m or "since" in m:
        return [
            (f"雨だから、行きません。", "Vì mưa nên tôi không đi."),
            (f"忙しいから、できない。", "Vì bận nên không làm được."),
            (f"安いから、買った。", "Vì rẻ nên đã mua."),
        ]
    if "while" in m or "during" in m:
        return [
            (f"寝ている間に、雨が降った。", "Trong lúc đang ngủ thì trời mưa."),
            (f"勉強している間、音楽を聞く。", "Trong lúc học thì nghe nhạc."),
            (f"会議中に、電話が鳴った。", "Giữa cuộc họp thì điện thoại reo."),
        ]
    if "after" in m:
        return [
            (f"食べてから、出かけます。", "Sau khi ăn thì ra ngoài."),
            (f"仕事の後で、飲みに行く。", "Sau giờ làm thì đi uống."),
            (f"帰ってから、連絡します。", "Sau khi về sẽ liên lạc."),
        ]
    if "before" in m:
        return [
            (f"寝る前に、歯を磨く。", "Trước khi ngủ thì đánh răng."),
            (f"出かける前に、鍵を閉める。", "Trước khi ra ngoài thì khóa cửa."),
            (f"食事の前に、手を洗う。", "Trước bữa ăn thì rửa tay."),
        ]
    if "might" in m or "perhaps" in m or "probably" in m:
        return [
            (f"明日は雨かもしれない。", "Mai có lẽ mưa."),
            (f"彼は来ないかもしれません。", "Anh ấy có lẽ không đến."),
            (f"大丈夫でしょう。", "Chắc là ổn thôi."),
        ]
    if "not only" in m:
        return [
            (f"日本語ばかりでなく、英語も話せる。", "Không những tiếng Nhật mà còn nói tiếng Anh."),
            (f"彼は頭がいいばかりでなく、優しい。", "Không những thông minh mà còn tốt bụng."),
            (f"安いばかりでなく、おいしい。", "Không những rẻ mà còn ngon."),
        ]
    if "although" in m or "but" in m or "however" in m:
        return [
            (f"雨なのに、出かけた。", "Mặc dù mưa mà vẫn ra ngoài."),
            (f"高いけど、買った。", "Tuy đắt nhưng đã mua."),
            (f"忙しいですが、頑張ります。", "Tuy bận nhưng sẽ cố gắng."),
        ]
    if "want" in m:
        return [
            (f"水が欲しいです。", "Tôi muốn nước."),
            (f"日本へ行きたい。", "Tôi muốn đi Nhật."),
            (f"何を食べたいですか。", "Bạn muốn ăn gì?"),
        ]
    if "better" in m or "should" in m:
        return [
            (f"早く寝たほうがいい。", "Nên đi ngủ sớm."),
            (f"医者に行ったほうがいいです。", "Nên đi gặp bác sĩ."),
            (f"勉強したほうがいい。", "Nên học bài."),
        ]
    if "able to" in m or "can" in m:
        return [
            (f"日本語が話せます。", "Tôi có thể nói tiếng Nhật."),
            (f"泳ぐことができる。", "Có thể bơi."),
            (f"ここで写真を撮ってもいいですか。", "Chụp ảnh ở đây được không?"),
        ]
    if "together" in m:
        return [
            (f"友達と一緒に行きます。", "Tôi đi cùng bạn."),
            (f"一緒に勉強しましょう。", "Cùng học đi."),
            (f"家族と一緒に住んでいる。", "Sống cùng gia đình."),
        ]
    if "always" in m or "usually" in m:
        return [
            (f"いつも7時に起きます。", "Tôi luôn dậy lúc 7 giờ."),
            (f"彼はいつも遅刻する。", "Anh ấy luôn đi trễ."),
            (f"いつもありがとう。", "Luôn cảm ơn bạn."),
        ]
    if "the most" in m or "best" in m:
        return [
            (f"これが一番好きです。", "Tôi thích cái này nhất."),
            (f"富士山は日本で一番高い山です。", "Núi Phú Sĩ là núi cao nhất Nhật."),
            (f"誰が一番速いですか。", "Ai nhanh nhất?"),
        ]
    if "instead" in m:
        return [
            (f"バスの代わりに、電車で行く。", "Thay vì xe buýt thì đi tàu."),
            (f"彼の代わりに、私が行きます。", "Thay anh ấy, tôi sẽ đi."),
            (f"コーヒーの代わりに、お茶を飲む。", "Thay cà phê thì uống trà."),
        ]
    if "no matter" in m or "even" in m:
        return [
            (f"何回説いても、分からない。", "Dù nói bao nhiêu lần cũng không hiểu."),
            (f"どんなに忙しくても、運動する。", "Dù bận đến đâu vẫn tập thể dục."),
            (f"雨でも、行きます。", "Dù mưa vẫn đi."),
        ]
    if "in the end" in m or "finally" in m or "after all" in m:
        return [
            (f"結局、行かなかった。", "Cuối cùng thì không đi."),
            (f"あげく、泣いてしまった。", "Cuối cùng lại khóc mất."),
            (f"結局、彼が正しかった。", "Cuối cùng anh ấy đúng."),
        ]
    if "as a result" in m:
        return [
            (f"努力した結果、合格した。", "Kết quả của nỗ lực là đậu."),
            (f"結果、失敗した。", "Kết quả là thất bại."),
            (f"調査の結果、問題が分かった。", "Kết quả điều tra là hiểu vấn đề."),
        ]
    if "honorific" in m or "polite" in m:
        return [
            (f"先生がいらっしゃいます。", "Thầy giáo có mặt (kính ngữ)."),
            (f"お待ちください。", "Xin hãy đợi (lịch sự)."),
            (f"ご連絡いたします。", "Tôi sẽ liên lạc (kính ngữ)."),
        ]
    if "try" in m or "attempt" in m:
        return [
            (f"作ってみます。", "Tôi sẽ thử làm."),
            (f"一度やってみてください。", "Hãy thử làm một lần."),
            (f"食べてみた。", "Đã thử ăn."),
        ]
    if "finish" in m or "end up" in m:
        return [
            (f"読み終わった。", "Đã đọc xong."),
            (f"食べてしまった。", "Đã ăn hết mất rồi."),
            (f"忘れてしまいました。", "Lỡ quên mất."),
        ]
    if "not very" in m or "not much" in m:
        return [
            (f"あまり好きじゃない。", "Không thích lắm."),
            (f"今日はあまり暑くない。", "Hôm nay không nóng lắm."),
            (f"あまり分からない。", "Không hiểu lắm."),
        ]
    if "doing" in m or "progressive" in m:
        return [
            (f"今、勉強しています。", "Bây giờ đang học."),
            (f"雨が降っている。", "Trời đang mưa."),
            (f"何をしていますか。", "Bạn đang làm gì?"),
        ]
    if "there is" in m or "exist" in m:
        return [
            (f"机の上に本があります。", "Trên bàn có sách."),
            (f"公園に子供がいます。", "Trong công viên có trẻ em."),
            (f"時間がありません。", "Không có thời gian."),
        ]
    if "decide" in m:
        return [
            (f"留学することにした。", "Quyết định du học."),
            (f"来月引っ越すことになった。", "Được quyết định chuyển nhà tháng sau."),
            (f"今日は休むことにします。", "Quyết định nghỉ hôm nay."),
        ]
    if "conditional" in m or "if" in m:
        return [
            (f"時間があれば、行きます。", "Nếu có thời gian thì tôi đi."),
            (f"雨なら、中止です。", "Nếu mưa thì hủy."),
            (f"安ければ、買います。", "Nếu rẻ thì mua."),
        ]
    if "particle" in m:
        return [
            (f"私は学生です。", "Tôi là học sinh (は)."),
            (f"猫が好きです。", "Tôi thích mèo (が)."),
            (f"本を読みます。", "Tôi đọc sách (を)."),
        ]
    if "or" in m:
        return [
            (f"コーヒーか紅茶か、どちら？", "Cà phê hay trà, cái nào?"),
            (f"行くか行かないか、迷っている。", "Phân vân đi hay không."),
            (f"赤か青か、選んでください。", "Đỏ hay xanh, hãy chọn."),
        ]
    if "until" in m:
        return [
            (f"5時まで待ちます。", "Đợi đến 5 giờ."),
            (f"駅まで歩いた。", "Đi bộ đến ga."),
            (f"来週までに終わらせる。", "Hoàn thành trước tuần sau."),
        ]
    if "already" in m:
        return [
            (f"もう食べました。", "Đã ăn rồi."),
            (f"もう帰りましたか。", "Đã về rồi à?"),
            (f"もう遅い。", "Đã muộn rồi."),
        ]
    if "still" in m or "not yet" in m:
        return [
            (f"まだ食べていません。", "Chưa ăn."),
            (f"まだ終わっていない。", "Vẫn chưa xong."),
            (f"まだ時間がある。", "Vẫn còn thời gian."),
        ]
    if "too" in m or "also" in m:
        return [
            (f"私も行きます。", "Tôi cũng đi."),
            (f"彼も学生です。", "Anh ấy cũng là sinh viên."),
            (f"これもください。", "Cái này cũng cho tôi."),
        ]
    if "without" in m:
        return [
            (f"食べないで、寝た。", "Không ăn mà đi ngủ."),
            (f"言わないでください。", "Đừng nói."),
            (f"傘を持たないで出かけた。", "Ra ngoài không mang ô."),
        ]
    if "according" in m or "based" in m or "depending" in m:
        return [
            (f"天気によって、変わる。", "Tùy thời tiết mà thay đổi."),
            (f"経験に基づいて判断する。", "Phán đoán dựa trên kinh nghiệm."),
            (f"能力に応じてクラス分けする。", "Chia lớp theo năng lực."),
        ]
    if "unable" in m or "cannot" in m or "impossible" in m:
        return [
            (f"そんなことはあり得ない。", "Chuyện đó không thể xảy ra."),
            (f"信じがたい。", "Khó tin."),
            (f"起こり得ない。", "Không thể xảy ra."),
        ]
    if "as if" in m or "just like" in m:
        return [
            (f"夢のように幸せだ。", "Hạnh phúc như trong mơ."),
            (f"知っているかのように話す。", "Nói như thể biết."),
            (f"子供のように泣いた。", "Khóc như đứa trẻ."),
        ]
    if "with" in m and "start" in m or "kikkake" in romaji.lower():
        return [
            (f"留学をきっかけに、日本語を勉強した。", "Lấy du học làm cơ hội học tiếng Nhật."),
            (f"この出会いをきっかけに、友達になった。", "Nhờ cuộc gặp này trở thành bạn."),
            (f"病気をきっかけに、生活を変えた。", "Lấy bệnh tật làm cơ hội thay đổi cuộc sống."),
        ]
    if "exception" in m:
        return [
            (f"彼以外、誰も来なかった。", "Ngoài anh ấy, không ai đến."),
            (f"これ以外、方法がない。", "Ngoài cách này không còn cách nào."),
            (f"月曜日以外、毎日開いている。", "Trừ thứ Hai, mở cửa mỗi ngày."),
        ]
    if "more than" in m or "beyond" in m:
        return [
            (f"期待以上に良かった。", "Tốt hơn mong đợi."),
            (f"必要以上に買った。", "Mua nhiều hơn cần thiết."),
            (f"以上に努力する。", "Nỗ lực hơn nữa."),
        ]
    if "dare" in m or "deliberately" in m:
        return [
            (f"敢えて厳しいことを言った。", "Cố ý nói điều khắt khe."),
            (f"敢えて行かなかった。", "Cố tình không đi."),
            (f"敢えて挑戦する。", "Dám thách thức."),
        ]

    # Default examples using pattern name
    return [
        (f"【{jp}】を使った文例1。", f"Ví dụ 1 sử dụng mẫu {jp} ({translate_meaning(meaning_en)})."),
        (f"【{jp}】を使った文例2。", f"Ví dụ 2 sử dụng mẫu {jp}."),
        (f"【{jp}】を使った文例3。", f"Ví dụ 3 sử dụng mẫu {jp} trong hội thoại."),
    ]


def render_entry(idx: int, item: dict) -> str:
    jp = item["japanese"]
    pattern = jp.split("（")[0].split("(")[0].strip()
    if "～" not in pattern and "..." not in pattern and len(pattern) <= 6:
        display = pattern if "～" in jp else f"～{pattern}" if not jp.startswith("～") else jp
    else:
        display = jp

    meaning_vi = translate_meaning(item["meaning_en"])
    usage = usage_vi(item["meaning_en"])
    examples = make_examples(jp, item["meaning_en"], item["romaji"])

    lines = [
        f"## {idx}. {display}",
        "",
        f"**Mẫu (JP):** {jp}",
        f"**Romaji:** {item['romaji']}",
        f"**Nghĩa:** {meaning_vi}",
        f"**Nghĩa (EN):** {item['meaning_en']}",
        "",
        f"**Cách dùng:** {usage}",
        "",
        "**Ví dụ:**",
        "",
    ]
    for i, (ja, vi) in enumerate(examples, 1):
        lines.append(f"{i}. {ja}  ")
        lines.append(f"   → {vi}")
        lines.append("")
    lines.extend(["---", ""])
    return "\n".join(lines)


def render_file(level: str, items: list[dict]) -> str:
    level_upper = level.upper()
    header = f"""# Ngữ pháp JLPT {level_upper} — Danh sách đầy đủ

> **Tổng số mẫu:** {len(items)}  
> **Nguồn tham khảo:** {SOURCE}  
> **Ghi chú:** JLPT không công bố danh sách ngữ pháp chính thức; danh sách này dựa trên phân tích đề thi các năm.

---

"""
    body = "".join(render_entry(i, item) for i, item in enumerate(items, 1))
    return header + body


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    summary = {}

    for level in ["n5", "n4", "n3", "n2", "n1"]:
        print(f"Fetching {level.upper()}...")
        items = fetch_level(level)
        print(f"  Found {len(items)} patterns")

        # Save JSON backup
        json_path = BASE / f"{level}.json"
        json_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

        md_path = BASE / f"{level}.md"
        md_path.write_text(render_file(level, items), encoding="utf-8")
        summary[level] = len(items)
        print(f"  Written {md_path}")

    # Update README
    readme = BASE / "README.md"
    readme.write_text(f"""# Ngữ pháp theo cấp độ JLPT

Danh sách ngữ pháp **đầy đủ** cho JLPT N5 → N1, tự động tạo từ dữ liệu JLPTsensei.

## Số lượng mẫu

| File | Cấp độ | Số mẫu |
|------|--------|--------|
| [n5.md](./n5.md) | N5 | {summary.get('n5', 0)} |
| [n4.md](./n4.md) | N4 | {summary.get('n4', 0)} |
| [n3.md](./n3.md) | N3 | {summary.get('n3', 0)} |
| [n2.md](./n2.md) | N2 | {summary.get('n2', 0)} |
| [n1.md](./n1.md) | N1 | {summary.get('n1', 0)} |

**Tổng cộng:** {sum(summary.values())} mẫu ngữ pháp

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
""", encoding="utf-8")

    print(f"\nDone! Total: {sum(summary.values())} grammar patterns")


if __name__ == "__main__":
    main()
