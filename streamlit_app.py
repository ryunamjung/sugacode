import streamlit as st
import pandas as pd
from io import BytesIO

# 카테고리 정의
category_A = ['한의원', '보건의료원', '의원', '병원', '정신병원', '종합병원', 
              '치과병원', '치과의원', '한방병원', '상급종합병원', '요양병원', '공통']
category_B = ['소아전문응급의료센터', '권역외상센터', '권역응급의료센터', '전문응급의료센터', 
              '중앙응급의료센터', '지역응급의료기관', '지역응급의료센터']
category_C = ['분만취약지', '서울특별시 및 광역시 구지역 소재 요양기관', 
              '서울특별시 및 광역시 구지역 소재 요양기관이 아닌 경우', '의료취약지역']

st.title("\U0001F3E5 수가 필터링 시스템")

uploaded_file = st.file_uploader("1️⃣ 엑셀 파일을 업로드해주세요", type=['xlsx'])

def safe_split(x):
    if pd.isna(x):
        return []
    return [i.strip() for i in str(x).split('/') if i.strip() != '']

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df['병원등급_split'] = df['병원등급'].apply(safe_split)
    dept_series = pd.Series(dtype=str)
    for col in [f'진료과{i}' for i in range(1, 7)]:
        if col in df.columns:
            dept_series = pd.concat([dept_series, df[col].dropna().astype(str)])
    unique_depts = sorted(set(dept_series))
    return df, unique_depts

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:  # 엔진 변경
        df.to_excel(writer, index=False, sheet_name='결과')
    return output.getvalue()

if uploaded_file:
    df, unique_depts = load_data(uploaded_file)

    st.subheader("2️⃣ A 등급 필터 (선택한 항목만 포함)")
    selected_A = st.multiselect("A 등급 선택", category_A, default=['공통'])

    st.subheader("3️⃣ B 등급 필터 (선택한 항목만 포함, 선택 안 된 항목은 제외)")
    selected_B = st.multiselect("B 등급 선택", category_B, default=category_B)

    st.subheader("4️⃣ C 등급 필터 (선택한 항목만 포함, 선택 안 된 항목은 제외)")
    selected_C = st.multiselect("C 등급 선택", category_C, default=category_C)

    st.subheader("5️⃣ 제외등급 필터")
    exclude_list = df['제외'].dropna().unique().tolist() if '제외' in df.columns else []
    selected_exclude = st.multiselect("제외할 등급 선택", sorted(exclude_list))

    st.subheader("6️⃣ 진료과 필터")
    selected_depts = st.multiselect("진료과 선택", unique_depts, default=['공통'] if '공통' in unique_depts else None)

    st.subheader("7️⃣ 암진료/이식 여부 필터")
    exclude_cancer = st.radio("암진료여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])
    exclude_transplant = st.radio("이식여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])

    st.subheader("8️⃣ 검사실 필터 (제외할 검사실 선택)")
    testroom_values = sorted(set(val for col in ['검사실1', '검사실2', '검사실3'] if col in df.columns for val in df[col].dropna().unique()))
    selected_testroom_exclude = st.multiselect("제외할 검사실 선택", testroom_values)

    if st.button("🔍 최종조회"):
        mask = pd.Series(True, index=df.index)

        if selected_A:
            a_mask = df['병원등급_split'].apply(lambda grades: any(g in selected_A for g in grades if g in category_A) or not any(g in category_A for g in grades))
            mask &= a_mask

        if selected_B:
            b_mask = df['병원등급_split'].apply(lambda grades: all(g in selected_B for g in grades if g in category_B) or not any(g in category_B for g in grades))
            mask &= b_mask
        else:
            b_mask = df['병원등급_split'].apply(lambda grades: not any(g in category_B for g in grades))
            mask &= b_mask

        if selected_C:
            c_mask = df['병원등급_split'].apply(lambda grades: all(g in selected_C for g in grades if g in category_C) or not any(g in category_C for g in grades))
            mask &= c_mask
        else:
            c_mask = df['병원등급_split'].apply(lambda grades: not any(g in category_C for g in grades))
            mask &= c_mask

        if selected_exclude and '제외' in df.columns:
            mask &= ~df['제외'].isin(selected_exclude)

        if selected_depts:
            dept_mask = df[[f'진료과{i}' for i in range(1, 7)]].apply(lambda row: any(dept in selected_depts for dept in row.astype(str)), axis=1)
            mask &= dept_mask

        if exclude_cancer == "O를 제외" and '종양여부' in df.columns:
            mask &= df['종양여부'] != 'O'

        if exclude_transplant == "O를 제외" and '이식' in df.columns:
            mask &= df['이식'] != 'O'

        if selected_testroom_exclude:
            testroom_mask = ~df[[col for col in ['검사실1', '검사실2', '검사실3'] if col in df.columns]].isin(selected_testroom_exclude).any(axis=1)
            mask &= testroom_mask

        final_result = df[mask].drop_duplicates(subset=['EDI코드', '명칭', '산정명칭'])

        st.subheader("📋 최종 필터링 결과")

        # ✅ 결과 요약 표시 추가
        st.success(f"총 {len(final_result):,}건이 조회되었습니다.")
        st.dataframe(final_result[['EDI코드', '명칭', '산정명칭'] + (['특이사항'] if '특이사항' in final_result.columns else [])], use_container_width=True)

        st.download_button(
            label="📅 필터링 결과 다운로드",
            data=to_excel(final_result),
            file_name='병원필터링결과.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )



