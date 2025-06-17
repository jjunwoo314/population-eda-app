import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# Home 페이지 (기존 유지)
# ---------------------
class Home:
    def __init__(self, login, register, find_pw):
        self.login = login
        self.register = register
        self.find_pw = find_pw

    def run(self):
        st.title("🏠 홈 페이지")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        이 앱은 두 개의 데이터를 탐색합니다:

        - **자전거 대여 데이터 (bike sharing)**: EDA 탭에서 확인 가능
        - **인구 변화 데이터 (population_trends.csv)**: EDA 탭에서 업로드 후 분석 가능

        👉 상단 메뉴에서 EDA를 선택하고, population_trends.csv를 업로드하여 분석을 시작하세요.
        """)

# ---------------------
# Login, Register, FindPassword, UserInfo, Logout (기존 유지)
# ---------------------
# ... (생략, 원본 그대로 유지)

# ---------------------
# EDA 페이지 클래스 (수정본)
# ---------------------
class EDA:
    def __init__(self):
        pass

    def run(self):
        st.title("📊 지역별 인구 분석 EDA")

        file = st.file_uploader("population_trends.csv 업로드", type="csv")
        if file:
            df = pd.read_csv(file)

            # --- 기본 전처리 ---
            # '세종' 지역의 결측치 '-'를 0으로 치환
            df.loc[df['지역'] == '세종', :] = df.loc[df['지역'] == '세종', :].replace('-', 0)
            # 전체 '-'도 숫자 0으로 교체(필요하면)
            df.replace('-', 0, inplace=True)

            # '인구', '출생아수(명)', '사망자수(명)' 숫자 변환 (int)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 지역명 영문 매핑 함수 (예시, 필요시 더 추가)
            region_en_map = {
                "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
                "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
                "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
                "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
                "제주": "Jeju"
            }
            df['Region_EN'] = df['지역'].map(region_en_map).fillna(df['지역'])

            # 탭 구성
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Basic Stats", "Yearly Trend", "Regional Analysis", "Change Analysis", "Visualization"
            ])

            # --- 탭1: 기초 통계 ---
            with tab1:
                st.header("🔍 Data Info & Summary Statistics")
                buf = io.StringIO()
                df.info(buf=buf)
                st.text(buf.getvalue())

                st.subheader("Summary Statistics")
                st.dataframe(df.describe())

                st.subheader("Missing & Duplicate")
                st.write(f"- Total missing values: {df.isnull().sum().sum()}")
                st.write(f"- Duplicate rows: {df.duplicated().sum()}")

            # --- 탭2: 연도별 전국 인구 추이 및 2035년 예측 ---
            with tab2:
                st.header("📈 Yearly Total Population Trend")

                total = df[df['지역'] == '전국'].sort_values('연도')
                fig, ax = plt.subplots()

                sns.lineplot(data=total, x='연도', y='인구', marker='o', ax=ax)
                ax.set_title("Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                # 최근 3년 출생/사망 반영 인구 예측 (간단 선형 예측)
                recent = total.tail(4).copy()
                # 연도별 인구 증감 평균 (diff)
                pop_delta = recent['인구'].diff().iloc[1:].mean()

                # 최근 3년 출생자수 및 사망자수 평균 차이
                birth_delta = recent['출생아수(명)'].diff().iloc[1:].mean()
                death_delta = recent['사망자수(명)'].diff().iloc[1:].mean()
                net_change = birth_delta - death_delta

                last_year = recent['연도'].iloc[-1]
                years_to_predict = 2035 - last_year
                predicted_pop = recent['인구'].iloc[-1] + years_to_predict * (pop_delta + net_change)

                ax.axhline(predicted_pop, ls='--', color='red', label=f'2035 Predicted: {int(predicted_pop):,}')
                ax.legend()

                st.pyplot(fig)

            # --- 탭3: 지역별 최근 5년 인구 변화량 및 변화율 (영문 지역명) ---
            with tab3:
                st.header("📍 Population Change by Region (Last 5 Years)")

                regions = df[df['지역'] != '전국'].copy()
                regions = regions.sort_values(['지역', '연도'])

                # 최근 5년 데이터만 남김
                max_year = regions['연도'].max()
                min_year_5 = max_year - 5 + 1
                recent_5yrs = regions[regions['연도'] >= min_year_5]

                # 변화량 계산
                change = recent_5yrs.groupby('지역').apply(
                    lambda x: x.loc[x['연도'] == max_year, '인구'].values[0] - x.loc[x['연도'] == min_year_5, '인구'].values[0]
                ).sort_values(ascending=False)

                # 영어 지역명으로 변경
                change.index = change.index.map(region_en_map).fillna(change.index)

                # 수평 막대 그래프 (변화량, 천 단위)
                fig1, ax1 = plt.subplots(figsize=(10, 8))
                sns.barplot(x=change.values / 1000, y=change.index, ax=ax1, palette='Blues_r')
                for i, val in enumerate(change.values):
                    ax1.text(val / 1000, i, f'{int(val):,}', va='center')
                ax1.set_title("Population Change (Last 5 Years)")
                ax1.set_xlabel("Change (thousands)")
                ax1.set_ylabel("")
                st.pyplot(fig1)

                # 변화율 계산 (%)
                rate = recent_5yrs.groupby('지역').apply(
                    lambda x: (x.loc[x['연도'] == max_year, '인구'].values[0] - x.loc[x['연도'] == min_year_5, '인구'].values[0]) /
                              x.loc[x['연도'] == min_year_5, '인구'].values[0] * 100
                ).sort_values(ascending=False)
                rate.index = rate.index.map(region_en_map).fillna(rate.index)

                # 변화율 그래프
                fig2, ax2 = plt.subplots(figsize=(10, 8))
                sns.barplot(x=rate.values, y=rate.index, ax=ax2, palette='Blues_r')
                for i, val in enumerate(rate.values):
                    ax2.text(val, i, f'{val:.1f}%', va='center')
                ax2.set_title("Population Change Rate (%) (Last 5 Years)")
                ax2.set_xlabel("Change Rate (%)")
                ax2.set_ylabel("")
                st.pyplot(fig2)

                st.markdown("""
                **Analysis:**
                - This chart shows the absolute and relative population changes over the past 5 years by region (excluding 'Nationwide').
                - Regions on top have experienced the greatest increases in population.
                - Negative values indicate population decline.
                """)

            # --- 탭4: 증감률 상위 100개 사례 (컬러바) ---
            with tab4:
                st.header("📊 Top 100 Population Changes")

                df['Change'] = df.groupby('지역')['인구'].diff()
                top100 = df[df['지역'] != '전국'].sort_values('Change', ascending=False).head(100).copy()

                # 컬러맵 적용 (파랑 증가, 빨강 감소)
                def color_map(val):
                    color = ''
                    if val > 0:
                        color = 'background-color: #a6cee3'  # 연한 파랑
                    elif val < 0:
                        color = 'background-color: #fb9a99'  # 연한 빨강
                    return color

                styled = top100.style.format({'Change': '{:,.0f}'}).applymap(color_map, subset=['Change'])
                st.dataframe(styled)

            # ---
