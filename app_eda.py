import streamlit as st
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# 세션 상태 초기화 (Firebase 관련 제거)
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        st.title("🏠 Population Analysis App (No Login Needed)")
        st.markdown("""
        This app analyzes population trends using `population_trends.csv`.

        📌 Go to the **EDA** tab to upload and analyze the data.
        """)

# ---------------------
# 로그인 페이지 클래스 (Firebase 제거, 간단한 안내만)
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인 (현재 비활성화됨)")
        st.info("로그인 기능은 현재 비활성화 되어 있습니다.\nFirebase 설정이 없으므로 사용 불가합니다.")

    def run(self):
        pass

# ---------------------
# 회원가입 페이지 클래스 (Firebase 제거, 간단 안내)
# ---------------------
class Register:
    def __init__(self, login_page_url=None):
        st.title("📝 회원가입 (현재 비활성화됨)")
        st.info("회원가입 기능은 현재 비활성화 되어 있습니다.\nFirebase 설정이 없으므로 사용 불가합니다.")

    def run(self):
        pass

# ---------------------
# 비밀번호 찾기 페이지 클래스 (Firebase 제거, 간단 안내)
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기 (현재 비활성화됨)")
        st.info("비밀번호 찾기 기능은 현재 비활성화 되어 있습니다.\nFirebase 설정이 없으므로 사용 불가합니다.")

    def run(self):
        pass

# ---------------------
# 사용자 정보 수정 페이지 클래스 (Firebase 제거, 간단 안내)
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보 (현재 비활성화됨)")
        st.info("사용자 정보 수정 기능은 현재 비활성화 되어 있습니다.\nFirebase 설정이 없으므로 사용 불가합니다.")

    def run(self):
        pass

# ---------------------
# 로그아웃 페이지 클래스 (Firebase 제거, 간단 처리)
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.experimental_rerun()

    def run(self):
        pass

# ---------------------
# EDA 페이지 클래스 (기존 그대로 유지)
# ---------------------
class EDA:
    def __init__(self):
        pass

    def run(self):
        st.title("📊 Population Trend EDA")

        file = st.file_uploader("Upload population_trends.csv", type=["csv"])
        if file:
            df = pd.read_csv(file)
            df.replace('-', 0, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구','출생아수(명)','사망자수(명)']].astype(int)

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Summary", "Trend", "Regional", "Change", "Visualization"
            ])

            with tab1:
                st.subheader("🔍 Summary Statistics")
                st.dataframe(df.describe())

                st.subheader("🧾 Data Structure")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())

                st.subheader("❗ 결측치 및 중복 확인")
                st.write("결측치 개수:")
                st.dataframe(df.isnull().sum())
                st.write("중복 행 개수:", df.duplicated().sum())

            with tab2:
                national = df[df['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(data=national, x='연도', y='인구', ax=ax)
                ax.set_title("National Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                recent = national.sort_values('연도').tail(3)
                avg_net = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                last_year = national['연도'].max()
                projected_2035 = national['인구'].iloc[-1] + avg_net * (2035 - last_year)
                ax.plot(2035, projected_2035, 'ro')
                ax.text(2035, projected_2035, f"2035: {int(projected_2035):,}", color='red')
                st.pyplot(fig)

            with tab3:
                latest_year = df['연도'].max()
                past_year = latest_year - 5

                latest = df[df['연도'] == latest_year]
                past = df[df['연도'] == past_year]
                merged = latest.merge(past, on='지역', suffixes=('_latest','_past'))
                merged = merged[merged['지역'] != '전국']
                merged['change'] = merged['인구_latest'] - merged['인구_past']
                merged['change_rate'] = merged['change'] / merged['인구_past'] * 100
                merged['region_en'] = merged['지역']

                top_change = merged.sort_values('change', ascending=False)

                fig, ax = plt.subplots(figsize=(10,8))
                sns.barplot(data=top_change, x='change', y='region_en', ax=ax)
                ax.set_title("Population Change by Region (5 years)")
                ax.set_xlabel("Change (thousands)")
                for container in ax.containers:
                    ax.bar_label(container, fmt='%.0f', label_type='edge')
                st.pyplot(fig)

                fig2, ax2 = plt.subplots(figsize=(10,8))
                sns.barplot(data=top_change, x='change_rate', y='region_en', ax=ax2)
                ax2.set_title("Population Change Rate (%)")
                ax2.set_xlabel("Change Rate (%)")
                for container in ax2.containers:
                    ax2.bar_label(container, fmt='%.2f', label_type='edge')
                st.pyplot(fig2)

                st.markdown("""
                - Above: Absolute population change over 5 years  
                - Below: Percentage change based on population 5 years ago
                """)

            with tab4:
                df_diff = df[df['지역'] != '전국'].sort_values(['지역','연도'])
                df_diff['증감'] = df_diff.groupby('지역')['인구'].diff()
                top100 = df_diff.sort_values('증감', ascending=False).head(100)

                styled = top100[['연도','지역','인구','증감']].style.background_gradient(
                    subset=['증감'], cmap='RdBu_r').format({
                        '인구': '{:,}',
                        '증감': '{:+,}'
                    })
                st.subheader("📈 Top 100 Population Changes")
                st.dataframe(styled)

            with tab5:
                pivot = df.pivot_table(index='지역', columns='연도', values='인구').drop('전국',errors='ignore').fillna(0)
                fig, ax = plt.subplots(figsize=(12,6))
                pivot.T.plot.area(ax=ax, colormap='tab20')
                ax.set_title("Regional Population Stacked Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Home = Home
Page_EDA = EDA
Page_Login = Login
Page_Register = Register
Page_FindPW = FindPassword
Page_User = UserInfo
Page_Logout = Logout

# ---------------------
# 네비게이션 실행
# ---------------------
PAGES = {
    "Home": Page_Home,
    "EDA": Page_EDA,
    "Login": Page_Login,
    "Register": Page_Register,
    "Find Password": Page_FindPW,
    "User Info": Page_User,
    "Logout": Page_Logout,
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]()
page.run()