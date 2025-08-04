import streamlit as st
import datetime
from quickstart import create_event_with_image

st.title("カレンダー×画像生成アプリ")

title = st.text_input("予定タイトル", "ゼミ")
desc = st.text_area("説明", "研究室でゼミ")
location = st.text_input("場所", "〒761-0396 香川県高松市林町2217-20")
date = st.date_input("日付", datetime.date.today())
start_time = st.time_input("開始時刻", datetime.time(9, 0))
end_time = st.time_input("終了時刻", datetime.time(17, 0))
mail_to = st.text_input("画像付きメールの送り先アドレス", "")

if st.button("予定を作成＆画像生成"):
    with st.spinner("処理中..."):
        result = create_event_with_image(
            event_title=title,
            event_description=desc,
            event_location=location,
            event_date=date,
            start_time=start_time,
            end_time=end_time,
            attendees_list=[],
            mail_to=mail_to
        )
    if 'error' in result:
        st.error(f"エラーが発生しました: {result['error']}")
    else:
        st.success("予定と画像が作成されました！")
        st.markdown(f"[Googleカレンダーの予定を開く]({result['event_url']})")
        st.markdown(f"[Google Driveの画像リンク]({result['image_url']})")
        st.image(result['image_path'], caption="生成画像のプレビュー")
