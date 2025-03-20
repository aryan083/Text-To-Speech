# Import necessary libraries
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import pyttsx3
import threading

# Function to convert text to speech and play it
def convertAndPlay():
    # Get available voices and set the selected voice
    voices = bot.getProperty('voices')
    bot.setProperty('voice', voices[voice_var.get()].id)
    
    # Set speech rate based on the selected speed
    bot.setProperty('rate', speed_scale.get())
    
    # Get text from the text box
    text = text_box.get(0.0, tk.END)
    
    # Check if there is text to convert
    if len(text) > 1:
        # Use text-to-speech engine to say the text
        bot.say(text)
        bot.runAndWait()
    else:
        # Show a warning if there is no text
        messagebox.showwarning('Warning', 'First Enter Some Text To Convert Into Audio')

# Function to save the entered text as an audio file
def saveAudio():
    # Initialize a new text-to-speech engine
    bot = pyttsx3.init()
    
    # Get available voices and set the selected voice
    voices = bot.getProperty('voices')
    bot.setProperty('voice', voices[voice_var.get()].id)
    
    # Set speech rate based on the selected speed
    bot.setProperty('rate', speed_scale.get())
    
    # Get text from the text box
    text = text_box.get(0.0, tk.END)
    
    # Check if there is non-empty text
    if len(text.strip()) > 1:
        # Ask user for a file name to save the audio as
        filename = filedialog.asksaveasfilename(defaultextension="wav")
        
        # Check if a filename is provided
        if filename:
            # Save the text as an audio file
            bot.save_to_file(text, filename)
            bot.runAndWait()
            
            # Show a success message
            messagebox.showinfo('Successful', 'Audio is saved')
    else:
        # Show a warning if there is no text
        messagebox.showwarning("Warning", 'First Enter Some Text To Convert Into Audio')

# Function to stop the text-to-speech engine if it is currently busy
def stopEngine():
    if bot.isBusy():
        print(bot.isBusy())
        bot.stop()

# Create the main Tkinter window
root = tk.Tk()
root.title("Text To Speech Generative AI")
root.geometry("600x280")
root.configure(bg="#B0E0E6")  
root.resizable(0, 0)

# Initialize the text-to-speech engine
bot = pyttsx3.init()

# Create a variable to store the selected voice
voice_var = tk.IntVar()

# Create a ScrolledText widget for multiline text input
text_box = ScrolledText(root, font=("Sitka Smaall", 11), bd=2, relief=tk.GROOVE, wrap=tk.WORD, undo=True)
text_box.place(x=5, y=5, height=270, width=390)

# Create a frame for voice and speed controls
frame = tk.Frame(root, bd=2, relief=tk.SUNKEN, bg="#b45f06")  
frame.place(x=395, y=5, height=270, width=200)

# Create a label frame for changing speech speed
frame2 = ttk.Labelframe(frame, text='Change Speed')
frame2.grid(row=0, column=0, pady=5, padx=4)

# Create a scale for adjusting speech speed
speed_scale = tk.Scale(frame2, from_=50, to=150, orient=tk.HORIZONTAL, length=170, bg='#ffffff')
speed_scale.set(100)
speed_scale.grid(row=2, columnspan=1, ipadx=5, ipady=5)

# Create a label frame for changing voice
frame3 = ttk.Labelframe(frame, text='Change Voice')
frame3.grid(row=1, column=0, pady=5)

# Create radio buttons for selecting voice type
R1 = tk.Radiobutton(frame3, text="Male", variable=voice_var, value=0)
R1.grid(row=0, column=0, ipadx=7, ipady=5, padx=5)

R2 = tk.Radiobutton(frame3, text="Female", variable=voice_var, value=1)
R2.grid(row=0, column=1, ipadx=7, ipady=5, padx=5)

# Create a frame for buttons
frame4 = tk.Frame(frame, bd=2, relief=tk.SUNKEN, bg="#5fa6e7")  
frame4.grid(row=2, column=0, pady=10)

# Create buttons for converting and playing, saving audio, clearing text, and exiting
btn_1 = ttk.Button(frame4, text='Convert & Play', width=15, command=lambda: threading.Thread(target=convertAndPlay, daemon=True).start(), style='Cust.TButton')
btn_1.grid(row=0, column=0, ipady=5, padx=4, pady=5)

btn_2 = ttk.Button(frame4, text='Save as Audio', width=15, command=saveAudio, style='Cust.TButton')
btn_2.grid(row=1, column=0, ipady=5, padx=4, pady=5)

btn_3 = ttk.Button(frame4, text='Clear', width=10, command=lambda: text_box.delete(0.0, tk.END))
btn_3.grid(row=0, column=1, ipady=5, padx=4, pady=5)

btn_4 = ttk.Button(frame4, text='Exit', width=10, command=root.quit)
btn_4.grid(row=1, column=1, ipady=5, padx=4, pady=5)

# Configure the style for Tkinter buttons
style = ttk.Style()
style.configure('Cust.TButton', foreground='black', background='#FFD700')  # Adjust text and background colors

# Start the Tkinter event loop
root.mainloop()
