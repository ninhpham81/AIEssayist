import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from datetime import datetime
import pandas as pd
import re

st.set_page_config(page_title="AIEssayist Pro v8.0 Ecosystem", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# Thêm CSS để điều chỉnh khoảng cách dòng (line-height) thành 1.6 (tương đương 1.15 em) cho dễ đọc hơn
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; color: #2C3E50; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { color: #27AE60; background-color: white; border-radius: 8px 8px 0 0; border-bottom: 3px solid #27AE60; }
    div[data-testid="stBlock"] { background-color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .eco-title { color: #27AE60; font-weight: 800; margin-bottom: 0px;}
    .eco-subtitle { color: #7F8C8D; font-size: 1.1em; margin-top: 5px; margin-bottom: 20px;}
    .markdown-text-container p, .markdown-text-container li { line-height: 1.6; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_connections():
    try:
        ai_client = genai.Client(api_key="AQ.Ab8RN6J8RxtZraVKgu7Q_J1nXtoj3SuGqfTG_Z3XE4aE3EVOjg")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        gs_client = gspread.authorize(creds)
        
        spreadsheet = gs_client.open_by_key("1Y0BlBZlLceKrEE1EbBHl-9RofU1X6y-nMRa7ErUIo-E")
        sheet_main = spreadsheet.sheet1
        sheet_wall = spreadsheet.worksheet("Community_Wall")
        sheet_lib = spreadsheet.worksheet("Public_Library")
        sheet_challenge = spreadsheet.worksheet("Weekly_Challenges")
        
        return ai_client, sheet_main, sheet_wall, sheet_lib, sheet_challenge
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu hoặc API: {e}")
        return None, None, None, None, None

ai_client, sheet, sheet_wall, sheet_lib, sheet_challenge = init_connections()

if "plan_text" not in st.session_state: st.session_state.plan_text = ""
if "tree_map_text" not in st.session_state: st.session_state.tree_map_text = ""
if "current_topic" not in st.session_state: st.session_state.current_topic = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "tutor_active" not in st.session_state: st.session_state.tutor_active = False
if "chat_session" not in st.session_state: st.session_state.chat_session = None

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
            "C2 (Proficient) - Bản xứ / Chuyên gia",
            "SAT Writing - Hành văn học thuật Mỹ",
            "Creative Content - Tự do / Sáng tạo"
        ]
    )
    
    global_focus = st.multiselect(
        "🔍 Mục tiêu cải thiện chính:",
        ["Từ vựng học thuật", "Ngữ pháp cốt lõi", "Sự mạch lạc (Coherence)", "Phát triển ý tưởng (Brainstorming)"],
        default=["Từ vựng học thuật", "Ngữ pháp cốt lõi"]
    )
    
    st.info(f"💡 **Smart Tip:** Hệ thống tự động ghi nhớ level **{global_level.split(' ')[0]}** để điều chỉnh độ khó.")

    st.markdown("---")
    st.markdown("### 📖 Trạm Tra Cứu Nhanh")
    st.caption("Dán từ/cụm từ/câu vào đây để AI phân tích nghĩa hoặc điểm ngữ pháp tức thì.")
    lookup_text = st.text_area("🔍 Nhập văn bản cần tra:", height=100, key="quick_lookup")
    
    if st.button("Dịch & Phân Tích", width="stretch"):
        if lookup_text and ai_client:
            with st.spinner("Đang phân tích..."):
                prompt_dict = f"""
                Bạn là một chuyên gia ngôn ngữ học. Phân tích văn bản sau: "{lookup_text}".
                - Nếu là 1 từ hoặc cụm từ ngắn: Cung cấp nghĩa Tiếng Việt, Phiên âm IPA, và 1 câu ví dụ minh họa bằng Tiếng Anh (kèm dịch nghĩa).
                - Nếu là một câu dài hoặc đoạn văn: Dịch nghĩa toàn bộ sang Tiếng Việt. Sau đó bóc tách giải thích cấu trúc ngữ pháp chính hoặc các từ vựng khó trong câu đó.
                Trình bày ngắn gọn, súc tích, dễ hiểu.
                """
                try:
                    dict_res = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt_dict)
                    st.success("Kết quả tra cứu:")
                    st.markdown(dict_res.text)
                except Exception as e:
                    st.error(f"Lỗi: {e}")

st.markdown("<h1 class='eco-title'>🌱 HỆ SINH THÁI WRITING THÔNG MINH</h1>", unsafe_allow_html=True)
st.markdown("<p class='eco-subtitle'>Khởi tạo Ý Tưởng -> Luyện Tập Cùng AI -> Chấm Điểm & Tối Ưu -> Xây Dựng Thói Quen -> Lan Tỏa Cộng Đồng</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💡 1. Trạm Khởi Tạo & Mindmap", 
    "🏋️ 2. Phòng Luyện Tập AI",
    "⚖️ 3. Xưởng Chấm Điểm & Tối Ưu", 
    "📂 4. Hồ Sơ (Logs)",
    "🌍 5. Rừng Cộng Đồng",
    "📚 6. Kho Học Liệu"
])

with tab1:
    col_t1_left, col_t1_right = st.columns([1.2, 1.8])
    
    with col_t1_left:
        st.markdown(f"### 🗺️ Nhập hạt giống ý tưởng")
        plan_topic = st.text_area("👉 Đưa cho tôi một chủ đề / Đề bài:", placeholder="Ví dụ: Lợi ích của việc đi du lịch...", height=100)
        btn_plan = st.button("🚀 Kích hoạt phân tích ý tưởng", type="primary", width="stretch")
        
        st.markdown("---")
        if st.session_state.tree_map_text:
            st.markdown("### 🧠 Sơ đồ Tư duy (Mindmap)")
            st.caption("Bức tranh toàn cảnh giúp bạn không bao giờ bí ý tưởng. (Nhấn biểu tượng phóng to ở góc để xem rõ hơn)")
            try:
                # Đảm bảo Graphviz render theo chiều dọc
                st.graphviz_chart(st.session_state.tree_map_text, width="stretch")
            except Exception as e:
                st.error("Sơ đồ đang gặp lỗi hiển thị. Bạn thử tạo lại nhé.")

    with col_t1_right:
        if btn_plan:
            if not plan_topic or not ai_client: 
                st.error("❌ Hệ sinh thái cần một hạt giống (chủ đề) để nảy mầm hoặc API chưa kết nối!")
            else:
                with st.spinner('Hệ thống đang thiết kế Bản đồ tư duy và Dàn ý bài viết...'):
                    try:
                        # 1. KHÔI PHỤC DÀN Ý + TỪ VỰNG + BÀI MẪU + THÊM NGỮ PHÁP
                        prompt_plan = f"""
                        Đóng vai trò là một chuyên gia ngôn ngữ học. Lập dàn ý và viết bài mẫu cho chủ đề: '{plan_topic}'.
                        ĐÚNG TRÌNH ĐỘ: {global_level}.
                        
                        TRÌNH BÀY ĐÚNG 4 PHẦN SAU (Bắt buộc dùng Markdown, trình bày gọn gàng, Dùng <br> để xuống dòng trong danh sách nếu cần):
                        
                        PHẦN 1: DÀN Ý CHI TIẾT (Giải thích bằng tiếng Việt)
                        - I. Mở bài
                        - II. Thân bài (chia luận điểm rõ ràng)
                        - III. Kết bài
                        
                        PHẦN 2: TỪ VỰNG THÔNG MINH (Bắt buộc tuân thủ đúng format)
                        - **[Từ vựng Tiếng Anh]** /Phiên âm IPA/ : [Nghĩa Tiếng Việt]
                          > Ví dụ: [Một câu ví dụ bằng Tiếng Anh chứa từ vựng đó]
                          
                        PHẦN 3: ĐIỂM NGỮ PHÁP QUAN TRỌNG (MỚI)
                        - Đưa ra 1-2 cấu trúc ngữ pháp "ăn điểm" phù hợp với trình độ {global_level} nên dùng trong chủ đề này.
                        - Giải thích cách dùng và cho 1 ví dụ.

                        PHẦN 4: BÀI VĂN MẪU HOÀN CHỈNH
                        - Viết một bài văn tiếng Anh hoàn chỉnh (đủ Mở, Thân, Kết).
                        - Trình độ ngôn ngữ của bài viết phải tương xứng với {global_level}.
                        """
                        res_plan = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt_plan)
                        st.session_state.plan_text = res_plan.text
                        
                        # 2. KHỐNG CHẾ MINDMAP DỌC & CỠ CHỮ 12 BẰNG TEMPLATE CỨNG
                        prompt_mind = f"""
                        Tạo một sơ đồ tư duy (mindmap) bằng ngôn ngữ DOT (Graphviz) cho chủ đề: '{plan_topic}'.
                        QUY TẮC BẮT BUỘC:
                        1. CHỈ xuất ra mã DOT hợp lệ. TUYỆT ĐỐI KHÔNG bọc trong các thẻ markdown như ```dot.
                        2. BẠN PHẢI SỬ DỤNG CHÍNH XÁC TEMPLATE DƯỚI ĐÂY (chỉ thay thế text tiếng Việt).
                        
                        digraph G {{
                           rankdir=TB; /* Ép buộc dọc */
                           nodesep=0.4;
                           ranksep=0.6;
                           node [shape=box, style="filled,rounded", fontname="Arial", fontsize=12, margin="0.1,0.1"];
                           edge [color="#27AE60", penwidth=1.5];
                           
                           "Chủ đề chính (ngắn gọn)" [fillcolor="#FFDDC1", fontsize=14, fontname="Arial Bold"];
                           "MỞ BÀI" [fillcolor="#C1E1C1", fontname="Arial Bold"];
                           "THÂN BÀI" [fillcolor="#AED9E0", fontname="Arial Bold"];
                           "KẾT BÀI" [fillcolor="#FFC8A2", fontname="Arial Bold"];
                           
                           "Chủ đề chính (ngắn gọn)" -> "MỞ BÀI";
                           "Chủ đề chính (ngắn gọn)" -> "THÂN BÀI";
                           "Chủ đề chính (ngắn gọn)" -> "KẾT BÀI";
                           
                           /* BẠN HÃY THÊM CÁC Ý TƯỞNG CON DƯỚI ĐÂY (giữ text thật ngắn, tối đa 5 chữ) */
                           "MỞ BÀI" -> "Ý mở bài 1";
                           "THÂN BÀI" -> "Luận điểm 1";
                           "THÂN BÀI" -> "Luận điểm 2";
                           "KẾT BÀI" -> "Ý kết bài 1";
                        }}
                        """
                        res_mind = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt_mind)
                        raw_dot = res_mind.text.strip()
                        if raw_dot.startswith('```'):
                            raw_dot = re.sub(r'^```[a-zA-Z]*\n', '', raw_dot)
                            raw_dot = re.sub(r'\n```$', '', raw_dot)

                        st.session_state.tree_map_text = raw_dot
                        st.session_state.current_topic = plan_topic
                    except Exception as e: 
                        st.error(f"Lỗi hệ sinh thái: {e}")
        
        if st.session_state.plan_text:
            st.success(f"Dàn ý & Bài mẫu đã được tối ưu hóa cho: **{global_level}**")
            # Bọc markdown trong một container có class riêng để nhận CSS line-height
            st.markdown(f"<div class='markdown-text-container'>{st.session_state.plan_text}</div>", unsafe_allow_html=True)
        elif not btn_plan:
             st.info("👈 Nhập chủ đề bên trái và bấm nút để khởi tạo không gian ý tưởng.")

