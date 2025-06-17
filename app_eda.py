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
    def __init__(self, *args, **kwargs):
        pass  # 기존 내용 제거하거나 비워두기

    def run(self):
        st.title("🏠 Population Analysis App (No Login Needed)")
        st.markdown("""
        This app analyzes population trends using `population_trends.csv`.

        📌 Go to the **EDA** tab to upload and analyze the data.
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
        pass  # constructor 비워두기

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
                # 지역명은 한글로 유지하거나 영어로 변경 가능
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
    "Home": Home,
    "EDA": EDA,
    # Login, Register, FindPassword 등 페이지는 여기서 빼두기
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]()
page.run()