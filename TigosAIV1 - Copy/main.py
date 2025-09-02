import customtkinter
import requests
import json
import os
import pyttsx3
from PIL import Image
import io
import threading
import time
import sys
from tkinter import filedialog, messagebox

# --- File Paths and Configuration ---
POLLINATION_API_KEY = "59vIpw8_btRcbiEW"
HEADERS = {"TigosProjects1": POLLINATION_API_KEY}

SETTINGS_FILE = "user_settings.json"
CHAT_HISTORY_FILE = "chat_history.json"
IMAGE_HISTORY_FILE = "image_history.json"
TTS_HISTORY_FILE = "tts_history.json"
DEFAULT_PROFILE_PIC = "Assets/default_profile.png"

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
class TigosApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- General App Setup ---
        self.title("TigosProjects1")
        self.geometry("1200x800")
        
        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("green")

        try:
            self.iconbitmap(resource_path("Assets/icon.ico"))
        except Exception:
            print("Warning: Could not set application icon.")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Load User Settings and History ---
        self.settings = load_data(SETTINGS_FILE, {"username": "User", "profile_pic": None})
        self.chat_history = load_data(CHAT_HISTORY_FILE, [])
        self.image_history = load_data(IMAGE_HISTORY_FILE, [])
        self.tts_history = load_data(TTS_HISTORY_FILE, [])

        # --- Tab View ---
        self.tab_view = customtkinter.CTkTabview(self, fg_color="#1e1e1e", segmented_button_selected_color="#444444", segmented_button_unselected_color="#2c2c2c")
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_view.add("Chat")
        self.tab_view.add("Image Generation")
        self.tab_view.add("Text to Speech")
        self.tab_view.add("Settings")

        # --- Setup Tabs ---
        self.setup_chat_tab()
        self.setup_image_gen_tab()
        self.setup_tts_tab()
        self.setup_settings_tab()

    # --- CHAT TAB ---
    def setup_chat_tab(self):
        self.chat_frame = self.tab_view.tab("Chat")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1)

        # Configs Frame
        config_frame = customtkinter.CTkFrame(self.chat_frame, fg_color="#2c2c2c")
        config_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)
        
        customtkinter.CTkLabel(config_frame, text="Model:", text_color="#ffffff").grid(row=0, column=0, padx=(10, 0), pady=10, sticky="w")
        self.chat_models = ["openai", "mistral", "gemini"]
        self.chat_model_menu = customtkinter.CTkOptionMenu(config_frame, values=self.chat_models, fg_color="#333333", button_color="#444444", button_hover_color="#555555")
        self.chat_model_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Chat display area - now a scrollable frame for bubbles
        self.chat_display_scroll = customtkinter.CTkScrollableFrame(self.chat_frame, fg_color="#1a1a1a", corner_radius=10)
        self.chat_display_scroll.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display_scroll.grid_columnconfigure(0, weight=1)

        # Input and controls frame
        input_frame = customtkinter.CTkFrame(self.chat_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input = customtkinter.CTkEntry(input_frame, placeholder_text="Type your message...", fg_color="#333333", text_color="#ffffff", border_color="#555555")
        self.chat_input.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.chat_input.bind("<Return>", self.send_chat_message)

        self.send_button = customtkinter.CTkButton(input_frame, text="Send", command=self.send_chat_message, corner_radius=10, fg_color="#008000", hover_color="#006600")
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=10)
        
        self.update_chat_display()

    def update_chat_display(self):
        for widget in self.chat_display_scroll.winfo_children():
            widget.destroy()

        for message in self.chat_history:
            is_user = message['type'] == 'user'
            text = message['text']
            sender = self.settings["username"] if is_user else "AI"
            
            # Use different colors for user/AI
            bg_color = "#008000" if is_user else "#444444"
            
            # Outer frame to hold the message bubble
            outer_frame = customtkinter.CTkFrame(self.chat_display_scroll, fg_color="transparent")
            outer_frame.grid(row=len(self.chat_display_scroll.winfo_children()), column=0, padx=10, pady=5, sticky="ew")
            
            # Configure columns to push the bubble left or right
            outer_frame.grid_columnconfigure(0, weight=1 if is_user else 0)
            outer_frame.grid_columnconfigure(1, weight=0 if is_user else 1)

            # Bubble frame with rounded corners
            bubble_frame = customtkinter.CTkFrame(outer_frame, corner_radius=15, fg_color=bg_color)
            bubble_frame.grid(row=0, column=1 if is_user else 0, sticky="e" if is_user else "w")
            
            # Label for sender and message
            sender_label = customtkinter.CTkLabel(bubble_frame, text=f"**{sender}**", font=customtkinter.CTkFont(weight="bold"), text_color="#ffffff")
            sender_label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")
            
            message_label = customtkinter.CTkLabel(bubble_frame, text=text, wraplength=400, justify="left", text_color="#ffffff")
            message_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")
        
        self.chat_display_scroll.update_idletasks()
        self.chat_display_scroll.after(100, lambda: self.chat_display_scroll.yview_moveto(1.0)) # Auto-scroll with a slight delay

    def send_chat_message(self, event=None):
        user_message = self.chat_input.get()
        if not user_message:
            return

        self.chat_history.append({"type": "user", "text": user_message})
        self.update_chat_display()
        self.chat_input.delete(0, "end")

        threading.Thread(target=self.get_ai_response, args=(user_message,)).start()

    def get_ai_response(self, user_message):
        try:
            selected_model = self.chat_model_menu.get()
            url = f"https://text.pollinations.ai/{user_message}?model={selected_model}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            ai_message = response.text
            self.chat_history.append({"type": "ai", "text": ai_message})
            save_data(self.chat_history, CHAT_HISTORY_FILE)
            self.after(0, self.update_chat_display)
        except Exception as e:
            self.chat_history.append({"type": "ai", "text": f"Error: Could not get a response. {e}"})
            self.after(0, self.update_chat_display)

    # --- IMAGE GENERATION TAB ---
    def setup_image_gen_tab(self):
        self.image_frame = self.tab_view.tab("Image Generation")
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(1, weight=1)

        # Controls and Configs
        controls_frame = customtkinter.CTkFrame(self.image_frame, fg_color="#2c2c2c")
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)

        prompt_frame = customtkinter.CTkFrame(controls_frame, fg_color="transparent")
        prompt_frame.grid(row=0, column=0, sticky="ew")
        prompt_frame.grid_columnconfigure(0, weight=1)
        
        customtkinter.CTkLabel(prompt_frame, text="Prompt:", text_color="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.image_prompt_entry = customtkinter.CTkEntry(prompt_frame, placeholder_text="A surreal city in a digital garden...", fg_color="#333333", text_color="#ffffff", border_color="#555555")
        self.image_prompt_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # Configs Frame
        config_frame = customtkinter.CTkFrame(controls_frame, fg_color="transparent")
        config_frame.grid(row=1, column=0, sticky="ew")
        config_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        customtkinter.CTkLabel(config_frame, text="Model:", text_color="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.image_models = ["flux", "variation", "dreamshaper", "anything", "pixart"]
        self.image_model_menu = customtkinter.CTkOptionMenu(config_frame, values=self.image_models, fg_color="#333333", button_color="#444444", button_hover_color="#555555")
        self.image_model_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        customtkinter.CTkLabel(config_frame, text="Resolution:", text_color="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.resolution_options = ["512x512", "768x768", "1024x1024"]
        self.resolution_menu = customtkinter.CTkOptionMenu(config_frame, values=self.resolution_options, fg_color="#333333", button_color="#444444", button_hover_color="#555555")
        self.resolution_menu.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        self.nologo_var = customtkinter.StringVar(value="on")
        customtkinter.CTkCheckBox(config_frame, text="No Logo", variable=self.nologo_var, onvalue="on", offvalue="off", fg_color="green", text_color="#ffffff", hover_color="#006600").grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        self.generate_image_btn = customtkinter.CTkButton(controls_frame, text="Generate Image", command=self.generate_image, corner_radius=10, fg_color="#008000", hover_color="#006600")
        self.generate_image_btn.grid(row=2, column=0, padx=5, pady=10, sticky="ew")

        # Image display area
        self.image_display_frame = customtkinter.CTkFrame(self.image_frame, fg_color="#1a1a1a", corner_radius=10)
        self.image_display_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)
        
        self.image_label = customtkinter.CTkLabel(self.image_display_frame, text="", image=None)
        self.image_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # History and Download buttons
        history_frame = customtkinter.CTkFrame(self.image_frame, fg_color="transparent")
        history_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        history_frame.grid_columnconfigure((0, 1), weight=1)
        
        customtkinter.CTkButton(history_frame, text="View History", command=self.view_image_history, fg_color="#444444", hover_color="#555555").grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.download_image_btn = customtkinter.CTkButton(history_frame, text="Download Image", command=self.download_image, fg_color="#444444", hover_color="#555555")
        self.download_image_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.current_image_data = None

    def generate_image(self):
        # Implementation from previous code
        prompt = self.image_prompt_entry.get()
        if not prompt:
            return
        
        self.generate_image_btn.configure(state="disabled", text="Generating...")
        
        threading.Thread(target=self.get_image, args=(prompt,)).start()

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
            image_stream = io.BytesIO(image_data)
            pil_image = Image.open(image_stream)

            ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=(pil_image.width, pil_image.height))
            
            self.after(0, self.update_image_display, ctk_image, image_data)
            self.image_history.append({"prompt": prompt, "model": selected_model, "resolution": resolution, "nologo": nologo})
            save_data(self.image_history, IMAGE_HISTORY_FILE)

        except Exception as e:
            self.after(0, lambda: self.image_label.configure(text=f"Error: {e}"))
        finally:
            self.after(0, lambda: self.generate_image_btn.configure(state="normal", text="Generate Image"))

    def update_image_display(self, ctk_image, image_data):
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image
        self.current_image_data = {"data": image_data}

    def download_image(self):
        if self.current_image_data:
            filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if filename:
                with open(filename, "wb") as f:
                    f.write(self.current_image_data['data'])
                messagebox.showinfo("Success", f"Image downloaded to {filename}")

    def view_image_history(self):
        # Implementation to show history in a new window/pop-up
        pass
    
    # --- TEXT TO SPEECH TAB ---
    def setup_tts_tab(self):
        self.tts_frame = self.tab_view.tab("Text to Speech")
        self.tts_frame.grid_columnconfigure(0, weight=1)
        self.tts_frame.grid_rowconfigure(1, weight=1)

        # Configs Frame
        config_frame = customtkinter.CTkFrame(self.tts_frame, fg_color="#2c2c2c")
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        config_frame.grid_columnconfigure((0, 1), weight=1)
        
        customtkinter.CTkLabel(config_frame, text="Voice:", text_color="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tts_voices = ["nova", "echo", "fable", "onyx", "shimmer"]
        self.tts_voice_menu = customtkinter.CTkOptionMenu(config_frame, values=self.tts_voices, fg_color="#333333", button_color="#444444", button_hover_color="#555555")
        self.tts_voice_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Prompt Textbox
        self.tts_prompt_box = customtkinter.CTkTextbox(self.tts_frame, height=200, wrap="word", fg_color="#1a1a1a", text_color="#ffffff", border_color="#555555", corner_radius=10)
        self.tts_prompt_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Control buttons
        button_frame = customtkinter.CTkFrame(self.tts_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.preview_btn = customtkinter.CTkButton(button_frame, text="Audio Preview", command=self.preview_audio, corner_radius=10, fg_color="#444444", hover_color="#555555")
        self.preview_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.download_audio_btn = customtkinter.CTkButton(button_frame, text="Download Audio", command=self.download_audio, corner_radius=10, fg_color="#008000", hover_color="#006600")
        self.download_audio_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # History
        self.tts_history_box = customtkinter.CTkTextbox(self.tts_frame, height=100, state="disabled", fg_color="#1a1a1a", text_color="#ffffff")
        self.tts_history_box.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.update_tts_history_display()

    def update_tts_history_display(self):
        self.tts_history_box.configure(state="normal")
        self.tts_history_box.delete("1.0", "end")
        for text in self.tts_history:
            self.tts_history_box.insert("end", f"- {text[:50]}...\n")
        self.tts_history_box.configure(state="disabled")

    def preview_audio(self):
        text_to_speak = self.tts_prompt_box.get("1.0", "end-1c")
        if not text_to_speak:
            return
        
        self.tts_history.append(text_to_speak)
        save_data(self.tts_history, TTS_HISTORY_FILE)
        self.update_tts_history_display()
        
        threading.Thread(target=self.speak_text_offline, args=(text_to_speak,)).start()

    def speak_text_offline(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def download_audio(self):
        text_to_speak = self.tts_prompt_box.get("1.0", "end-1c")
        if not text_to_speak:
            return

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
            messagebox.showinfo("Success", f"Audio downloaded to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download audio: {e}")

    # --- SETTINGS TAB ---
    def setup_settings_tab(self):
        self.settings_frame = self.tab_view.tab("Settings")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_rowconfigure(0, weight=1)

        # Outer settings frame
        settings_container = customtkinter.CTkFrame(self.settings_frame, fg_color="#2c2c2c", corner_radius=10)
        settings_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        settings_container.grid_columnconfigure(0, weight=1)
        settings_container.grid_rowconfigure(0, weight=1)

        # Inner scrollable frame for settings content
        scrollable_settings = customtkinter.CTkScrollableFrame(settings_container, fg_color="transparent")
        scrollable_settings.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_settings.grid_columnconfigure(0, weight=1)
        
        # Profile Section
        profile_frame = customtkinter.CTkFrame(scrollable_settings, fg_color="#3a3a3a", corner_radius=10)
        profile_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        profile_frame.grid_columnconfigure(1, weight=1)
        
        customtkinter.CTkLabel(profile_frame, text="Profile Settings", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        
        # Profile Picture
        self.profile_image_label = customtkinter.CTkLabel(profile_frame, text="", width=100, height=100)
        self.profile_image_label.grid(row=1, column=0, padx=10, pady=10)
        self.load_profile_image()

        profile_controls = customtkinter.CTkFrame(profile_frame, fg_color="transparent")
        profile_controls.grid(row=1, column=1, sticky="w", padx=(0, 10))
        
        customtkinter.CTkLabel(profile_controls, text="Username:", font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = customtkinter.CTkEntry(profile_controls, placeholder_text="Enter your name", width=200)
        self.username_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.username_entry.insert(0, self.settings["username"])
        
        customtkinter.CTkButton(profile_controls, text="Change Profile Picture", command=self.change_profile_pic, fg_color="#555555", hover_color="#666666").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        customtkinter.CTkButton(profile_frame, text="Save Profile", command=self.save_settings, corner_radius=10, fg_color="#008000", hover_color="#006600").grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # General Preferences Section
        preferences_frame = customtkinter.CTkFrame(scrollable_settings, fg_color="#3a3a3a", corner_radius=10)
        preferences_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        preferences_frame.grid_columnconfigure(1, weight=1)
        
        customtkinter.CTkLabel(preferences_frame, text="App Preferences", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        
        # Add more preference options here in the future
        customtkinter.CTkLabel(preferences_frame, text="Theme:", font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.theme_menu = customtkinter.CTkOptionMenu(preferences_frame, values=["Dark", "Light", "System"])
        self.theme_menu.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        self.theme_menu.set(customtkinter.get_appearance_mode())
        self.theme_menu.bind("<<ComboboxSelected>>", self.change_theme)

    def load_profile_image(self):
        try:
            image_path = self.settings.get("profile_pic", None)
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
            else:
                img = Image.open(resource_path(DEFAULT_PROFILE_PIC))
            
            # Resize image to fit
            img = img.resize((100, 100), Image.LANCZOS)
            ctk_image = customtkinter.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            self.profile_image_label.configure(image=ctk_image)
            self.profile_image_label.image = ctk_image
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
        save_data(self.settings, SETTINGS_FILE)
        messagebox.showinfo("Saved", "Settings have been saved successfully!")
        self.update_chat_display() # Update chat with new username

    def change_theme(self, event=None):
        new_mode = self.theme_menu.get()
        customtkinter.set_appearance_mode(new_mode)
        # We could also save this setting to the file for persistence

if __name__ == "__main__":
    app = TigosApp()
    app.mainloop()