with tab2:
    st.markdown("### 🏋️ Phòng Luyện Tập AI: Gia sư 1 kèm 1")
    st.caption(f"Gia sư đã được cấu hình cho trình độ: **{global_level}**. AI sẽ hướng dẫn từng bước, ra bài tập, chấm và yêu cầu bạn sửa đến khi chuẩn.")
    
    col_t2_1, col_t2_2 = st.columns([1, 2])
    
    with col_t2_1:
        tutor_topic = st.text_input("📝 Đề tài luyện viết hôm nay:", value=st.session_state.current_topic)
        
        if st.button("🚀 BẬT PHÒNG LUYỆN TẬP", width="stretch", type="primary"):
            if tutor_topic and ai_client:
                st.session_state.tutor_active = True
                st.session_state.chat_history = []
                
                system_prompt = f"""
                Bạn là một Gia sư luyện viết (Writing Tutor) cực kỳ kiên nhẫn và chuyên nghiệp. 
                Học viên đang ở trình độ MỤC TIÊU: {global_level}. Chủ đề hôm nay: "{tutor_topic}".
                
                QUY TRÌNH HƯỚNG DẪN 1 KÈM 1 (Rất quan trọng):
                1. Chào mừng học viên và bẻ nhỏ bài viết (VD: Bắt đầu bằng việc viết 1 câu Introduction).
                2. Gợi ý 1-2 từ vựng cấp độ {global_level.split(' ')[0]} phù hợp để viết câu đó.
                3. YÊU CẦU học sinh TỰ VIẾT CÂU ĐÓ và gửi cho bạn. KHÔNG BAO GIỜ VIẾT HỘ HOÀN TOÀN.
                4. Khi học sinh gửi câu: 
                   - Nếu sai/yếu: Chỉ ra lỗi sai, giải thích vì sao, đưa ra CÂU MẪU SỬA LẠI, và yêu cầu học sinh viết lại câu khác tương tự.
                   - Nếu đúng/hay: Khen ngợi và chuyển sang hướng dẫn bước tiếp theo (VD: Thân bài 1).
                Hãy bắt đầu ngay lập tức bằng việc hướng dẫn bước 1!
                """
                
                with st.spinner("Gia sư đang thiết lập phòng học..."):
                    try:
                        chat_session = ai_client.chats.create(model="gemini-2.5-flash", config={"system_instruction": system_prompt})
                        st.session_state.chat_session = chat_session
                        response = st.session_state.chat_session.send_message("Xin chào Gia sư, tôi đã sẵn sàng luyện viết từng câu.")
                        st.session_state.chat_history.append({"role": "ai", "content": response.text})
                    except Exception as e: st.error(f"Lỗi khởi động Gia sư: {e}")
            else: st.warning("Vui lòng nhập chủ đề.")
            
        if st.button("🛑 KẾT THÚC BUỔI HỌC", width="stretch"):
            st.session_state.tutor_active = False
            st.session_state.chat_history = []
            st.rerun()

    with col_t2_2:
        chat_box = st.container(height=450)
        with chat_box:
            if not st.session_state.tutor_active:
                st.info("👈 Bấm 'Bật phòng luyện tập' để bắt đầu tương tác với Gia sư AI.")
            else:
                for msg in st.session_state.chat_history:
                    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                        st.markdown(msg["content"])
        
        if st.session_state.tutor_active:
            user_msg = st.chat_input("✍️ Viết câu của bạn vào đây và nhấn Enter...")
            if user_msg:
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with chat_box:
                    with st.chat_message("user"): st.markdown(user_msg)
                    with st.chat_message("assistant"):
                        with st.spinner("Gia sư đang đọc và chấm..."):
                            try:
                                reply = st.session_state.chat_session.send_message(user_msg)
                                st.markdown(reply.text)
                                st.session_state.chat_history.append({"role": "ai", "content": reply.text})
                            except: st.error("Mất kết nối với Gia sư.")

