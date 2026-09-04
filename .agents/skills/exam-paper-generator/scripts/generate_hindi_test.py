#!/usr/bin/env python3
"""
Comprehensive Hindi Board Examination Paper Generator
Supports generating 25M, 50M, and 100M state-board compliant question papers
for any selected chapters/units using ground-truth textbook data.

Usage:
    python3 generate_hindi_test.py --chapters 2,3 --marks 100
    python3 generate_hindi_test.py --chapters 1,2 --marks 25
    python3 generate_hindi_test.py --chapters 4,5 --marks 50
"""

import argparse
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Candidate paths for references file
REF_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "..", "references", "hindi", "class10_textbook.json"),
    "/Users/krishnakanth/.hermes/skills/productivity/exam-paper-generator/references/hindi/class10_textbook.json",
    "/Users/krishnakanth/Projects/workflow/.agents/skills/exam-paper-generator/references/hindi/class10_textbook.json",
    "/Users/krishnakanth/.gemini/config/skills/exam-paper-generator/references/hindi/class10_textbook.json"
]

RENDER_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "render_paper.py"),
    "/Users/krishnakanth/.hermes/skills/productivity/exam-paper-generator/scripts/render_paper.py",
    "/Users/krishnakanth/Projects/workflow/.agents/skills/exam-paper-generator/scripts/render_paper.py",
    "/Users/krishnakanth/.gemini/config/skills/exam-paper-generator/scripts/render_paper.py"
]

DIST_DIR = "/Users/krishnakanth/Projects/workflow/dist"
os.makedirs(DIST_DIR, exist_ok=True)

def get_ref_file():
    for p in REF_CANDIDATES:
        ap = os.path.abspath(p)
        if os.path.exists(ap):
            return ap
    raise FileNotFoundError("class10_textbook.json could not be located in any known paths.")

def get_render_script():
    for p in RENDER_CANDIDATES:
        ap = os.path.abspath(p)
        if os.path.exists(ap):
            return ap
    raise FileNotFoundError("render_paper.py could not be located in any known paths.")

