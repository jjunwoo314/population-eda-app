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
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login, register, find_pw):
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
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스 (기존 요청사항 유지)
# ---------------------

class EDA:
    def __init__(self):
        st.title("📊 지역별 인구 분석 EDA")

        file = st.file_uploader("population_trends.csv 업로드", type="csv")
        if file:
            df = pd.read_csv(file)

            # 기본 전처리
            df.replace('-', 0, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].astype(int)

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
            ])

            with tab1:
                st.header("🔍 기초 통계 및 데이터 정보")
                st.subheader("📌 데이터프레임 구조")
                buffer = st.empty()
                with st.spinner("로딩 중..."):
                    import io
                    buf = io.StringIO()
                    df.info(buf=buf)
                    buffer.text(buf.getvalue())
                st.subheader("📊 요약 통계")
                st.dataframe(df.describe())
                st.subheader("결측치 및 중복 확인")
                st.write(f"- 결측치 총합: {df.isnull().sum().sum()}개")
                st.write(f"- 중복 행 수: {df.duplicated().sum()}개")

            with tab2:
                st.header("📈 연도별 전국 인구 추이")
                total = df[df['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(x='연도', y='인구', data=total, marker='o', ax=ax)

                recent = total.sort_values('연도').tail(4)
                delta = (recent['인구'].diff().iloc[-3:]).mean()
                last_year = recent['연도'].iloc[-1]
                predicted = recent['인구'].iloc[-1] + (2035 - last_year) * delta

                ax.axhline(predicted, ls='--', color='red', label=f'2035 예측: {int(predicted):,}')
                ax.legend()
                ax.set_title("Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                st.pyplot(fig)

            with tab3:
                st.header("📍 최근 5년 지역별 인구 변화량")
                regions = df[df['지역'] != '전국']
                change = regions.groupby('지역').apply(
                    lambda x: x.sort_values('연도').iloc[-1]['인구'] - x.sort_values('연도').iloc[-5]['인구']
                ).sort_values(ascending=False)

                fig1, ax1 = plt.subplots(figsize=(10, 8))
                sns.barplot(x=change.values / 1000, y=change.index, ax=ax1)
                for i, val in enumerate(change.values):
                    ax1.text(val / 1000, i, f'{int(val):,}', va='center')
                ax1.set_title("Top Region Population Change (5yrs)")
                ax1.set_xlabel("Change (k)")
                st.pyplot(fig1)

                # 변화율
                rate = regions.groupby('지역').apply(
                    lambda x: (x.sort_values('연도').iloc[-1]['인구'] - x.sort_values('연도').iloc[-5]['인구']) /
                              x.sort_values('연도').iloc[-5]['인구'] * 100
                ).sort_values(ascending=False)

                fig2, ax2 = plt.subplots(figsize=(10, 8))
                sns.barplot(x=rate.values, y=rate.index, ax=ax2)
                for i, val in enumerate(rate.values):
                    ax2.text(val, i, f'{val:.1f}%', va='center')
                ax2.set_title("Top Region Population Change Rate (%)")
                ax2.set_xlabel("Change Rate (%)")
                st.pyplot(fig2)

            with tab4:
                st.header("📊 증감률 상위 사례")
                df['증감'] = df.groupby('지역')['인구'].diff()
                top100 = df[df['지역'] != '전국'].sort_values('증감', ascending=False).head(100)
                styled = top100.style.background_gradient(subset=['증감'], cmap='RdBu').format({'증감': '{:,.0f}'})
                st.dataframe(styled)

            with tab5:
                st.header("🗺️ 지역별 연도별 인구 누적 영역그래프")
                pivot = df[df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')
                fig, ax = plt.subplots(figsize=(12, 6))
                pivot.plot.area(ax=ax)
                ax.set_title("Population by Region Over Time")
                ax.set_ylabel("Population")
                st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
PAGES = {
    "Home": lambda: Home(Page_Login, Page_Register, Page_FindPW),
    "EDA": lambda: EDA(),
}


st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]()
page.run()