with tab3:
    col_in, col_out = st.columns([1, 1])
    with col_in:
        st.markdown("### ⚖️ Xưởng Đánh Giá & Tối Ưu")
        st.info(f"Hệ thống sẽ dùng tiêu chuẩn **{global_level}** để chấm điểm bài viết này.")
        
        topic_check = st.text_input("👉 Chủ đề (Topic):", value=st.session_state.current_topic, key="check_topic")
        content_check = st.text_area("✍️ Nội dung bài viết hoàn chỉnh của bạn:", height=300, key="check_content")
        
        if st.button("✨ Phân Tích & Tối Ưu Hóa (Smart Check)", type="primary"):
            if not topic_check or not content_check or not ai_client: st.error("❌ Vui lòng nhập nội dung và kiểm tra API!")
            else:
                with st.spinner('Siêu máy tính đang quét lỗi và tìm giải pháp tối ưu...'):
                    try:
                        prompt_grade = f"""
                        Đóng vai trò là giám khảo chấm thi khắt khe cho trình độ {global_level}. 
                        Đề bài: '{topic_check}'. Bài làm: '{content_check}'.
                        Trả về cấu trúc RÕ RÀNG sau (Bằng tiếng Việt):
                        1. 🎯 TRÌNH ĐỘ TỔNG QUÁT: [Điền mức Band/Điểm tương đương]
                        2. 📊 ĐÁNH GIÁ CHI TIẾT: (Nhận xét về Ngữ pháp, Từ vựng, Mạch lạc)
                        3. 🛠️ SMART UPGRADE (Tối ưu hóa): Trích xuất 2-3 câu viết kém/sai nhất trong bài, chỉ ra lỗi, và đưa ra CÂU MẪU ĐÃ ĐƯỢC VIẾT LẠI (Viết lại theo đúng chuẩn học thuật {global_level}).
                        """
                        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt_grade)
                        full_feedback = response.text
                        
                        level = "Chưa rõ"
                        for line in full_feedback.split('\n'):
                            if "TRÌNH ĐỘ TỔNG QUÁT" in line:
                                level = line.replace("1. TRÌNH ĐỘ TỔNG QUÁT:", "").replace("🎯", "").strip()
                                break
                                
                        if sheet:
                            sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), topic_check, global_level, content_check, level, full_feedback, "Optimized"])
                        
                        with col_out:
                            st.success(f"Thẩm định thành công. Đạt ngưỡng: **{level}**")
                            st.markdown(full_feedback)
                    except Exception as e: st.error(f"Lỗi: {e}")