def load_textbook():
    ref_file = get_ref_file()
    with open(ref_file, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_chapter_keys(requested_str, tb):
    toc = tb.get("table_of_contents", [])
    chapters_dict = tb.get("chapters", {})
    selected_keys = []
    
    req_clean = requested_str.strip().lower()
    if req_clean in ("all", "full", "whole"):
        return [item["key"] for item in toc if item.get("chapter_no") is not None]

    parts = [p.strip() for p in requested_str.replace("and", ",").replace("&", ",").split(",") if p.strip()]
    for p in parts:
        if p.isdigit():
            num = int(p)
            for item in toc:
                if item.get("chapter_no") == num:
                    selected_keys.append(item["key"])
                    break
        else:
            found = False
            for item in toc:
                if p in item["key"].lower() or p in item["title"].lower():
                    selected_keys.append(item["key"])
                    found = True
                    break
            if not found and p in chapters_dict:
                selected_keys.append(p)

    if not selected_keys:
        selected_keys = ["chapter_2", "chapter_3"]
    return list(dict.fromkeys(selected_keys))

def extract_meta(c):
    title = c.get("title") or c.get("chapter_title") or c.get("metadata", {}).get("title") or c.get("metadata", {}).get("chapter_title") or "पाठ"
    genre = c.get("genre") or c.get("metadata", {}).get("genre") or ""
    author = c.get("author") or c.get("metadata", {}).get("author") or "रचनाकार"
    if isinstance(author, dict):
        author = author.get("name") or author.get("short_name") or "रचनाकार"
    is_poem = any(w in genre for w in ["कविता", "काव्य", "दोहे", "पद"])
    return title, genre, author, is_poem

def extract_poem_stanza(c):
    if "poem_stanzas" in c and c["poem_stanzas"]:
        st = c["poem_stanzas"][0]
        text = st.get("text") or st.get("stanza") or str(st)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return "\n".join(lines[:4])
    for k, v in c.items():
        if isinstance(v, dict) and "poem" in v:
            p = v["poem"]
            if isinstance(p, dict) and "full_text" in p:
                lines = [l.strip() for l in p["full_text"].split("\n") if l.strip()]
                return "\n".join(lines[:4])
    return None

def extract_prose_passage(c):
    if "story_summary_points" in c and c["story_summary_points"]:
        pts = c["story_summary_points"]
        if isinstance(pts[0], dict):
            return " ".join([p.get("description", "") for p in pts[:4] if p.get("description")])
        elif isinstance(pts[0], str):
            return " ".join(pts[:3])
    if "vishay_pravesh" in c and isinstance(c["vishay_pravesh"], str) and len(c["vishay_pravesh"]) > 60:
        return c["vishay_pravesh"]
    for k, v in c.items():
        if isinstance(v, dict) and "vishay_pravesh" in v and isinstance(v["vishay_pravesh"], str):
            return v["vishay_pravesh"]
    return None

def build_paper(tb, chapter_keys, marks):
    selected_data = [tb["chapters"][k] for k in chapter_keys if k in tb["chapters"]]
    if not selected_data:
        selected_data = [tb["chapters"]["chapter_2"], tb["chapters"]["chapter_3"]]
    
    # Analyze chapters
    meta_list = [extract_meta(c) for c in selected_data]
    titles = [m[0] for m in meta_list]
    titles_str = " & ".join([f"पाठ: {t}" for t in titles])

    poem_chapters = [(c, m) for c, m in zip(selected_data, meta_list) if m[3]]
    prose_chapters = [(c, m) for c, m in zip(selected_data, meta_list) if not m[3]]

    # Determine poem passage
    if poem_chapters:
        c_poem, (p_title, p_genre, p_author, _) = poem_chapters[0]
        poem_text = extract_poem_stanza(c_poem)
    else:
        # Fallback to Chapter 3 or Chapter 1
        p_title = "हम भारतवासी"
        p_author = "आर.पी. 'निशंक'"
        poem_text = "हम भारतवासी दुनिया को पावन धाम बनायेंगे।\nमन में श्रद्धा और प्रेम का अद्भुत दृश्य दिखायेंगे॥\nऊँच-नीच का भेद मिटाकर, दिल में प्यार बसायेंगे।\nनफ़रत का हम तोड़ कुहासा, अमृत रस सरसायेंगे॥"

    # Determine prose passage
    if prose_chapters:
        c_prose, (pr_title, pr_genre, pr_author, _) = prose_chapters[0]
        prose_text = extract_prose_passage(c_prose)
    else:
        pr_title = "ईदगाह"
        pr_author = "प्रेमचंद"
        prose_text = "रमज़ान के तीस रोज़ों के बाद ईद का मनोहर और सुहावना प्रभात आया। गाँव में ईदगाह जाने की तैयारियाँ शुरू हुईं। हामिद के पास केवल तीन पैसे थे, फिर भी वह सब बच्चों में सबसे अधिक प्रसन्न था। दादी अमीना को चिंता थी कि तीन कोस पैदल चलकर छोटा बच्चा कैसे जाएगा।"

    time_str = "45 मिनट (45 Mins)" if marks <= 25 else ("1 घंटा 30 मिनट (1.5 Hours)" if marks <= 50 else "3 घंटे 15 मिनट (3 Hours 15 Mins)")
    assessment_type = "FORMATIVE ASSESSMENT / UNIT TEST" if marks <= 25 else ("TERMINAL ASSESSMENT" if marks <= 50 else "SUMMATIVE ASSESSMENT / MODEL PUBLIC EXAMINATION")

    metadata = {
        "board_title": f"BOARD OF SECONDARY EDUCATION, A.P. :: VIJAYAWADA\nSSC 10th CLASS - {assessment_type}",
        "class": "CLASS X (10th)",
        "subject": "द्वितीय भाषा हिंदी (HINDI SECOND LANGUAGE)",
        "chapter_name": titles_str,
        "paper_code": "02H (HINDI SL)",
        "medium": "HINDI / TELUGU / ENGLISH",
        "time": time_str,
        "max_marks": marks,
        "instructions": [
            "प्रथम 15 मिनट प्रश्न-पत्र पढ़ने और समझने के लिए निर्धारित हैं।",
            "सभी प्रश्नों के उत्तर दी गई उत्तर-पुस्तिका में साफ़-सुथरे अक्षरों में लिखिए।",
            "प्रश्नों के अंक उनके सामने दाहिनी ओर दिए गए हैं।",
            "कक्षा 10 बोर्ड पाठ्यक्रम के अनुसार वर्तनी और व्याकरण की शुद्धता पर विशेष ध्यान दीजिए।"
        ]
    }

    sections = []

    # ==========================================
    # 25 MARKS BLUEPRINT
    # ==========================================
    if marks <= 25:
        # Section I: Comprehension (5M)
        if poem_chapters:
            q1_content = f"पद्यांश:\n{poem_text}\n\nउपर्युक्त पद्यांश पढ़कर प्रश्नों के उत्तर एक-एक वाक्य में दीजिए:\n" \
                         f"1. यह पद्यांश किस पाठ से लिया गया है और इसके कवि कौन हैं?\n" \
                         f"2. पद्यांश में समाज से किस बुराई को मिटाने का संकल्प लिया गया है?\n" \
                         f"3. 'अमृत रस सरसाना' का भावार्थ क्या है?\n" \
                         f"4. पद्यांश से एक तुकांत शब्द युग्म लिखिए।\n" \
                         f"5. इस पद्यांश से हमें क्या नैतिक सीख मिलती है?"
        else:
            q1_content = f"गद्यांश:\n{prose_text}\n\nउपर्युक्त गद्यांश पढ़कर प्रश्नों के उत्तर दीजिए:\n" \
                         f"1. प्रस्तुत गद्यांश किस पाठ से लिया गया है और इसके लेखक कौन हैं?\n" \
                         f"2. गद्यांश के मुख्य पात्र की मनोदशा का वर्णन कीजिए।\n" \
                         f"3. गद्यांश से एक मुहावरा या कठिन शब्द चुनकर अर्थ लिखिए।\n" \
                         f"4. इस अंश से हमें क्या संदेश मिलता है?\n" \
                         f"5. उपयुक्त शीर्षक दीजिए।"

        sections.append({
            "section_id": "I",
            "title": "SECTION - I",
            "instruction": "सूचना: पद्यांश/गद्यांश पढ़कर पूछे गए प्रश्नों के उत्तर लिखिए। (अर्थग्राह्यता एवं प्रतिक्रिया)",
            "marks_total": "5 x 1 = 5M",
            "questions": [{"q_no": 1, "type": "short_answer", "question": q1_content, "marks": "5M"}]
        })

        # Section II: Short Answer (4M)
        sa_q = []
        q_no = 2
        for t, g, a, ip in meta_list[:2]:
            role = "कवि" if ip else "लेखक"
            sa_q.append({
                "q_no": q_no,
                "type": "short_answer",
                "question": f"'{t}' पाठ के आधार पर {role} {a} के विचारों अथवा मुख्य पात्र के चरित्र पर 3-4 पंक्तियाँ लिखिए।",
                "marks": "2M"
            })
            q_no += 1
        sections.append({
            "section_id": "II",
            "title": "SECTION - II",
            "instruction": "सूचना: इन प्रश्नों के उत्तर 3-4 पंक्तियों में लिखिए। प्रत्येक प्रश्न के 2 अंक हैं।",
            "marks_total": "2 x 2 = 4M",
            "questions": sa_q
        })

        # Section III: Long Essay with Choice (8M)
        t1, g1, a1, _ = meta_list[0]
        t2, g2, a2, _ = meta_list[1] if len(meta_list) > 1 else meta_list[0]
        sections.append({
            "section_id": "III",
            "title": "SECTION - III",
            "instruction": "सूचना: किसी एक प्रश्न का उत्तर 8-10 पंक्तियों में विस्तार से लिखिए। (आंतरिक विकल्प)",
            "marks_total": "1 x 8 = 8M",
            "questions": [
                {
                    "q_no": q_no,
                    "heading": "किसी एक प्रश्न का उत्तर विस्तारपूर्वक लिखिए:",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": f"क) '{t1}' पाठ का सारांश अपने शब्दों में लिखते हुए {a1} के सामाजिक संदेश को स्पष्ट कीजिए।",
                        "format": "भूमिका, विषय-विस्तार और निष्कर्ष"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": f"ख) '{t2}' पाठ के मुख्य पात्र अथवा मूल भाव की विशेषताओं का विस्तार से विश्लेषण कीजिए।",
                        "format": "चरित्र-चित्रण, सामाजिक प्रासंगिकता और सीख"
                    }
                }
            ]
        })
        q_no += 1

        # Section IV: Grammar (8M)
        sections.append({
            "section_id": "IV",
            "title": "SECTION - IV",
            "instruction": "सूचना: कोष्ठक में दी गई सूचना के अनुसार प्रश्नों के उत्तर लिखिए। (भाषा की बात)",
            "marks_total": "8 x 1 = 8M",
            "questions": [
                {"q_no": q_no, "type": "short_answer", "question": "i) 'सावन' शब्द का तत्सम रूप पहचानकर लिखिए।", "marks": "1M"},
                {"q_no": q_no + 1, "type": "short_answer", "question": "ii) 'भारतवासी' का समास विग्रह करके समास का नाम लिखिए।", "marks": "1M"},
                {"q_no": q_no + 2, "type": "short_answer", "question": "iii) 'हामिद दादी के लिए चिमटा लाया।' - रेखांकित पद में कारक पहचानिए।", "marks": "1M"},
                {"q_no": q_no + 3, "type": "short_answer", "question": "iv) 'निराशा' (निः + आशा) में कौन-सी संधि है?", "marks": "1M"},
                {"q_no": q_no + 4, "type": "short_answer", "question": "v) 'अमृत' शब्द का विलोम शब्द लिखिए।", "marks": "1M"},
                {"q_no": q_no + 5, "type": "short_answer", "question": "vi) 'पावन' शब्द के दो पर्यायवाची शब्द लिखिए।", "marks": "1M"},
                {"q_no": q_no + 6, "type": "short_answer", "question": "vii) 'कलेजा ठंडा होना' - मुहावरे का अर्थ लिखकर वाक्य प्रयोग कीजिए।", "marks": "1M"},
                {"q_no": q_no + 7, "type": "short_answer", "question": "viii) 'बच्चा मैदान में खेलता है।' - लिंग बदलकर वाक्य पुनः लिखिए।", "marks": "1M"}
            ]
        })

    # ==========================================
    # 50 MARKS BLUEPRINT
    # ==========================================
    elif marks <= 50:
        # Section I: Comprehension (10M)
        sections.append({
            "section_id": "I",
            "title": "SECTION - I",
            "instruction": "सूचना: पद्यांश व गद्यांश पढ़कर पूछे गए प्रश्नों के उत्तर लिखिए। (अर्थग्राह्यता एवं प्रतिक्रिया)",
            "marks_total": "2 x 5 = 10M",
            "questions": [
                {
                    "q_no": 1,
                    "type": "short_answer",
                    "question": f"निम्नलिखित पद्यांश पढ़कर 5 प्रश्नों के उत्तर दीजिए:\n\n{poem_text}\n\n"
                                f"1. यह पद्यांश किस पाठ से लिया गया है और इसके कवि कौन हैं?\n"
                                "2. पद्यांश में विश्व को क्या बनाने का पावन संकल्प लिया गया है?\n"
                                "3. 'नफ़रत का कुहासा तोड़ना' का अर्थ स्पष्ट कीजिए।\n"
                                "4. पद्यांश में प्रयुक्त किसी एक तुकांत शब्द-युग्म को लिखिए।\n"
                                "5. इस पद्यांश से छात्रों को क्या प्रेरणा मिलती है?",
                    "marks": "5M"
                },
                {
                    "q_no": 2,
                    "type": "short_answer",
                    "question": f"निम्नलिखित गद्यांश पढ़कर 5 प्रश्नों के उत्तर दीजिए:\n\n"
                                f"पाठ संदर्भ: {pr_title} ({pr_author})\n{prose_text}\n\n"
                                "1. प्रस्तुत गद्यांश के रचनाकार कौन हैं?\n"
                                "2. लेखक ने यहाँ समाज के किस मानवीय भाव को प्रकट किया है?\n"
                                "3. मुख्य पात्र के आचरण से उसके चरित्र की कौन-सी विशेषता उजागर होती है?\n"
                                "4. गद्यांश से एक कठिन शब्द छाँटकर उसका अर्थ लिखिए।\n"
                                "5. इस अंश के लिए एक उपयुक्त शीर्षक सुझाइए।",
                    "marks": "5M"
                }
            ]
        })

        # Section II: Short Answer & Essays (24M)
        t1, g1, a1, ip1 = meta_list[0]
        t2, g2, a2, ip2 = meta_list[1] if len(meta_list) > 1 else meta_list[0]
        sections.append({
            "section_id": "II",
            "title": "SECTION - II",
            "instruction": "सूचना: इन प्रश्नों के उत्तर निर्देशानुसार लिखिए। (अभिव्यक्ति एवं सृजनात्मकता)",
            "marks_total": "24M",
            "questions": [
                {
                    "q_no": 3,
                    "type": "short_answer",
                    "question": f"'{t1}' पाठ के आधार पर {a1} जी का संक्षिप्त साहित्यिक परिचय (4-5 पंक्तियाँ) दीजिए।",
                    "marks": "4M"
                },
                {
                    "q_no": 4,
                    "type": "short_answer",
                    "question": f"'{t2}' पाठ के आधार पर मुख्य भाव अथवा मुख्य पात्र की दो विशेषताओं का उल्लेख कीजिए।",
                    "marks": "4M"
                },
                {
                    "q_no": 5,
                    "heading": "निबंधात्मक प्रश्न (आंतरिक विकल्प):",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": f"क) '{t1}' का मूल भाव अपने शब्दों में स्पष्ट करते हुए वर्तमान जीवन में इसकी प्रासंगिकता सिद्ध कीजिए।",
                        "format": "विस्तृत निबंध (10-12 पंक्तियाँ)"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": f"ख) '{t2}' पाठ में चित्रित सामाजिक संवेदना, त्याग और कर्तव्य-बोध पर अपने विचार व्यक्त कीजिए।",
                        "format": "विस्तृत निबंध (10-12 पंक्तियाँ)"
                    }
                },
                {
                    "q_no": 6,
                    "heading": "सृजनात्मक अभिव्यक्ति (पत्र अथवा निबंध):",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": "क) अपने मित्र को पत्र लिखकर बोर्ड परीक्षा की तैयारी तथा नैतिक मूल्यों के महत्व पर प्रकाश डालिए।",
                        "format": "औपचारिक/अनौपचारिक पत्र प्रारूप"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": "ख) 'पर्यावरण संरक्षण अथवा राष्ट्रीय एकता और सद्भावना' विषय पर एक सुंदर निबंध लिखिए।",
                        "format": "निबंध रूपरेखा"
                    }
                }
            ]
        })

        # Section III: Grammar (16M)
        sections.append({
            "section_id": "III",
            "title": "SECTION - III",
            "instruction": "सूचना: व्याकरण संबंधी प्रश्नों के उत्तर निर्देशानुसार लिखिए। (भाषा की बात)",
            "marks_total": "16 x 1 = 16M",
            "questions": [
                {"q_no": 7, "type": "short_answer", "question": "i) 'सावन' शब्द का तत्सम रूप लिखिए।", "marks": "1M"},
                {"q_no": 8, "type": "short_answer", "question": "ii) 'अनुराग' का विलोम शब्द लिखिए।", "marks": "1M"},
                {"q_no": 9, "type": "short_answer", "question": "iii) 'वारि' और 'नीर' किस शब्द के पर्यायवाची हैं?", "marks": "1M"},
                {"q_no": 10, "type": "short_answer", "question": "iv) 'प्रतिदिन' में कौन-सा समास है?", "marks": "1M"},
                {"q_no": 11, "type": "short_answer", "question": "v) 'पावन' का संधि विच्छेद कीजिए।", "marks": "1M"},
                {"q_no": 12, "type": "short_answer", "question": "vi) 'सुंदर' शब्द की भाववाचक संज्ञा क्या होगी?", "marks": "1M"},
                {"q_no": 13, "type": "short_answer", "question": "vii) 'हामिद ने चिमटा खरीदा।' - रेखांकित पद में कारक बताइए।", "marks": "1M"},
                {"q_no": 14, "type": "short_answer", "question": "viii) 'कलेजा ठंडा होना' - मुहावरे का अर्थ लिखकर वाक्य प्रयोग कीजिए।", "marks": "1M"},
                {"q_no": 15, "type": "short_answer", "question": "ix) 'निराशा' शब्द में उपसर्ग पहचानिए।", "marks": "1M"},
                {"q_no": 16, "type": "short_answer", "question": "x) 'भारतीय' शब्द में प्रत्यय अलग कीजिए।", "marks": "1M"},
                {"q_no": 17, "type": "short_answer", "question": "xi) 'पुस्तक' का बहुवचन रूप लिखिए।", "marks": "1M"},
                {"q_no": 18, "type": "short_answer", "question": "xii) 'लड़की गाती है।' - लिंग बदलकर वाक्य पुनः लिखिए।", "marks": "1M"},
                {"q_no": 19, "type": "short_answer", "question": "xiii) 'जो सब कुछ जानता हो' - एक शब्द में लिखिए।", "marks": "1M"},
                {"q_no": 20, "type": "short_answer", "question": "xiv) 'हम भारतवासी विश्व में शांति लाएँगे।' - काल पहचानिए।", "marks": "1M"},
                {"q_no": 21, "type": "short_answer", "question": "xv) 'अशुद्ध वाक्य शुद्ध कीजिए: उसने तीन पुस्तक खरीदा।'", "marks": "1M"},
                {"q_no": 22, "type": "short_answer", "question": "xvi) 'दिल बैठ जाना' - मुहावरे का अर्थ स्पष्ट कीजिए।", "marks": "1M"}
            ]
        })

    # ==========================================
    # 100 MARKS BLUEPRINT (SSC PUBLIC BOARD MODEL)
    # ==========================================
    else:
        # Section I: अर्थग्राह्यता एवं प्रतिक्रिया (Reading Comprehension) - 20 Marks
        sections.append({
            "section_id": "I",
            "title": "SECTION - I",
            "instruction": "भाग - क : अर्थग्राह्यता एवं प्रतिक्रिया (पठित व अपठित गद्यांश/पद्यांश पढ़कर उत्तर लिखिए)",
            "marks_total": "4 x 5 = 20M",
            "questions": [
                {
                    "q_no": 1,
                    "type": "short_answer",
                    "question": f"निम्नलिखित पठित पद्यांश को ध्यानपूर्वक पढ़कर दिए गए प्रश्नों के उत्तर लिखिए:\n\n{poem_text}\n\n"
                                f"1. यह पद्यांश किस पाठ से लिया गया है और इसके कवि कौन हैं?\n"
                                "2. कवि संसार को क्या बनाना चाहते हैं?\n"
                                "3. 'नफ़रत का कुहासा तोड़ना' का क्या तात्पर्य है?\n"
                                "4. पद्यांश में प्रयुक्त किसी एक तुकांत (rhyming) शब्द-युग्म को लिखिए।\n"
                                "5. इस पद्यांश से प्रकृति व समाज के प्रति क्या प्रेरणा मिलती है?",
                    "marks": "5M"
                },
                {
                    "q_no": 2,
                    "type": "short_answer",
                    "question": f"निम्नलिखित पठित गद्यांश को पढ़कर पूछे गए प्रश्नों के उत्तर संक्षेप में लिखिए:\n\n"
                                f"पाठ संदर्भ: {pr_title} (लेखक: {pr_author})\n{prose_text}\n\n"
                                f"1. प्रस्तुत गद्यांश किस पाठ से संबंधित है और इसके लेखक कौन हैं?\n"
                                "2. लेखक ने यहाँ समाज के किस यथार्थ और भावना को उजागर किया है?\n"
                                "3. मुख्य पात्र के आचरण से उसके चरित्र की कौन-सी विशेषता प्रकट होती है?\n"
                                "4. गद्यांश से 'प्रसन्न' अथवा 'सुहावना' का विलोम शब्द लिखिए।\n"
                                "5. इस गद्यांश से विद्यार्थियों को क्या नैतिक सीख मिलती है?",
                    "marks": "5M"
                },
                {
                    "q_no": 3,
                    "type": "short_answer",
                    "question": "अपठित गद्यांश पढ़कर निम्नलिखित प्रश्नों के उत्तर एक-एक वाक्य में दीजिए:\n\n"
                                "सच्चा राष्ट्रप्रेम केवल नारों और भाषणों में नहीं अपितु समाज के प्रत्येक वर्ग के कल्याण, एकता और कर्मठता में निहित है। जब तक समाज में भेदभाव, अशिक्षा और विषमता रहेगी, तब तक कोई भी राष्ट्र पूर्ण रूप से स्वतंत्र और समर्थ नहीं कहला सकता। इसलिए प्रत्येक नागरिक का यह कर्तव्य है कि वह स्वार्थ से ऊपर उठकर देशहित को सर्वोपरि माने और सत्य, अहिंसा व सद्भाव का मार्ग अपनाए।\n\n"
                                "1. सच्चा राष्ट्रप्रेम किसमें निहित है?\n"
                                "2. राष्ट्र के पूर्ण विकास में कौन-कौन सी बाधाएँ हैं?\n"
                                "3. प्रत्येक नागरिक का क्या पुनीत कर्तव्य है?\n"
                                "4. 'कर्तव्य' शब्द का वर्ण-विच्छेद या एक पर्यायवाची शब्द लिखिए।\n"
                                "5. इस गद्यांश के लिए एक उपयुक्त शीर्षक सुझाइए।",
                    "marks": "5M"
                },
                {
                    "q_no": 4,
                    "type": "data_analysis",
                    "heading": "पाठ्य-पुस्तक तालिका का विश्लेषण करके नीचे दिए गए प्रश्नों के सही उत्तर लिखिए:",
                    "table": {
                        "headers": ["पाठ का नाम", "विधा", "रचनाकार", "मुख्य भाव / संदेश"],
                        "rows": [
                            ["बरसते बादल", "कविता", "सुमित्रानंदन पंत", "प्रकृति-सौंदर्य व उल्लास"],
                            ["ईदगाह", "कहानी", "प्रेमचंद", "त्याग, विवेक व मातृत्व प्रेम"],
                            ["हम भारतवासी", "कविता", "आर.पी. 'निशंक'", "विश्वबंधुत्व, त्याग व देशभक्ति"],
                            ["कण-कण का अधिकारी", "कविता", "डॉ. रामधारी सिंह 'दिनकर'", "श्रम का महत्व व सामाजिक समानता"]
                        ]
                    },
                    "sub_questions": [
                        "i) 'ईदगाह' किस विधा की रचना है? (कहानी / कविता / निबंध)",
                        "ii) 'कण-कण का अधिकारी' कविता के रचयिता कौन हैं?",
                        "iii) विश्वबंधुत्व और देशभक्ति का संदेश देने वाले पाठ का नाम बताइए।",
                        "iv) सुमित्रानंदन पंत जी की रचना किस प्रमुख भाव पर आधारित है?",
                        "v) इन चारों पाठों में से कौन-सा पाठ गद्य विधा के अंतर्गत आता है?"
                    ],
                    "marks": "5M"
                }
            ]
        })

        # Section II: अभिव्यक्ति एवं सृजनात्मकता (Expression & Essay Writing) - 40 Marks
        t1, g1, a1, ip1 = meta_list[0]
        t2, g2, a2, ip2 = meta_list[1] if len(meta_list) > 1 else meta_list[0]
        r1 = "कवि" if ip1 else "लेखक"
        r2 = "कवि" if ip2 else "लेखक"

        sections.append({
            "section_id": "II",
            "title": "SECTION - II",
            "instruction": "भाग - ख : अभिव्यक्ति एवं सृजनात्मकता (लघु उत्तरीय एवं विस्तृत निबंधात्मक प्रश्न)",
            "marks_total": "40M",
            "questions": [
                {
                    "q_no": 5,
                    "type": "short_answer",
                    "question": f"{r1} {a1} जी का साहित्यिक परिचय 4-5 पंक्तियों में दीजिए। (प्रमुख रचनाएँ, विशेषताएँ व सम्मान)",
                    "marks": "4M"
                },
                {
                    "q_no": 6,
                    "type": "short_answer",
                    "question": f"{r2} {a2} जी की भाषा-शैली और साहित्यिक योगदान पर संक्षेप में प्रकाश डालिए।",
                    "marks": "4M"
                },
                {
                    "q_no": 7,
                    "type": "short_answer",
                    "question": f"'{t1}' पाठ के आधार पर बताइए कि मनुष्य को जीवन में निराशा और स्वार्थ त्यागकर क्या सीखना चाहिए?",
                    "marks": "4M"
                },
                {
                    "q_no": 8,
                    "type": "short_answer",
                    "question": f"'{t2}' पाठ के मुख्य पात्र अथवा केंद्रीय विचार की दो प्रमुख विशेषताओं का विस्तार से उल्लेख कीजिए।",
                    "marks": "4M"
                },
                {
                    "q_no": 9,
                    "heading": "निबंधात्मक प्रश्न - 1 (आंतरिक विकल्प 8 अंक):",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": f"क) '{t1}' पाठ का भावार्थ अथवा सारांश अपने शब्दों में विस्तार से लिखते हुए इसके उद्देश्य पर प्रकाश डालिए।",
                        "format": "विस्तृत निबंध (प्रसंग, भावार्थ, जीवन-मूल्य)"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": f"ख) 'सच्चे नागरिक देश और समाज के प्रति समर्पित होते हैं।' '{t1}' के संदर्भ में इस कथन की समीक्षा कीजिए।",
                        "format": "विस्तृत निबंध (भूमिका, विवेचन, निष्कर्ष)"
                    }
                },
                {
                    "q_no": 10,
                    "heading": "निबंधात्मक प्रश्न - 2 (आंतरिक विकल्प 8 अंक):",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": f"क) '{t2}' पाठ बाल मनोविज्ञान, त्याग और मानवीय संवेदना की अमर रचना है। पाठ के आधार पर सिद्ध कीजिए।",
                        "format": "चरित्र-चित्रण व कहानी/पाठ की तात्विक समीक्षा"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": "ख) 'बुजुर्गों का सम्मान और उनकी आवश्यकताओं की चिंता करना युवा पीढ़ी का प्रथम कर्तव्य है।' अपने विचार व्यक्त कीजिए।",
                        "format": "सामाजिक दृष्टिकोण एवं नैतिक मूल्य"
                    }
                },
                {
                    "q_no": 11,
                    "heading": "सृजनात्मक अभिव्यक्ति / पत्र लेखन (8 अंक):",
                    "marks": "8M",
                    "choice_a": {
                        "type": "essay",
                        "title": "क) अपने विद्यालय के प्रधानाध्यापक जी को पत्र लिखकर पुस्तकालय में नई हिंदी पत्र-पत्रिकाएँ और संदर्भ पुस्तकें मँगवाने हेतु प्रार्थना कीजिए।",
                        "format": "औपचारिक पत्र प्रारूप"
                    },
                    "choice_b": {
                        "type": "essay",
                        "title": "ख) 'हिंदी दिवस अथवा राष्ट्रीय एकता और सद्भावना' विषय पर एक प्रेरक भाषण अथवा विस्तृत निबंध तैयार कीजिए।",
                        "format": "भाषण/निबंध रूपरेखा"
                    }
                }
            ]
        })

        # Section III: भाषा की बात / व्याकरण (Grammar) - 24 Marks
        g24 = [
            {"q_no": 12, "type": "short_answer", "question": "1. 'सावन' शब्द का तत्सम रूप लिखिए।", "marks": "1M"},
            {"q_no": 13, "type": "short_answer", "question": "2. 'सूरज' शब्द का तत्सम रूप लिखिए।", "marks": "1M"},
            {"q_no": 14, "type": "short_answer", "question": "3. 'गगन' और 'आकाश' किस शब्द के पर्यायवाची हैं?", "marks": "1M"},
            {"q_no": 15, "type": "short_answer", "question": "4. 'वारि' शब्द के दो पर्यायवाची शब्द लिखिए।", "marks": "1M"},
            {"q_no": 16, "type": "short_answer", "question": "5. 'अमृत' शब्द का विलोम शब्द लिखिए।", "marks": "1M"},
            {"q_no": 17, "type": "short_answer", "question": "6. 'प्रकाश' शब्द का विलोम शब्द लिखिए।", "marks": "1M"},
            {"q_no": 18, "type": "short_answer", "question": "7. 'पावन' (पौ + अन) में कौन-सी संधि है?", "marks": "1M"},
            {"q_no": 19, "type": "short_answer", "question": "8. 'निराशा' का संधि विच्छेद कीजिए।", "marks": "1M"},
            {"q_no": 20, "type": "short_answer", "question": "9. 'भारतवासी' का समास विग्रह कर समास का नाम लिखिए।", "marks": "1M"},
            {"q_no": 21, "type": "short_answer", "question": "10. 'माता-पिता' में कौन-सा समास है?", "marks": "1M"},
            {"q_no": 22, "type": "short_answer", "question": "11. 'बेईमान' शब्द में उपसर्ग पहचानकर अलग कीजिए।", "marks": "1M"},
            {"q_no": 23, "type": "short_answer", "question": "12. 'सफलता' शब्द में मूल शब्द और प्रत्यय अलग कीजिए।", "marks": "1M"},
            {"q_no": 24, "type": "short_answer", "question": "13. 'हामिद ने चिमटा खरीदा।' - रेखांकित पद में कारक बताइए।", "marks": "1M"},
            {"q_no": 25, "type": "short_answer", "question": "14. 'पेड़ से पत्ता गिरा।' - रेखांकित पद में कौन-सा कारक है?", "marks": "1M"},
            {"q_no": 26, "type": "short_answer", "question": "15. 'लड़का पुस्तक पढ़ता है।' - वाक्य का लिंग बदलकर पुनः लिखिए।", "marks": "1M"},
            {"q_no": 27, "type": "short_answer", "question": "16. 'चिड़िया आकाश में उड़ती है।' - वचन बदलकर वाक्य लिखिए।", "marks": "1M"},
            {"q_no": 28, "type": "short_answer", "question": "17. 'हम भारतवासी विश्व में शांति लाएँगे।' - काल पहचानिए।", "marks": "1M"},
            {"q_no": 29, "type": "short_answer", "question": "18. 'गाँधीजी सत्य बोलते थे।' - वाक्य को वर्तमान काल में बदलिए।", "marks": "1M"},
            {"q_no": 30, "type": "short_answer", "question": "19. 'दिल में प्यार बसाना' - मुहावरे का अर्थ लिखकर वाक्य प्रयोग कीजिए।", "marks": "1M"},
            {"q_no": 31, "type": "short_answer", "question": "20. 'कलेजा ठंडा होना' - मुहावरे का सही अर्थ क्या है?", "marks": "1M"},
            {"q_no": 32, "type": "short_answer", "question": "21. 'चम-चम बिजली चमक रही रे...' - में कौन-सा अलंकार है?", "marks": "1M"},
            {"q_no": 33, "type": "short_answer", "question": "22. 'कनक-कनक तैं सौ गुनी...' - में कौन-सा अलंकार है?", "marks": "1M"},
            {"q_no": 34, "type": "short_answer", "question": "23. 'जो सब कुछ जानता हो' - वाक्यांश के लिए एक शब्द लिखिए।", "marks": "1M"},
            {"q_no": 35, "type": "short_answer", "question": "24. अशुद्ध वाक्य शुद्ध कीजिए: 'उसने तीन पुस्तक खरीदा।'", "marks": "1M"}
        ]
        sections.append({
            "section_id": "III",
            "title": "SECTION - III",
            "instruction": "भाग - ग : भाषा की बात (व्याकरण - सभी प्रश्नों के उत्तर निर्देशानुसार दीजिए)",
            "marks_total": "24 x 1 = 24M",
            "questions": g24
        })

        # Section IV: Part B (वैकल्पिक वस्तुनिष्ठ प्रश्न / Objective Bits) - 16 Marks
        mcq16 = [
            {"q_no": 36, "type": "mcq", "question": "हामिद के पास कुल कितने पैसे थे?", "options": ["A) 2 पैसे", "B) 3 पैसे", "C) 5 पैसे", "D) 10 पैसे"], "marks": "1M"},
            {"q_no": 37, "type": "mcq", "question": "'हम भारतवासी' कविता के कवि कौन हैं?", "options": ["A) सुमित्रानंदन पंत", "B) आर.पी. 'निशंक'", "C) प्रेमचंद", "D) कबीरदास"], "marks": "1M"},
            {"q_no": 38, "type": "mcq", "question": "'ईदगाह' पाठ साहित्य की किस विधा के अंतर्गत आता है?", "options": ["A) कहानी", "B) कविता", "C) नाटक", "D) निबंध"], "marks": "1M"},
            {"q_no": 39, "type": "mcq", "question": "हामिद ने मेले से अपनी दादी के लिए क्या खरीदा?", "options": ["A) वकील", "B) सिपाही", "C) चिमटा", "D) रेवड़ियाँ"], "marks": "1M"},
            {"q_no": 40, "type": "mcq", "question": "कवि 'निशंक' के अनुसार भारतवासी संसार में क्या मिटाना चाहते हैं?", "options": ["A) खुशियाँ", "B) ऊँच-नीच का भेद", "C) प्रेम", "D) श्रद्धा"], "marks": "1M"},
            {"q_no": 41, "type": "mcq", "question": "हिंदी दिवस प्रतिवर्ष किस तिथि को मनाया जाता है?", "options": ["A) 15 अगस्त", "B) 14 सितंबर", "C) 26 जनवरी", "D) 2 अक्टूबर"], "marks": "1M"},
            {"q_no": 42, "type": "mcq", "question": "'उपन्यास सम्राट' की उपाधि से किसे सम्मानित किया गया है?", "options": ["A) जयशंकर प्रसाद", "B) प्रेमचंद", "C) रामधारी सिंह दिनकर", "D) सूर्यकांत त्रिपाठी निराला"], "marks": "1M"},
            {"q_no": 43, "type": "mcq", "question": "'पावन' शब्द का सही संधि विच्छेद क्या होगा?", "options": ["A) पौ + अन", "B) पो + अन", "C) पाव + अन", "D) पा + वन"], "marks": "1M"},
            {"q_no": 44, "type": "mcq", "question": "'भारतवासी' शब्द में कौन-सा समास है?", "options": ["A) तत्पुरुष समास", "B) द्वंद्व समास", "C) द्विगु समास", "D) अव्ययीभाव समास"], "marks": "1M"},
            {"q_no": 45, "type": "mcq", "question": "'निर्मल' शब्द का सही विलोम शब्द पहचानिए:", "options": ["A) स्वच्छ", "B) मलीन", "C) पावन", "D) सुंदर"], "marks": "1M"},
            {"q_no": 46, "type": "mcq", "question": "'वारि' शब्द का सही पर्यायवाची शब्द है:", "options": ["A) हवा", "B) जल", "C) अग्नि", "D) पर्वत"], "marks": "1M"},
            {"q_no": 47, "type": "mcq", "question": "'कलेजा ठंडा होना' मुहावरे का सही अर्थ क्या है?", "options": ["A) बहुत ठंड लगना", "B) संतोष होना / शांति मिलना", "C) बीमार होना", "D) डर जाना"], "marks": "1M"},
            {"q_no": 48, "type": "mcq", "question": "'सत्यमेव जयते' का वास्तविक संदेश क्या है?", "options": ["A) असत्य की जीत होती है", "B) सत्य की ही विजय होती है", "C) धन की जीत होती है", "D) शक्ति की जीत होती है"], "marks": "1M"},
            {"q_no": 49, "type": "mcq", "question": "दादी अमीना ने हामिद के चिमटा लाने पर क्या अनुभव किया?", "options": ["A) क्रोध", "B) गर्व, ममता और भावुकता", "C) निराशा", "D) उपेक्षा"], "marks": "1M"},
            {"q_no": 50, "type": "mcq", "question": "'प्रतिदिन' शब्द में कौन-सा समास है?", "options": ["A) तत्पुरुष", "B) कर्मधारय", "C) अव्ययीभाव", "D) बहुव्रीहि"], "marks": "1M"},
            {"q_no": 51, "type": "mcq", "question": "इस प्रश्न-पत्र के अनुसार विद्यार्थियों में किस गुण का विकास आवश्यक है?", "options": ["A) नैतिक चरित्र व देशप्रेम", "B) केवल रटना", "C) प्रतिस्पर्धा", "D) अभिमान"], "marks": "1M"}
        ]
        sections.append({
            "section_id": "IV",
            "title": "SECTION - IV",
            "instruction": "भाग - घ : बहुविकल्पीय वस्तुनिष्ठ प्रश्न (Part - B Objective Bits)",
            "marks_total": "16 x 1 = 16M",
            "questions": mcq16
        })

    paper = {
        "metadata": metadata,
        "sections": sections
    }
    return paper

