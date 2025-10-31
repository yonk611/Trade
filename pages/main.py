import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="수산물 무역량 분석 대시보드",
    page_icon="🐟",
    layout="wide"
)

# 제목
st.title("🐟 수산물 수출입 무역량 분석 대시보드")
st.markdown("데이터 출처: 해양수산부 국가별 수산물 수출입 현황")
st.markdown("---")

# CSV 파일 로드
@st.cache_data
def load_data():
    df = pd.read_csv(
        'haeyangsusanbu_guggabyeolsusanmulsuculibhyeonhwang_20250731.CSV',
        encoding='utf-8-sig'
    )
    return df

try:
    df = load_data()
    
    # 데이터 전처리
    df['기준년월'] = pd.to_datetime(df['기준년월'].astype(str) + '-01')
    df['연도'] = df['기준년월'].dt.year
    df['월'] = df['기준년월'].dt.month
    df['당월수출입미화금액(달러)'] = pd.to_numeric(df['당월수출입미화금액(달러)'], errors='coerce')
    df['당해누계수출입미화금액(달러)'] = pd.to_numeric(df['당해누계수출입미화금액(달러)'], errors='coerce')
    
except FileNotFoundError:
    st.error("❌ CSV 파일을 찾을 수 없습니다. 파일 경로를 확인하세요.")
    st.stop()

# 필터 설정
col1, col2, col3 = st.columns(3)

with col1:
    export_import = st.selectbox(
        "수출/수입 선택",
        options=['수출', '수입', '수출+수입'],
        index=0
    )

with col2:
    all_countries = sorted(df['국가명'].dropna().unique())
    selected_country = st.selectbox(
        "국가 선택 (전체 분석 또는 특정 국가)",
        options=['전체'] + all_countries,
        index=0
    )

with col3:
    chart_type = st.selectbox(
        "차트 유형",
        options=['월별 추이', '수출입 비교', '상위 국가별 순위'],
        index=0
    )

st.markdown("---")

# 데이터 필터링
if export_import == '수출':
    filtered_df = df[df['수출입구분명'] == '수출'].copy()
elif export_import == '수입':
    filtered_df = df[df['수출입구분명'] == '수입'].copy()
else:
    filtered_df = df.copy()

if selected_country != '전체':
    filtered_df = filtered_df[filtered_df['국가명'] == selected_country]

# 연도 데이터 추출
available_years = sorted(filtered_df['연도'].dropna().unique())

# ============ KPI 메트릭 표시 ============
st.subheader("📊 주요 통계 지표")

if len(available_years) >= 2:
    current_year = available_years[-1]
    previous_year = available_years[-2]
    
    current_data = filtered_df[filtered_df['연도'] == current_year]['당해누계수출입미화금액(달러)'].sum()
    previous_data = filtered_df[filtered_df['연도'] == previous_year]['당해누계수출입미화금액(달러)'].sum()
    
    year_over_year = ((current_data - previous_data) / previous_data * 100) if previous_data != 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"{previous_year}년 총합",
            value=f"${previous_data:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label=f"{current_year}년 누적",
            value=f"${current_data:,.0f}",
            delta=f"${current_data-previous_data:,.0f}"
        )
    
    with col3:
        st.metric(
            label="전년도 대비 증가율",
            value=f"{year_over_year:.2f}%",
            delta="📈 증가" if year_over_year > 0 else "📉 감소"
        )
    
    with col4:
        monthly_avg = filtered_df[filtered_df['연도'] == current_year]['당월수출입미화금액(달러)'].mean()
        st.metric(
            label=f"{current_year}년 월평균",
            value=f"${monthly_avg:,.0f}",
            delta=None
        )

st.markdown("---")

# ============ 데이터 테이블 표시 ============
st.subheader("📋 상세 데이터")

display_cols = ['기준년월', '국가명', '수산물수출입품목명', '수출입구분명', '당월수출입미화금액(달러)', '당해누계수출입미화금액(달러)']
available_cols = [col for col in display_cols if col in filtered_df.columns]

st.dataframe(
    filtered_df[available_cols].sort_values('기준년월', ascending=False).head(20),
    use_container_width=True
)

st.markdown("---")

# ============ 그래프 생성 ============
st.subheader("📈 시각화 분석")

