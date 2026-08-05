import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import traceback

# Cấu hình trang (Luôn đặt ở dòng đầu tiên của Streamlit)
st.set_page_config(
    page_title="AIEssayist - AI for Life 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: bold; color: #1565c0; }
    .highlight-box { padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 6px solid; color: #1e1e1e; line-height: 1.6; }
    .correct-box { background-color: #e8f5e9; border-left-color: #2e7d32; }
    .upgrade-box { background-color: #e3f2fd; border-left-color: #1565c0; }
    .repo-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #e91e63; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
''', unsafe_allow_html=True)

# Khởi tạo mô hình an toàn chống sập
MY_API_KEY = "AQ.Ab8RN6J8RxtZraVKgu7Q_J1nXtoj3SuGqfTG_Z3XE4aE3EVOjg"
model = None
try:
    if MY_API_KEY:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    model = None

def init_gspread():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            return client
    except Exception as e:
        return None
    return None

# Khởi tạo Session State mặc định
if 'local_repo' not in st.session_state:
    st.session_state['local_repo'] = [
        {
            "contributor": "Hệ thống AI (Mẫu chuẩn)", 
            "level": "4. Level C1: Cao cấp (IELTS 7.0–8.0)", 
            "score": "7.5", 
            "topic": "Education", 
            "sub_topic": "Online Learning",
            "timestamp": "15/06/2026 08:30:00",
            "essay": "In the modern era, online learning has emerged as a formidable alternative to traditional classroom education.\n\nWhile some argue that nothing can replace face-to-face interaction, I believe that virtual platforms offer flexibility and accessibility that are essential for today's learners.",
            "feedback": "**A. Mở bài:** Sử dụng từ vựng học thuật tốt.\n\n**B. Thân bài:** Lập luận chặt chẽ.\n\n**C. Kết bài:** Thuyết phục."
        }
    ]

def load_repository():
    return st.session_state.get('local_repo', [])

def handle_save_repo(contributor, level, score, topic, sub_topic, essay, feedback):
    try:
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        new_item = {
            "contributor": contributor, "level": level, "score": str(score),
            "topic": topic, "sub_topic": sub_topic, "timestamp": current_time,
            "essay": essay, "feedback": feedback
        }
        if 'local_repo' not in st.session_state:
            st.session_state['local_repo'] = []
        st.session_state['local_repo'].insert(0, new_item)
        st.session_state['save_success'] = True
    except Exception as e:
        st.error(f"Lỗi khi lưu bài vào kho: {str(e)}")

def export_to_pdf(title, mode, outline_text, score, feedback, upgrades):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, spaceAfter=15, textColor='#1565c0')
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=6, textColor='#e91e63')
        body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8)
        
        story.append(Paragraph(f"AIEssayist Learning Report", title_style))
        story.append(Paragraph(f"<b>Target Level:</b> {mode}", body_style))
        story.append(Spacer(1, 15))
        
        if outline_text:
            story.append(Paragraph("1. WRITING PLAN & VOCABULARY", h2_style))
            story.append(Paragraph(outline_text.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 15))
        
        if score:
            story.append(Paragraph("2. SCORE & DETAILED FEEDBACK", h2_style))
            story.append(Paragraph(f"<b>Overall Score:</b> {score}", body_style))
            story.append(Paragraph(feedback.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 15))
            
        if upgrades:
            story.append(Paragraph("3. SENTENCE UPGRADES", h2_style))
            for item in upgrades:
                story.append(Paragraph(f"<b>Original:</b> {item.get('original', '')}", body_style))
                story.append(Paragraph(f"<b>Reason:</b> {item.get('reason', '')}", body_style))
                story.append(Paragraph(f"<b>Standard Fix:</b> {item.get('standard_fix', '')}", body_style))
                story.append(Paragraph(f"<b>Advanced Upgrade:</b> {item.get('advanced_upgrade', '')}", body_style))
                story.append(Paragraph("----------------------------------------------------------------", body_style))
                
        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        return b""

for key in ['outline_data', 'mindmap_data', 'res_data', 'current_essay', 'current_topic', 'save_success', 'save_duplicate']:
    if key not in st.session_state:
        st.session_state[key] = None

bt = "`" * 3

def main():
    with st.sidebar:
        st.title("🛡️ Trung tâm Điều khiển")
        client_test = init_gspread()
        if client_test:
            st.success("✅ Đã kết nối Google Database")
        else:
            st.info("💡 Đang chạy chế độ AI Độc lập mượt mà")
        st.write("---")
        st.header("📸 Quét bài viết tay")
        uploaded_file = st.file_uploader("Tải lên ảnh bài luận:", type=["png", "jpg", "jpeg"])
        ocr_button = st.button("🔍 Bắt đầu quét chữ")

    st.title("🚀 AIEssayist: Writing Ecosystem 2026")
    st.subheader("Hệ sinh thái Writing: Mindmap siêu lớn - Kho tham khảo chi tiết")
    st.write("---")

    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.header("📝 Nhập liệu")
        mode = st.selectbox("🎯 TRÌNH ĐỘ MỤC TIÊU:", [
            "1. Level A1–A2: Tiền cơ bản", "2. Level B1: Trung cấp thấp", "3. Level B2: Trung cấp trên",
            "4. Level C1: Cao cấp", "5. Level C2: Thành thạo", "6. Học sinh giỏi Tỉnh", "10. HSG Quốc gia"
        ])

        with st.expander("💡 BƯỚC 1: LÊN Ý TƯỞNG", expanded=True):
            writing_topic = st.text_area("Nhập chủ đề cụ thể (Ví dụ: Family, Online Learning):", placeholder="Ví dụ: Family...")
            generate_suon = st.button("🚀 Tạo Sườn bài & Mindmap lớn")
        
        st.write("---")
        st.subheader("🤖 BƯỚC 2: CHẤM ĐIỂM")
        
        if uploaded_file and ocr_button:
            with st.spinner("🔄 Đang bóc tách nét chữ..."):
                try:
                    if model:
                        img = Image.open(uploaded_file)
                        response = model.generate_content(["OCR extract handwritten text accurately. Return only the text.", img])
                        st.session_state['ocr_text'] = response.text
                        st.success("Quét chữ thành công!")
                    else:
                        st.warning("Mô hình AI chưa sẵn sàng.")
                except Exception as e:
                    st.error(f"Lỗi khi quét ảnh: {str(e)}")

        essay_input = st.text_area("Dán bài luận vào đây:", value=st.session_state.get('ocr_text', ''), height=250)
        analyze_button = st.button("📊 Bắt đầu Chấm điểm & Nâng cấp")

    # Xử lý sự kiện tạo sườn bài
    if model and generate_suon and writing_topic:
        st.session_state['current_topic'] = writing_topic
        is_low_level = any(x in mode for x in ["1.","2.","3.","6.","7.","8."])
        lang_instruction = "Giải thích chi tiết bằng TIẾNG VIỆT, các câu mẫu thì viết bằng TIẾNG ANH." if is_low_level else "Write EVERYTHING entirely in professional academic ENGLISH."
        
        try:
            with st.spinner("📋 AI đang soạn cấu trúc sườn bài..."):
                p_outline_pure = f'''Create a detailed essay roadmap for topic: "{writing_topic}" targeting "{mode}". Requirements: {lang_instruction}
                CRITICAL INSTRUCTION FOR VOCABULARY LIST: You MUST provide key words. For EACH word, you MUST include the English word, its Phonetic transcription (IPA) inside / /, and its Vietnamese meaning. Example: "- **Environment** /ɪnˈvaɪrənmənt/: Môi trường". Do NOT skip the phonetics.'''
                res_out = model.generate_content(p_outline_pure)
                st.session_state['outline_data'] = res_out.text
        except Exception as e:
            st.error(f"Lỗi tạo sườn bài: {str(e)}")
                
        try:
            with st.spinner("🧠 Đang thiết kế Mindmap Siêu Lớn..."):
                p_mindmap = f'''
                Generate ONLY raw valid Graphviz DOT code for a mindmap about: "{writing_topic}". 
                Strict rules: 
                1. Start with "digraph G {{" and end with "}}". Do NOT use markdown code blocks. 
                2. Keep node text short (1-3 words). 
                3. CRITICAL STYLE: Use 'rankdir=LR; size="15,15"; ranksep=4.0; nodesep=2.0;'.
                4. node [shape=box, style="filled,rounded", fillcolor="#e3f2fd", fontname="Arial-Bold", fontsize=70, penwidth=4, margin="0.8,0.4"]; edge [penwidth=4, color="#1565c0"];
                5. Root node MUST be giant: root_node_name [fontsize=90, fillcolor="#ffcdd2", margin=1.0].
                '''
                res_map = model.generate_content(p_mindmap)
                raw_dot = res_map.text.strip()
                if bt in raw_dot:
                    raw_dot = raw_dot.split(bt)[1].replace('dot', '').replace('graphviz', '').strip()
                st.session_state['mindmap_data'] = raw_dot
        except Exception as e:
            st.session_state['mindmap_data'] = None
        
        st.rerun()

    # Xử lý sự kiện phân tích / chấm điểm
    if model and analyze_button and essay_input:
        st.session_state['current_essay'] = essay_input
        try:
            with st.spinner(f"🤖 Giám khảo AI đang thẩm định bài luận..."):
                lang_rule = "Write 'feedback' and 'reason' in VIETNAMESE" if any(x in mode for x in ["1.","2.","3.","6.","7.","8."]) else "Write everything in ENGLISH"
                p_an = f'''
                Analyze essay: "{essay_input}" based on "{mode}". {lang_rule}.
                Classify this essay into one general category: [Education, Technology, Environment, Health, Society, Economy, Media, Government, History].
                Return strictly a JSON object with: 
                "score": "Overall score string", 
                "numeric_score": 7.0,
                "topic_category": "Main Category (from the list)",
                "feedback": "Detailed review with explicit architectural blocks: A. Mở bài, B. Thân bài, C. Kết bài.", 
                "upgrades": [
                    {{
                        "original": "Original sentence", 
                        "reason": "Why it needs fix", 
                        "standard_fix": "Grammar fix (Basic Level)", 
                        "advanced_upgrade": "Advanced version"
                    }}
                ]
                '''
                res_an = model.generate_content(p_an)
                res_txt = res_an.text.strip()
                if f'{bt}json' in res_txt: 
                    res_txt = res_txt.split(f'{bt}json')[1].split(bt)[0].strip()
                elif bt in res_txt: 
                    res_txt = res_txt.split(bt)[1].split(bt)[0].strip()
                st.session_state['res_data'] = json.loads(res_txt)
        except Exception as e:
            st.error(f"Lỗi phân tích cú pháp bài luận hoặc JSON: {str(e)}")
        st.rerun()

    with col_right:
        st.header("📊 Kết quả Trợ lý AI")
        
        if st.session_state['outline_data'] or st.session_state['res_data']:
            st.subheader("📥 Xuất dữ liệu học tập")
            bytes_data_pdf = export_to_pdf(
                st.session_state.get('current_topic', 'My Essay'),
                mode,
                st.session_state.get('outline_data', ''),
                st.session_state.get('res_data', {}).get('score', '') if st.session_state.get('res_data') else "",
                st.session_state.get('res_data', {}).get('feedback', '') if st.session_state.get('res_data') else "",
                st.session_state.get('res_data', {}).get('upgrades', []) if st.session_state.get('res_data') else []
            )
            if bytes_data_pdf:
                st.download_button(
                    label="📥 TẢI HOÀN CHỈNH BÁO CÁO VỀ MÁY (FILE PDF)",
                    data=bytes_data_pdf,
                    file_name="AIEssayist_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.write("---")

        if st.session_state['res_data'] is not None:
            res = st.session_state['res_data']
            num_score = res.get('numeric_score', 0)
            is_qualified = num_score >= 6.0
            
            st.markdown("### 📋 Trạng thái Đóng góp Kho tham khảo")
            if is_qualified:
                st.success(f"🎉 Bài viết đạt {num_score} điểm. Đủ điều kiện vinh danh!")
                contributor = st.text_input("Tên người đóng góp bài viết:", value="Học sinh ẩn danh")
                topic_detected = res.get('topic_category', 'Topic')
                specific_topic = st.session_state.get('current_topic', '')
                
                if st.session_state.get('save_success'):
                    st.success("✅ Đã đưa bài viết vào kho thành công!")
                    st.session_state['save_success'] = False
                
                st.button("📌 XÁC NHẬN LƯU BÀI VIẾT VÀO KHO", 
                          on_click=handle_save_repo, 
                          args=(contributor, mode, res.get('score', 'N/A'), topic_detected, specific_topic, st.session_state['current_essay'], res.get('feedback', '')))
            else:
                st.warning(f"⚠️ Yêu cầu bài viết đạt từ 6.0 trở lên để lưu vào kho cộng đồng.")
            st.write("---")

        tab1, tab2, tab3, tab4 = st.tabs(["💡 Kế hoạch viết", "💯 Chấm điểm bài", "🚀 Nâng cấp câu", "📚 KHO THAM KHẢO"])

        with tab1:
            try:
                if st.session_state['outline_data'] is not None:
                    st.markdown(st.session_state['outline_data'])
                    if st.session_state['mindmap_data']:
                        st.write("---")
                        st.subheader("🧠 Sơ đồ tư duy trực quan (Mindmap Cực Lớn)")
                        st.graphviz_chart(st.session_state['mindmap_data'], use_container_width=True)
                else:
                    st.info("Hãy tạo sườn bài để nhận cẩm nang viết.")
            except Exception as e:
                st.error("Không thể hiển thị biểu đồ Mindmap.")

        with tab2:
            try:
                if st.session_state['res_data'] is not None:
                    res = st.session_state['res_data']
                    st.metric(f"🏆 ĐIỂM TỔNG KẾT ({mode})", str(res.get("score", "N/A")))
                    st.markdown(res.get('feedback', '').replace('\n', '\n\n'))
                else:
                    st.info("Vui lòng dán bài luận ở khối bên trái và nhấn chấm điểm.")
            except Exception as e:
                st.error("Đã xảy ra lỗi hiển thị kết quả chấm điểm.")
        
        with tab3:
            try:
                if st.session_state['res_data'] is not None:
                    st.subheader(f"🚀 Lộ trình nâng cấp bài viết ({mode})")
                    for item in st.session_state['res_data'].get('upgrades', []):
                        st.write(f"**❌ Gốc:** *{item.get('original', '')}*")
                        st.info(f"💡 **Lý do:** {item.get('reason', '')}")
                        st.markdown(f'<div class="highlight-box correct-box">🟢 **Sửa đúng:**<br>{item.get("standard_fix", "")}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="highlight-box upgrade-box">🔥 **Nâng cấp:**<br><strong>{item.get("advanced_upgrade", "")}</strong></div>', unsafe_allow_html=True)
                        st.write("---")
                else:
                    st.info("Vui lòng chấm điểm để nhận các gợi ý nâng cấp câu văn.")
            except Exception as e:
                st.error("Lỗi hiển thị danh sách nâng cấp.")

        with tab4:
            try:
                st.subheader("📁 Tuyển tập bài luận xuất sắc")
                repo_data = load_repository()
                for idx, item in enumerate(repo_data):
                    st.markdown(f"""
                    <div class="repo-card">
                        <h3 style="color:#1565c0; margin:0;">📝 Bài mẫu #{idx+1}: Chủ đề {item.get('topic', 'N/A')}</h3>
                        <p style="margin:5px 0;">👤 <b>Tác giả:</b> {item.get('contributor', 'N/A')} | 🎯 <b>Level:</b> {item.get('level', 'N/A')}</p>
                        <p style="margin:0;">🏆 <b>Điểm:</b> <span style="color:#2e7d32; font-weight:bold;">{item.get('score', 'N/A')}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("👁️ Xem chi tiết nội dung"):
                        st.info(item.get('essay', ''))
                        st.write("**Nhận xét của AI:**")
                        st.write(item.get('feedback', ''))
                    st.write("---")
            except Exception as e:
                st.error("Lỗi tải kho tham khảo.")

if __name__ == "__main__":
    try:
        main()
    except Exception as global_err:
        st.error("Ứng dụng gặp sự cố nghiêm trọng khi khởi chạy.")
        st.code(str(global_err), language="text")
        with st.expander("Xem chi tiết lỗi hệ thống"):
            st.code(traceback.format_exc(), language="python")
