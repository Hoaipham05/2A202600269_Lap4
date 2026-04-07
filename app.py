import streamlit as st
from agent import graph

# ================= UI CONFIG =================
st.set_page_config(
    page_title="TravelBuddy",
    page_icon="✈️",
    layout="centered"
)

st.title("✈️ TravelBuddy - Trợ lý Du lịch AI")

# ================= SESSION =================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ================= DISPLAY CHAT =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= INPUT =================
user_input = st.chat_input("Nhập yêu cầu du lịch...")

if user_input:
    # hiển thị user
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # gọi agent
    with st.chat_message("assistant"):
        with st.spinner("TravelBuddy đang suy nghĩ..."):
            result = graph.invoke({
                "messages": [("human", user_input)]
            })

            response = result["messages"][-1].content

            st.markdown(response)

    # lưu assistant
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })