import google.generativeai as genai
import streamlit as st
from datetime import datetime, timedelta
import time
import pyttsx3
import speech_recognition as sr

# ---------- Configuration ----------
genai.configure(api_key="AIzaSyBs0tJumqCnwjowFa2oWN7b3Y6SVOzSGGY")

# ---------- ChatBot Class ----------
class ChatBot:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-pro-latest")
        self.chat = None
        self.last_request_time = datetime.now()
        self.request_delay = timedelta(seconds=3)
        self.setup_bot()
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()

        # Set Hindi voice if available
        for voice in self.engine.getProperty('voices'):
            if 'hindi' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def setup_bot(self):
        if "chat" not in st.session_state:
            st.session_state.chat = self.model.start_chat(history=[])
        self.chat = st.session_state.chat

    def enforce_rate_limit(self):
        elapsed = datetime.now() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep((self.request_delay - elapsed).total_seconds())
        self.last_request_time = datetime.now()

    def get_response(self, user_input):
        try:
            self.enforce_rate_limit()
            response = self.chat.send_message(
                user_input,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500
                )
            )
            return response.text
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                return "⚠️ I'm at my usage limit. Please try again later."
            return f"⚠️ Error: {str(e)[:100]}..."

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            st.info("🎤 Listening... Please speak clearly.")
            audio = self.recognizer.listen(source)
            try:
                return self.recognizer.recognize_google(audio)
            except Exception as e:
                st.error(f"❌ Could not understand audio: {e}")
                return None

# ---------- Main App ----------
def main():
    st.set_page_config(page_title="🎙️ Voice-Enabled AI ChatBot", page_icon="🤖", layout="centered")
    st.markdown("<h1 style='text-align: center;'>🤖 Multilingual Voice ChatBot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Type or Speak in English/Hindi and chat with AI!</p>", unsafe_allow_html=True)
    st.divider()

    bot = ChatBot()

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 Hello! How can I assist you today?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"{message['content']}")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🎙️ Speak", use_container_width=True):
            user_input = bot.listen()
            if user_input:
                process_input(user_input, bot)

    with col2:
        prompt = st.chat_input("Type your message here...")
        if prompt:
            process_input(prompt, bot)

# ---------- Input Processor ----------
def process_input(prompt, bot):
    st.session_state.messages.append({"role": "user", "content": f"🗣️ {prompt}"})

    with st.chat_message("user"):
        st.markdown(f"🗣️ {prompt}")

    if prompt.lower() in ['quit', 'exit', 'bye', 'बंद करो', 'अलविदा']:
        farewell = "👋 Goodbye! Have a great day! / अलविदा! आपका दिन शुभ हो!"
        st.session_state.messages.append({"role": "assistant", "content": farewell})
        bot.speak(farewell)
        st.rerun()
    else:
        with st.spinner("🤔 Thinking..."):
            response = bot.get_response(prompt)

        st.session_state.messages.append({"role": "assistant", "content": response})

        with st.chat_message("assistant"):
            st.markdown(response)

        bot.speak(response)
        st.rerun()

# ---------- Run App ----------
if __name__ == "__main__":
    main()
