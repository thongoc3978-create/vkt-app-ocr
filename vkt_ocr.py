import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import io
import datetime

# ==========================================
# CẤU HÌNH HỆ THỐNG VKT
# ==========================================
st.set_page_config(page_title="VKT OCR Pro", layout="wide")

# Thông tin liên hệ mặc định
CONTACT_INFO = {
    "hotline": "0978048348",
    "email": "thongoc3978@gmail.com",
    "system_name": "VKT SYSTEM: CHUYỂN ĐỔI CHỮ VIẾT TAY SANG EXCEL"
}

# ==========================================
# XỬ LÝ API KEY TỰ ĐỘNG
# ==========================================
# Ưu tiên lấy Key từ hệ thống bảo mật (Secrets), nếu không có thì hỏi người dùng
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        st.warning("⚠️ Chưa cấu hình Key tự động.")
        api_key = st.text_input("Nhập Google API Key:", type="password")

# ==========================================
# HÀM XỬ LÝ AI (CORE ENGINE)
# ==========================================
def process_image(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Bạn là chuyên gia nhập liệu VKT. Nhiệm vụ: Trích xuất dữ liệu từ ảnh bảng chấm công viết tay sang JSON.
    
    QUY TẮC BẮT BUỘC:
    1. Đọc kỹ bảng, xác định các cột: STT, Mã NV, Tên NV, Các ngày (1-31), Tổng công.
    2. Chú ý các ký tự viết tay như: X, P, KP, con số (4, 8, v.v.).
    3. Output phải là một JSON Array thuần túy. KHÔNG dùng markdown ```json.
    4. Cấu trúc mỗi dòng: {"stt": "...", "ma_nv": "...", "ten_nv": "...", "ngay_1": "...", ... "ngay_31": "...", "tong": "..."}
    5. Nếu ô trống, để giá trị null.
    """
    
    try:
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_bytes},
            prompt
        ])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (UI)
# ==========================================
st.title(f"🚀 {CONTACT_INFO['system_name']}")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Tải ảnh lên")
    uploaded_file = st.file_uploader("Chọn ảnh bảng chấm công (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, caption="Ảnh gốc", use_column_width=True)

with col2:
    st.subheader("2. Kết quả & Tải về")
    if uploaded_file and st.button("⚡ BẮT ĐẦU XỬ LÝ NGAY", type="primary"):
        if not api_key:
            st.error("❌ Thiếu API Key. Vui lòng kiểm tra lại.")
        else:
            with st.spinner("⏳ VKT AI đang đọc nét chữ viết tay..."):
                # Xử lý
                bytes_data = uploaded_file.getvalue()
                raw_result = process_image(bytes_data, api_key)
                
                # Làm sạch dữ liệu
                clean_json = raw_result.replace("```json", "").replace("```", "").strip()
                
                try:
                    data = json.loads(clean_json)
                    df = pd.DataFrame(data)
                    
                    # Hiển thị bảng
                    st.success("✅ Đã tách dữ liệu thành công!")
                    st.dataframe(df, height=300)
                    
                    # Tạo file Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='ChamCong')
                    
                    # Nút tải về
                    file_name = f"VKT_BangChamCong_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
                    st.download_button(
                        label="📥 TẢI FILE EXCEL VỀ MÁY",
                        data=output.getvalue(),
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error("⚠️ AI chưa đọc được ảnh này hoặc ảnh quá mờ.")
                    with st.expander("Xem chi tiết lỗi"):
                        st.write(raw_result)

# Footer
st.markdown("---")
st.markdown(f"**Hỗ trợ kỹ thuật:** Hotline {CONTACT_INFO['hotline']} | Email: {CONTACT_INFO['email']}")
