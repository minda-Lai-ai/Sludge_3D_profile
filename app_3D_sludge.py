import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import io      
import plotly.graph_objects as go

# 可選的字型處理（Plotly/Streamlit組合下通常直接支援中文）
st.set_page_config(page_title="油槽內油泥分布圖", layout="wide")

# Sidebar: 參數設定
st.sidebar.header("油槽參數設定")
tank_name = st.sidebar.text_input("油槽名稱", value="S602 油槽油泥分布圖")
radius = st.sidebar.number_input("油槽半徑 (公尺)", value=45.73, min_value=0.1)
grid_points = st.sidebar.slider("柱狀點解析度 (個點數)", min_value=10, max_value=100, value=50)
elev = st.sidebar.slider("仰角 (度)", min_value=0, max_value=90, value=45)
azim = st.sidebar.slider("方位角 (度)", min_value=0, max_value=360, value=270)
z_bot = st.sidebar.number_input("油槽底部高度 (公尺)", value=0.0)
z_top = st.sidebar.number_input("油槽頂部高度 (公尺)", value=3.5)
show_labels = st.sidebar.checkbox("顯示數據標籤", value=True)

st.title("油槽內油泥分布圖")

# 資料輸入: 手動 or EXCEL 上傳
st.subheader("數據輸入")
upload_opt = st.radio("選擇資料輸入方式：", ["上傳 EXCEL 檔", "手動輸入數據"])
uploaded_file = None
data = None

if upload_opt == "上傳 EXCEL 檔":
    uploaded_file = st.file_uploader("請上傳 oil_sludge_measurements.xlsx", type=["xlsx"])
    if uploaded_file:
        try:
            data = pd.read_excel(uploaded_file)
            st.success("檔案讀取成功！")
        except Exception as e:
            st.error(f"檔案讀取失敗：{str(e)}")
else:
    st.text("手動輸入 24 組 X, Y, Z 資料")
    input_data = st.data_editor(pd.DataFrame({"X": [0.0]*24, "Y": [0.0]*24, "Z": [0.0]*24}), num_rows="fixed")
    data = input_data

if data is not None:
    x = data['X'].values
    y = data['Y'].values
    z = data['Z'].values
    st.write(f"資料範圍：x=[{x.min():.2f}, {x.max():.2f}], y=[{y.min():.2f}, {y.max():.2f}], z=[{z.min():.2f}, {z.max():.2f}]")
    
    # 執行鍵
    if st.button("執行 → 3D油泥分布圖"):
        # 產生格點 & 插值
        grid_x, grid_y = np.meshgrid(
            np.linspace(-radius, radius, grid_points),
            np.linspace(-radius, radius, grid_points)
        )
        grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')
        grid_z[grid_x**2 + grid_y**2 > radius**2] = np.nan

        # 3D 圖：用 Plotly 繪製 & 互動
        trace = go.Surface(
            x=grid_x, y=grid_y, z=grid_z,
            colorscale=[[0, "darkblue"], [0.2, "deepskyblue"], [0.8, "yellow"], [1, "red"]],
            colorbar=dict(title="油泥高度(公尺)")
        )
        layout = go.Layout(
            title=dict(text=tank_name, x=0.5, xanchor='center', font=dict(size=20)),
            scene=dict(
                xaxis_title="X (公尺)",
                yaxis_title="Y (公尺)",
                zaxis_title="高度 Z (公尺)",
                xaxis=dict(range=[radius, -radius]),
                yaxis=dict(range=[radius, -radius]),
                zaxis=dict(range=[z_bot, z_top]),
            ),
            width=950, height=700
        )
        fig = go.Figure(data=[trace], layout=layout)

        # 標籤顯示
        if show_labels:
            for idx in range(len(x)):
                if x[idx]**2 + y[idx]**2 <= radius**2:
                    fig.add_trace(go.Scatter3d(
                        x=[x[idx]], y=[y[idx]], z=[z[idx]+0.2], 
                        mode='text', 
                        text=[f"A{idx+1}"],
                        textposition="top center",
                        textfont=dict(size=12, color="black", family="Arial"),
                        showlegend=False
                    ))

        # 展示互動 3D 圖
        st.plotly_chart(fig, use_container_width=True)

        # 存檔功能：圖片、PDF、EXCEL
        st.subheader("資料&圖表下載")
        st.download_button("下載 Excel(原始數據)", data.to_csv(index=False).encode("utf-8-sig"), "data.csv")
        # 圖片下載（Plotly支援）：可用fig.write_image存成PNG
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format="png", dpi=300)
        img_buf.seek(0)
        st.download_button("下載圖片 (PNG)", img_buf, "oil_sludge_Label.png", mime="image/png")

        # PDF下載（建議：轉成圖片或使用reportlab/matplotlib組合，進階可開發Statistics摘要+Data）
        # 可延伸設計...

else:
    st.info("請先上傳 EXCEL 或手動輸入數據")

# 作者資訊
st.caption("Designed by Minda")