with tab4:
    st.header("📂 Hồ Sơ Thói Quen Viết Lách")
    st.write("Lưu trữ toàn bộ các bài viết bạn đã nhờ AI chấm điểm tại 'Xưởng Đánh Giá'.")
    if st.button("🔄 Đồng bộ dữ liệu đám mây"): st.cache_data.clear()
    try:
        if sheet:
            all_rows = sheet.get_all_values()
            if len(all_rows) > 1:
                df = pd.DataFrame(all_rows[1:], columns=["Timestamp", "Topic", "Target Level", "Content", "Achieved Level", "Feedback", "Status"]).iloc[::-1]
                st.dataframe(df[['Timestamp', 'Topic', 'Target Level', 'Achieved Level']], width="stretch")
                
                df['Select_Label'] = df['Timestamp'] + " - " + df['Topic']
                sel_label = st.selectbox("📖 Mở lại hồ sơ cũ:", df['Select_Label'].tolist())
                if sel_label:
                    row = df[df['Select_Label'] == sel_label].iloc[0]
                    st.markdown(f"### 📌 {row['Topic']} (Mục tiêu: {row['Target Level']})")
                    st.code(row['Content'], language='text')
                    st.info(row['Feedback'])
        else:
             st.warning("Google Sheets chưa được kết nối.")
    except Exception as e: st.info(f"Chưa ghi nhận dữ liệu lịch sử hoặc lỗi: {e}")

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
                    sheet_wall.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), f"POST_{datetime.now().strftime('%M%S')}", post_topic, post_essay, "Chưa có comment"])
                    st.success("✅ Đã gieo mầm thành thành công!")
                else: st.error("❌ Nhập đủ thông tin hoặc lỗi kết nối!")
                
        with col_w2:
            st.markdown("### 💬 Mạng lưới tương tác")
            try:
                if sheet_wall:
                    wall_rows = sheet_wall.get_all_values()
                    if len(wall_rows) > 1:
                        wall_df = pd.DataFrame(wall_rows[1:], columns=["Time", "ID", "Topic", "Content", "Comments"])
                        for _, row in wall_df.iloc[::-1].iterrows():
                            with st.expander(f"📌 {row['Topic']}"):
                                st.code(row['Content'], language="text")
                                st.caption(f"💬 Phản hồi: {row['Comments']}")
                                new_cmt = st.text_input("Để lại hạt giống góp ý:", key=f"in_{row['ID']}")
                                if st.button("Gửi góp ý", key=f"btn_{row['ID']}"):
                                    cell = sheet_wall.find(row['ID'])
                                    sheet_wall.update_cell(cell.row, 5, row['Comments'] + f" | [Góp ý]: {new_cmt}")
                                    st.success("✅ Đã gửi!")
                    else: st.info("Bảng tin trống.")
            except: pass

    with sub_tab2:
        st.markdown("### 📚 Thư Viện Cấu Trúc Hay (Đóng góp chung)")
        col_l1, col_l2 = st.columns([1, 1])
        with col_l1:
            new_struct = st.text_input("💡 Cấu trúc câu / Từ vựng:")
            struct_note = st.text_input("💡 Ứng dụng cho level nào / Ý nghĩa:")
            if st.button("🔒 Đóng góp vào Sinh thái"):
                if new_struct and struct_note and sheet_lib:
                    sheet_lib.append_row([datetime.now().strftime("%Y-%m-%d"), new_struct, struct_note])
                    st.success("✅ Đóng góp thành công!")
        with col_l2:
            try:
                if sheet_lib:
                    lib_rows = sheet_lib.get_all_values()
                    if len(lib_rows) > 1:
                        lib_df = pd.DataFrame(lib_rows[1:], columns=["Date", "Structure", "Note"])
                        st.dataframe(lib_df[["Structure", "Note"]], width="stretch")
            except: pass

    with sub_tab3:
        st.info("🔥 **THỬ THÁCH TUẦN NÀY:** Viết 150 từ: 'The impact of AI on smart ecosystems'.")
        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            user_name = st.text_input("Bí danh bảng xếp hạng:")
            challenge_essay = st.text_area("✍️ Bài dự thi:", height=150)
            if st.button("🏅 Nộp bài & Chấm AI"):
                if user_name and challenge_essay and ai_client and sheet_challenge:
                    with st.spinner("AI chấm điểm xếp hạng..."):
                        res_c = ai_client.models.generate_content(model='gemini-2.5-flash', contents=f"Chấm khắt khe văn bản sau lấy điểm từ 1-100. Format: ĐIỂM SỐ TỔNG: [Số]. Nhận xét 1 câu. Bài: {challenge_essay}")
                        score = "70"
                        for line in res_c.text.split('\n'):
                            if "ĐIỂM SỐ TỔNG" in line:
                                score = "".join(filter(str.isdigit, line))
                                break
                        sheet_challenge.append_row([datetime.now().strftime("%Y-%m-%d"), user_name, score, challenge_essay])
                        st.success(f"🎉 Hoàn thành! Điểm: {score}/100")
        with col_g2:
            try:
                if sheet_challenge:
                    c_rows = sheet_challenge.get_all_values()
                    if len(c_rows) > 1:
                        c_df = pd.DataFrame(c_rows[1:], columns=["Date", "Name", "Score", "Essay"])
                        c_df["Score"] = pd.to_numeric(c_df["Score"])
                        st.dataframe(c_df.sort_values(by="Score", ascending=False).reset_index(drop=True)[["Name", "Score"]], width="stretch")
            except: pass

