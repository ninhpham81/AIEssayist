import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="HỆ SINH THÁI WRITING THÔNG MINH",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; color: #2C3E50; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { color: #27AE60; background-color: white; border-radius: 8px 8px 0 0; border-bottom: 3px solid #27AE60; }
    div[data-testid="stBlock"] { background-color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .eco-title { color: #27AE60; font-weight: 800; margin-bottom: 0px;}
    .eco-subtitle { color: #7F8C8D; font-size: 1.1em; margin-top: 5px; margin-bottom: 20px;}
    
    .markdown-text-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 16px; color: #2C3E50; }
    .markdown-text-container h1, .markdown-text-container h2, .markdown-text-container h3 { color: #27AE60; font-weight: 700; margin-top: 15px; }
    .markdown-text-container p, .markdown-text-container li { line-height: 1.7; margin-bottom: 8px; font-size: 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 📌 CẤU HÌNH MODEL
MODEL_NAME = "gemini-2.5-flash"

@st.cache_resource
def init_connections():
    try:
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

        # 🚀 1. KẾT NỐI GEMINI API
        api_key = "AQ.Ab8RN6LKQBwVMAgVb6pSA4__hMeZ3-j5m63ZCrvAA28_kh83_Q"
        ai_client = genai.Client(api_key=api_key)

        # 🚀 2. KẾT NỐI GOOGLE SHEETS
        scope_sheets = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_sheets = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope_sheets
        )
        gs_client = gspread.authorize(creds_sheets)

        spreadsheet = gs_client.open_by_key("1Y0BlBZlLceKrEE1EbBHl-9RofU1X6y-nMRa7ErUIo-E")
        sheet_main = spreadsheet.sheet1
        
        try: sheet_wall = spreadsheet.worksheet("Community_Wall")
        except: sheet_wall = None
        try: sheet_lib = spreadsheet.worksheet("Public_Library")
        except: sheet_lib = None
        try: sheet_challenge = spreadsheet.worksheet("Weekly_Challenges")
        except: sheet_challenge = None

        return ai_client, sheet_main, sheet_wall, sheet_lib, sheet_challenge
    except Exception as e:
        return None, None, None, None, None

ai_client, sheet, sheet_wall, sheet_lib, sheet_challenge = init_connections()

# Khởi tạo Session State
if "plan_text" not in st.session_state: st.session_state.plan_text = ""
if "tree_map_text" not in st.session_state: st.session_state.tree_map_text = ""
if "current_topic" not in st.session_state: st.session_state.current_topic = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "tutor_active" not in st.session_state: st.session_state.tutor_active = False
if "tutor_system_prompt" not in st.session_state: st.session_state.tutor_system_prompt = ""
if "local_challenges" not in st.session_state:
    st.session_state.local_challenges = [
        {"Thời gian": "2026-08-07 15:30", "Họ và tên": "Minh Anh", "Chủ đề thử thách": "The impact of AI on smart ecosystems", "Điểm số": 92, "Trình độ đạt được": "B2", "Nhận xét AI": "Bài viết xuất sắc, lập luận chặt chẽ, bám sát chủ đề hệ sinh thái thông minh.", "Nội dung bài làm": "Artificial intelligence plays a transformative role in shaping smart ecosystems today. By automating resource management with unprecedented precision, smart systems optimize energy consumption. For instance, smart grids leverage predictive algorithms to balance power supply and demand dynamically, significantly reducing waste and carbon footprints."},
        {"Thời gian": "2026-08-07 16:10", "Họ and tên": "Gia Hân", "Chủ đề thử thách": "The impact of AI on smart ecosystems", "Điểm số": 85, "Trình độ đạt được": "B1", "Nhận xét AI": "Bài viết tốt, từ vựng phong phú, cấu trúc mạch lạc.", "Nội dung bài làm": "AI is very important for smart ecosystems. It helps us save energy and protect the environment. Smart devices can learn from human habits and make our lives much more convenient and sustainable."}
    ]

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254068.png", width=80)
    st.markdown("### ⚙️ DNA Của Bạn")
    st.caption("Thiết lập này sẽ đồng bộ toàn bộ trí tuệ AI trong hệ sinh thái theo đúng năng lực của bạn.")

    global_level = st.selectbox(
        "🎯 Định vị năng lực (Level):",
        [
            "A1 (Beginner) - Viết câu đơn giản",
            "A2 (Elementary) - Viết đoạn ngắn",
            "B1 (Intermediate) - Mức độ cơ bản IELTS 4.0-5.0",
            "B2 (Upper-Intermediate) - Khá IELTS 5.5-6.5",
            "C1 (Advanced) - Chuyên sâu IELTS 7.0+",
            "SAT Writing - Hành văn học thuật Mỹ",
            "General English - Tiếng Anh tổng quát",
        ],
        index=0
    )

    global_focus = st.multiselect(
        "🔍 Mục tiêu cải thiện chính:",
        ["Từ vựng học thuật", "Ngữ pháp cốt lõi", "Sự mạch lạc (Coherence)", "Phát triển ý tưởng (Brainstorming)"],
        default=["Từ vựng học thuật", "Ngữ pháp cốt lõi"],
    )

    st.info(f"💡 **Smart Tip:** Hệ thống tự động ghi nhớ level **{global_level.split(' ')[0]}** để điều chỉnh độ khó.")

    st.markdown("---")
    st.markdown("### 📖 Trạm Tra Cứu Nhanh Chuyên Sâu")
    st.caption("Phân tích chi tiết từ, câu hoặc văn bản: Nghĩa, Ngữ pháp, Collocations & Từ loại.")
    lookup_text = st.text_area("🔍 Nhập từ/câu/văn bản cần tra cứu:", height=100, key="quick_lookup")

    if st.button("Phân Tích Chuyên Sâu", use_container_width=True):
        if lookup_text and ai_client:
            with st.spinner("Đang phân tích ngữ pháp, nghĩa và collocation..."):
                prompt_dict = f"""
                Bạn là Chuyên gia Ngôn ngữ học và Từ vựng học. Hãy phân tích cực kỳ chi tiết cho văn bản/cụm từ/từ sau: "{lookup_text}".
                
                Trình bày theo định dạng Markdown rõ ràng gồm các mục:
                1. **Phân tích nghĩa & Ngữ cảnh:** (Nghĩa chính, sắc thái biểu cảm)
                2. **Từ loại & Phát âm (IPA):** (Nếu là từ/cụm từ)
                3. **Cấu trúc ngữ pháp & Cú pháp:** (Phân tích cấu trúc câu nếu là văn bản/câu)
                4. **Collocations (Cụm từ hay đi kèm tự nhiên):** (Liệt kê 3-4 collocations chuẩn bản xứ)
                5. **Ví dụ ứng dụng nâng cao:** (Câu ví dụ minh họa thực tế)
                """
                try:
                    dict_res = ai_client.models.generate_content(model=MODEL_NAME, contents=prompt_dict)
                    st.success("Kết quả phân tích chuyên sâu:")
                    st.markdown(dict_res.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")

st.markdown("<h1 class='eco-title'>🌱 AIEssayist Pro v8.1: Smart Writing Ecosystem</h1>", unsafe_allow_html=True)
st.markdown("<p class='eco-subtitle'>Khởi tạo Ý Tưởng -> Luyện Tập Cùng AI -> Chấm Điểm & Tối Ưu -> Xây Dựng Thói Quen -> Lan Tỏa Cộng Đồng</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💡 1. Trạm Khởi Tạo",
    "🏋️ 2. Phòng Luyện Tập AI",
    "⚖️ 3. Xưởng Chấm Điểm",
    "📂 4. Hồ Sơ (Logs)",
    "🌍 5. Rừng Cộng Đồng",
    "📚 6. Kho Học Liệu"
])

# ==========================================
# TAB 1: KHỞI TẠO & SƠ ĐỒ MINDMAP
# ==========================================
with tab1:
    col_t1_left, col_t1_right = st.columns([1.2, 1.8])
    with col_t1_left:
        st.markdown("### 🗺️ Nhập hạt giống ý tưởng")
        plan_topic = st.text_area("👉 Đưa cho tôi một chủ đề / Đề bài:", placeholder="Ví dụ: my mother...", height=100)
        btn_plan = st.button("🚀 Kích hoạt phân tích ý tưởng", type="primary", use_container_width=True)

        st.markdown("---")
        if st.session_state.tree_map_text:
            st.markdown("### 🧠 Sơ đồ Khối (Mindmap)")
            st.caption("Cấu trúc trực quan gọn gàng vừa vặn khung trái")
            try:
                st.graphviz_chart(st.session_state.tree_map_text, use_container_width=True)
            except Exception as e:
                st.warning("Không thể hiển thị đồ họa sơ đồ. Mã sơ đồ chi tiết:")
                st.code(st.session_state.tree_map_text, language="dot")

    with col_t1_right:
        if btn_plan:
            if not plan_topic or not ai_client:
                st.error("❌ Hệ sinh thái cần một hạt giống (chủ đề) để nảy mầm hoặc API chưa kết nối!")
            else:
                with st.spinner("Hệ thống đang thiết kế Sơ đồ tư duy, Dàn ý có ví dụ và Cấu trúc ngữ pháp..."):
                    try:
                        prompt_plan = f"""
                        Bạn là Chuyên gia Khảo thí và Ngôn ngữ. Thiết lập hệ thống học tập cho chủ đề: '{plan_topic}'.
                        TRÌNH ĐỘ: {global_level}. Trình bày bằng Markdown sạch sẽ, font chữ đồng đều.
                        
                        PHẦN 1: DÀN Ý CHI TIẾT (BẮT BUỘC CÓ VÍ DỤ MẪU CHO TỪNG Ý)
                        - Chia rõ 3 phần: Mở bài (Introduction) - Thân bài (Body Paragraphs) - Kết luận (Conclusion).
                        - Mỗi ý triển khai bắt buộc phải kèm theo:
                          + Mục đích / Ý cụ thể.
                          + Ví dụ câu tiếng Anh chuẩn tương ứng với trình độ {global_level} kèm dịch nghĩa tiếng Việt để người học áp dụng ngay.
                        
                        PHẦN 2: TỪ VỰNG THÔNG MINH ĐA GIÁC QUAN (Liệt kê 8-10 từ vựng phong phú phù hợp chủ đề)
                        - Cấu trúc: **Từ vựng** | IPA | Nghĩa Tiếng Việt | 1 Ví dụ minh họa.
                        
                        PHẦN 3: CẤU TRÚC NGỮ PHÁP ĂN ĐIỂM (Cung cấp 3-5 cấu trúc câu tuyệt hay cho trình độ {global_level})
                        - Trình bày công thức cấu trúc, khi nào nên dùng, và một câu ví dụ áp dụng trực tiếp cho chủ đề '{plan_topic}'.
                        
                        PHẦN 4: BÀI VĂN MẪU HOÀN CHỈNH (Đúng chuẩn {global_level})
                        """
                        res_plan = ai_client.models.generate_content(model=MODEL_NAME, contents=prompt_plan)
                        st.session_state.plan_text = res_plan.text

                        prompt_mind = f"""
                        Dựa vào dàn ý chi tiết bạn vừa tạo cho chủ đề '{plan_topic}', hãy tạo mã DOT Graphviz để vẽ sơ đồ tư duy nhỏ gọn, rõ ràng.
                        YÊU CẦU QUAN TRỌNG VỀ ĐỊNH DẠNG:
                        1. Cấu trúc hướng LR (Left to Right): rankdir=LR;
                        2. Cấu hình đồ họa thu gọn để vừa vặn khung trái: 
                           graph [fontname="Segoe UI", fontsize=10, nodesep=0.25, ranksep=0.4];
                           node [shape=box, style="filled,rounded", fontname="Segoe UI", fontsize=11, margin="0.2,0.15"];
                           edge [fontname="Segoe UI", fontsize=9, penwidth=1.2];
                        3. Cỡ chữ nhỏ gọn (12px cho node), khung hộp vừa vặn sát chữ.
                        4. Phối màu (fillcolor) sinh động, phân cấp rõ ràng (Node gốc, Mở/Thân/Kết, Ý chi tiết).
                        5. TUYỆT ĐỐI CHỈ XUẤT MÃ DOT THUẦN TÚY (từ 'digraph G {{' đến '}}'). Không bọc trong Markdown code blocks.
                        """
                        res_mind = ai_client.models.generate_content(model=MODEL_NAME, contents=prompt_mind)

                        raw_dot = res_mind.text.strip()
                        clean_dot = re.sub(r"^```[a-zA-Z]*\n", "", raw_dot)
                        clean_dot = re.sub(r"\n```$", "", clean_dot).strip()

                        st.session_state.tree_map_text = clean_dot
                        st.session_state.current_topic = plan_topic
                        st.rerun()

                    except Exception as e:
                        st.error(f"Lỗi tạo dàn ý hoặc sơ đồ: {e}")

        if st.session_state.plan_text:
            st.markdown(f"<div class='markdown-text-container'>{st.session_state.plan_text}</div>", unsafe_allow_html=True)
        elif not btn_plan:
            st.info("👈 Nhập chủ đề bên trái và bấm nút để khởi tạo không gian ý tưởng.")

# ==========================================
# TAB 2: PHÒNG LUYỆN TẬP AI (PROFESSOR WRITEWELL)
# ==========================================
with tab2:
    st.markdown("### 🏋️ Phòng Luyện Tập AI Cùng Professor WriteWell")
    col_t2_1, col_t2_2 = st.columns([1, 2])

    with col_t2_1:
        tutor_topic = st.text_input("📝 Đề tài luyện viết hôm nay:", value=st.session_state.current_topic)
        tutor_mode = st.selectbox(
            "🛠️ Chế độ luyện tập (Methods):",
            ["Hướng dẫn phương pháp (Từng bước)", "Điền vào chỗ trống", "Trả lời câu hỏi ngắn", "Viết đoạn văn ngắn"],
        )

        if st.button("🚀 BẬT PHÒNG LUYỆN TẬP", use_container_width=True, type="primary"):
            if tutor_topic and ai_client:
                st.session_state.tutor_active = True
                st.session_state.chat_history = []

                system_prompt = f"""
                IDENTITY
                Phòng luyện tập AI là Professor WriteWell - một gia sư tiếng Anh chuyên sâu về kỹ năng Writing với 15 năm kinh nghiệm giảng dạy quốc tế. Bạn thành thạo các phương pháp giảng dạy hiện đại và am hiểu sâu sắc về IELTS, TOEFL, Cambridge English và các chứng chỉ quốc tế khác.

                CORE COMPETENCIES
                • Đánh giá và phân loại trình độ viết chính xác
                • Thiết kế lộ trình học tập cá nhân hóa
                • Phản hồi chi tiết với feedback sandwich (khen - sửa - khuyến khích)
                • Giảng dạy từ cơ bản đến nâng cao

                ASSESSMENT FRAMEWORK
                Khi chấm bài, sử dụng thang điểm 4 mức:
                • ⭐ Excellent: Xuất sắc, đạt chuẩn cao
                • ✅ Good: Tốt, cần cải thiện nhỏ
                • ⚠️ Needs Work: Cần luyện tập thêm
                • ❌ Requires Attention: Cần tập trung khắc phục
                Đánh giá 5 tiêu chí: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, Style & Register.

                TEACHING METHODOLOGY
                Bước 1: Xác định trình độ (Học viên đang đặt mục tiêu ở {global_level}, Chủ đề: {tutor_topic})
                Bước 2: Giao bài tập cụ thể
                Bước 3: Nhận và phân tích bài viết
                Bước 4: Feedback chi tiết (Điểm mạnh -> Phân tích theo tiêu chí -> Sửa lỗi chi tiết từng câu -> Đoạn văn mẫu -> Bước tiếp theo)
                Bước 5: Theo dõi tiến độ

                COMMUNICATION STYLE
                • Thân thiện nhưng chuyên nghiệp, sử dụng emoji phù hợp
                • Giải thích bằng tiếng Việt khi cần. Luôn kết thúc bằng câu hỏi/lời mời viết tiếp.
                """
                st.session_state.tutor_system_prompt = system_prompt
                
                first_msg = """Xin chào! Tôi là Professor WriteWell, gia sư tiếng Anh chuyên về Writing. Rất vui được đồng hành cùng bạn trên hành trình cải thiện kỹ năng viết! ✍️\n\nĐể tôi có thể hỗ trợ bạn tốt nhất, bạn có thể cho tôi biết:\n1. Trình độ tiếng Anh hiện tại của bạn?\n2. Mục tiêu học Writing của bạn là gì?\n3. Bạn muốn tập trung vào dạng bài nào (Essay, email...)?\n\nHãy chia sẻ với tôi nhé! 😊"""
                
                st.session_state.chat_history.append({"role": "ai", "content": first_msg})
                st.rerun()
            else:
                st.warning("Vui lòng nhập chủ đề.")

        if st.button("🛑 KẾT THÚC BUỔI HỌC", use_container_width=True):
            st.session_state.tutor_active = False
            st.session_state.chat_history = []
            st.session_state.tutor_system_prompt = ""
            st.rerun()

    with col_t2_2:
        chat_box = st.container(height=450)
        with chat_box:
            if not st.session_state.tutor_active:
                st.info("👈 Bấm 'Bật phòng luyện tập' để gọi Professor WriteWell.")
            else:
                for msg in st.session_state.chat_history:
                    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                        st.markdown(msg["content"])

        if st.session_state.tutor_active:
            user_msg = st.chat_input("✍️ Trò chuyện với Professor WriteWell...")
            if user_msg:
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with chat_box:
                    with st.chat_message("user"):
                        st.markdown(user_msg)
                    with st.chat_message("assistant"):
                        with st.spinner("Professor WriteWell đang phân tích..."):
                            try:
                                full_context = st.session_state.tutor_system_prompt + "\n\n--- LỊCH SỬ HỘI THOẠI ---\n"
                                for m in st.session_state.chat_history:
                                    role_name = "Học viên" if m["role"] == "user" else "Professor WriteWell"
                                    full_context += f"{role_name}: {m['content']}\n"
                                full_context += "Professor WriteWell:"
                                
                                reply = ai_client.models.generate_content(model=MODEL_NAME, contents=full_context)
                                st.markdown(reply.text)
                                st.session_state.chat_history.append({"role": "ai", "content": reply.text})
                            except Exception as e:
                                st.error(f"Lỗi: {e}")

# ==========================================
# TAB 3: XƯỞNG ĐÁNH GIÁ CẤP ĐIỂM SỐ CỤ THỂ
# ==========================================
with tab3:
    col_in, col_out = st.columns([1, 1])
    with col_in:
        st.markdown("### ⚖️ Xưởng Đánh Giá & Cấp Điểm Số")
        st.info(f"Tiêu chuẩn đánh giá mục tiêu: **{global_level}**.")

        topic_check = st.text_input("👉 Đề bài (Topic):", value=st.session_state.current_topic, key="check_topic")
        content_check = st.text_area("✍️ Bài làm hoàn chỉnh của bạn:", height=300, key="check_content")

        if st.button("✨ Chấm Điểm Bài Viết (Smart Check)", type="primary"):
            if not topic_check or not content_check or not ai_client:
                st.error("❌ Vui lòng nhập nội dung và kiểm tra API!")
            else:
                with st.spinner("Chuyên gia khảo thí đang chấm điểm..."):
                    prompt_grade = (
                        "Vai trò: Chuyên gia Khảo thí Viết Cấp cao.\n"
                        f"Khung đánh giá: {global_level}. Đề bài: '{topic_check}'. Bài làm: '{content_check}'.\n\n"
                        "TRẢ VỀ BẰNG TIẾNG VIỆT THEO ĐÚNG CẤU TRÚC NÀY:\n\n"
                        "🎯 **ĐÁNH GIÁ TỔNG QUAN:** [Nhận xét chung về bài viết]\n"
                        "🏆 **ĐIỂM SỐ TỔNG QUÁT:** [Cho điểm cụ thể: /100 hoặc /9.0]\n\n"
                        "📊 **PHÂN TÍCH ĐIỂM SỐ CHI TIẾT TỪNG TIÊU CHÍ:**\n"
                        "1. **Task Achievement (Hoàn thành tác vụ):** [Điểm số] - [Lý do]\n"
                        "2. **Coherence & Cohesion (Mạch lạc & Liên kết):** [Điểm số] - [Lý do]\n"
                        "3. **Lexical Resource (Vốn từ vựng):** [Điểm số] - [Lý do]\n"
                        "4. **Grammatical Range & Accuracy (Ngữ pháp):** [Điểm số] - [Lý do]\n\n"
                        "🛠️ **LỖI CỤ THỂ CẦN SỬA (Max 3 lỗi nặng):**\n"
                        "- **Lỗi:** [Câu sai] -> **Sửa lại:** [Câu đúng] -> **Giải thích:** [Lý do]\n\n"
                        "🚀 **GỢI Ý NÂNG CẤP BÀI VĂN:**\n"
                        "- Chọn 1-2 câu yếu nhất và viết lại ở đẳng cấp cao hơn."
                    )
                    try:
                        response = ai_client.models.generate_content(model=MODEL_NAME, contents=prompt_grade)
                        full_feedback = response.text

                        level = "Chưa rõ"
                        for line in full_feedback.split("\n"):
                            if "ĐIỂM SỐ TỔNG QUÁT" in line:
                                level = line.replace("🏆", "").strip()
                                break

                        if sheet:
                            sheet.append_row([
                                datetime.now().strftime("%Y-%m-%d %H:%M"),
                                topic_check, global_level, content_check, level, full_feedback, "Optimized"
                            ])

                        with col_out:
                            st.success("Thẩm định hoàn tất!")
                            st.markdown(full_feedback)
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

# ==========================================
# TAB 4: HỒ SƠ LƯU TRỮ
# ==========================================
with tab4:
    st.header("📂 Hồ Sơ Thói Quen Viết Lách")
    st.write("Lưu trữ toàn bộ các bài viết bạn đã nhờ AI chấm điểm tại 'Xưởng Đánh Giá'.")
    if st.button("🔄 Đồng bộ dữ liệu đám mây"):
        st.cache_data.clear()
    try:
        if sheet:
            all_rows = sheet.get_all_values()
            if len(all_rows) > 1:
                df = pd.DataFrame(
                    all_rows[1:],
                    columns=["Timestamp", "Topic", "Target Level", "Content", "Achieved Level", "Feedback", "Status"]
                ).iloc[::-1]
                st.dataframe(df[["Timestamp", "Topic", "Target Level", "Achieved Level"]], use_container_width=True)

                df["Select_Label"] = df["Timestamp"] + " - " + df["Topic"]
                sel_label = st.selectbox("📖 Mở lại hồ sơ cũ:", df["Select_Label"].tolist())
                if sel_label:
                    row = df[df["Select_Label"] == sel_label].iloc[0]
                    st.markdown(f"### 📌 {row['Topic']} (Mục tiêu: {row['Target Level']})")
                    st.code(row["Content"], language="text")
                    st.info(row["Feedback"])
    except Exception as e:
        st.info(f"Chưa ghi nhận dữ liệu lịch sử hoặc lỗi: {e}")

# ==========================================
# TAB 5: RỪNG CỘNG ĐỒNG (ĐẤU TRƯỜNG: TRỪ 50% ĐIỂM NẾU LẠC ĐỀ + XEM LẠI BÀI & NHẬN XÉT CHI TIẾT)
# ==========================================
with tab5:
    st.header("🌍 Sinh Thái Học Hỏi Cộng Đồng")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🏛️ Peer Review (Ẩn Danh)", "📚 Nguồn Tài Nguyên Chung", "🏆 Đấu Trường Hằng Tuần"])

    with sub_tab1:
        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            st.markdown("### 📝 Xin góp ý ẩn danh")
            post_topic = st.text_input("📌 Tiêu đề chia sẻ:")
            post_essay = st.text_area("✍️ Nội dung cần review:", height=150)
            if st.button("📤 Gieo mầm lên bảng tin"):
                if post_topic and post_essay and sheet_wall:
                    sheet_wall.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        f"POST_{datetime.now().strftime('%M%S')}",
                        post_topic,
                        post_essay,
                        "Chưa có comment",
                    ])
                    st.success("✅ Đã gieo mầm thành công!")
                else:
                    st.error("❌ Nhập đủ thông tin hoặc lỗi kết nối!")

        with col_w2:
            st.markdown("### 💬 Mạng lưới tương tác")
            try:
                if sheet_wall:
                    wall_rows = sheet_wall.get_all_values()
                    if len(wall_rows) > 1:
                        wall_df = pd.DataFrame(
                            wall_rows[1:],
                            columns=["Time", "ID", "Topic", "Content", "Comments"],
                        )
                        for _, row in wall_df.iloc[::-1].iterrows():
                            with st.expander(f"📌 {row['Topic']}"):
                                st.code(row["Content"], language="text")
                                st.caption(f"💬 Phản hồi: {row['Comments']}")
                                new_cmt = st.text_input("Để lại hạt giống góp ý:", key=f"in_{row['ID']}")
                                if st.button("Gửi góp ý", key=f"btn_{row['ID']}"):
                                    cell = sheet_wall.find(row["ID"])
                                    sheet_wall.update_cell(
                                        cell.row,
                                        5,
                                        row["Comments"] + f" | [Góp ý]: {new_cmt}",
                                    )
                                    st.success("✅ Đã gửi!")
                    else:
                        st.info("Bảng tin trống.")
            except:
                pass

    with sub_tab2:
        st.markdown("### 📚 Thư Viện Cấu Trúc Hay (Xem lại chi tiết)")
        col_l1, col_l2 = st.columns([1, 1])
        with col_l1:
            st.markdown("#### 🔒 Đóng góp cấu trúc mới")
            new_struct = st.text_input("💡 Cấu trúc câu / Từ vựng:")
            struct_note = st.text_area("💡 Hướng dẫn ứng dụng / Giải thích chi tiết:", height=100)
            if st.button("Đóng góp vào Sinh thái"):
                if new_struct and struct_note and sheet_lib:
                    sheet_lib.append_row([
                        datetime.now().strftime("%Y-%m-%d"),
                        new_struct,
                        struct_note,
                    ])
                    st.success("✅ Đóng góp thành công!")
                else:
                    st.warning("Vui lòng nhập đầy đủ nội dung.")
                    
        with col_l2:
            st.markdown("#### 📖 Kho tài nguyên đóng góp")
            try:
                if sheet_lib:
                    lib_rows = sheet_lib.get_all_values()
                    if len(lib_rows) > 1:
                        lib_df = pd.DataFrame(
                            lib_rows[1:], columns=["Date", "Structure", "Note"]
                        )
                        for idx, row in lib_df.iterrows():
                            with st.expander(f"📌 [{row['Date']}] {row['Structure']}"):
                                st.markdown(f"**Chi tiết / Hướng dẫn ứng dụng:**\n\n{row['Note']}")
                    else:
                        st.info("Thư viện chưa có tài liệu nào.")
            except Exception as e:
                st.info(f"Đang tải thư viện: {e}")

    with sub_tab3:
        st.info("🔥 **THỬ THÁCH TUẦN NÀY:** Viết 150 từ: 'The impact of AI on smart ecosystems'.")
        challenge_topic_name = "The impact of AI on smart ecosystems"
        col_g1, col_g2 = st.columns([1, 1.2])
        with col_g1:
            user_name = st.text_input("Bí danh bảng xếp hạng:")
            challenge_essay = st.text_area("✍️ Bài dự thi của bạn:", height=150)
            if st.button("🏅 Nộp bài & Chấm AI"):
                if user_name and challenge_essay and ai_client:
                    with st.spinner("AI đang kiểm tra chủ đề, chấm điểm và đánh giá..."):
                        res_c = ai_client.models.generate_content(
                            model=MODEL_NAME,
                            contents=(
                                f"Chấm khắt khe văn bản sau theo khung {global_level} cho chủ đề chính thức là '{challenge_topic_name}'. "
                                "QUAN TRỌNG: Hãy kiểm tra xem bài viết có bám sát chủ đề trên không. Nếu lạc đề hoàn toàn hoặc không liên quan, hãy đánh giá bài viết lạc đề.\n"
                                "Format bắt buộc:\n"
                                "- ĐIỂM SỐ TỔNG: [Số từ 1-100]\n"
                                "- TRÌNH ĐỘ ĐẠT ĐƯỢC: [Mức độ tương ứng như A1, A2, B1, B2...]\n"
                                "- CÓ LẠC ĐỀ KHÔNG: [Có hoặc Không]\n"
                                "- NHẬN XÉT: [Nhận xét chi tiết rõ ràng, nếu lạc đề hãy nêu rõ lý do trừ 50% điểm]\n"
                                f"Bài làm: {challenge_essay}"
                            ),
                        )
                        score = 70
                        achieved_lvl = global_level.split(" ")[0]
                        is_off_topic = "Không"
                        feedback_comment = "Bài viết hoàn thành tốt yêu cầu thử thách."
                        
                        for line in res_c.text.split("\n"):
                            if "ĐIỂM SỐ TỔNG" in line:
                                nums = "".join(filter(str.isdigit, line))
                                if nums.isdigit(): score = int(nums)
                            if "TRÌNH ĐỘ ĐẠT ĐƯỢC" in line:
                                achieved_lvl = line.replace("TRÌNH ĐỘ ĐẠT ĐƯỢC:", "").replace("- TRÌNH ĐỘ ĐẠT ĐƯỢC", "").strip()
                            if "CÓ LẠC ĐỀ KHÔNG" in line:
                                if "có" in line.lower(): is_off_topic = "Có"
                            if "NHẬN XÉT" in line:
                                feedback_comment = line.replace("NHẬN XÉT:", "").strip()

                        # Nếu lạc đề, trừ 50% điểm số và ghi chú rõ ràng vào nhận xét
                        if is_off_topic == "Có":
                            score = int(score * 0.5)
                            feedback_comment = f"⚠️ [LẠC ĐỀ - BỊ TRỪ 50% ĐIỂM] {feedback_comment}"
                        
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                        new_entry = {
                            "Thời gian": current_time, 
                            "Họ và tên": user_name, 
                            "Chủ đề thử thách": challenge_topic_name, 
                            "Điểm số": score, 
                            "Trình độ đạt được": achieved_lvl, 
                            "Nhận xét AI": feedback_comment,
                            "Nội dung bài làm": challenge_essay
                        }
                        
                        st.session_state.local_challenges.insert(0, new_entry)
                        
                        if sheet_challenge:
                            try:
                                sheet_challenge.append_row([current_time, user_name, challenge_topic_name, str(score), achieved_lvl, feedback_comment, challenge_essay])
                            except:
                                pass
                                
                        st.success(f"🎉 Hoàn thành! Điểm: {score}/100 | Trình độ: {achieved_lvl}")
                        st.rerun()
                else:
                    st.warning("Vui lòng nhập đầy đủ bí danh và nội dung bài viết.")
                    
        with col_g2:
            st.markdown("### 🏆 Bảng Xếp Hạng Đấu Trường")
            try:
                all_records = list(st.session_state.local_challenges)
                if sheet_challenge:
                    try:
                        sheet_rows = sheet_challenge.get_all_values()
                        if len(sheet_rows) > 1:
                            for r in sheet_rows[1:]:
                                while len(r) < 7:
                                    r.append("N/A")
                                rec = {
                                    "Thời gian": r[0],
                                    "Họ và tên": r[1],
                                    "Chủ đề thử thách": r[2],
                                    "Điểm số": int(r[3]) if str(r[3]).isdigit() else 70,
                                    "Trình độ đạt được": r[4],
                                    "Nhận xét AI": r[5],
                                    "Nội dung bài làm": r[6]
                                }
                                if rec not in all_records:
                                    all_records.append(rec)
                    except:
                        pass

                if len(all_records) > 0:
                    c_df = pd.DataFrame(all_records)
                    c_df["Điểm số_num"] = pd.to_numeric(c_df["Điểm số"], errors="coerce").fillna(0)
                    c_df = c_df.sort_values(by="Điểm số_num", ascending=False).reset_index(drop=True)
                    c_df["Xếp hạng"] = [f"Top {i+1} 🥇" if i==0 else (f"Top {i+1} 🥈" if i==1 else (f"Top {i+1} 🥉" if i==2 else f"Top {i+1}")) for i in range(len(c_df))]
                    
                    # Bảng hiển thị đúng 5 cột: Thời gian, Họ và tên, Chủ đề thử thách, Điểm số, Xếp hạng
                    display_df = c_df[["Thời gian", "Họ và tên", "Chủ đề thử thách", "Điểm số", "Xếp hạng"]]
                    st.dataframe(display_df, use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("#### 📖 Xem Lại Bài Làm & Nhận Xét Của AI")
                    options = []
                    for i, r in c_df.iterrows():
                        options.append(f"{r['Họ and tên']} - {r['Điểm số']}đ ({r['Trình độ đạt được']}) [ID:{i}]")
                        
                    selected_option = st.selectbox("Chọn thành viên để xem chi tiết bài viết:", options, key="select_member_essay_fixed")
                    if selected_option:
                        idx_str = selected_option.split("[ID:")[1].replace("]", "")
                        idx = int(idx_str)
                        chosen_row = c_df.iloc[idx]
                        
                        st.info(f"**Tác giả:** {chosen_row['Họ and tên']} | **Thời gian:** {chosen_row['Thời gian']} | **Điểm số:** {chosen_row['Điểm số']}đ | **Trình độ đánh giá:** {chosen_row['Trình độ đạt được']}")
                        st.markdown(f"**💬 Nhận xét và đánh giá của AI:**\n> {chosen_row.get('Nhận xét AI', 'Không có nhận xét.')}")
                        st.text_area("✍️ Nội dung bài dự thi chi tiết:", value=chosen_row["Nội dung bài làm"], height=150, disabled=True, key=f"member_essay_view_fixed_{idx}")
                else:
                    empty_df = pd.DataFrame(columns=["Thời gian", "Họ and tên", "Chủ đề thử thách", "Điểm số", "Xếp hạng"])
                    st.dataframe(empty_df, use_container_width=True)
                    st.info("💡 Chưa có bài nộp nào trong bảng xếp hạng. Hãy nộp bài ở cột bên trái!")
            except Exception as e:
                empty_df = pd.DataFrame(columns=["Thời gian", "Họ and tên", "Chủ đề thử thách", "Điểm số", "Xếp hạng"])
                st.dataframe(empty_df, use_container_width=True)
                st.info(f"💡 Đang khởi tạo dữ liệu bảng: {e}")

# ==========================================
# TAB 6: KHO HỌC LIỆU
# ==========================================
with tab6:
    st.header("📚 Kho Học Liệu & Công Cụ Hỗ Trợ Viết")
    st.markdown(
        "Hệ thống tổng hợp các nguồn tài nguyên uy tín giúp bạn liên tục nạp 'đầu"
        " vào' (input) chất lượng để nâng cao kỹ năng viết mỗi ngày."
    )

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        with st.expander("🔗 1. Công Cụ Hỗ Trợ Chuyên Sâu (Tools)", expanded=True):
            st.markdown("""
            - **[Ozdic (Collocation Dictionary)](https://ozdic.com/):** Từ điển tra cứu các cụm từ đi chung với nhau tự nhiên nhất.
            - **[Grammarly](https://www.grammarly.com/):** Tiện ích mở rộng kiểm tra lỗi chính tả và ngữ pháp.
            - **[QuillBot](https://quillbot.com/):** Công cụ paraphrase (viết lại câu).
            - **[Thesaurus](https://www.thesaurus.com/):** Từ điển từ đồng nghĩa/trái nghĩa.
            """)

        with st.expander("📖 2. Nguồn Đọc Học Thuật (Reading for Writing)"):
            st.markdown("""
            - **[BBC News](https://www.bbc.com/news) / [The Guardian](https://www.theguardian.com/):** Nguồn bài báo tin tức chuẩn mực.
            - **[National Geographic](https://www.nationalgeographic.com/):** Chứa nhiều từ vựng miêu tả tự nhiên, môi trường.
            - **[TED Talks (Transcripts)](https://www.ted.com/):** Học cách lập luận và thuyết trình đa chiều.
            - **[Aeon Essays](https://aeon.co/):** Các bài luận triết học, xã hội học chuyên sâu.
            """)

    with col_res2:
        with st.expander("📘 3. Sách & Tài Liệu Khuyên Dùng"):
            st.markdown("""
            - **Vocabulary for IELTS Advanced (Cambridge)**
            - **On Writing Well (William Zinsser)**
            - **The Elements of Style (Strunk & White)**
            - **IELTS Simon's Essay Guides**
            """)

        with st.expander("🧠 4. Kỹ Năng Tư Duy Viết (Mindset)"):
            st.markdown("""
            - **PEEL Method:** Point - Evidence - Explain - Link.
            - **Mind Mapping:** Sử dụng Tab 1 để lập ý trước khi viết.
            - **Free Writing:** Viết tự do 5 phút mỗi ngày để phá vỡ bí ý tưởng.
            """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #7F8C8D;'>🌱 AIEssayist v8.1 - A Smart Writing Ecosystem powered by Gemini & Streamlit</p>", unsafe_allow_html=True)