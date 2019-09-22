#!/usr/bin/python3
# -*- coding:utf-8 -*-

from PIL import Image,ImageDraw,ImageFont
import datetime
import epd4in2
import os
import pyowm
import pytz
import re
import time
import time
import traceback

font_clock = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 100)
font_clock_width, font_clock_height = font_clock.getsize("0")
font_misc = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 40)
font_misc_width, font_misc_height = font_misc.getsize("0")
font_caption = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 25)
font_caption_width, font_caption_height = font_caption.getsize("0")
font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 20)
font_small_width, font_small_height = font_small.getsize("0")
tz = pytz.timezone('Europe/Berlin')

def conv_weather_time(weather):
    w_time = weather.get_reference_time('date')
    w_time = w_time.astimezone(tz)
    return w_time.strftime("%H:%M")

def get_weather():
    weather = None
    forecast = None
    try:
        pyowm_key = None
        pyowm_location = None
        try:
            pyowm_key = os.environ['OWM_API_KEY']
            pyowm_location = os.environ['OWM_LOCATION']
        except:
            return weather, forecast
        owm = pyowm.OWM(pyowm_key)
        sf = owm.weather_at_place(pyowm_location)
        weather = sf.get_weather()
        forecaster = owm.three_hours_forecast(pyowm_location)
        forecast = forecaster.get_forecast()
    except:
        pass
    return weather, forecast


def draw_weather(draw, image, x, y, weather, caption):
    icon_name = weather.get_weather_icon_name()
    icon_name = re.sub("[nd]", ".png", icon_name)
    img = Image.open(os.path.join(os.path.dirname(__file__), "icons/" + icon_name))
    img.load()
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[-1])
    img = background.convert('1')

    new_dimension = 90
    width, height = img.size
    left = (width - new_dimension)/2
    top = (height - new_dimension)/2
    right = (width + new_dimension)/2
    bottom = (height + new_dimension)/2
    img = img.crop((left, top, right, bottom))

    draw.text((x + (100 - len(caption) * font_caption_width)/2, y), caption, font = font_caption, fill = 0)
    image.paste(img, (x + 5, y + font_caption_height))
    temp = str(round(weather.get_temperature('celsius')['temp'])) + "°C " + str(round(weather.get_humidity())) + "%"
    draw.text((x + (100 - len(temp) * font_small_width)/2, y + font_caption_height + 90), temp, font = font_small, fill = 0)
    draw.line((x + 100, y, x + 100, epd4in2.EPD_HEIGHT), fill = 0, width = 2)


def main():
    epd = epd4in2.EPD()
    epd.init()
    epd.Clear(0xFF)

    while True:
        Himage = Image.new('1', (epd4in2.EPD_WIDTH, epd4in2.EPD_HEIGHT), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)
        clock_current = datetime.datetime.now(tz)
        clock_dest = clock_current.replace(second = 0, microsecond = 0) + datetime.timedelta(
            minutes = 1, seconds = 1)

        clock = clock_current.strftime("%H:%M")
        draw.text(((epd4in2.EPD_WIDTH - len(clock)*font_clock_width) / 2, 0), clock, font = font_clock, fill = 0)

        draw.line((0, font_clock_height + 10, epd4in2.EPD_WIDTH, font_clock_height + 10), fill = 0, width = 5)

        date = clock_current.strftime("%a - %d.%m.%y")
        draw.text(((epd4in2.EPD_WIDTH - len(date)*font_misc_width) / 2, font_clock_height + 20), date, font = font_misc, fill = 0)
        
        weather, forecast = get_weather()
        if weather == None:
            clock_last = clock_last_fail
            epd.display(epd.getbuffer(Himage))
            continue
        weather_list = forecast.get_weathers()
        forecast_disp = []

        for w in weather_list:
            w_time = w.get_reference_time('date')
            w_time = w_time.astimezone(tz)
            w_time_cur = clock_current + datetime.timedelta(hours = 3)
            if w_time < w_time_cur:
                continue
            forecast_disp.append(w)

        draw_weather(draw, Himage, 0, (font_clock_height + font_misc_height + 30), weather, "Now")
        draw_weather(draw, Himage, 100, (font_clock_height + font_misc_height + 30),
                forecast_disp[0], conv_weather_time(forecast_disp[0]))
        draw_weather(draw, Himage, 200, (font_clock_height + font_misc_height + 30),
                forecast_disp[2], conv_weather_time(forecast_disp[2]))
        draw_weather(draw, Himage, 300, (font_clock_height + font_misc_height + 30),
                forecast_disp[4], conv_weather_time(forecast_disp[4]))
        epd.display(epd.getbuffer(Himage))

        clock_current = datetime.datetime.now(tz)

        if clock_dest < clock_current:
            continue
        time.sleep(int((clock_dest - clock_current).total_seconds()))

    epd.sleep()

if __name__== "__main__":
    main()