with tab6:
    st.header("📚 Kho Học Liệu & Công Cụ Hỗ Trợ Viết")
    st.markdown("Hệ thống tổng hợp các nguồn tài nguyên uy tín giúp bạn liên tục nạp 'đầu vào' (input) chất lượng để nâng cao kỹ năng viết mỗi ngày.")

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        with st.expander("🔗 1. Công Cụ Hỗ Trợ Chuyên Sâu (Tools)", expanded=True):
            st.markdown("""
            - **[Ozdic (Collocation Dictionary)](https://ozdic.com/):** Từ điển tra cứu các cụm từ đi chung với nhau tự nhiên nhất (Cực kỳ quan trọng để nâng band IELTS/SAT).
            - **[Grammarly](https://www.grammarly.com/):** Tiện ích mở rộng kiểm tra lỗi chính tả và ngữ pháp cơ bản khi gõ phím.
            - **[QuillBot](https://quillbot.com/):** Công cụ paraphrase (viết lại câu) hữu ích để đa dạng hóa vốn từ.
            - **[Thesaurus](https://www.thesaurus.com/):** Từ điển từ đồng nghĩa/trái nghĩa giúp tránh lặp từ.
            """)

        with st.expander("📖 2. Nguồn Đọc Học Thuật (Reading for Writing)"):
            st.markdown("""
            *Để viết tốt, bạn cần đọc nhiều văn bản chuẩn mực để thấm văn phong.*
            - **[BBC News](https://www.bbc.com/news) / [The Guardian](https://www.theguardian.com/):** Nguồn bài báo tin tức chuẩn mực ngữ pháp Anh.
            - **[National Geographic](https://www.nationalgeographic.com/):** Chứa nhiều từ vựng miêu tả tự nhiên, môi trường, xã hội cực tốt.
            - **[TED Talks (Transcripts)](https://www.ted.com/):** Đọc bản ghi lời thoại để học cách lập luận, thuyết trình và phát triển ý tưởng đa chiều.
            - **[Aeon Essays](https://aeon.co/):** Các bài luận triết học, xã hội học chuyên sâu (Dành cho trình độ C1/C2).
            """)
            
    with col_res2:
        with st.expander("📘 3. Sách & Tài Liệu Khuyên Dùng"):
            st.markdown("""
            - **Vocabulary for IELTS Advanced (Cambridge):** Sách nạp từ vựng kinh điển theo từng chủ đề.
            - **On Writing Well (William Zinsser):** Cuốn sách nổi tiếng dành cho những ai muốn hành văn rõ ràng, mạch lạc, bớt sáo rỗng.
            - **The Elements of Style (Strunk & White):** Cuốn sách gối đầu giường về ngữ pháp và văn phong tiếng Anh chuẩn mực.
            - **IELTS Simon's Essay Guides:** Bộ tổng hợp các bài mẫu của cựu giám khảo Simon - Đơn giản nhưng đạt band cao.
            """)
            
        with st.expander("🧠 4. Kỹ Năng Tư Duy Viết (Mindset)"):
            st.markdown("""
            - **PEEL Method:** Cấu trúc tiêu chuẩn cho 1 đoạn văn: **P**oint (Ý chính) - **E**vidence (Bằng chứng) - **E**xplain (Giải thích) - **L**ink (Liên kết).
            - **Mind Mapping:** Luôn vẽ sơ đồ tư duy trước khi viết để không lạc đề (Hãy dùng Tab 1 của Hệ sinh thái này).
            - **Free Writing (Viết tự do):** Dành 5 phút mỗi ngày đặt bút viết liên tục bất cứ thứ gì trong đầu mà không sửa lỗi. Phương pháp này giúp phá vỡ "Writer's Block" (Hội chứng bí ý tưởng).
            """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #7F8C8D;'>🌱 AIEssayist v8.1 - A Smart Writing Ecosystem powered by Gemini & Streamlit</p>", unsafe_allow_html=True)