def main():
    parser = argparse.ArgumentParser(description="Generate Hindi Exam Paper (25M, 50M, 100M)")
    parser.add_argument("-c", "--chapters", type=str, default="2,3", help="Chapters/Lessons to include (e.g. '2,3' or '1,2' or 'all')")
    parser.add_argument("-m", "--marks", type=int, default=100, choices=[25, 50, 100], help="Total marks (25, 50, 100)")
    parser.add_argument("-o", "--open", action="store_true", help="Open generated PDF on macOS")
    args = parser.parse_args()

    tb = load_textbook()
    render_script = get_render_script()
    chapter_keys = parse_chapter_keys(args.chapters, tb)
    paper_data = build_paper(tb, chapter_keys, args.marks)

    ch_label = "_".join([k.replace("chapter_", "ch").replace("unit_", "u") for k in chapter_keys[:3]])
    out_json = os.path.join(DIST_DIR, f"hindi_class10_{ch_label}_{args.marks}m.json")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(paper_data, f, ensure_ascii=False, indent=2)

    cmd = ["python3", render_script, out_json, "-d", DIST_DIR]
    if args.open:
        cmd.append("--open")
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Error rendering paper:\n{res.stderr}")
        sys.exit(res.returncode)

    pdf_path = os.path.join(DIST_DIR, f"hindi_class10_{ch_label}_{args.marks}m.pdf")
    if os.path.exists(pdf_path):
        print(f"[✓] Successfully compiled PDF: {pdf_path}")
        print(f"MEDIA:{pdf_path}")
    else:
        for line in res.stdout.splitlines():
            if line.strip().endswith(".pdf"):
                pdf_path = line.strip().split()[-1]
                print(f"[✓] Generated PDF: {pdf_path}")
                print(f"MEDIA:{pdf_path}")
                break

if __name__ == "__main__":
    main()
