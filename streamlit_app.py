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

uploaded_file = st.file_uploader("1\u20e3 엑셀 파일을 업로드해주세요", type=['xlsx'])

def safe_split(x):
    if pd.isna(x):
        return []
    return [i.strip() for i in str(x).split('/') if i.strip() != '']

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df['병원등급_split'] = df['병원등급'].apply(safe_split)
    dept_series = pd.Series(dtype=str)
    for col in ['진료과1', '진료과2', '진료과3', '진료과4', '진료과5', '진료과6']:
        if col in df.columns:
            dept_series = pd.concat([dept_series, df[col].dropna().astype(str)])
    unique_depts = sorted(set(dept_series))
    return df, unique_depts

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='결과')
    return output.getvalue()

if uploaded_file:
    df, unique_depts = load_data(uploaded_file)

    st.subheader("2\u20e3 A 등급 필터")
    selected_A = st.multiselect("A 등급 선택", category_A, default=['공통'])

    st.subheader("3\u20e3 B 등급 필터")
    selected_B = st.multiselect("B 등급 선택", category_B, default=category_B)

    st.subheader("4\u20e3 C 등급 필터")
    selected_C = st.multiselect("C 등급 선택", category_C, default=category_C)

    st.subheader("5\u20e3 제외등급 필터")
    exclude_list = df['제외'].dropna().unique().tolist() if '제외' in df.columns else []
    selected_exclude = st.multiselect("제외할 등급 선택", sorted(exclude_list))

    st.subheader("6\u20e3 진료과 필터")
    selected_depts = st.multiselect("진료과 선택", unique_depts, default=['공통'] if '공통' in unique_depts else None)

    st.subheader("7\u20e3 암진료/이식 여부 필터")
    exclude_cancer = st.radio("암진료여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])
    exclude_transplant = st.radio("이식여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])

    st.subheader("8\u20e3 검사실 필터")
    testroom_values = []
    for col in ['검사실1', '검사실2', '검사실3']:
        if col in df.columns:
            testroom_values += df[col].dropna().unique().tolist()
    testroom_values = sorted(set(testroom_values))
    selected_testroom_exclude = st.multiselect("제외할 검사실 선택", testroom_values)

    def filter_A(df):
        return df[df['병원등급_split'].apply(lambda grades: (
            len([g for g in grades if g in category_A]) == 0
        ) or any(g in selected_A for g in grades))]

    def filter_B(df):
        return df[df['병원등급_split'].apply(lambda grades: (
            len([g for g in grades if g in category_B]) == 0
        ) or all(g in selected_B for g in grades if g in category_B))]

    def filter_C(df):
        return df[df['병원등급_split'].apply(lambda grades: (
            len([g for g in grades if g in category_C]) == 0
        ) or all(g in selected_C for g in grades if g in category_C))]

    def filter_exclude(df):
        if not selected_exclude or '제외' not in df.columns:
            return df
        return df[~df['제외'].isin(selected_exclude)]

    def filter_dept(df):
        if not selected_depts:
            return df
        dept_cols = [col for col in df.columns if col.startswith('진료과')]
        dept_match = pd.DataFrame(False, index=df.index, columns=dept_cols)
        for col in dept_cols:
            dept_match[col] = df[col].astype(str).isin(selected_depts)
        return df[dept_match.any(axis=1)]

    def filter_cancer_transplant(df):
        if '종양여부' in df.columns and exclude_cancer == "O를 제외":
            df = df[df['종양여부'] != 'O']
        if '이식' in df.columns and exclude_transplant == "O를 제외":
            df = df[df['이식'] != 'O']
        return df

    def filter_testroom(df):
        if not selected_testroom_exclude:
            return df
        test_cols = [col for col in ['검사실1', '검사실2', '검사실3'] if col in df.columns]
        test_match = pd.DataFrame(False, index=df.index, columns=test_cols)
        for col in test_cols:
            test_match[col] = df[col].astype(str).isin(selected_testroom_exclude)
        return df[~test_match.any(axis=1)]

    # 필터링
    status_container = st.status("\U0001F504 필터링을 진행 중입니다...", expanded=True)
    progress_bar = st.progress(0)
    with status_container:
        st.write("Step 1: A 등급 필터 적용 중...")
        df = filter_A(df)
        progress_bar.progress(1/6)

        st.write("Step 2: B 등급 필터 적용 중...")
        df = filter_B(df)
        progress_bar.progress(2/6)

        st.write("Step 3: C 등급 필터 적용 중...")
        df = filter_C(df)
        progress_bar.progress(3/6)

        st.write("Step 4: 제외등급 및 검사실 필터 적용 중...")
        df = filter_exclude(df)
        df = filter_testroom(df)
        progress_bar.progress(4/6)

        st.write("Step 5: 진료과 필터 적용 중...")
        df = filter_dept(df)
        progress_bar.progress(5/6)

        st.write("Step 6: 암진료/이식 여부 필터 적용 중...")
        df = filter_cancer_transplant(df)
        progress_bar.progress(6/6)

    st.success("\u2705 필터링 완료")

    columns_to_show = ['EDI코드', '명칭', '산정명칭']
    if '특이사항' in df.columns:
        columns_to_show.append('특이사항')

    final_result = df[columns_to_show].drop_duplicates()

    st.subheader("\U0001F4CB 최종 필터링 결과")
    st.dataframe(final_result, use_container_width=True)

    st.download_button(
        label="\U0001F4C5 필터링 결과 다운로드",
        data=to_excel(final_result),
        file_name='병원필터링결과.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

