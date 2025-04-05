#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
from waveshare_epd import epd7in5_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

from vasttrafik_client import VasttrafikClient
from collections import defaultdict
from datetime import datetime
import dateutil.parser

maindir = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(level=logging.DEBUG)

def init_display():
    logging.info("Initializing display")
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()
    return epd

def display_background(epd):
    logging.info("Displaying background image")
    image = Image.open(os.path.join(maindir, 'background-01.bmp'))
    #epd.display(epd.getbuffer(image))
    time.sleep(2)
    return image

def clear_and_sleep(epd):
    logging.info("Clearing display and going to sleep")
    epd.init()
    epd.Clear()
    epd.sleep()

def handle_keyboard_interrupt():
    logging.info("ctrl + c: exit requested by user")
    epd7in5_V2.epdconfig.module_exit(cleanup=True)
    exit()

def find_position():
        while True:
            draw = ImageDraw.Draw(background)
            draw.text((x, y), 'X', font=font35, fill=0)
            epd.display(epd.getbuffer(background))

            print(f"Text at: ({x}, {y})")
            cmd = input("Move: [w/a/s/d] or [q]uit: ").strip().lower()

            if cmd == 'w': y -= 2
            elif cmd == 's': y += 2
            elif cmd == 'a': x -= 2
            elif cmd == 'd': x += 2
            elif cmd == 'q': break

def draw_clock(background):
    font = ImageFont.truetype(os.path.join(maindir, 'Font.ttc'), 25)
    x, y = 118, 45 # Middle of sun for two digit numbers

    draw = ImageDraw.Draw(background)
    current_hour = datetime.now().strftime("%H")  # or "%I" for 12-hour format
    draw.text((x, y), current_hour, font=font, fill=0)

def get_bus_times():
    auth_key = "ZTlHRHZhSEZKaTBaNmp2NlFMdVprTlh3X09BYTpfY0RsbURpT205T0tqX1Z2VWQwS3Zya2ZYVm9h"
    vt = VasttrafikClient(auth_key)

    stop_gid = "9021014004830000"  # ← Mossen
    response = vt.get(f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{stop_gid}/departures")

    if not response.ok:
        print("Fel:", response.status_code, response.text)
        return {}

    data = response.json()
    departures = data["results"]

    # Gruppera avgångar per riktning
    directions = defaultdict(list)

    for d in departures:
        direction = d["serviceJourney"]["directionDetails"]["shortDirection"]
        estimated_time = dateutil.parser.isoparse(d["estimatedOtherwisePlannedTime"])
        directions[direction].append(estimated_time)

    # Returnera de två kommande tiderna som strängar per riktning
    simplified_output = {}

    for direction, times in directions.items():
        sorted_times = sorted(times)
        simplified_output[direction] = [t.strftime("%H:%M") for t in sorted_times[:2]]

    return simplified_output

def draw_bus_times(background, bus_times):
    smallfont = ImageFont.truetype(os.path.join(maindir, 'Font.ttc'), 25)
    largefont = ImageFont.truetype(os.path.join(maindir, 'Font.ttc'), 30)
    x, y = 70, 525 # Middle of sun for two digit numbers
    for direction, times in bus_times.items():
        draw = ImageDraw.Draw(background)
        draw.text((x, y), direction, font=largefont, fill=0)
        y += 40
        print(direction)
        for t in times:
            draw.text((x + 10, y), f"- {t}", font=smallfont, fill=0)
            y += 28
        y += 20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## 

def main():
    try:
        # MAIN PROGRAM
        logging.info("Running dashboard software")
        epd = init_display()
        number_of_partial_refreshes = 0

        while True:
            background = display_background(epd)
            
            draw_clock(background)

            bus_times = get_bus_times()
            draw_bus_times(background, bus_times)

            # Either do partial refresh or complete refresh
            if number_of_partial_refreshes > 10:
                epd.init()
                logging.info("Running major refresh")
                epd.display(epd.getbuffer(background))
                number_of_partial_refreshes = 0
            else:
                epd.init_part()  # <- Switch to partial mode
                logging.info("Running partial refresh")
                epd.display_Partial(epd.getbuffer(background),0, 0, epd.width, epd.height) # Från (0,0) till (width, height) alltså uppdaterar vi hela skärmen
                number_of_partial_refreshes += 1

            #logging.info("Goto Sleep...")
            #epd.sleep() #Fungerar inte utan att starta om man också ska uppdatera skärmen, och det spelar ingen roll om den är ipluggad
            time.sleep(60)



    except IOError as e:
        logging.error(f"IOError: {e}")
    except KeyboardInterrupt:
        handle_keyboard_interrupt()

if __name__ == "__main__":
    main()


