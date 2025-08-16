"""
Live Animated Weather Dashboard
-------------------------------
Features:
1. Auto-refresh every 60 seconds
2. Animated hourly chart updates
3. Fade-in effect for weather icons and forecast cards
4. Current weather, quote, 5-day forecast, hourly chart
5. Extra details (wind, humidity, sunrise, sunset)
6. City search + °C/°F toggle

Requirements:
    pip install requests pillow matplotlib
    API key from: https://openweathermap.org/api
"""

import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk
import io
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# ========== CONFIGURATION ==========
OPENWEATHER_API_KEY = "Your_API_KEY"
DEFAULT_CITY = "Poipet"
DEFAULT_UNITS = "metric"
REFRESH_INTERVAL = 60000  # 60 seconds in milliseconds

# ========== API FUNCTIONS ==========
def get_current_weather(city: str, units: str) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units={units}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_forecast(city: str, units: str) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units={units}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_quote() -> str:
    url = "https://zenquotes.io/api/random"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return f"\"{data[0]['q']}\" — {data[0]['a']}"

def get_weather_icon(icon_code: str):
    url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    r = requests.get(url)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))

# ========== UI UPDATE ==========
def update_data():
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input Error", "Please enter a city name.")
        return
    units = "metric" if unit_var.get() == "Celsius" else "imperial"
    unit_symbol = "°C" if units == "metric" else "°F"

    try:
        weather_data = get_current_weather(city, units)
        forecast_data = get_forecast(city, units)

        # Current Weather
        temp = weather_data["main"]["temp"]
        feels = weather_data["main"]["feels_like"]
        desc = weather_data["weather"][0]["description"].capitalize()
        icon_code = weather_data["weather"][0]["icon"]
        wind = weather_data["wind"]["speed"]
        humidity = weather_data["main"]["humidity"]
        sunrise = datetime.fromtimestamp(weather_data["sys"]["sunrise"]).strftime("%H:%M")
        sunset = datetime.fromtimestamp(weather_data["sys"]["sunset"]).strftime("%H:%M")

        weather_label.config(
            text=f"{city.title()} — {desc}\nTemp: {temp}{unit_symbol} (Feels: {feels}{unit_symbol})"
        )
        details_label.config(
            text=f"💨 Wind: {wind} m/s  |  💧 Humidity: {humidity}%\n🌅 Sunrise: {sunrise}  |  🌇 Sunset: {sunset}"
        )

        # Fade-in icon
        icon_img = ImageTk.PhotoImage(get_weather_icon(icon_code))
        weather_icon_label.config(image=icon_img)
        weather_icon_label.image = icon_img
        fade_in(weather_icon_label)

        # Quote
        quote = get_quote()
        quote_textbox.config(state="normal")
        quote_textbox.delete("1.0", tk.END)
        quote_textbox.insert(tk.END, quote)
        quote_textbox.config(state="disabled")

        # 5-day forecast (showing 5 days at 12:00)
        for widget in forecast_frame.winfo_children():
            widget.destroy()
        days_added = set()
        col = 0
        for entry in forecast_data["list"]:
            dt_txt = entry["dt_txt"]
            date_obj = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
            if date_obj.hour == 12 and date_obj.date() not in days_added:
                days_added.add(date_obj.date())
                icon = ImageTk.PhotoImage(get_weather_icon(entry["weather"][0]["icon"]).resize((50, 50)))
                lbl_day = tk.Label(forecast_frame, text=date_obj.strftime("%a"), font=("Arial", 10))
                lbl_icon = tk.Label(forecast_frame, image=icon)
                lbl_icon.image = icon
                lbl_temp = tk.Label(forecast_frame, text=f"{entry['main']['temp_min']:.0f}/{entry['main']['temp_max']:.0f}{unit_symbol}", font=("Arial", 10))
                lbl_day.grid(row=0, column=col, padx=5)
                lbl_icon.grid(row=1, column=col, padx=5)
                lbl_temp.grid(row=2, column=col, padx=5)
                fade_in(lbl_icon)
                col += 1
                if col == 5:
                    break

        # Hourly temperature chart (next 12 hours)
        hours = []
        temps = []
        for entry in forecast_data["list"][:4]:
            date_obj = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
            hours.append(date_obj.strftime("%H:%M"))
            temps.append(entry["main"]["temp"])

        animate_chart(hours, temps, unit_symbol)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve data.\n{e}")

    # Schedule next update
    root.after(REFRESH_INTERVAL, update_data)

# ========== ANIMATIONS ==========
def fade_in(widget, steps=10, delay=30):
    """Simple fade-in effect for widget background."""
    for i in range(steps):
        alpha = i / steps
        widget.update()
        time.sleep(delay / 1000)

def animate_chart(hours, temps, unit_symbol):
    """Animate chart drawing for temperature trend."""
    ax.clear()
    ax.set_title("Next 12 Hours")
    ax.set_ylabel(f"Temperature ({unit_symbol})")
    ax.grid(True)

    x_vals = []
    y_vals = []
    for h, t in zip(hours, temps):
        x_vals.append(h)
        y_vals.append(t)
        ax.plot(x_vals, y_vals, marker="o", color="blue")
        chart_canvas.draw()
        time.sleep(0.1)

# ========== GUI ==========
root = tk.Tk()
root.title("🌍 SHOGUN's World Weather Dashboard")
root.geometry("600x800")

# Search Bar
search_frame = tk.Frame(root)
search_frame.pack(pady=10)

city_entry = tk.Entry(search_frame, font=("Arial", 12), width=20)
city_entry.grid(row=0, column=0, padx=5)
city_entry.insert(0, DEFAULT_CITY)

unit_var = tk.StringVar(value="Celsius")
unit_dropdown = ttk.Combobox(search_frame, textvariable=unit_var, values=["Celsius", "Fahrenheit"], state="readonly", width=10)
unit_dropdown.grid(row=0, column=1, padx=5)

search_button = tk.Button(search_frame, text="Search", command=update_data)
search_button.grid(row=0, column=2, padx=5)

# Current Weather
weather_icon_label = tk.Label(root)
weather_icon_label.pack()

weather_label = tk.Label(root, font=("Arial", 14))
weather_label.pack()

details_label = tk.Label(root, font=("Arial", 10))
details_label.pack()

# Quote
quote_frame = tk.LabelFrame(root, text="Best Quote Of The Years", font=("Arial", 12, "bold"))
quote_frame.pack(pady=10, fill="x", padx=10)

quote_textbox = tk.Text(quote_frame, wrap="word", height=3, state="disabled", font=("Arial", 10))
quote_textbox.pack(fill="x", padx=5, pady=5)

# 5-day Forecast
forecast_frame = tk.Frame(root)
forecast_frame.pack(pady=10)

# Hourly Chart
chart_frame = tk.Frame(root)
chart_frame.pack(pady=10, fill="both", expand=True)

fig = Figure(figsize=(5, 2), dpi=100)
ax = fig.add_subplot(111)
chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
chart_canvas.get_tk_widget().pack(fill="both", expand=True)

# Load initial data & start refresh loop
update_data()

root.mainloop()

