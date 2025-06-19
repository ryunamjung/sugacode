import streamlit as st
import pandas as pd
from io import BytesIO

# 카테고리 정의 (업데이트된 A, B, C 기준)
category_A = ['한의원', '보건의료원', '의원', '병원', '정신병원', '종합병원', 
              '치과병원', '치과의원', '한방병원', '상급종합병원', '요양병원', '공통']
category_B = ['소아전문응급의료센터', '권역외상센터', '권역응급의료센터', '전문응급의료센터', 
              '중앙응급의료센터', '지역응급의료기관', '지역응급의료센터']
category_C = ['분만취약지', '서울특별시 및 광역시 구지역 소재 요양기관', 
              '서울특별시 및 광역시 구지역 소재 요양기관이 아닌 경우', '의료취약지역']

st.title("🏥 수가 필터링 시스템")

uploaded_file = st.file_uploader("1️⃣ 엑셀 파일을 업로드해주세요", type=['xlsx'])

def safe_split(x):
    if pd.isna(x):
        return []
    # '/'로 split 후, 각 요소 strip하고 빈 문자열 제거
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

    # 2️⃣ 병원등급 필터 - A
    st.subheader("2️⃣ A 등급 필터 (선택한 항목만 포함)")
    selected_A = st.multiselect("A 등급 선택", category_A, default=['공통'])

    # 3️⃣ 병원등급 필터 - B
    st.subheader("3️⃣ B 등급 필터 (선택한 항목만 포함, 선택 안 된 항목은 제외)")
    selected_B = st.multiselect("B 등급 선택", category_B, default=category_B)

    # 4️⃣ 병원등급 필터 - C
    st.subheader("4️⃣ C 등급 필터 (선택한 항목만 포함, 선택 안 된 항목은 제외)")
    selected_C = st.multiselect("C 등급 선택", category_C, default=category_C)

    # 5️⃣ 제외등급 필터
    st.subheader("5️⃣ 제외등급 필터")
    exclude_list = df['제외'].dropna().unique().tolist() if '제외' in df.columns else []
    selected_exclude = st.multiselect("제외할 등급 선택", sorted(exclude_list))

    # 6️⃣ 진료과 필터
    st.subheader("6️⃣ 진료과 필터")
    selected_depts = st.multiselect("진료과 선택", unique_depts, default=['공통'] if '공통' in unique_depts else None)


    # 7️⃣ 암진료/이식 여부 필터
    st.subheader("7️⃣ 암진료/이식 여부 필터")
    exclude_cancer = st.radio("암진료여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])
    exclude_transplant = st.radio("이식여부에서 'O'를 제외할까요?", ['전체', "O를 제외"])

    # 8️⃣ 검사실 필터 (새로 추가)
    st.subheader("8️⃣ 검사실 필터 (제외할 검사실 선택)")
    testroom_values = []
    for col in ['검사실1', '검사실2', '검사실3']:
        if col in df.columns:
            testroom_values += df[col].dropna().unique().tolist()
    testroom_values = sorted(set(testroom_values))
    selected_testroom_exclude = st.multiselect("제외할 검사실 선택", testroom_values)

    # 필터 함수들 정의
    def filter_A(df):
        if not selected_A:
            return pd.DataFrame(columns=df.columns)  # 선택 안 하면 빈 결과

        def check(grades):
            a_items = [item for item in grades if item in category_A]
            if len(a_items) == 0:
                return True  # 빈값 포함
            return any(item in selected_A for item in a_items)

        mask = df['병원등급_split'].apply(check)
        return df[mask]

    def filter_B(df):
        if not selected_B:
            # B등급 선택이 없으면, B등급 항목이 하나도 없는 데이터만 포함
            def no_b_items(grades):
                b_items = [item for item in grades if item in category_B]
                return len(b_items) == 0
            return df[df['병원등급_split'].apply(no_b_items)]

        def check(grades):
            b_items = [item for item in grades if item in category_B]

            # 빈값은 무조건 포함
            if len(b_items) == 0:
                return True

            # 선택되지 않은 항목 존재 시 제외
            for item in b_items:
                if item not in selected_B:
                    return False
            return True

        return df[df['병원등급_split'].apply(check)]

    def filter_C(df):
        if not selected_C:
            # C등급 선택이 없으면, C등급 항목이 하나도 없는 데이터만 포함
            def no_c_items(grades):
                c_items = [item for item in grades if item in category_C]
                return len(c_items) == 0
            return df[df['병원등급_split'].apply(no_c_items)]

        def check(grades):
            c_items = [item for item in grades if item in category_C]

            # 빈값은 무조건 포함
            if len(c_items) == 0:
                return True

            # 선택되지 않은 항목 존재 시 제외
            for item in c_items:
                if item not in selected_C:
                    return False
            return True

        return df[df['병원등급_split'].apply(check)]

    def filter_exclude(df):
        if not selected_exclude or '제외' not in df.columns:
            return df
        return df[~df['제외'].isin(selected_exclude)]

    def filter_dept(df):
        if not selected_depts:
            return df

        def check(row):
            for i in range(1,7):
                dept = str(row.get(f'진료과{i}', '')).strip()
                if dept in selected_depts:
                    return True
            return False

        mask = df.apply(check, axis=1)
        return df[mask]

    def filter_cancer_transplant(df):
        if '종양여부' in df.columns and exclude_cancer == "O를 제외":
            df = df[df['종양여부'] != 'O']
        if '이식' in df.columns and exclude_transplant == "O를 제외":
            df = df[df['이식'] != 'O']
        return df

    def filter_testroom(df):
        if not selected_testroom_exclude:
            return df
        def check(row):
            for col in ['검사실1', '검사실2', '검사실3']:
                if col in df.columns:
                    val = str(row.get(col, '')).strip()
                    if val in selected_testroom_exclude:
                        return False
            return True
        mask = df.apply(check, axis=1)
        return df[mask]

    # 순서대로 필터링
    step1 = filter_A(df)
    step2 = filter_B(step1)
    step3 = filter_C(step2)
    step4 = filter_exclude(step3)
    step5 = filter_testroom(step4)  # 검사실 필터 추가
    step6 = filter_dept(step5)
    final_result = filter_cancer_transplant(step6)

    # 중복 제거 및 필요한 컬럼만 선택 (특이사항 추가)
    columns_to_show = ['EDI코드', '명칭', '산정명칭']
    if '특이사항' in final_result.columns:
        columns_to_show.append('특이사항')

    final_result = final_result[columns_to_show].drop_duplicates()

    st.subheader("📋 최종 필터링 결과")
    st.dataframe(final_result, use_container_width=True)

    st.download_button(
        label="📅 필터링 결과 다운로드",
        data=to_excel(final_result),
        file_name='병원필터링결과.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
