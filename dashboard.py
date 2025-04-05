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
    current_hour = datetime.now().strftime("%M")  # or "%I" for 12-hour format
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
    x, y = 70, 525 
    for direction, times in bus_times.items():
        draw = ImageDraw.Draw(background)
        draw.text((x, y), direction, font=largefont, fill=0)
        y += 40
        print(direction)
        for t in times:
            draw.text((x + 10, y), f"- {t}", font=smallfont, fill=0)
            y += 28
        y += 20

import requests

def get_available_bikes(station_id):
    try:
        url = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_zg/sv/station_status.json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()

        stations = data.get("data", {}).get("stations", [])
        if not stations:
            logging.info("No station data found in feed.")
            return None

        # Build a lookup dictionary 
        station_map = {s["station_id"]: s for s in stations}

        if station_id not in station_map:
            logging.info(f"Station ID {station_id} not found.")
            return None

        return station_map[station_id].get("num_bikes_available", -1)

    except requests.RequestException as e:
        print(f"Network or API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None  # In case of error

def draw_num_of_bikes(background, num_of_bikes):
    smallfont = ImageFont.truetype(os.path.join(maindir, 'Font.ttc'), 25)
    largefont = ImageFont.truetype(os.path.join(maindir, 'Font.ttc'), 30)
    x, y = 260, 270

    draw = ImageDraw.Draw(background)
    draw.text((x, y), "Antal cyklar:", font=largefont, fill=0)
    y += 40
    draw.text((x + 10, y), f"- {num_of_bikes}", font=smallfont, fill=0)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## 

def main():

    while not os.path.exists("/dev/spidev0.0"):
        loggin.info("Waiting for SPI...")
        time.sleep(1)


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

            num_of_bikes = get_available_bikes("31107695") #31107695 är mossen
            draw_num_of_bikes(background, num_of_bikes)

            # Either do partial refresh or complete refresh
            if number_of_partial_refreshes > 15:
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
            time.sleep(45)



    except IOError as e:
        logging.error(f"IOError: {e}")
    except KeyboardInterrupt:
        handle_keyboard_interrupt()

if __name__ == "__main__":
    main()