if chart_type == '월별 추이':
    # 월별 추이 그래프
    monthly_data = filtered_df.groupby(['연도', '월'])['당월수출입미화금액(달러)'].sum().reset_index()
    monthly_data['년월'] = monthly_data['연도'].astype(str) + '-' + monthly_data['월'].astype(str).str.zfill(2)
    
    fig = px.line(
        monthly_data,
        x='년월',
        y='당월수출입미화금액(달러)',
        color='연도',
        markers=True,
        title="월별 수산물 수출입액 추이",
        labels={'당월수출입미화금액(달러)': '금액 (달러)', '년월': '년월'}
    )
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == '수출입 비교':
    # 수출입 비교
    export_import_data = df.groupby(['연도', '수출입구분명'])['당해누계수출입미화금액(달러)'].sum().reset_index()
    
    fig = px.bar(
        export_import_data,
        x='연도',
        y='당해누계수출입미화금액(달러)',
        color='수출입구분명',
        title="연도별 수출/수입 비교",
        labels={'당해누계수출입미화금액(달러)': '금액 (달러)', '연도': '연도'},
        barmode='group'
    )
    fig.update_layout(
        template='plotly_white',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

else:  # 상위 국가별 순위
    # 상위 국가별 순위
    country_data = filtered_df.groupby('국가명')['당해누계수출입미화금액(달러)'].sum().sort_values(ascending=False).head(10)
    
    fig = px.bar(
        x=country_data.index,
        y=country_data.values,
        title="상위 10개 국가별 수산물 거래액",
        labels={'x': '국가', 'y': '금액 (달러)'},
        text=country_data.values
    )
    fig.update_traces(
        texttemplate='$%{text:,.0f}',
        textposition='auto'
    )
    fig.update_layout(
        template='plotly_white',
        height=500,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============ 전년도 대비 분석 텍스트 ============
st.subheader("💡 전년도 대비 분석 요약")

if len(available_years) >= 2:
    current_year = available_years[-1]
    previous_year = available_years[-2]
    
    current_total = filtered_df[filtered_df['연도'] == current_year]['당해누계수출입미화금액(달러)'].sum()
    previous_total = filtered_df[filtered_df['연도'] == previous_year]['당해누계수출입미화금액(달러)'].sum()
    
    increase_amount = current_total - previous_total
    increase_rate = (increase_amount / previous_total * 100) if previous_total != 0 else 0
    
    # 수출/수입 각각 계산
    export_current = df[(df['연도'] == current_year) & (df['수출입구분명'] == '수출')]['당해누계수출입미화금액(달러)'].sum()
    export_previous = df[(df['연도'] == previous_year) & (df['수출입구분명'] == '수출')]['당해누계수출입미화금액(달러)'].sum()
    
    import_current = df[(df['연도'] == current_year) & (df['수출입구분명'] == '수입')]['당해누계수출입미화금액(달러)'].sum()
    import_previous = df[(df['연도'] == previous_year) & (df['수출입구분명'] == '수입')]['당해누계수출입미화금액(달러)'].sum()
    
    summary_text = f"""
    **{current_year}년 수산물 무역 성과:**
    
    - 🎯 **{current_year}년 누적 거래액:** ${current_total:,.0f}
    - 📈 **전년도({previous_year}년) 대비 증가액:** ${increase_amount:,.0f}
    - 💹 **전년도 대비 증가율:** **{increase_rate:.2f}%**
    
    **수출 현황:**
    - {current_year}년: ${export_current:,.0f}
    - {previous_year}년: ${export_previous:,.0f}
    - 증감: {((export_current - export_previous) / export_previous * 100):.2f}% {'📈 증가' if export_current > export_previous else '📉 감소'}
    
    **수입 현황:**
    - {current_year}년: ${import_current:,.0f}
    - {previous_year}년: ${import_previous:,.0f}
    - 증감: {((import_current - import_previous) / import_previous * 100):.2f}% {'📈 증가' if import_current > import_previous else '📉 감소'}
    """
    
    if increase_rate > 0:
        st.success(summary_text)
    else:
        st.warning(summary_text)

# ============ 데이터 다운로드 ============
st.markdown("---")
st.subheader("📥 데이터 다운로드")

csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')

st.download_button(
    label="📊 분석 데이터 다운로드 (CSV)",
    data=csv_data,
    file_name="수산물무역분석.csv",
    mime="text/csv"
)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
🐟 데이터 출처: 해양수산부 공공데이터포털 | 마지막 업데이트: 2025년 7월 31일
</div>
""", unsafe_allow_html=True)
