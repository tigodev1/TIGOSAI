import customtkinter as ctk
import requests
import json
import os
import pyttsx3
from PIL import Image, ImageTk
import io
import threading
import time
import sys
from tkinter import filedialog, messagebox
import base64
import uuid
import re

# --- File Paths and Configuration ---
POLLINATION_API_KEY = "59vIpw8_btRcbiEW"
HEADERS = {"TigosProjects1": POLLINATION_API_KEY}

SETTINGS_FILE = "user_settings.json"
CHAT_HISTORY_FILE = "chat_history.json"
IMAGE_HISTORY_FILE = "image_history.json"
TTS_HISTORY_FILE = "tts_history.json"
DEFAULT_PROFILE_PIC = "Assets/default_profile.png"
DEFAULT_AI_PIC = "Assets/ai_profile.png"
DEFAULT_CHAT_ICON = "Assets/chat_icon.png"

# --- Utility Functions ---
def load_data(filename, default_value):
    """Loads data from a JSON file with a default fallback."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default_value

def save_data(data, filename):
    """Saves data to a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Main Application Class ---
class TigosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- General App Setup ---
        self.title("TigosProjects1")
        self.geometry("1280x720")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        try:
            self.iconbitmap(resource_path("Assets/icon.ico"))
        except Exception:
            print("Warning: Could not set application icon.")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Load Data ---
        self.settings = load_data(SETTINGS_FILE, {"username": "User", "profile_pic": None, "theme": "Dark"})
        self.chat_history = load_data(CHAT_HISTORY_FILE, {"chats": {}, "current_chat_id": None})
        self.image_history = load_data(IMAGE_HISTORY_FILE, [])
        self.tts_history = load_data(TTS_HISTORY_FILE, [])

        # Ensure at least one chat exists
        if not self.chat_history["chats"]:
            chat_id = str(uuid.uuid4())
            self.chat_history["chats"][chat_id] = []
            self.chat_history["current_chat_id"] = chat_id
            save_data(self.chat_history, CHAT_HISTORY_FILE)

        self.current_chat_id = self.chat_history["current_chat_id"]

        # --- Sidebar ---
        self.setup_sidebar()

        # --- Main Content Frame ---
        self.main_content = ctk.CTkFrame(self, fg_color="#36393F")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # --- Modal Frame for Enlarged Images and Settings ---
        self.modal_frame = None

        # --- Setup Chat View ---
        self.setup_chat_view()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=80, fg_color="#202225", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(2, weight=1)

        # Chat List
        self.chat_list_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.chat_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.chat_list_frame.grid_columnconfigure(0, weight=1)

        self.chat_buttons = {}
        self.update_chat_list()

        # New Chat Button
        try:
            img = Image.open(resource_path("Assets/new_chat_icon.png")).resize((24, 24), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
        except Exception:
            ctk_img = None
        new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="",
            image=ctk_img,
            command=self.create_new_chat,
            fg_color="#202225",
            hover_color="#5865F2",
            corner_radius=15,
            width=60,
            height=60
        )
        new_chat_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Profile Section
        profile_frame = ctk.CTkFrame(self.sidebar, fg_color="#202225")
        profile_frame.grid(row=3, column=0, padx=10, pady=10, sticky="s")
        profile_frame.grid_columnconfigure(0, weight=1)

        try:
            img_path = self.settings.get("profile_pic", DEFAULT_PROFILE_PIC)
            img = Image.open(resource_path(img_path)).resize((32, 32), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
        except Exception:
            ctk_img = None
        self.profile_btn = ctk.CTkButton(
            profile_frame,
            text=self.settings["username"],
            image=ctk_img,
            command=self.show_settings,
            fg_color="#202225",
            hover_color="#5865F2",
            corner_radius=10,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        )
        self.profile_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    def update_chat_list(self):
        for widget in self.chat_list_frame.winfo_children():
            widget.destroy()
        self.chat_buttons.clear()

        for idx, chat_id in enumerate(self.chat_history["chats"]):
            name = f"Chat {idx + 1}"
            try:
                img = Image.open(resource_path(DEFAULT_CHAT_ICON)).resize((24, 24), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
            except Exception:
                ctk_img = None
            btn = ctk.CTkButton(
                self.chat_list_frame,
                text="",
                image=ctk_img,
                command=lambda cid=chat_id: self.switch_chat(cid),
                fg_color="#202225" if chat_id != self.current_chat_id else "#5865F2",
                hover_color="#5865F2",
                corner_radius=15,
                width=60,
                height=60
            )
            btn.grid(row=idx, column=0, padx=5, pady=2, sticky="ew")
            self.chat_buttons[chat_id] = btn

    def create_new_chat(self):
        chat_id = str(uuid.uuid4())
        self.chat_history["chats"][chat_id] = []
        self.chat_history["current_chat_id"] = chat_id
        self.current_chat_id = chat_id
        save_data(self.chat_history, CHAT_HISTORY_FILE)
        self.update_chat_list()
        self.update_chat_display()

    def switch_chat(self, chat_id):
        self.current_chat_id = chat_id
        self.chat_history["current_chat_id"] = chat_id
        save_data(self.chat_history, CHAT_HISTORY_FILE)
        self.update_chat_list()
        self.update_chat_display()

    def setup_chat_view(self):
        # Config Frame
        self.config_frame = ctk.CTkFrame(self.main_content, fg_color="#36393F", corner_radius=15)
        self.config_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.config_frame.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(self.config_frame, text="Chat Model:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=0, column=0, padx=5, pady=5)
        self.chat_models = ["openai", "mistral", "gemini"]
        self.chat_model_menu = ctk.CTkOptionMenu(self.config_frame, values=self.chat_models, fg_color="#4F545C", button_color="#5865F2", button_hover_color="#7289DA", font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12))
        self.chat_model_menu.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(self.config_frame, text="Image Model:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=0, column=2, padx=5, pady=5)
        self.image_models = ["flux", "variation", "dreamshaper", "anything", "pixart"]
        self.image_model_menu = ctk.CTkOptionMenu(self.config_frame, values=self.image_models, fg_color="#4F545C", button_color="#5865F2", button_hover_color="#7289DA", font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12))
        self.image_model_menu.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(self.config_frame, text="Resolution:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=0, column=4, padx=5, pady=5)
        self.resolution_options = ["512x512", "768x768", "1024x1024"]
        self.resolution_menu = ctk.CTkOptionMenu(self.config_frame, values=self.resolution_options, fg_color="#4F545C", button_color="#5865F2", button_hover_color="#7289DA", font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12))
        self.resolution_menu.grid(row=0, column=5, padx=5, pady=5)

        self.nologo_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(self.config_frame, text="No Logo", variable=self.nologo_var, onvalue="on", offvalue="off", fg_color="#5865F2", hover_color="#7289DA", text_color="#B9BBBE", font=ctk.CTkFont(size=12)).grid(row=0, column=6, padx=5, pady=5)

        # Chat Display
        self.chat_display_scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="#2F3136", corner_radius=15)
        self.chat_display_scroll.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.chat_display_scroll.grid_columnconfigure(0, weight=1)

        # Input Frame
        input_frame = ctk.CTkFrame(self.main_content, fg_color="#36393F", corner_radius=15)
        input_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text=f"Message @{self.settings['username']} (e.g., 'Generate me an image...' or /tts <text>)", height=40, fg_color="#40444B", text_color="#ffffff", border_color="#4F545C", corner_radius=10, font=ctk.CTkFont(size=14))
        self.chat_input.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.chat_input.bind("<Return>", self.send_chat_message)

        send_btn = ctk.CTkButton(input_frame, text="", image=self.load_send_icon(), command=self.send_chat_message, width=40, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10)
        send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.update_chat_display()

    def load_send_icon(self):
        try:
            img = Image.open(resource_path("Assets/send_icon.png")).resize((24, 24), Image.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
        except Exception:
            return None

    def update_chat_display(self):
        for widget in self.chat_display_scroll.winfo_children():
            widget.destroy()

        messages = self.chat_history["chats"].get(self.current_chat_id, [])
        for message in messages:
            is_user = message['type'] == 'user'
            text = message['text']
            sender = self.settings["username"] if is_user else "AI"
            image_data = message.get('image_data', None)

            # Message Frame
            msg_frame = ctk.CTkFrame(self.chat_display_scroll, fg_color="transparent")
            msg_frame.grid(row=len(self.chat_display_scroll.winfo_children()), column=0, padx=10, pady=8, sticky="ew")
            msg_frame.grid_columnconfigure(1, weight=1)

            # Profile Picture
            try:
                img_path = self.settings.get("profile_pic", DEFAULT_PROFILE_PIC) if is_user else DEFAULT_AI_PIC
                img = Image.open(resource_path(img_path)).resize((40, 40), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
            except Exception:
                ctk_img = None
            profile_label = ctk.CTkLabel(msg_frame, text="", image=ctk_img)
            profile_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nw")

            # Content Frame
            content_frame = ctk.CTkFrame(msg_frame, fg_color="#4F545C" if is_user else "#40444B", corner_radius=15)
            content_frame.grid(row=0, column=1, padx=0, pady=5, sticky="w")
            content_frame.grid_columnconfigure(0, weight=1)

            # Sender and Timestamp
            sender_label = ctk.CTkLabel(content_frame, text=f"{sender}  •  {time.strftime('%H:%M')}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE")
            sender_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

            # Message Text
            text_label = ctk.CTkLabel(content_frame, text=text, wraplength=600, justify="left", text_color="#DCDEDD", font=ctk.CTkFont(size=14))
            text_label.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

            # Image Thumbnail
            if image_data:
                try:
                    img = Image.open(io.BytesIO(base64.b64decode(image_data))).resize((100, 100), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                    img_label = ctk.CTkLabel(content_frame, text="", image=ctk_img)
                    img_label.grid(row=2, column=0, padx=15, pady=(5, 10), sticky="w")
                    img_label.bind("<Button-1>", lambda e, data=image_data: self.show_enlarged_image(data))
                except Exception:
                    pass

        self.chat_display_scroll.update_idletasks()
        self.chat_display_scroll.after(100, lambda: self.chat_display_scroll.yview_moveto(1.0))

    def show_enlarged_image(self, image_data):
        if self.modal_frame:
            self.modal_frame.destroy()

        self.modal_frame = ctk.CTkFrame(self, fg_color="#2F3136", corner_radius=15)
        self.modal_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.6)
        self.modal_frame.grid_rowconfigure(0, weight=1)
        self.modal_frame.grid_columnconfigure(0, weight=1)

        try:
            img = Image.open(io.BytesIO(base64.b64decode(image_data)))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(min(img.width, 600), min(img.height, 400)))
            img_label = ctk.CTkLabel(self.modal_frame, text="", image=ctk_img)
            img_label.grid(row=0, column=0, padx=10, pady=10)
        except Exception:
            ctk.CTkLabel(self.modal_frame, text="Error loading image", text_color="#DCDEDD").grid(row=0, column=0, padx=10, pady=10)

        button_frame = ctk.CTkFrame(self.modal_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_frame, text="Download", command=lambda: self.download_image(image_data), fg_color="#5865F2", hover_color="#7289DA", corner_radius=10).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Close", command=self.close_modal, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def close_modal(self):
        if self.modal_frame:
            self.modal_frame.destroy()
            self.modal_frame = None

    def send_chat_message(self, event=None):
        user_message = self.chat_input.get().strip()
        if not user_message:
            return

        self.chat_input.delete(0, "end")

        # Detect image generation command
        image_pattern = re.compile(r"^(generate|create)\s+(me\s+)?an?\s+image\s+(.+)", re.IGNORECASE)
        image_match = image_pattern.match(user_message)
        if image_match:
            prompt = image_match.group(3)
            self.chat_history["chats"][self.current_chat_id].append({"type": "user", "text": f"Generating image: {prompt}"})
            self.update_chat_display()
            threading.Thread(target=self.get_image, args=(prompt,)).start()
            return
        elif user_message.startswith("/tts"):
            text_to_speak = user_message[4:].strip()
            if text_to_speak:
                self.chat_history["chats"][self.current_chat_id].append({"type": "user", "text": f"Generating TTS: {text_to_speak}"})
                self.update_chat_display()
                threading.Thread(target=self.preview_audio, args=(text_to_speak,)).start()
                self.tts_history.append(text_to_speak)
                save_data(self.tts_history, TTS_HISTORY_FILE)
            return

        self.chat_history["chats"][self.current_chat_id].append({"type": "user", "text": user_message})
        self.update_chat_display()
        threading.Thread(target=self.get_ai_response, args=(user_message,)).start()

    def get_ai_response(self, user_message):
        try:
            selected_model = self.chat_model_menu.get()
            url = f"https://text.pollinations.ai/{user_message}?model={selected_model}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            ai_message = response.text
            self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": ai_message})
            save_data(self.chat_history, CHAT_HISTORY_FILE)
            self.after(0, self.update_chat_display)
        except Exception as e:
            self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Error: Could not get a response. {e}"})
            self.after(0, self.update_chat_display)

    def get_image(self, prompt):
        try:
            selected_model = self.image_model_menu.get()
            resolution = self.resolution_menu.get()
            width, height = resolution.split('x')
            nologo = "true" if self.nologo_var.get() == "on" else "false"

            url = f"https://image.pollinations.ai/prompt/{prompt}?model={selected_model}&width={width}&height={height}&nologo={nologo}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()

            image_data = response.content
            self.chat_history["chats"][self.current_chat_id].append({
                "type": "user",
                "text": f"Generated image: {prompt}",
                "image_data": base64.b64encode(image_data).decode('utf-8')
            })
            save_data(self.chat_history, CHAT_HISTORY_FILE)
            self.image_history.append({"prompt": prompt, "model": selected_model, "resolution": resolution, "nologo": nologo})
            save_data(self.image_history, IMAGE_HISTORY_FILE)
            self.after(0, self.update_chat_display)
        except Exception as e:
            self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Error generating image: {e}"})
            self.after(0, self.update_chat_display)

    def download_image(self, image_data):
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if filename:
            try:
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(image_data))
                self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Image downloaded to {filename}"})
                save_data(self.chat_history, CHAT_HISTORY_FILE)
                self.after(0, self.update_chat_display)
            except Exception as e:
                self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Error downloading image: {e}"})
                self.after(0, self.update_chat_display)

    def preview_audio(self, text_to_speak):
        engine = pyttsx3.init()
        engine.say(text_to_speak)
        engine.runAndWait()

    def show_settings(self):
        if self.modal_frame:
            self.modal_frame.destroy()

        self.modal_frame = ctk.CTkFrame(self, fg_color="#2F3136", corner_radius=15)
        self.modal_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.8)
        self.modal_frame.grid_rowconfigure(0, weight=1)
        self.modal_frame.grid_columnconfigure(0, weight=1)

        scrollable_settings = ctk.CTkScrollableFrame(self.modal_frame, fg_color="transparent")
        scrollable_settings.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_settings.grid_columnconfigure(0, weight=1)

        # Profile Section
        profile_frame = ctk.CTkFrame(scrollable_settings, fg_color="#40444B", corner_radius=15)
        profile_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        profile_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(profile_frame, text="Profile Settings", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")

        self.profile_image_label = ctk.CTkLabel(profile_frame, text="", width=100, height=100)
        self.profile_image_label.grid(row=1, column=0, padx=10, pady=10)
        self.load_profile_image()

        profile_controls = ctk.CTkFrame(profile_frame, fg_color="transparent")
        profile_controls.grid(row=1, column=1, sticky="w", padx=(0, 10))

        ctk.CTkLabel(profile_controls, text="Username:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = ctk.CTkEntry(profile_controls, placeholder_text="Enter your name", width=200, fg_color="#4F545C", text_color="#ffffff", border_color="#5865F2", corner_radius=10, font=ctk.CTkFont(size=14))
        self.username_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.username_entry.insert(0, self.settings["username"])

        ctk.CTkButton(profile_controls, text="Change Profile Picture", command=self.change_profile_pic, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(profile_frame, text="Save Profile", command=self.save_settings, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Preferences Section
        preferences_frame = ctk.CTkFrame(scrollable_settings, fg_color="#40444B", corner_radius=15)
        preferences_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        preferences_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(preferences_frame, text="App Preferences", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")

        ctk.CTkLabel(preferences_frame, text="Theme:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.theme_menu = ctk.CTkOptionMenu(preferences_frame, values=["Dark", "Light", "System"], fg_color="#4F545C", button_color="#5865F2", button_hover_color="#7289DA", font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12), command=self.change_theme)
        self.theme_menu.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        self.theme_menu.set(self.settings.get("theme", "Dark"))

        # TTS Voices
        tts_frame = ctk.CTkFrame(scrollable_settings, fg_color="#40444B", corner_radius=15)
        tts_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        tts_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tts_frame, text="TTS Voice:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B9BBBE").grid(row=0, column=0, padx=20, pady=5, sticky="w")
        self.tts_voices = ["nova", "echo", "fable", "onyx", "shimmer"]
        self.tts_voice_menu = ctk.CTkOptionMenu(tts_frame, values=self.tts_voices, fg_color="#4F545C", button_color="#5865F2", button_hover_color="#7289DA", font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12))
        tts_frame.grid(row=0, column=1, padx=20, pady=5, sticky="ew")

        # History Buttons
        history_frame = ctk.CTkFrame(scrollable_settings, fg_color="#40444B", corner_radius=15)
        history_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        history_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(history_frame, text="View Image History", command=self.view_image_history, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(history_frame, text="View TTS History", command=self.view_tts_history, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        close_btn = ctk.CTkButton(self.modal_frame, text="Close", command=self.close_modal, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=10, pady=10)

    def view_image_history(self):
        if self.modal_frame:
            self.modal_frame.destroy()

        self.modal_frame = ctk.CTkFrame(self, fg_color="#2F3136", corner_radius=15)
        self.modal_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.6)
        self.modal_frame.grid_rowconfigure(0, weight=1)
        self.modal_frame.grid_columnconfigure(0, weight=1)

        scrollable_frame = ctk.CTkScrollableFrame(self.modal_frame, fg_color="transparent")
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        for idx, item in enumerate(self.image_history):
            frame = ctk.CTkFrame(scrollable_frame, fg_color="#40444B", corner_radius=15)
            frame.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
            ctk.CTkLabel(frame, text=f"Prompt: {item['prompt'][:50]}...", wraplength=500, text_color="#DCDEDD", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(frame, text=f"Model: {item['model']}, Resolution: {item['resolution']}", text_color="#B9BBBE", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        ctk.CTkButton(self.modal_frame, text="Close", command=self.close_modal, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=10, pady=10)

    def view_tts_history(self):
        if self.modal_frame:
            self.modal_frame.destroy()

        self.modal_frame = ctk.CTkFrame(self, fg_color="#2F3136", corner_radius=15)
        self.modal_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.6)
        self.modal_frame.grid_rowconfigure(0, weight=1)
        self.modal_frame.grid_columnconfigure(0, weight=1)

        scrollable_frame = ctk.CTkScrollableFrame(self.modal_frame, fg_color="transparent")
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        for idx, text in enumerate(self.tts_history):
            frame = ctk.CTkFrame(scrollable_frame, fg_color="#40444B", corner_radius=15)
            frame.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
            ctk.CTkLabel(frame, text=f"TTS: {text[:50]}...", wraplength=500, text_color="#DCDEDD", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkButton(frame, text="Download", command=lambda t=text: self.download_audio(t), fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=0, column=1, padx=10, pady=5, sticky="e")

        ctk.CTkButton(self.modal_frame, text="Close", command=self.close_modal, fg_color="#5865F2", hover_color="#7289DA", corner_radius=10, font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=10, pady=10)

    def download_audio(self, text_to_speak):
        filename = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if not filename:
            return

        selected_voice = self.tts_voice_menu.get()
        try:
            url = f"https://text.pollinations.ai/{text_to_speak}?model=openai-audio&voice={selected_voice}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()

            with open(filename, "wb") as f:
                f.write(response.content)
            self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Audio downloaded to {filename}"})
            save_data(self.chat_history, CHAT_HISTORY_FILE)
            self.after(0, self.update_chat_display)
        except Exception as e:
            self.chat_history["chats"][self.current_chat_id].append({"type": "ai", "text": f"Error downloading audio: {e}"})
            self.after(0, self.update_chat_display)

    def load_profile_image(self):
        try:
            image_path = self.settings.get("profile_pic", None)
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
            else:
                img = Image.open(resource_path(DEFAULT_PROFILE_PIC))
            img = img.resize((100, 100), Image.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            self.profile_image_label.configure(image=ctk_image)
            self.profile_image_label.image = ctk_image

            img_small = img.resize((32, 32), Image.LANCZOS)
            ctk_image_small = ctk.CTkImage(light_image=img_small, dark_image=img_small, size=(32, 32))
            self.profile_btn.configure(image=ctk_image_small)
            self.profile_btn.image = ctk_image_small
        except Exception as e:
            print(f"Error loading profile image: {e}")
            messagebox.showerror("Error", "Failed to load profile image.")

    def change_profile_pic(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.settings["profile_pic"] = file_path
            self.load_profile_image()
            self.save_settings()

    def save_settings(self):
        self.settings["username"] = self.username_entry.get()
        self.settings["theme"] = self.theme_menu.get()
        save_data(self.settings, SETTINGS_FILE)
        self.profile_btn.configure(text=self.settings["username"])
        messagebox.showinfo("Saved", "Settings have been saved successfully!")
        self.update_chat_display()

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)
        self.settings["theme"] = choice
        save_data(self.settings, SETTINGS_FILE)

if __name__ == "__main__":
    app = TigosApp()
    app.mainloop()