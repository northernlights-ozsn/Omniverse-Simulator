import streamlit as st
import json
import os

def check_password():
    try:
        stored_password = st.secrets["password"]
    except (FileNotFoundError, KeyError):
        return True # ローカル環境ではパススルー

    def password_entered():
        if st.session_state["password_input"] == stored_password:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("Project: CORE Observation Station")
        st.text_input("Enter Passcode", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.title("Project: CORE Observation Station")
        st.text_input("Enter Passcode", type="password", on_change=password_entered, key="password_input")
        st.error("Invalid Passcode.")
        return False
    return True

def save_settings(params, filename="last_session.json"):
    with open(filename, "w") as f:
        json.dump(params, f)

def load_settings(filename="last_session.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None