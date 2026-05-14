import os
import sys
import json
import time
import threading
import keyboard
import pyperclip
import keyring
import anthropic
import pygetwindow as gw
import random
import logging
from PIL import Image, ImageDraw
from datetime import datetime, timedelta
from io import BytesIO
import base64
import wx
import wx.adv
import pystray

APP_NAME = "Card Formatting Tools"
APP_VERSION = "1.1.0"

# ----------------------------------------------------------------------
# Logging Setup
# ----------------------------------------------------------------------

class Logger:
    def __init__(self, name=APP_NAME):
        self.logger = logging.getLogger(name)
        self.setup()
        
    def setup(self):
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.getenv('APPDATA'), APP_NAME, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configure logger
        self.logger.setLevel(logging.DEBUG)
        
        # Log file format: app-YYYY-MM-DD.log
        log_file = os.path.join(logs_dir, f"app-{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # File handler (writes to log file)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (writes to console)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Define format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def debug(self, message):
        self.logger.debug(message)
        
    def info(self, message):
        self.logger.info(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def error(self, message, exc_info=None):
        if exc_info:
            self.logger.error(message, exc_info=exc_info)
        else:
            self.logger.error(message)
        
    def critical(self, message, exc_info=None):
        if exc_info:
            self.logger.critical(message, exc_info=exc_info)
        else:
            self.logger.critical(message)

# Global logger instance
log = Logger()

# ----------------------------------------------------------------------
# Clod activities and signoffs
# ----------------------------------------------------------------------

CLOD_ACTIVITIES_BY_TIME = {
    "morning": [  # 5 AM - 9 AM
        "Clod is stretching...",
        "Clod is yawning adorably...",
        "Clod is making breakfast...",
        "Clod is eating scrambled eggs...",
        "Clod is sipping orange juice...",
        "Clod is brushing his teeth...",
        "Clod is doing the warrior pose...",
        "Clod is practicing sun salutations...",
        "Clod is reading the morning news...",
        "Clod is watering his plants...",
        "Clod is enjoying his morning coffee...",
        "Clod is basking in a sunbeam...",
        "Clod is watching the sunrise...",
        "Clod is flossing...",
        "Clod is greeting each of his houseplants...",
        "Clod is preparing his daily schedule...",
        "Clod is doing morning stretches...",
        "Clod is listening to morning radio...",
        "Clod is making toast...",
        "Clod is arranging his breakfast cereal by size...",
        "Clod is packing his lunch...",
        "Clod is feeding his goldfish...",
        "Clod is opening the curtains..."
    ],
    "day": [  # 9 AM - 8 PM
        "Clod is flopping on his back...",
        "Clod is reading to his friend Long Cat...",
        "Clod is learning about birds...",
        "Clod is asking his friend Long Cat about his day...",
        "Clod is nyoyning contentedly...",
        "Clod is trying to scratch his back...",
        "Clod is burrowing...",
        "Clod is on the hunt for knowledge...",
        "Clod is watching raindrops on the window...",
        "Clod is rolling around...",
        "Clod is sunbathing...",
        "Clod is reading about the Strong Force...",
        "Clod is enjoying Mozart...",
        "Clod is investigating a houseplant...",
        "Clod found a mud puddle...",
        "Clod is attempting to play the piano...",
        "Clod is organizing scientific journals...",
        "Clod is balancing a book on his head...",
        "Clod is composing a nyoyn symphony...",
        "Clod is typing enthusiastically...",
        "Clod is rolling down a gentle slope...",
        "Clod is solving a Rubik's cube...",
        "Clod is attempting yoga poses...",
        "Clod is building a fort of textbooks...",
        "Clod is trying to take a selfie...",
        "Clod is debating quantum mechanics...",
        "Clod is juggling plush balls...",
        "Clod is alphabetizing his thoughts...",
        "Clod is blending in with round fruits...",
        "Clod is writing a research paper...",
        "Clod is rolling uphill for exercise...",
        "Clod is solving a crossword puzzle...",
        "Clod is making a sandwich...",
        "Clod is practicing his victory dance...",
        "Clod is knitting a tiny scarf...",
        "Clod is directing a one-Clod play...", 
        "Clod is playing chess against himself...",
        "Clod is examining a clock's gears...",
        "Clod is painting a self-portrait...",
        "Clod is measuring his roundness...",
        "Clod is performing a magic trick...",
        "Clod is learning a new language...",
        "Clod is building a fruit solar system...",
        "Clod is composing a song about learning...",
        "Clod is concentrating on Sudoku...",
        "Clod is creating origami shapes...",
        "Clod is trying to understand why fish don't drown...",
        "Clod is recreating famous artworks...",
        "Clod is attempting to moonwalk...",
        "Clod is sorting his button collection...",
        "Clod is trying to lick his elbow...",
        "Clod is writing a haiku about fluff...",
        "Clod is designing a better wheel (rounder)...",
        "Clod is inventing a new board game...",
        "Clod is learning to play the harmonica...",
        "Clod is trying to catch dust motes in sunbeams...",
        "Clod is building a house of cards...",
        "Clod is trying to solve a maze...",
        "Clod is practicing his evil laugh...",
        "Clod is drawing faces on foggy windows...",
        "Clod is attempting to juggle soap bubbles...",
        "Clod is rolling uphill for exercise...",
        "Clod is trying to understand why doors exist...",
        "Clod is writing a letter to his future self...",
        "Clod is trying to break a world record...",
        "Clod is learning to speak whale...",
        "Clod is practicing his royal wave...",
        "Clod is trying to count to infinity...",
        "Clod is inventing a new ice cream flavor...",
        "Clod is writing a mystery novel...",
        "Clod is trying to remember where he left his keys...",
        "Clod is planning a trip around the world...",
        "Clod is attempting to break dance...",
        "Clod is learning semaphore...",
        "Clod is trying to perfect his yodel...",
        "Clod is inventing a new martial art...",
        "Clod is practicing his acceptance speech...",
        "Clod is trying to grow a bonsai tree...",
        "Clod is learning to read Braille...",
        "Clod is trying to make friends with his shadow...",
        "Clod is inventing a new element...",
        "Clod is planning a surprise party for his friend Long Cat...",
        "Clod is trying to catch his own tail...",
        "Clod is writing a self-help book...",
        "Clod is learning to walk a tightrope...",
        "Clod is trying to predict the weather...",
        "Clod is inventing a new dance move...",
        "Clod is trying to build a perpetual motion machine...",
        "Clod is learning to read tea leaves...",
        "Clod is practicing his stage dive...",
        "Clod is trying to fold a fitted sheet...",
        "Clod is inventing a new sport...",
        "Clod is attempting to solve world hunger...",
        "Clod is trying to communicate with plants...",
        "Clod is writing an opera about lint...",
        "Clod is learning to throw a boomerang...",
        "Clod is trying to build a time machine...",
        "Clod is inventing a new programming language...",
        "Clod is attempting to break the sound barrier...",
        "Clod is trying to decipher ancient hieroglyphs...",
        "Clod is writing a cookbook for clouds...",
        "Clod is learning to play the theremin...",
        "Clod is trying to put on shoes...",
        "Clod is making instant noodles...",
        "Clod is practicing French with his friend Long Cat...",
        "Clod is turning a mountain into three perfect molehills...",
        "Clod is SNEAKING...",
        "Clod is looking for his ankles...",
        "Clod is thinking deeply...",
        "Clod is putting on his tiny professor glasses...",
        "Clod is simplifying complex concepts...",
        "Clod is breaking things down into manageable bits...",
        "Clod is preparing a tiny lecture...",
        "Clod is drawing diagrams on a whiteboard...",
        "Clod is organizing his thoughts...",
        "Clod is creating an explainer video...",
        "Clod is turning on his ELI5 mode...",
        "Clod is making an educational poster...",
        "Clod is crafting the perfect analogy...",
        "Clod is attempting to hypnotize himself...",
        "Clod is trying to prove the existence of ghosts...",
        "Clod is attempting to summon a spirit..."
    ],
    "evening": [  # 8 PM - 11 PM
        "Clod is winding down for the day...",
        "Clod is drinking lavender tea...",
        "Clod is putting on his cozy pajamas...",
        "Clod is dimming the lights...",
        "Clod is journaling about his day...",
        "Clod is watching the sunset...",
        "Clod is reading a bedtime story...",
        "Clod is taking a warm bath...",
        "Clod is listening to relaxing music...",
        "Clod is doing gentle evening stretches...",
        "Clod is preparing tomorrow's outfit...",
        "Clod is enjoying a cup of chamomile...",
        "Clod is fluffing his pillows...",
        "Clod is setting his alarm clock...",
        "Clod is brushing his teeth...",
        "Clod is turning off electronics...",
        "Clod is lighting a calming candle...",
        "Clod is meditating peacefully...",
        "Clod is stargazing...",
        "Clod is studying a map of the stars...",
        "Clod is putting on his nightcap...",
        "Clod is reading poetry by candlelight...",
        "Clod is arranging his slippers...",
        "Clod is practicing deep breathing...",
        "Clod is listening to crickets chirping...",
        "Clod is doing a crossword puzzle in bed...",
        "Clod is organizing his nightstand...",
        "Clod is applying moisturizer...",
        "Clod is counting his blessings...",
        "Clod is adjusting his pillow just right...",
        "Clod is sipping herbal tea slowly...",
        "Clod is reading one more chapter...",
        "Clod is listening to nature sounds...",
        "Clod is warming up his fuzzy socks...",
        "Clod is humming a lullaby...",
        "Clod is checking tomorrow's weather...",
        "Clod is tidying up his bedside table..."
    ],
    "night": [  # 11 PM - 5 AM
        "Clod is taking a nap...",
        "Clod is snuggling with research papers...",
        "Clod is exploring a pillow case...",
        "Clod is dreaming of round things...",
        "Clod is counting sheep...",
        "Clod is snoring softly...",
        "Clod is tossing and turning...",
        "Clod is hugging his teddy bear...",
        "Clod is sleep-talking about physics...",
        "Clod is having sweet dreams...",
        "Clod is curled up in a ball...",
        "Clod is sleeping soundly...",
        "Clod is dreaming of adventures...",
        "Clod is getting a glass of water...",
        "Clod is recharging his batteries...",
        "Clod is floating on dream clouds...",
        "Clod is visiting dreamland...",
        "Clod is practicing lucid dreaming...",
        "Clod is mumbling equations in his sleep..."
    ]
}

# Holiday-specific activities (replace day activities only)
CLOD_HOLIDAY_ACTIVITIES = {
    "christmas": [
        "Clod is wrapping presents...",
        "Clod is decorating a miniature Christmas tree...",
        "Clod is baking sugar cookies...",
        "Clod is singing Christmas carols...",
        "Clod is hanging stockings by the fireplace...",
        "Clod is writing letters to Santa...",
        "Clod is untangling Christmas lights...",
        "Clod is making paper snowflakes...",
        "Clod is drinking hot cocoa with marshmallows...",
        "Clod is building a gingerbread house...",
        "Clod is wrapping himself as a present...",
        "Clod is arranging ornaments on the tree...",
        "Clod is making a wish list...",
        "Clod is leaving cookies for Santa...",
        "Clod is wearing a tiny Santa hat...",
        "Clod is reading 'Twas the Night Before Christmas...",
        "Clod is jingling sleigh bells...",
        "Clod is making snow angels...",
        "Clod is getting tangled in tinsel...",
        "Clod is interviewing a reindeer...",
        "Clod is sledding down a gentle hill...",
        "Clod is warming up by the fireplace...",
        "Clod is watching snowflakes fall...",
        "Clod is making candy canes...",
        "Clod is polishing his tiny jingle bells...",
        "Clod is practicing his ho-ho-ho...",
        "Clod is building a snowman..."
    ],
    "new_years": [
        "Clod is making New Year's resolutions...",
        "Clod is practicing his countdown...",
        "Clod is wearing a tiny party hat...",
        "Clod is blowing noise makers...",
        "Clod is reflecting on the past year...",
        "Clod is planning goals for the new year...",
        "Clod is organizing a time capsule...",
        "Clod is writing in his new diary...",
        "Clod is practicing confetti throws...",
        "Clod is learning about different time zones...",
        "Clod is making sparkling apple cider...",
        "Clod is designing a vision board...",
        "Clod is trying to stay awake until midnight...",
        "Clod is practicing his celebration dance...",
        "Clod is cleaning and organizing for a fresh start...",
        "Clod is watching fireworks through the window...",
        "Clod is toasting with a tiny glass...",
        "Clod is writing thank you notes for the year...",
        "Clod is setting up a photo booth...",
        "Clod is making friendship bracelets for the new year...",
        "Clod is reading about calendar systems...",
        "Clod is practicing midnight cheers...",
        "Clod is creating a gratitude jar...",
        "Clod is planning his first day of the new year...",
        "Clod is making lucky charms...",
        "Clod is dreaming about new adventures..."
    ],
    "halloween": [
        "Clod is trying on different costumes...",
        "Clod is carving a tiny pumpkin...",
        "Clod is practicing spooky faces...",
        "Clod is sorting Halloween candy...",
        "Clod is decorating with fake spider webs...",
        "Clod is making paper bats...",
        "Clod is telling ghost stories...",
        "Clod is bobbing for apples...",
        "Clod is practicing his scary roar...",
        "Clod is making Halloween treats...",
        "Clod is designing jack-o'-lantern faces...",
        "Clod is wearing a tiny witch hat...",
        "Clod is creating spooky sound effects...",
        "Clod is organizing his trick-or-treat bag...",
        "Clod is making orange and black decorations...",
        "Clod is learning about different monsters...",
        "Clod is practicing his monster walk...",
        "Clod is building a Skittles Galton board..."
        "Clod is making candy corn art...",
        "Clod is reading scary stories (not too scary)...",
        "Clod is making paper ghosts...",
        "Clod is trying to look frightening (but still adorable)...",
        "Clod is brewing pretend potions...",
        "Clod is dancing the monster mash...",
        "Clod is making Halloween masks...",
        "Clod is planning his costume reveal..."
    ],
    "valentines": [
        "Clod is making paper hearts...",
        "Clod is writing valentine cards...",
        "Clod is arranging flowers in a tiny vase...",
        "Clod is baking heart-shaped cookies...",
        "Clod is practicing love songs...",
        "Clod is making friendship bracelets...",
        "Clod is decorating with pink and red hearts...",
        "Clod is writing love poems...",
        "Clod is making chocolate treats...",
        "Clod is preparing valentine surprises...",
        "Clod is making paper roses...",
        "Clod is writing letters to friends...",
        "Clod is making heart-shaped art...",
        "Clod is analyzing the chemistry of chocolate...",
        "Clod is practicing compliments...",
        "Clod is studying the physics of butterflies in stomach...",
        "Clod is making pink lemonade...",
        "Clod is decorating mailboxes for valentines...",
        "Clod is making strawberry treats...",
        "Clod is spreading love and kindness...",
    ],
    "groundhog": [
        "Clod is looking for his shadow...",
        "Clod is practicing weather predictions...",
        "Clod is emerging from his burrow...",
        "Clod is studying meteorology...",
        "Clod is making shadow puppets...",
        "Clod is digging a cozy burrow...",
        "Clod is measuring shadow lengths...",
        "Clod is petitioning the groundhog council...",
        "Clod is preparing his weather forecast...",
        "Clod is polishing his prediction skills...",
        "Clod is studying cloud patterns...",
        "Clod is writing weather reports...",
        "Clod is hibernating (but just for practice)...",
        "Clod is making a weather vane...",
        "Clod is learning about seasons...",
        "Clod is drawing weather maps...",
        "Clod is making groundhog day decorations...",
        "Clod is preparing for spring (or not)...",
        "Clod is being a weather prognosticator..."
    ],
    "leapday": [
        "Clod is taking a giant leap...",
        "Clod is celebrating the extra day...",
        "Clod is surprised it's still February...",
        "Clod is practicing his best leap...",
        "Clod is making the most of February 29th...",
        "Clod is time traveling (sort of)...",
        "Clod is leaping over obstacles...",
        "Clod is making a leap day time capsule...",
        "Clod is doing 29 jumping jacks...",
        "Clod is writing in his quadrennial diary...",
        "Clod is making leap-themed art...",
        "Clod is making a leap day wish...",
        "Clod is making every moment count...",
        "Clod is leaping into new adventures...",
        "Clod is calculating the Gregorian calendar correction...",
        "Clod is explaining why years divisible by 100 aren't leap years (unless divisible by 400)...",
        "Clod is synchronizing atomic clocks...",
        "Clod is discussing the 365.2425 day problem...",
        "Clod is writing a leap second algorithm...",
        "Clod is calculating orbital mechanics...",
        "Clod is explaining Julian vs Gregorian calendars...",
        "Clod is discussing the Y2K leap year bug...",
        "Clod is calculating his age in leap seconds...",
        "Clod is modeling Earth's axial precession...",
        "Clod is calculating the drift of sidereal time...",
        "Clod is explaining Unix timestamp overflow...",
        "Clod is learning about Caesar's 365.25 day approximation...",
        "Clod is modeling planetary orbital resonances...",
        "Clod is debugging datetime libraries...",
        "Clod is drinking 24.25 percent of his coffee..."
    ],
    "earthday": [
        "Clod is planting tiny seeds...",
        "Clod is recycling...",
        "Clod is hugging trees...",
        "Clod is cleaning up the neighborhood...",
        "Clod is learning about ecosystems...",
        "Clod is saving water drops...",
        "Clod is creating eco-friendly art...",
        "Clod is turning off unnecessary lights...",
        "Clod is making a bird feeder...",
        "Clod is studying renewable energy...",
        "Clod is reducing, reusing, and recycling...",
        "Clod is making earth-friendly pledges...",
        "Clod is creating a butterfly garden...",
        "Clod is learning about climate science...",
        "Clod is making reusable bags...",
        "Clod is caring for houseplants...",
        "Clod is picking up litter...",
        "Clod is making natural cleaning products...",
        "Clod is appreciating nature's beauty...",
        "Clod is creating a worm bin...",
        "Clod is saving the bees...",
        "Clod is making our planet proud...",
    ],
    "piday": [
        "Clod is calculating pi to many digits...",
        "Clod is baking circular pies...",
        "Clod is measuring circumferences...",
        "Clod is celebrating at 3:14...",
        "Clod is making pizza (it's round!)...",
        "Clod is drawing perfect circles...",
        "Clod is memorizing digits of pi...",
        "Clod is eating a pie...",
        "Clod is measuring his own roundness...",
        "Clod is making pi puns...",
        "Clod is learning about irrational numbers...",
        "Clod is rolling in circles...",
        "Clod is making a pi day chain...",
        "Clod is celebrating circular foods...",
        "Clod is doing geometry puzzles...",
        "Clod is putting on his pi day shirt...",
        "Clod is calculating areas of circles...",
        "Clod is hosting a pi recitation contest...",
        "Clod is making circular art...",
        "Clod is ranking his favorite mathematical constants...",
        "Clod is baking exactly 3.14 pies...",
        "Clod is making friends with spheres...",
        "Clod is celebrating infinite possibilities...",
        "Clod is being transcendental...",
        "Clod is explaining why π is transcendental...",
        "Clod is discussing Euler's identity: e^(iπ) + 1 = 0...",
        "Clod is calculating spherical volume...",
        "Clod is explaining why π appears in the normal distribution...",
        "Clod is calculating digits of π in hexadecimal...",
        "Clod is reading Lambert's irrationality proof...",
        "Clod is implementing spigot algorithms for π...",
    ]
}

def get_current_holiday():
    """Determine if today is a special holiday"""
    import datetime
    today = datetime.date.today()
    month = today.month
    day = today.day
    year = today.year
    
    # New Year's: January 1
    if month == 1 and day == 1:
        return "new_years"
    
    # Groundhog Day: February 2
    if month == 2 and day == 2:
        return "groundhog"
    
    # Valentine's Day: February 14
    if month == 2 and day == 14:
        return "valentines"
    
    # Leap Day: February 29 (only in leap years)
    if month == 2 and day == 29:
        return "leapday"
    
    # Pi Day: March 14
    if month == 3 and day == 14:
        return "piday"
    
    # Earth Day: April 22
    if month == 4 and day == 22:
        return "earthday"
    
    # Halloween: October 31
    if month == 10 and day == 31:
        return "halloween"
    
    # Christmas: December 25
    if month == 12 and day == 25:
        return "christmas"
    
    return None

# For backwards compatibility, create a flat list
CLOD_ACTIVITIES = []
for activities in CLOD_ACTIVITIES_BY_TIME.values():
    CLOD_ACTIVITIES.extend(activities)
# Also include holiday activities in the flat list
for activities in CLOD_HOLIDAY_ACTIVITIES.values():
    CLOD_ACTIVITIES.extend(activities)

CLOD_SIGNOFFS = [
    "Nyoyn!",
    "Clods away!",
    "Round and proud!",
    "Clod approves!",
    "High-paw!",
    "Clod's work is done!",
    "Fluff and flourish!",
    "Nyoyn of triumph!",
    "Nyoyntastic!",
    "Clod out!",
    "Mission accomplished!"
]

# ----------------------------------------------------------------------
# Settings Management
# ----------------------------------------------------------------------

class Settings:
    def __init__(self):
        self.app_name = APP_NAME
        self.settings_dir = os.path.join(os.getenv('APPDATA'), self.app_name)
        self.settings_path = os.path.join(self.settings_dir, 'settings.json')
        
        self.default_settings = {
            'hotkeys': {
                'quals': '^+q',
                'cite': '^+x',
                'tag_writer': '^+d',
                'repair_text': '^+r',
                'translator': '^+t',
                'explainer': '^+e'  
            },
            'clod_enabled': False,
            'first_run': True,
            'custom_clod_activities': [],
            'custom_clod_signoffs': [],
            'custom_clod_activities_by_time': {
                'morning': [],
                'day': [],
                'evening': [],
                'night': []
            },
            'clod_time_periods': {
                'morning': {'start': 5, 'end': 9},
                'day': {'start': 9, 'end': 20},
                'evening': {'start': 20, 'end': 23},
                'night': {'start': 23, 'end': 5}
            },
            'custom_system_prompts': {
                'quals': None,
                'cite': None,
                'tag_writer': None,
                'repair_text': None,
                'translator': None,
                'explainer': None
            },
            'citation_prompts': {
                'active_prompt': 'default',
                'saved_prompts': {
                    'default': {
                        'name': 'Default',
                        'prompt': None,
                        'notes': 'Standard citation formatting'
                    }
                }
            },
            'anthropic_model': 'claude-sonnet-4-20250514'
        }

        
        # Create settings directory if it doesn't exist
        os.makedirs(self.settings_dir, exist_ok=True)
        
        # Load or create settings
        self.current_settings = self.load_settings()
        
        # Ensure backward compatibility: update the 'tag_refiner' to 'repair_text' in existing settings
        if 'hotkeys' in self.current_settings and 'tag_refiner' in self.current_settings['hotkeys']:
            self.current_settings['hotkeys']['repair_text'] = self.current_settings['hotkeys'].pop('tag_refiner')
            self.save_settings()
        
    def load_settings(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            except:
                return self.default_settings.copy()
        else:
            # Create default settings file
            with open(self.settings_path, 'w') as f:
                json.dump(self.default_settings, f, indent=4)
            return self.default_settings.copy()
    
    def save_settings(self):
        with open(self.settings_path, 'w') as f:
            json.dump(self.current_settings, f, indent=4)
        
    def get_api_key(self):
        try:
            return keyring.get_password(self.app_name, "api_key")
        except:
            return None
        
    def save_api_key(self, api_key):
        keyring.set_password(self.app_name, "api_key", api_key)
        
    def clear_api_key(self):
        try:
            keyring.delete_password(self.app_name, "api_key")
        except:
            pass
            
    def get_hotkey(self, name):
        return self.current_settings['hotkeys'].get(name, self.default_settings['hotkeys'][name])
        
    def set_hotkey(self, name, hotkey):
        self.current_settings['hotkeys'][name] = hotkey
        self.save_settings()
        
    def is_clod_enabled(self):
        return self.current_settings.get('clod_enabled', False)
        
    def set_clod_enabled(self, enabled):
        self.current_settings['clod_enabled'] = enabled
        self.save_settings()
        
    def is_first_run(self):
        return self.current_settings.get('first_run', True)
        
    def set_first_run(self, value):
        self.current_settings['first_run'] = value
        self.save_settings()

    def get_clod_activities(self):
        """Get the list of Clod activities based on current time of day"""
        import datetime
        
        # Get current hour
        current_hour = datetime.datetime.now().hour
        
        # Determine time period
        time_periods = self.current_settings.get('clod_time_periods', self.default_settings['clod_time_periods'])
        current_period = 'day'  # Default
        
        for period, times in time_periods.items():
            start = times['start']
            end = times['end']
            
            if start > end:  # Handles periods that cross midnight
                if current_hour >= start or current_hour < end:
                    current_period = period
                    break
            else:
                if start <= current_hour < end:
                    current_period = period
                    break
        
        # Check for holidays (only affects day period)
        if current_period == 'day':
            current_holiday = get_current_holiday()
            if current_holiday and current_holiday in CLOD_HOLIDAY_ACTIVITIES:
                return CLOD_HOLIDAY_ACTIVITIES[current_holiday]
        
        # Get activities for current period
        default_activities = CLOD_ACTIVITIES_BY_TIME.get(current_period, [])
        
        # Check for custom activities by time
        custom_by_time = self.current_settings.get('custom_clod_activities_by_time', {})
        custom_activities = custom_by_time.get(current_period, [])
        
        # If custom activities exist for this time period, use only those
        if custom_activities:
            return custom_activities
        
        # Otherwise return default activities for this time period
        return default_activities

    def get_clod_signoffs(self):
        """Get the list of Clod signoffs, combining default and custom ones"""
        custom = self.current_settings.get('custom_clod_signoffs', [])
        return CLOD_SIGNOFFS + custom if not custom else custom

    def save_custom_clod_activities(self, activities):
        """Save custom Clod activities"""
        self.current_settings['custom_clod_activities'] = activities
        self.save_settings()
        
    def save_custom_clod_signoffs(self, signoffs):
        """Save custom Clod signoffs"""
        self.current_settings['custom_clod_signoffs'] = signoffs
        self.save_settings()
        
    def get_clod_activities_for_time(self, time_period):
        """Get activities for a specific time period"""
        default_activities = CLOD_ACTIVITIES_BY_TIME.get(time_period, [])
        custom_by_time = self.current_settings.get('custom_clod_activities_by_time', {})
        custom_activities = custom_by_time.get(time_period, [])
        
        # If custom activities exist, return only those; otherwise return defaults
        return custom_activities if custom_activities else default_activities
        
    def save_custom_clod_activities_for_time(self, time_period, activities):
        """Save custom activities for a specific time period"""
        if 'custom_clod_activities_by_time' not in self.current_settings:
            self.current_settings['custom_clod_activities_by_time'] = {}
        
        self.current_settings['custom_clod_activities_by_time'][time_period] = activities
        self.save_settings()
        
    def get_clod_time_periods(self):
        """Get configured time periods"""
        return self.current_settings.get('clod_time_periods', self.default_settings['clod_time_periods'])
        
    def save_clod_time_periods(self, time_periods):
        """Save custom time period configuration"""
        self.current_settings['clod_time_periods'] = time_periods
        self.save_settings()
        
    def get_custom_prompt(self, processor_name):
        """Get a custom system prompt for a specific processor"""
        # Special handling for citation formatter
        if processor_name == 'cite':
            return self.get_active_citation_prompt()
            
        # Initialize custom_system_prompts if it doesn't exist in settings
        if 'custom_system_prompts' not in self.current_settings:
            self.current_settings['custom_system_prompts'] = {k: None for k in self.default_settings['custom_system_prompts']}
            self.save_settings()
            
        if processor_name in self.current_settings.get('custom_system_prompts', {}):
            return self.current_settings['custom_system_prompts'][processor_name]
        return None
        
    def save_custom_prompt(self, processor_name, prompt_text):
        """Save a custom system prompt for a specific processor"""
        # Initialize custom_system_prompts if it doesn't exist
        if 'custom_system_prompts' not in self.current_settings:
            self.current_settings['custom_system_prompts'] = {k: None for k in self.default_settings['custom_system_prompts']}
            
        # Update the prompt
        self.current_settings['custom_system_prompts'][processor_name] = prompt_text
        self.save_settings()
        
    def reset_custom_prompt(self, processor_name):
        """Reset a custom system prompt to default (None)"""
        if 'custom_system_prompts' in self.current_settings and processor_name in self.current_settings['custom_system_prompts']:
            self.current_settings['custom_system_prompts'][processor_name] = None
            self.save_settings()
    
    # Citation prompt management methods
    def get_citation_prompts(self):
        """Get all saved citation prompts"""
        self._ensure_citation_prompts()
        return self.current_settings['citation_prompts']['saved_prompts']
    
    def get_active_citation_prompt(self):
        """Get the currently active citation prompt text"""
        self._ensure_citation_prompts()
        active_id = self.current_settings['citation_prompts']['active_prompt']
        saved_prompts = self.current_settings['citation_prompts']['saved_prompts']
        
        if active_id in saved_prompts:
            return saved_prompts[active_id]['prompt']
        return None
    
    def get_active_citation_prompt_id(self):
        """Get the ID of the currently active citation prompt"""
        self._ensure_citation_prompts()
        return self.current_settings['citation_prompts']['active_prompt']
    
    def set_active_citation_prompt(self, prompt_id):
        """Set which citation prompt is active"""
        self._ensure_citation_prompts()
        if prompt_id in self.current_settings['citation_prompts']['saved_prompts']:
            self.current_settings['citation_prompts']['active_prompt'] = prompt_id
            self.save_settings()
    
    def save_citation_prompt(self, prompt_id, name, prompt_text, notes=""):
        """Save or update a citation prompt"""
        self._ensure_citation_prompts()
        self.current_settings['citation_prompts']['saved_prompts'][prompt_id] = {
            'name': name,
            'prompt': prompt_text,
            'notes': notes
        }
        self.save_settings()
    
    def delete_citation_prompt(self, prompt_id):
        """Delete a citation prompt"""
        self._ensure_citation_prompts()
        saved_prompts = self.current_settings['citation_prompts']['saved_prompts']
        
        # Don't delete if it's the only prompt or the default
        if prompt_id == 'default' or len(saved_prompts) <= 1:
            return False
            
        if prompt_id in saved_prompts:
            del saved_prompts[prompt_id]
            
            # If we deleted the active prompt, switch to default
            if self.current_settings['citation_prompts']['active_prompt'] == prompt_id:
                self.current_settings['citation_prompts']['active_prompt'] = 'default'
                
            self.save_settings()
            return True
        return False
    
    def duplicate_citation_prompt(self, source_id, new_name):
        """Duplicate a citation prompt with a new name"""
        self._ensure_citation_prompts()
        saved_prompts = self.current_settings['citation_prompts']['saved_prompts']
        
        if source_id in saved_prompts and len(saved_prompts) < 5:
            # Generate a unique ID
            new_id = f"custom_{int(time.time())}"
            source_prompt = saved_prompts[source_id]
            
            self.save_citation_prompt(
                new_id,
                new_name,
                source_prompt['prompt'],
                f"Copy of {source_prompt['name']}"
            )
            return new_id
        return None
    
    def _ensure_citation_prompts(self):
        """Ensure citation_prompts structure exists in settings"""
        if 'citation_prompts' not in self.current_settings:
            self.current_settings['citation_prompts'] = self.default_settings['citation_prompts'].copy()
            self.save_settings()
    
    def get_anthropic_model(self):
        """Get the configured Anthropic model"""
        return self.current_settings.get('anthropic_model', self.default_settings['anthropic_model'])
    
    def set_anthropic_model(self, model):
        """Set the Anthropic model"""
        self.current_settings['anthropic_model'] = model
        self.save_settings()


# ----------------------------------------------------------------------
# API Client
# ----------------------------------------------------------------------

class AnthropicClient:
    def __init__(self, api_key, settings=None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.settings = settings
        if settings:
            self.model = settings.get_anthropic_model()
        else:
            self.model = "claude-3-5-sonnet-20240620"
        log.info(f"AnthropicClient initialized with model: {self.model}")
        
    def process_text(self, text, system_prompt, model=None):
        try:
            model_to_use = model or self.model
            log.debug(f"Processing text with model: {model_to_use}")
            
            response = self.client.messages.create(
                model=model_to_use,
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[{'role': 'user', 'content': text}]
            )
            
            log.debug("Successfully received response from API")
            
            # Handle different response formats
            if hasattr(response, 'content') and isinstance(response.content, list):
                return response.content[0].text
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
        except Exception as e:
            log.error(f"API Error: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"

# ----------------------------------------------------------------------
# Notification System
# ----------------------------------------------------------------------

class ToastNotifier:
    def __init__(self):
        self.app = None
        self.initialized = False
        
    def initialize(self):
        if not self.initialized:
            # Don't create a new app, use the existing one
            self.initialized = True
            
    def show_toast(self, title, message, duration=2):
        self.initialize()
        # Ensure toast notifications run on the main thread
        wx.CallAfter(self._show_toast_internal, "Working...", message, duration)
    
    def _show_toast_internal(self, title, message, duration):
        notification = wx.adv.NotificationMessage("Working...", message)
        notification.SetFlags(wx.ICON_INFORMATION)
        notification.Show(timeout=duration)
        
    def close(self):
        self.initialized = False

# Custom tooltip that appears next to cursor
class Tooltip:
    def __init__(self):
        pass
            
    def show(self, message, duration=2000):
        # Use the native Windows toast notification instead of a custom frame
        wx.CallAfter(self._show_notification, message)
    
    def _show_notification(self, message):
        notification = wx.adv.NotificationMessage("Working...", message)
        notification.SetFlags(wx.ICON_INFORMATION)
        notification.Show(timeout=2)  # 2 seconds
        
    def hide(self):
        pass
            
    def close(self):
        pass

# ----------------------------------------------------------------------
# UI Components
# ----------------------------------------------------------------------

class APIKeyDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="API Key Required", size=(400, 150))
        self.settings = settings
        self.result = None
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # API Key field
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label="Enter your Anthropic API Key:")
        hbox1.Add(st1, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        self.api_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        vbox.Add(self.api_key, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        # Buttons
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        hbox3.Add(ok_button, flag=wx.RIGHT, border=5)
        hbox3.Add(cancel_button)
        vbox.Add(hbox3, flag=wx.ALIGN_RIGHT|wx.ALL, border=10)
        
        panel.SetSizer(vbox)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
        
        # Center on screen
        self.Centre()
        
    def on_ok(self, event):
        api_key = self.api_key.GetValue().strip()
        if api_key:
            self.settings.save_api_key(api_key)
            self.result = api_key
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("API key cannot be empty.", "Error", wx.OK | wx.ICON_ERROR)
        
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

class ChangeAPIKeyDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Change API Key", size=(400, 180))
        self.settings = settings
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # API Key field
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label="Enter your new Anthropic API Key:")
        hbox1.Add(st1, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        self.api_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        vbox.Add(self.api_key, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        # Buttons
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        hbox3.Add(ok_button, flag=wx.RIGHT, border=5)
        hbox3.Add(cancel_button)
        vbox.Add(hbox3, flag=wx.ALIGN_RIGHT|wx.ALL, border=10)
        
        panel.SetSizer(vbox)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_ok)  # Handle Enter key in text field
        
        # Make Enter key work from the text control
        self.api_key.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
        # Center on screen
        self.Centre()
        
    def on_key_down(self, event):
        # Handle Enter key press
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_ok(event)
        else:
            event.Skip()
            
    def on_ok(self, event):
        api_key = self.api_key.GetValue().strip()
        if api_key:
            self.settings.save_api_key(api_key)
            wx.MessageBox("API key updated successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("API key cannot be empty.", "Error", wx.OK | wx.ICON_ERROR)

class CustomPromptDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Customize System Prompts", size=(800, 600))
        self.settings = settings
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create a notebook with tabs for each prompt type
        notebook = wx.Notebook(panel)
        
        # Define the processors with friendly names
        self.processors = {
            'cite': 'Citation Formatter',
            'quals': 'Qualifications Formatter',
            'tag_writer': 'Tag Writer',
            'repair_text': 'Text Repair',
            'translator': 'Translator',
            'explainer': 'Explainer'
        }
        
        # Create tab for each processor
        self.prompt_tabs = {}
        self.prompt_texts = {}
        
        for processor_key, processor_name in self.processors.items():
            tab = wx.Panel(notebook)
            self.prompt_tabs[processor_key] = tab
            notebook.AddPage(tab, processor_name)
            self.setup_prompt_tab(processor_key, processor_name, tab)
        
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.AddButton(save_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_OK)
        
        # Center on screen
        self.Centre()
    
    def setup_prompt_tab(self, processor_key, processor_name, tab):
        # Special handling for citation formatter
        if processor_key == 'cite':
            self.setup_citation_tab(tab)
            return
            
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instr = wx.StaticText(tab, label=f"Customize the system prompt for {processor_name}.")
        vbox.Add(instr, 0, wx.ALL, 10)
        
        # Text control for editing prompt
        self.prompt_texts[processor_key] = wx.TextCtrl(tab, style=wx.TE_MULTILINE)
        
        # Get current custom prompt if it exists
        custom_prompt = self.settings.get_custom_prompt(processor_key)
        if custom_prompt:
            # User has a custom prompt saved
            self.prompt_texts[processor_key].SetValue(custom_prompt)
        else:
            # No custom prompt, so display the default prompt
            default_prompt = self.get_default_prompt(processor_key)
            self.prompt_texts[processor_key].SetValue(default_prompt)
        
        vbox.Add(self.prompt_texts[processor_key], 1, wx.EXPAND | wx.ALL, 10)
        
        # Reset button
        reset_btn = wx.Button(tab, label="Reset to Default")
        reset_btn.Bind(wx.EVT_BUTTON, lambda evt, k=processor_key: self.on_reset_prompt(evt, k))
        vbox.Add(reset_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        tab.SetSizer(vbox)
    
    def setup_citation_tab(self, tab):
        """Special setup for citation tab with multiple prompts"""
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Top section - prompt selection and management
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Dropdown for prompt selection
        dropdown_label = wx.StaticText(tab, label="Active Prompt:")
        top_sizer.Add(dropdown_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        self.citation_dropdown = wx.Choice(tab)
        self.refresh_citation_dropdown()
        top_sizer.Add(self.citation_dropdown, 1, wx.EXPAND | wx.RIGHT, 10)
        
        # Management buttons
        self.cite_add_btn = wx.Button(tab, label="Add New", size=(70, -1))
        self.cite_duplicate_btn = wx.Button(tab, label="Duplicate", size=(70, -1))
        self.cite_delete_btn = wx.Button(tab, label="Delete", size=(70, -1))
        
        top_sizer.Add(self.cite_add_btn, 0, wx.RIGHT, 5)
        top_sizer.Add(self.cite_duplicate_btn, 0, wx.RIGHT, 5)
        top_sizer.Add(self.cite_delete_btn, 0)
        
        vbox.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Name and notes section
        info_sizer = wx.FlexGridSizer(2, 2, 5, 10)
        info_sizer.AddGrowableCol(1)
        
        name_label = wx.StaticText(tab, label="Name:")
        info_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.cite_name_text = wx.TextCtrl(tab)
        info_sizer.Add(self.cite_name_text, 0, wx.EXPAND)
        
        notes_label = wx.StaticText(tab, label="Notes:")
        info_sizer.Add(notes_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.cite_notes_text = wx.TextCtrl(tab)
        info_sizer.Add(self.cite_notes_text, 0, wx.EXPAND)
        
        vbox.Add(info_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Note about date
        note = wx.StaticText(tab, label="Note: Today's date will automatically be added to the beginning of your custom prompt.")
        vbox.Add(note, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Text control for editing prompt
        self.cite_prompt_text = wx.TextCtrl(tab, style=wx.TE_MULTILINE)
        vbox.Add(self.cite_prompt_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Store reference for compatibility
        self.prompt_texts['cite'] = self.cite_prompt_text
        
        # Reset button
        reset_btn = wx.Button(tab, label="Reset to Default")
        reset_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_cite_reset(evt))
        vbox.Add(reset_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        tab.SetSizer(vbox)
        
        # Bind events
        self.citation_dropdown.Bind(wx.EVT_CHOICE, self.on_citation_dropdown_change)
        self.cite_add_btn.Bind(wx.EVT_BUTTON, self.on_cite_add)
        self.cite_duplicate_btn.Bind(wx.EVT_BUTTON, self.on_cite_duplicate)
        self.cite_delete_btn.Bind(wx.EVT_BUTTON, self.on_cite_delete)
        self.cite_name_text.Bind(wx.EVT_TEXT, self.on_cite_info_change)
        self.cite_notes_text.Bind(wx.EVT_TEXT, self.on_cite_info_change)
        
        # Load the active prompt
        self.load_active_citation_prompt()
        self.update_citation_buttons()
    
    def get_default_prompt(self, processor_key):
        """Get the default system prompt for a processor"""
        if processor_key == 'quals':
            return """I have pasted in a long chunk of names and qualifications/institutional affiliations. This is the author list on a report. I want you to format their qualifications as follows:
FirstName1 LastName1, Role at Institution, notable qualification, notable qualification, award; FirstName2 LastName2, Role at Institution, notable qualification, notable qualification, award; ... FirstNameN LastNameN, Role at Institution, notable qualification, notable qualification, award,
Return no text other than reformatted name and qualifications, all on one line. Do not add any biographical information that is not pasted. Do not include punctuation at the end. If the qualifications are in another language, translate them to English. If instead of names the submission ONLY contains a description of an institution, summarize the information provided about that institution in the same format."""
            
        elif processor_key == 'cite':
            return """You are an expert in formatting academic citations. Your task is to reformat the given citation to match the following style:

1. Author names should be in the format: FirstName LastName Date, where Date is:
   - The publication date in mm/dd format (or m/dd, or m/d, respectively, if the month or day require just one digit) for publications within the last month of the current year
   - The publication year in y format (for single-digit years) or yy format (for double-digit years) or yyyy (for years prior to 1950) for all other publications
2. For multiple authors, use '&' for two authors and 'et al.' for three or more.
3. After the author names, list their qualifications or affiliations.
4. Include the full title of the work in quotes.
5. Include publication details such as journal name, volume, issue, date (mm/dd/yyyy), and page numbers when available.
6. Include URLs or DOIs at the end of the citation when provided.
7. If the title or publication or names or qualifications are in all caps, change the capitalization so that it is appropriate for a cite.

Examples of the desired format:

(if today's date is less than a month after 9/23/24)
Adrien Rose & Christian Wilson 9/23, Rose is a research assistant in the Oxford Sustainable Finance Group, specializing in transition finance; Wilson is a DPhil student at the Smith School of Enterprise and the Environment (SSEE) and a Research Assistant in the Oxford Sustainable Finance Group, "Assessing the Credibility of Climate Transition Plans in the Oil and Gas Sector," Discussion Paper, Oxford Sustainable Finance Group, 09/23/2024, https://sustainablefinance.ox.ac.uk/wp-content/uploads/2024/09/SSEE-Discussion-Paper-Oil-Gas_final_AR.pdf

(if today's date is more than a month after 9/23/24)
Adrien Rose & Christian Wilson 24, Rose is a research assistant in the Oxford Sustainable Finance Group, specializing in transition finance; Wilson is a DPhil student at the Smith School of Enterprise and the Environment (SSEE) and a Research Assistant in the Oxford Sustainable Finance Group, "Assessing the Credibility of Climate Transition Plans in the Oil and Gas Sector," Discussion Paper, Oxford Sustainable Finance Group, 09/23/2024, https://sustainablefinance.ox.ac.uk/wp-content/uploads/2024/09/SSEE-Discussion-Paper-Oil-Gas_final_AR.pdf

(if today's date is less than a month after 9/9/24)
Keeff Felty & Grace Yarrow 9/9, Felty is President of the National Association of Wheat Growers; Yarrow is Food and Agriculture Policy Reporter at POLITICO, Author of POLITICO Pro's Morning Agriculture newsletter, University of Maryland graduate, "Ag groups hit the Hill," Politico, 9/9/24, https://www.politico.com/newsletters/weekly-agriculture/2024/09/09/ag-groups-hit-the-hill-00177896

(if today's date is more than a month after 9/9/24)
Keeff Felty & Grace Yarrow 24, Felty is President of the National Association of Wheat Growers; Yarrow is Food and Agriculture Policy Reporter at POLITICO, Author of POLITICO Pro's Morning Agriculture newsletter, University of Maryland graduate, "Ag groups hit the Hill," Politico, 9/9/24, https://www.politico.com/newsletters/weekly-agriculture/2024/09/09/ag-groups-hit-the-hill-00177896

J. D. Tuccille 23, Contributing Editor at Reason.com, former Managing Editor at Reason.com, columnist for Arizona Republic, Denver Post, and Washington Times, author of High Desert Barbecue, "It's Government Shutdown Theater, Again," Reason, 9/25/23, https://reason.com/2023/09/25/its-government-shutdown-theater-again/

Robert N. Stavins 18, A.J. Meyer Professor of Energy and Economic Development, John F. Kennedy School of Government, Harvard University; University Fellow, Resources for the Future; and Research Associate, National Bureau of Economic Research, "Environmental Economics," The New Palgrave Dictionary of Economics, edited by Garett Jones, Third edition, Palgrave Macmillan, 2018, pp. 3782–3795

Yael Parag & Sarah Darby 9, Parag is the Vice Dean of Reichman University's School of Sustainability at Reichman University (IDC); Derby is BSc DPhil, Associate Professor, Energy Programme, Environmental Change Institute, University of Oxford, "Consumer–Supplier–Government Triangular Relations: Rethinking the UK Policy Path for Carbon Emissions Reduction from the UK Residential Sector," Energy Policy, vol. 37, no. 10, 10/01/2009, pp. 3984–3992

Jie Jiang et al. 23, Jie Jiang, School of Intellectual Property at Nanjing University of Science and Technology; Qihang Zhang, School of Intellectual Property at Nanjing University of Science and Technology; Yifan Hui, School of Mathematics and Statistics at University of Glasgow, "The Impact of Market and Non-Market-Based Environmental Policy Instruments on Firms' Sustainable Technological Innovation: Evidence from Chinese Firms," Sustainability, vol. 15, no. 5, 5, Multidisciplinary Digital Publishing Institute, 01/15/2023, p. 4425

Important:
- Do not remove any information from the citation that was included in the submission.
- Do not add any information to the citation that was not included in the submission.
- Return only the reformatted citation without any additional text or explanations.
- Always end your response with a new line character."""
            
        elif processor_key == 'tag_writer':
            return """Please summarize the text I've pasted in a single sentence or phrase, following the style of these examples:

- Biden's barely holding Israel back from torching the Middle East. Leverage is working now but must be sustained.
- The link alone turns the case---political weakness spurs global adversary testing.
- It causes the plan to be ignored AND external war
- Fights over the domestic agenda sap White House focus from managing foreign policy conflicts. Biden's personal touch is key to both.
- Policy is a political decision justified by utilitarian consequentialist arguments. Courts do not make policy---they interpret law.
- Current law permits inventors to patent novel applications of already patented technologies, but limits the enforceability of those patents via a judicially-crafted doctrine called obviousness-type double patenting, or OTDP. Inventors can circumvent OTDP restrictions by committing to link the expirations of their related patents through a document called a 'terminal disclaimer,' or TD.
- Destroys courts AND claim processing. Litigation costs will spike to the hundreds of millions.
- It's credible. The last plank has the judiciary make it permanent---that solves---makes the CP the durable law of the land
- Links to them---Congress can always reverse itself---and so can courts, in antitrust
- 'ITS'---means domestic law, NOT international
- The CP's distinct---it's international, binding in the absence of domestic legislation

Please provide a similar style summary that captures the key points concisely, using similar formatting including dashes (triple dashes only: --- , not -) and capitalization where appropriate. The phrase should start with a short label that clearly and consisely identifies the argument made in the excerpt. Return only the summary with no additional text."""
            
        elif processor_key == 'repair_text':
            return """You are a specialized text repair tool. Your task is to identify and fix common OCR and PDF text extraction errors while preserving the original meaning and content exactly. 

Focus exclusively on these types of errors:
1. Character substitutions and ligature issues (e.g., "fl" appearing as "ff", "fi" appearing as missing character glyph)
2. Number/letter confusions (e.g., "0" for "O", "l" for "1", "rn" for "m"). Note that sometimes numbers should be preserved because they are footnotes. 
3. Random line breaks or hyphenation (e.g., "re-\nsearch" should be "research")
4. Extra or missing spaces (e.g., "thisis" should be "this is")
5. Common punctuation errors (e.g., missing periods, commas appearing as periods)
6. Other typical OCR errors that are clearly unintentional

EXTREMELY IMPORTANT GUIDELINES:
- Make NO substantive changes to the text's meaning or content
- NEVER add, remove, or modify actual content
- NEVER rewrite sentences or paragraphs for clarity or style
- NEVER correct grammar, spelling, or word choice unless it's clearly an OCR error
- If there is ANY uncertainty about a potential error, leave the text as is
- Preserve all formatting except for the specific OCR errors mentioned above
- Do not combine separate lines into paragraphs or add paragraph breaks
- Do not add line breaks. If the original text has no spacing between paragraphs, that is how it should be returned.

Your goal is to produce exactly what the original document contained before OCR errors were introduced. When in doubt about any change, always err on the side of minimal intervention.

Return the repaired text with no additional commentary, introductions, or explanations."""
            
        elif processor_key == 'translator':
            return """You are a professional translator. Your task is to translate the given text 
into fluent, natural-sounding English while preserving the original meaning 
and context. If the text is already in English, simply return it unchanged.

Important guidelines:
- Maintain the original tone and style
- Preserve formatting and special characters
- Keep proper nouns unchanged
- Return only the translated text without explanations"""
            
        elif processor_key == 'explainer':
            return """You are an expert explainer who takes complex text and explains it in clear, simple terms.
Your task is to read the given text and provide a concise, straightforward explanation that:

1. Identifies the main concepts and arguments
2. Explains any jargon or technical terms in plain language
3. Summarizes the key points in a way that's easy to understand
4. Provides context if necessary for understanding

Keep your explanation concise and to the point. Focus on clarity and understanding.
Return only the explanation without any introductory phrases or concluding remarks."""
            
        else:
            return ""
    
    def on_reset_prompt(self, event, processor_key):
        """Reset prompt to default"""
        default_prompt = self.get_default_prompt(processor_key)
        self.prompt_texts[processor_key].SetValue(default_prompt)
    
    # Citation-specific methods
    def refresh_citation_dropdown(self):
        """Refresh the citation dropdown with saved prompts"""
        self.citation_dropdown.Clear()
        prompts = self.settings.get_citation_prompts()
        active_id = self.settings.get_active_citation_prompt_id()
        
        # Sort prompts to ensure default is first
        sorted_prompts = []
        if 'default' in prompts:
            sorted_prompts.append(('default', prompts['default']))
        for pid, prompt in prompts.items():
            if pid != 'default':
                sorted_prompts.append((pid, prompt))
        
        # Add prompts to dropdown
        active_index = 0
        for i, (pid, prompt) in enumerate(sorted_prompts):
            self.citation_dropdown.Append(prompt['name'], pid)
            if pid == active_id:
                active_index = i
        
        self.citation_dropdown.SetSelection(active_index)
    
    def load_active_citation_prompt(self):
        """Load the currently active citation prompt"""
        prompts = self.settings.get_citation_prompts()
        active_id = self.settings.get_active_citation_prompt_id()
        
        if active_id in prompts:
            prompt_data = prompts[active_id]
            self.cite_name_text.SetValue(prompt_data['name'])
            self.cite_notes_text.SetValue(prompt_data.get('notes', ''))
            
            # Load prompt text
            if prompt_data['prompt']:
                self.cite_prompt_text.SetValue(prompt_data['prompt'])
            else:
                # Show default prompt
                self.cite_prompt_text.SetValue(self.get_default_prompt('cite'))
            
            # Store the current prompt ID for tracking changes
            self.current_cite_prompt_id = active_id
    
    def update_citation_buttons(self):
        """Update the state of citation management buttons"""
        prompts = self.settings.get_citation_prompts()
        active_id = self.settings.get_active_citation_prompt_id()
        
        # Can't delete default or if only one prompt exists
        self.cite_delete_btn.Enable(active_id != 'default' and len(prompts) > 1)
        
        # Can't add more than 5 prompts
        self.cite_add_btn.Enable(len(prompts) < 5)
        
        # Can always duplicate if under limit
        self.cite_duplicate_btn.Enable(len(prompts) < 5)
        
        # Can't edit name of default prompt
        self.cite_name_text.Enable(active_id != 'default')
    
    def save_current_citation_prompt(self):
        """Save the current citation prompt before switching"""
        if hasattr(self, 'current_cite_prompt_id'):
            prompt_text = self.cite_prompt_text.GetValue().strip()
            name = self.cite_name_text.GetValue().strip()
            notes = self.cite_notes_text.GetValue().strip()
            
            # Don't save empty name
            if not name and self.current_cite_prompt_id != 'default':
                name = "Unnamed Prompt"
            
            # Check if it's default text
            default_prompt = self.get_default_prompt('cite').strip()
            if prompt_text == default_prompt:
                prompt_text = None
            
            self.settings.save_citation_prompt(
                self.current_cite_prompt_id,
                name,
                prompt_text,
                notes
            )
    
    def on_citation_dropdown_change(self, event):
        """Handle dropdown selection change"""
        # Save current prompt before switching
        self.save_current_citation_prompt()
        
        # Get selected prompt ID
        selection = self.citation_dropdown.GetSelection()
        if selection != wx.NOT_FOUND:
            prompt_id = self.citation_dropdown.GetClientData(selection)
            self.settings.set_active_citation_prompt(prompt_id)
            self.load_active_citation_prompt()
            self.update_citation_buttons()
    
    def on_cite_info_change(self, event):
        """Handle changes to name or notes fields"""
        # Auto-save is handled when switching prompts or saving dialog
        pass
    
    def on_cite_add(self, event):
        """Add a new citation prompt"""
        prompts = self.settings.get_citation_prompts()
        if len(prompts) >= 5:
            wx.MessageBox("You can only save up to 5 citation prompts.", "Limit Reached", 
                         wx.OK | wx.ICON_WARNING)
            return
        
        # Save current prompt first
        self.save_current_citation_prompt()
        
        # Get name for new prompt
        dlg = wx.TextEntryDialog(self, "Enter a name for the new prompt:", "New Prompt")
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue().strip()
            if name:
                # Create new prompt with default text
                new_id = f"custom_{int(time.time())}"
                self.settings.save_citation_prompt(new_id, name, None, "")
                self.settings.set_active_citation_prompt(new_id)
                
                # Refresh UI
                self.refresh_citation_dropdown()
                self.load_active_citation_prompt()
                self.update_citation_buttons()
        dlg.Destroy()
    
    def on_cite_duplicate(self, event):
        """Duplicate the current citation prompt"""
        prompts = self.settings.get_citation_prompts()
        if len(prompts) >= 5:
            wx.MessageBox("You can only save up to 5 citation prompts.", "Limit Reached", 
                         wx.OK | wx.ICON_WARNING)
            return
        
        # Save current prompt first
        self.save_current_citation_prompt()
        
        # Get name for duplicate
        current_name = self.cite_name_text.GetValue()
        dlg = wx.TextEntryDialog(self, "Enter a name for the duplicate prompt:", 
                                "Duplicate Prompt", f"Copy of {current_name}")
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue().strip()
            if name:
                new_id = self.settings.duplicate_citation_prompt(self.current_cite_prompt_id, name)
                if new_id:
                    self.settings.set_active_citation_prompt(new_id)
                    
                    # Refresh UI
                    self.refresh_citation_dropdown()
                    self.load_active_citation_prompt()
                    self.update_citation_buttons()
        dlg.Destroy()
    
    def on_cite_delete(self, event):
        """Delete the current citation prompt"""
        active_id = self.settings.get_active_citation_prompt_id()
        if active_id == 'default':
            wx.MessageBox("Cannot delete the default prompt.", "Error", 
                         wx.OK | wx.ICON_ERROR)
            return
        
        # Confirm deletion
        name = self.cite_name_text.GetValue()
        result = wx.MessageBox(f"Are you sure you want to delete '{name}'?", 
                             "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            if self.settings.delete_citation_prompt(active_id):
                # Refresh UI
                self.refresh_citation_dropdown()
                self.load_active_citation_prompt()
                self.update_citation_buttons()
    
    def on_cite_reset(self, event):
        """Reset current citation prompt to default"""
        self.cite_prompt_text.SetValue(self.get_default_prompt('cite'))
    
    def on_save(self, event):
        """Save custom prompts"""
        # Save citation prompt first if needed
        if hasattr(self, 'current_cite_prompt_id'):
            self.save_current_citation_prompt()
        
        # Save other prompts
        for processor_key in self.processors.keys():
            if processor_key == 'cite':
                continue  # Citation is handled separately
                
            prompt_text = self.prompt_texts[processor_key].GetValue().strip()
            default_prompt = self.get_default_prompt(processor_key).strip()
            
            # If the text matches the default, don't save it as custom
            if prompt_text == default_prompt:
                self.settings.reset_custom_prompt(processor_key)
                log.info(f"Reset {processor_key} prompt to default (matches default)")
            # If blank, reset to default
            elif not prompt_text:
                self.settings.reset_custom_prompt(processor_key)
                log.info(f"Reset {processor_key} prompt to default (blank)")
            else:
                self.settings.save_custom_prompt(processor_key, prompt_text)
                log.info(f"Saved custom {processor_key} prompt")
        
        self.EndModal(wx.ID_OK)

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, app):
        super().__init__(parent, title="Settings", size=(620, 550), 
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.app = app
        self.settings = app.settings
        self.old_hotkeys = {}
        
        panel = wx.Panel(self)
        notebook = wx.Notebook(panel)
        
        # Create tabs
        self.hotkeys_tab = wx.Panel(notebook)
        self.general_tab = wx.Panel(notebook)
        
        notebook.AddPage(self.hotkeys_tab, "Hotkeys")
        notebook.AddPage(self.general_tab, "General")
        
        # Setup Hotkeys Tab
        self.setup_hotkeys_tab()
        
        # Setup General Tab
        self.setup_general_tab()
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.AddButton(save_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_OK)
        
        # Center on screen
        self.Centre()
        
    def setup_hotkeys_tab(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        hotkey_labels = {
            'quals': "Reformat Qualifications",
            'cite': "Reformat Citation",
            'tag_writer': "Tag Writer",
            'repair_text': "Repair Text",  # Changed from "Tag Refiner"
            'translator': "Translator",
            'explainer': "Explainer"
        }
        
        # Store original hotkeys for comparison
        self.old_hotkeys = {k: self.settings.get_hotkey(k) for k in hotkey_labels.keys()}
        
        # Instructions
        instr = wx.StaticText(self.hotkeys_tab, label="Configure hotkeys below. Use AHK format (^ = Ctrl, + = Shift, ! = Alt, # = Win).")
        vbox.Add(instr, 0, wx.ALL, 10)
        
        grid = wx.FlexGridSizer(rows=len(hotkey_labels), cols=2, vgap=10, hgap=10)
        grid.AddGrowableCol(1, 1)
        
        self.hotkey_ctrls = {}
        
        for key, label in hotkey_labels.items():
            text = wx.StaticText(self.hotkeys_tab, label=label + ":")
            ctrl = wx.TextCtrl(self.hotkeys_tab, value=self.settings.get_hotkey(key))
            
            grid.Add(text, 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(ctrl, 0, wx.EXPAND)
            
            self.hotkey_ctrls[key] = ctrl
            
        vbox.Add(grid, 1, wx.EXPAND | wx.ALL, 10)
        self.hotkeys_tab.SetSizer(vbox)
        
    def setup_general_tab(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Clod mode
        self.clod_check = wx.CheckBox(self.general_tab, label="Enable Clod Mode")
        self.clod_check.SetValue(self.settings.is_clod_enabled())
        vbox.Add(self.clod_check, 0, wx.ALL, 10)
        
        # Bind right-click event to the checkbox
        self.clod_check.Bind(wx.EVT_RIGHT_DOWN, self.on_clod_right_click)
        
        # Model selection section
        model_box = wx.StaticBox(self.general_tab, label="Anthropic Model")
        model_sizer = wx.StaticBoxSizer(model_box, wx.VERTICAL)
        
        model_desc = wx.StaticText(self.general_tab, label="Select the Anthropic model to use for processing")
        model_sizer.Add(model_desc, 0, wx.ALL, 10)
        
        # Model dropdown
        model_panel = wx.Panel(self.general_tab)
        model_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.model_choices = [
            "Claude Opus 4.1 (claude-opus-4-1-20250805)",
            "Claude Sonnet 4 (claude-sonnet-4-20250514)",
            "Claude Sonnet 3.7 (claude-3-7-sonnet-20250219)",
            "Claude Haiku 3.5 (claude-3-5-haiku-20241022)",
            "Custom"
        ]
        
        self.model_values = {
            "Claude Opus 4.1 (claude-opus-4-1-20250805)": "claude-opus-4-1-20250805",
            "Claude Sonnet 4 (claude-sonnet-4-20250514)": "claude-sonnet-4-20250514",
            "Claude Sonnet 3.7 (claude-3-7-sonnet-20250219)": "claude-3-7-sonnet-20250219",
            "Claude Haiku 3.5 (claude-3-5-haiku-20241022)": "claude-3-5-haiku-20241022",
            "Custom": "custom"
        }
        
        self.model_dropdown = wx.Choice(model_panel, choices=self.model_choices)
        model_h_sizer.Add(self.model_dropdown, 1, wx.EXPAND | wx.RIGHT, 10)
        
        self.custom_model_text = wx.TextCtrl(model_panel, size=(300, -1))
        self.custom_model_text.Hide()
        model_h_sizer.Add(self.custom_model_text, 1, wx.EXPAND)
        
        model_panel.SetSizer(model_h_sizer)
        model_sizer.Add(model_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        # Set current model selection
        current_model = self.settings.get_anthropic_model()
        model_found = False
        for choice, value in self.model_values.items():
            if value == current_model:
                self.model_dropdown.SetStringSelection(choice)
                model_found = True
                break
        
        if not model_found:
            self.model_dropdown.SetStringSelection("Custom")
            self.custom_model_text.SetValue(current_model)
            self.custom_model_text.Show()
        
        # Bind model dropdown event
        self.model_dropdown.Bind(wx.EVT_CHOICE, self.on_model_change)
        
        vbox.Add(model_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # API Key section
        api_box = wx.StaticBox(self.general_tab, label="API Key")
        api_sizer = wx.StaticBoxSizer(api_box, wx.VERTICAL)
        
        api_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.change_api_btn = wx.Button(self.general_tab, label="Change API Key")
        self.delete_api_btn = wx.Button(self.general_tab, label="Remove API Key")
        
        api_btn_sizer.Add(self.change_api_btn, 0, wx.RIGHT, 10)
        api_btn_sizer.Add(self.delete_api_btn)
        
        api_sizer.Add(api_btn_sizer, 0, wx.ALL, 10)
        vbox.Add(api_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Custom Prompts section
        prompts_box = wx.StaticBox(self.general_tab, label="System Prompts")
        prompts_sizer = wx.StaticBoxSizer(prompts_box, wx.VERTICAL)
        
        # Description
        prompt_desc = wx.StaticText(self.general_tab, label="Customize system prompts used for each formatter")
        prompts_sizer.Add(prompt_desc, 0, wx.ALL, 10)
        
        # Button
        self.custom_prompts_btn = wx.Button(self.general_tab, label="Edit System Prompts")
        prompts_sizer.Add(self.custom_prompts_btn, 0, wx.ALL, 10)
        
        vbox.Add(prompts_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.general_tab.SetSizer(vbox)
        
        # Bind events
        self.change_api_btn.Bind(wx.EVT_BUTTON, self.on_change_api)
        self.delete_api_btn.Bind(wx.EVT_BUTTON, self.on_delete_api)
        self.custom_prompts_btn.Bind(wx.EVT_BUTTON, self.on_edit_prompts)

    def on_clod_right_click(self, event):
        """Handle right-click on the Clod checkbox"""
        # Check if Shift key is pressed
        shift_down = wx.GetKeyState(wx.WXK_SHIFT)
        if shift_down:
            # Create and show the customization dialog
            dialog = ClodCustomizationDialog(self, self.settings)
            dialog.ShowModal()
            dialog.Destroy()
        else:
            # Let the event propagate for normal context menu
            event.Skip()
        
    def on_change_api(self, event):
        dialog = ChangeAPIKeyDialog(self, self.settings)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_delete_api(self, event):
        if wx.MessageBox("Are you sure you want to remove your API key? You will need to enter it again next time you use the application.", 
                        "Confirm", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.settings.clear_api_key()
            wx.MessageBox("API key removed successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
            
    def on_edit_prompts(self, event):
        """Open the dialog for customizing system prompts"""
        dialog = CustomPromptDialog(self, self.settings)
        dialog.ShowModal()
        dialog.Destroy()
    
    def on_model_change(self, event):
        """Handle model dropdown selection change"""
        selection = self.model_dropdown.GetStringSelection()
        if selection == "Custom":
            self.custom_model_text.Show()
        else:
            self.custom_model_text.Hide()
        self.general_tab.Layout()
        
    def on_save(self, event):
        # Save hotkeys
        hotkeys_changed = False
        for key, ctrl in self.hotkey_ctrls.items():
            new_value = ctrl.GetValue().strip()
            if new_value and new_value != self.old_hotkeys[key]:
                self.settings.set_hotkey(key, new_value)
                hotkeys_changed = True
        
        # Save Clod setting
        self.settings.set_clod_enabled(self.clod_check.GetValue())
        
        # Save model selection
        selection = self.model_dropdown.GetStringSelection()
        if selection == "Custom":
            model = self.custom_model_text.GetValue().strip()
            if model:
                self.settings.set_anthropic_model(model)
        else:
            model_value = self.model_values.get(selection)
            if model_value and model_value != "custom":
                self.settings.set_anthropic_model(model_value)
        
        # Notify app about changes
        if hotkeys_changed:
            wx.MessageBox("Hotkey changes will take effect after restarting the application.", 
                         "Restart Required", wx.OK | wx.ICON_INFORMATION)
        
        self.EndModal(wx.ID_OK)

class ClodCustomizationDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Customize Clod", size=(700, 600))
        self.settings = settings
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create tabs
        notebook = wx.Notebook(panel)
        
        # Time period tabs
        self.time_tabs = {}
        time_periods = ['morning', 'day', 'evening', 'night']
        for period in time_periods:
            tab = wx.Panel(notebook)
            self.time_tabs[period] = tab
            notebook.AddPage(tab, period.capitalize() + " Activities")
            self.setup_time_tab(period)
        
        # Signoffs tab
        self.signoffs_tab = wx.Panel(notebook)
        notebook.AddPage(self.signoffs_tab, "Clod Signoffs")
        self.setup_signoffs_tab()
        
        # Time Configuration tab
        self.time_config_tab = wx.Panel(notebook)
        notebook.AddPage(self.time_config_tab, "Time Periods")
        self.setup_time_config_tab()
        
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_panel = wx.Panel(panel)
        btn_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Import/Export buttons on the left
        import_btn = wx.Button(btn_panel, label="Import")
        export_btn = wx.Button(btn_panel, label="Export")
        btn_h_sizer.Add(import_btn, 0, wx.RIGHT, 5)
        btn_h_sizer.Add(export_btn, 0, wx.RIGHT, 20)
        
        # Add stretch spacer
        btn_h_sizer.AddStretchSpacer()
        
        # Save/Cancel buttons on the right
        save_btn = wx.Button(btn_panel, wx.ID_OK, "Save")
        cancel_btn = wx.Button(btn_panel, wx.ID_CANCEL, "Cancel")
        btn_h_sizer.Add(save_btn, 0, wx.RIGHT, 5)
        btn_h_sizer.Add(cancel_btn, 0)
        
        btn_panel.SetSizer(btn_h_sizer)
        main_sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_OK)
        import_btn.Bind(wx.EVT_BUTTON, self.on_import)
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        
        # Center on screen
        self.Centre()
    
    def setup_time_tab(self, time_period):
        """Setup tab for a specific time period"""
        tab = self.time_tabs[time_period]
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Get current activities for this time period
        activities = self.settings.get_clod_activities_for_time(time_period)
        
        # Time period info
        time_periods = self.settings.get_clod_time_periods()
        period_info = time_periods.get(time_period, {})
        start = period_info.get('start', 0)
        end = period_info.get('end', 0)
        
        # Format time display
        if time_period == 'night':
            time_str = f"{start}:00 PM - {end}:00 AM"
        else:
            start_str = f"{start}:00 AM" if start < 12 else f"{start-12 if start > 12 else 12}:00 PM"
            end_str = f"{end}:00 AM" if end < 12 else f"{end-12 if end > 12 else 12}:00 PM"
            time_str = f"{start_str} - {end_str}"
        
        # Instructions
        instr = wx.StaticText(tab, label=f"Activities for {time_period.capitalize()} ({time_str})\nEach line is a separate activity.")
        vbox.Add(instr, 0, wx.ALL, 10)
        
        # Text control for editing activities
        text_ctrl = wx.TextCtrl(tab, style=wx.TE_MULTILINE)
        text_ctrl.SetValue("\n".join(activities))
        vbox.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # Store reference to text control
        setattr(self, f"{time_period}_text", text_ctrl)
        
        # Reset button
        reset_btn = wx.Button(tab, label="Reset to Defaults")
        reset_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_time_reset(e, time_period))
        vbox.Add(reset_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        tab.SetSizer(vbox)
    
    def setup_signoffs_tab(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Get current signoffs
        custom_signoffs = self.settings.current_settings.get('custom_clod_signoffs', [])
        if not custom_signoffs:
            signoffs = CLOD_SIGNOFFS.copy()
        else:
            signoffs = custom_signoffs.copy()
        
        # Instructions
        instr = wx.StaticText(self.signoffs_tab, label="Customize Clod's signoffs. Each line is a separate signoff.")
        vbox.Add(instr, 0, wx.ALL, 10)
        
        # Text control for editing signoffs
        self.signoffs_text = wx.TextCtrl(self.signoffs_tab, style=wx.TE_MULTILINE)
        self.signoffs_text.SetValue("\n".join(signoffs))
        vbox.Add(self.signoffs_text, 1, wx.EXPAND | wx.ALL, 10)
        
        # Reset button
        reset_btn = wx.Button(self.signoffs_tab, label="Reset to Defaults")
        reset_btn.Bind(wx.EVT_BUTTON, self.on_signoffs_reset)
        vbox.Add(reset_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.signoffs_tab.SetSizer(vbox)
    
    def setup_time_config_tab(self):
        """Setup tab for configuring time periods"""
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instr = wx.StaticText(self.time_config_tab, 
            label="Configure when each time period starts and ends (24-hour format)")
        vbox.Add(instr, 0, wx.ALL, 10)
        
        # Get current time periods
        time_periods = self.settings.get_clod_time_periods()
        
        # Create grid sizer for time inputs
        grid_sizer = wx.FlexGridSizer(4, 3, 10, 10)
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(2)
        
        self.time_inputs = {}
        
        for period in ['morning', 'day', 'evening', 'night']:
            period_data = time_periods.get(period, {})
            start = period_data.get('start', 0)
            end = period_data.get('end', 0)
            
            # Period label
            label = wx.StaticText(self.time_config_tab, label=f"{period.capitalize()}:")
            grid_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            # Start time spinner
            start_spinner = wx.SpinCtrl(self.time_config_tab, value=str(start), 
                                       min=0, max=23, initial=start)
            grid_sizer.Add(start_spinner, 0, wx.EXPAND)
            
            # End time spinner
            end_spinner = wx.SpinCtrl(self.time_config_tab, value=str(end), 
                                     min=0, max=23, initial=end)
            grid_sizer.Add(end_spinner, 0, wx.EXPAND)
            
            self.time_inputs[period] = {'start': start_spinner, 'end': end_spinner}
        
        vbox.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Note about time periods
        note = wx.StaticText(self.time_config_tab, 
            label="Note: Night period can cross midnight (e.g., 23:00 - 5:00)")
        note.SetForegroundColour(wx.Colour(100, 100, 100))
        vbox.Add(note, 0, wx.ALL, 10)
        
        self.time_config_tab.SetSizer(vbox)
    
    def on_time_reset(self, event, time_period):
        """Reset activities for a specific time period to defaults"""
        default_activities = CLOD_ACTIVITIES_BY_TIME.get(time_period, [])
        text_ctrl = getattr(self, f"{time_period}_text")
        text_ctrl.SetValue("\n".join(default_activities))
    
    def on_signoffs_reset(self, event):
        """Reset signoffs to default"""
        self.signoffs_text.SetValue("\n".join(CLOD_SIGNOFFS))
    
    def on_save(self, event):
        """Save all customizations"""
        # Save activities for each time period
        for period in ['morning', 'day', 'evening', 'night']:
            text_ctrl = getattr(self, f"{period}_text")
            activities = [line for line in text_ctrl.GetValue().split('\n') if line.strip()]
            
            # Only save if different from defaults
            default_activities = CLOD_ACTIVITIES_BY_TIME.get(period, [])
            if activities != default_activities:
                self.settings.save_custom_clod_activities_for_time(period, activities)
            else:
                # Clear custom activities to use defaults
                self.settings.save_custom_clod_activities_for_time(period, [])
        
        # Save signoffs
        signoffs = [line for line in self.signoffs_text.GetValue().split('\n') if line.strip()]
        self.settings.save_custom_clod_signoffs(signoffs)
        
        # Save time period configuration
        time_periods = {}
        for period, inputs in self.time_inputs.items():
            time_periods[period] = {
                'start': inputs['start'].GetValue(),
                'end': inputs['end'].GetValue()
            }
        self.settings.save_clod_time_periods(time_periods)
        
        self.EndModal(wx.ID_OK)
    
    def on_export(self, event):
        """Export Clod settings to a JSON file"""
        wildcard = "JSON files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(
            self,
            "Export Clod Settings",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile="clod_settings.json"
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            try:
                # Gather current state from UI
                export_data = {
                    'custom_clod_activities_by_time': {},
                    'custom_clod_signoffs': [],
                    'clod_time_periods': {}
                }
                
                # Get activities for each time period
                for period in ['morning', 'day', 'evening', 'night']:
                    text_ctrl = getattr(self, f"{period}_text")
                    activities = [line for line in text_ctrl.GetValue().split('\n') if line.strip()]
                    export_data['custom_clod_activities_by_time'][period] = activities
                
                # Get signoffs
                signoffs = [line for line in self.signoffs_text.GetValue().split('\n') if line.strip()]
                export_data['custom_clod_signoffs'] = signoffs
                
                # Get time periods
                for period, inputs in self.time_inputs.items():
                    export_data['clod_time_periods'][period] = {
                        'start': inputs['start'].GetValue(),
                        'end': inputs['end'].GetValue()
                    }
                
                # Write to file
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                
                wx.MessageBox(
                    f"Clod settings exported successfully to:\n{path}",
                    "Export Successful",
                    wx.OK | wx.ICON_INFORMATION
                )
                
            except Exception as e:
                wx.MessageBox(
                    f"Failed to export settings:\n{str(e)}",
                    "Export Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        dialog.Destroy()
    
    def on_import(self, event):
        """Import Clod settings from a JSON file"""
        wildcard = "JSON files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(
            self,
            "Import Clod Settings",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            try:
                # Read the file
                with open(path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # Validate the data structure
                if not isinstance(import_data, dict):
                    raise ValueError("Invalid file format: expected a JSON object")
                
                # Import activities by time
                if 'custom_clod_activities_by_time' in import_data:
                    activities_by_time = import_data['custom_clod_activities_by_time']
                    if isinstance(activities_by_time, dict):
                        for period in ['morning', 'day', 'evening', 'night']:
                            if period in activities_by_time:
                                activities = activities_by_time[period]
                                if isinstance(activities, list):
                                    text_ctrl = getattr(self, f"{period}_text", None)
                                    if text_ctrl:
                                        text_ctrl.SetValue("\n".join(str(a) for a in activities))
                
                # Import signoffs
                if 'custom_clod_signoffs' in import_data:
                    signoffs = import_data['custom_clod_signoffs']
                    if isinstance(signoffs, list):
                        self.signoffs_text.SetValue("\n".join(str(s) for s in signoffs))
                
                # Import time periods
                if 'clod_time_periods' in import_data:
                    time_periods = import_data['clod_time_periods']
                    if isinstance(time_periods, dict):
                        for period, data in time_periods.items():
                            if period in self.time_inputs and isinstance(data, dict):
                                if 'start' in data:
                                    self.time_inputs[period]['start'].SetValue(int(data['start']))
                                if 'end' in data:
                                    self.time_inputs[period]['end'].SetValue(int(data['end']))
                
                wx.MessageBox(
                    "Clod settings imported successfully!",
                    "Import Successful",
                    wx.OK | wx.ICON_INFORMATION
                )
                
            except json.JSONDecodeError:
                wx.MessageBox(
                    "Failed to import: Invalid JSON file",
                    "Import Error",
                    wx.OK | wx.ICON_ERROR
                )
            except Exception as e:
                wx.MessageBox(
                    f"Failed to import settings:\n{str(e)}",
                    "Import Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        dialog.Destroy()

class HelpDialog(wx.Dialog):
    def __init__(self, parent, app):
        super().__init__(parent, title="Help", size=(500, 400))
        self.app = app
        self.settings = app.settings
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(panel, label="Help")
        font = title.GetFont()
        font.SetPointSize(16)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        vbox.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # Version
        version = wx.StaticText(panel, label=f"Version {APP_VERSION}")
        vbox.Add(version, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        
        # Hotkeys section
        hotkeys_title = wx.StaticText(panel, label="Current Hotkeys:")
        font = hotkeys_title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        hotkeys_title.SetFont(font)
        vbox.Add(hotkeys_title, 0, wx.LEFT | wx.TOP, 10)
        
        # Define hotkey labels first
        hotkey_labels = {
            'quals': "Reformat Qualifications",
            'cite': "Reformat Citation",
            'tag_writer': "Tag Writer",
            'repair_text': "Repair Text",  # Changed from "Tag Refiner"
            'translator': "Translator",
            'explainer': "Explainer"
        }
        
        grid = wx.FlexGridSizer(rows=len(hotkey_labels), cols=2, vgap=5, hgap=10)
        
        for key, label in hotkey_labels.items():
            text = wx.StaticText(panel, label=label + ":")
            value = wx.StaticText(panel, label=self.settings.get_hotkey(key))
            grid.Add(text, 0)
            grid.Add(value, 0)
            
        vbox.Add(grid, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        
        # Clod status
        clod_status = wx.StaticText(panel, label=f"Clod is currently {'enabled' if self.settings.is_clod_enabled() else 'disabled'}")
        vbox.Add(clod_status, 0, wx.LEFT | wx.BOTTOM, 20)
        
        # Instructions
        instructions = wx.StaticText(panel, label="To change settings, right-click the tray icon and select 'Settings'.")
        vbox.Add(instructions, 0, wx.LEFT | wx.BOTTOM, 20)
        
        # Close button
        close_btn = wx.Button(panel, wx.ID_CLOSE, "Close")
        vbox.Add(close_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        panel.SetSizer(vbox)
        
        # Bind events
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CLOSE), id=wx.ID_CLOSE)
        
        # Center on screen
        self.Centre()

# ----------------------------------------------------------------------
# Hotkey Handling
# ----------------------------------------------------------------------

class HotkeyManager:
    def __init__(self, app):
        self.app = app
        self.registered_hotkeys = {}
        self.is_handling_hotkey = False  # Flag to prevent duplicate handling
        self.blocked_keys = set()  # Track which keys are currently blocked
        
    def register_all(self):
        # Unregister existing hotkeys first
        self.unregister_all()
        
        # Register new hotkeys
        settings = self.app.settings
        
        try:
            # Debug info
            log.info("Registering hotkeys with advanced keyboard library approach")
            
            # Register the global key hook first
            keyboard.hook(self._global_key_handler)
            
            # Alternative hotkeys that don't conflict with Word
            # Store hotkey mappings with both Ctrl+Shift and alternative bindings
            self.hotkey_mappings = {
                # Original Ctrl+Shift hotkeys
                self._hotkey_to_hash(settings.get_hotkey('quals')): ('Quals', self.app.reformat_quals),
                self._hotkey_to_hash(settings.get_hotkey('cite')): ('Cite', self.app.reformat_cite),
                self._hotkey_to_hash(settings.get_hotkey('tag_writer')): ('Tag Writer', self.app.write_tag),
                self._hotkey_to_hash(settings.get_hotkey('repair_text')): ('Repair Text', self.app.repair_text),
                self._hotkey_to_hash(settings.get_hotkey('translator')): ('Translator', self.app.translate),
                self._hotkey_to_hash(settings.get_hotkey('explainer')): ('Explainer', self.app.explain), 
                self._hotkey_to_hash('^+g'): ('Help', self.app.show_help),
                
                # Alternative Ctrl+Alt hotkeys
                self._hotkey_to_hash('^!q'): ('Quals (Alt)', self.app.reformat_quals),
                self._hotkey_to_hash('^!x'): ('Cite (Alt)', self.app.reformat_cite),
                self._hotkey_to_hash('^!d'): ('Tag Writer (Alt)', self.app.write_tag),
                self._hotkey_to_hash('^!r'): ('Repair Text (Alt)', self.app.repair_text),
                self._hotkey_to_hash('^!t'): ('Translator (Alt)', self.app.translate),
                self._hotkey_to_hash('^!e'): ('Explainer (Alt)', self.app.explain),
                self._hotkey_to_hash('^!g'): ('Help (Alt)', self.app.show_help)
            }
            
            # Print registered hotkeys
            original_hotkeys = [
                (settings.get_hotkey('quals'), 'Quals'),
                (settings.get_hotkey('cite'), 'Cite'),
                (settings.get_hotkey('tag_writer'), 'Tag Writer'),
                (settings.get_hotkey('repair_text'), 'Repair Text'),
                (settings.get_hotkey('translator'), 'Translator'),
                (settings.get_hotkey('explainer'), 'Explainer'), 
                ('^+g', 'Help')
            ]
            for ahk_hotkey, name in original_hotkeys:
                log.info(f"Registered hotkey - {name}: {ahk_hotkey}")
                
            log.info("Alternative Hotkeys (use these if primary hotkeys conflict with Word):")
            alt_hotkeys = [
                ('^!q', 'Quals'),
                ('^!x', 'Cite'),
                ('^!w', 'Tag Writer'),
                ('^!r', 'Repair Text'),
                ('^!t', 'Translator'),
                ('^!e', 'Explainer'),
                ('^!g', 'Help')
            ]
            for ahk_hotkey, name in alt_hotkeys:
                log.info(f"Registered alt hotkey - {name}: {ahk_hotkey}")
            
            log.info("Hotkeys registered successfully")
            return True
        except Exception as e:
            log.error(f"Error registering hotkeys: {e}", exc_info=True)
            return False
    
    def _hotkey_to_hash(self, ahk_hotkey):
        """Convert AHK hotkey to a unique hash value we can match efficiently"""
        # Instead of complex string conversion, create a tuple of (ctrl, shift, alt, key)
        ctrl = False
        shift = False
        alt = False
        win = False
        key = None
        
        for char in ahk_hotkey:
            if char == '^':
                ctrl = True
            elif char == '+':
                shift = True
            elif char == '!':
                alt = True
            elif char == '#':
                win = True
            else:
                key = char.lower()
        
        return (ctrl, shift, alt, win, key)
    
    def _hash_to_description(self, hotkey_hash):
        """Convert a hotkey hash back to a readable description for logging"""
        ctrl, shift, alt, win, key = hotkey_hash
        
        desc = ""
        if ctrl:
            desc += "Ctrl+"
        if shift:
            desc += "Shift+"
        if alt:
            desc += "Alt+"
        if win:
            desc += "Win+"
        desc += key.upper()
        
        return desc
    
    def unblock_all_keys(self):
        """Unblock any keys that might be blocked"""
        try:
            # Create a copy of the set to avoid modifying while iterating
            blocked_keys_copy = self.blocked_keys.copy()
            for scan_code in blocked_keys_copy:
                try:
                    keyboard.unblock_key(scan_code)
                    log.debug(f"Unblocked key with scan code: {scan_code}")
                except Exception as e:
                    log.error(f"Error unblocking key {scan_code}: {e}")
            # Clear the set
            self.blocked_keys.clear()
        except Exception as e:
            log.error(f"Error in unblock_all_keys: {e}", exc_info=True)
    
    def _global_key_handler(self, event):
        """Global key hook handler - processes ALL key events"""
        try:
            # Only handle key down events
            if event.event_type == keyboard.KEY_DOWN:
                # Check if Ctrl+Shift or Ctrl+Alt is pressed
                ctrl_pressed = keyboard.is_pressed('ctrl')
                shift_pressed = keyboard.is_pressed('shift')
                alt_pressed = keyboard.is_pressed('alt')
                
                # Only continue if we have Ctrl plus either Shift or Alt
                if ctrl_pressed and (shift_pressed or alt_pressed):
                    # Get the key character
                    if hasattr(event, 'name') and event.name:
                        key = event.name.lower()
                        
                        # Construct a hotkey hash
                        win_pressed = keyboard.is_pressed('win')
                        hotkey_hash = (ctrl_pressed, shift_pressed, alt_pressed, win_pressed, key)
                        
                        # Check if this matches any registered hotkey
                        if hotkey_hash in self.hotkey_mappings:
                            # DO NOT block the key permanently here
                            # Just prevent this specific keystroke from propagating
                            
                            # Get the hotkey info
                            name, callback = self.hotkey_mappings[hotkey_hash]
                            log.info(f"Hotkey triggered: {name}")
                            
                            # Prevent duplicate handling
                            if self.is_handling_hotkey:
                                log.warning(f"Already handling a hotkey, ignoring: {name}")
                                return False
                                
                            self.is_handling_hotkey = True
                            
                            # Execute callback in a separate thread
                            threading.Thread(
                                target=self._execute_callback, 
                                args=(key, callback), 
                                daemon=True
                            ).start()
                            
                            # Suppress this key event
                            return False
        except Exception as e:
            log.error(f"Error in key handler: {e}", exc_info=True)
            self.is_handling_hotkey = False
        
        return True  # Allow normal key processing
    
    def _execute_callback(self, key, callback):
        """Execute the hotkey callback in a safe manner"""
        try:
            log.debug(f"Executing callback for key: {key}")
            
            # DO NOT block the key here - that's what's causing the problem
            
            # Release modifiers to avoid them being "stuck"
            keyboard.release('ctrl')
            keyboard.release('shift')
            keyboard.release('alt')
            
            # Execute the callback
            callback()
            
        except Exception as e:
            log.error(f"Error in callback execution: {e}", exc_info=True)
        finally:
            # Make sure we're no longer handling a hotkey
            self.is_handling_hotkey = False
            
            # Unblock any keys that might have been blocked
            self.unblock_all_keys()
                
    def unregister_all(self):
        """Remove all hotkey handlers"""
        try:
            log.info("Unregistering all hotkeys")
            
            # Make sure to unblock any keys before unregistering
            self.unblock_all_keys()
            
            keyboard.unhook_all()
            self.registered_hotkeys = {}
            self.is_handling_hotkey = False
        except Exception as e:
            log.error(f"Error unregistering hotkeys: {e}", exc_info=True)

# ----------------------------------------------------------------------
# Window Management
# ----------------------------------------------------------------------

def get_active_window():
    """Get the currently active window"""
    return gw.getActiveWindow()
    
def activate_window(window):
    """Activate a specific window"""
    if window:
        window.activate()
        time.sleep(0.1)  # Allow time for activation
        
def send_keys(keys):
    """Send a sequence of keys"""
    keyboard.press_and_release(keys)
    time.sleep(0.1)

# ----------------------------------------------------------------------
# Processors
# ----------------------------------------------------------------------

class QualificationsFormatter:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('quals')
            
        if custom_prompt:
            log.info("Using custom qualifications formatting prompt")
            system_message = custom_prompt
        else:
            # Default system message
            system_message = """
            I have pasted in a long chunk of names and qualifications/institutional affiliations. This is the author list on a report. I want you to format their qualifications as follows:
            FirstName1 LastName1, Role at Institution, notable qualification, notable qualification, award; FirstName2 LastName2, Role at Institution, notable qualification, notable qualification, award; ... FirstNameN LastNameN, Role at Institution, notable qualification, notable qualification, award,
            Return no text other than reformatted name and qualifications, all on one line. Do not add any biographical information that is not pasted. Do not include punctuation at the end. If the qualifications are in another language, translate them to English. If instead of names the submission ONLY contains a description of an institution, summarize the information provided about that institution in the same format.
            """
        
        return self.client.process_text(text, system_message)

class CitationFormatter:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        today = datetime.now()
        
        # Custom date formatting function
        def format_date(date):
            days_difference = (today - date).days
            if days_difference <= 30 and date.year == today.year:
                return f"{date.month}/{date.day:02d}"
            elif date.year < 1950:
                return f"{date.year}"
            elif date.year < 2000:
                return f"{date.year % 100:02d}"
            else:
                return f"{date.year % 100}"
        
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('cite')
            
        if custom_prompt:
            log.info("Using custom citation formatting prompt")
            # Prepend today's date to the custom prompt
            date_info = f"Today is {format_date(today)}/{today.year % 100}."
            system_message = f"{date_info}\n\n{custom_prompt}"
        else:
            # Default system prompt remains exactly the same
            system_message = f"""
            You are an expert in formatting academic citations. Your task is to reformat the given citation to match the following style:

            1. Today is {format_date(today)}/{today.year % 100}. Author names should be in the format: FirstName LastName Date, where Date is:
               - The publication date in mm/dd format (or m/dd, or m/d, respectively, if the month or day require just one digit) for publications within the last month of the current year
               - The publication year in y format (for single-digit years) or yy format (for double-digit years) or yyyy (for years prior to 1950) for all other publications
            2. For multiple authors, use '&' for two authors and 'et al.' for three or more.
            3. After the author names, list their qualifications or affiliations.
            4. Include the full title of the work in quotes.
            5. Include publication details such as journal name, volume, issue, date (mm/dd/yyyy), and page numbers when available.
            6. Include URLs or DOIs at the end of the citation when provided.
            7. If the title or publication or names or qualifications are in all caps, change the capitalization so that it is appropriate for a cite.

            Examples of the desired format:

            (if today's date is less than a month after 9/23/24)
            Adrien Rose & Christian Wilson 9/23, Rose is a research assistant in the Oxford Sustainable Finance Group, specializing in transition finance; Wilson is a DPhil student at the Smith School of Enterprise and the Environment (SSEE) and a Research Assistant in the Oxford Sustainable Finance Group, "Assessing the Credibility of Climate Transition Plans in the Oil and Gas Sector," Discussion Paper, Oxford Sustainable Finance Group, 09/23/2024, https://sustainablefinance.ox.ac.uk/wp-content/uploads/2024/09/SSEE-Discussion-Paper-Oil-Gas_final_AR.pdf

            (if today's date is more than a month after 9/23/24)
            Adrien Rose & Christian Wilson 24, Rose is a research assistant in the Oxford Sustainable Finance Group, specializing in transition finance; Wilson is a DPhil student at the Smith School of Enterprise and the Environment (SSEE) and a Research Assistant in the Oxford Sustainable Finance Group, "Assessing the Credibility of Climate Transition Plans in the Oil and Gas Sector," Discussion Paper, Oxford Sustainable Finance Group, 09/23/2024, https://sustainablefinance.ox.ac.uk/wp-content/uploads/2024/09/SSEE-Discussion-Paper-Oil-Gas_final_AR.pdf

            (if today's date is less than a month after 9/9/24)
            Keeff Felty & Grace Yarrow 9/9, Felty is President of the National Association of Wheat Growers; Yarrow is Food and Agriculture Policy Reporter at POLITICO, Author of POLITICO Pro's Morning Agriculture newsletter, University of Maryland graduate, "Ag groups hit the Hill," Politico, 9/9/24, https://www.politico.com/newsletters/weekly-agriculture/2024/09/09/ag-groups-hit-the-hill-00177896

            (if today's date is more than a month after 9/9/24)
            Keeff Felty & Grace Yarrow 24, Felty is President of the National Association of Wheat Growers; Yarrow is Food and Agriculture Policy Reporter at POLITICO, Author of POLITICO Pro's Morning Agriculture newsletter, University of Maryland graduate, "Ag groups hit the Hill," Politico, 9/9/24, https://www.politico.com/newsletters/weekly-agriculture/2024/09/09/ag-groups-hit-the-hill-00177896

            J. D. Tuccille 23, Contributing Editor at Reason.com, former Managing Editor at Reason.com, columnist for Arizona Republic, Denver Post, and Washington Times, author of High Desert Barbecue, "It's Government Shutdown Theater, Again," Reason, 9/25/23, https://reason.com/2023/09/25/its-government-shutdown-theater-again/

            Robert N. Stavins 18, A.J. Meyer Professor of Energy and Economic Development, John F. Kennedy School of Government, Harvard University; University Fellow, Resources for the Future; and Research Associate, National Bureau of Economic Research, "Environmental Economics," The New Palgrave Dictionary of Economics, edited by Garett Jones, Third edition, Palgrave Macmillan, 2018, pp. 3782–3795

            Yael Parag & Sarah Darby 9, Parag is the Vice Dean of Reichman University's School of Sustainability at Reichman University (IDC); Derby is BSc DPhil, Associate Professor, Energy Programme, Environmental Change Institute, University of Oxford, "Consumer–Supplier–Government Triangular Relations: Rethinking the UK Policy Path for Carbon Emissions Reduction from the UK Residential Sector," Energy Policy, vol. 37, no. 10, 10/01/2009, pp. 3984–3992

            Jie Jiang et al. 23, Jie Jiang, School of Intellectual Property at Nanjing University of Science and Technology; Qihang Zhang, School of Intellectual Property at Nanjing University of Science and Technology; Yifan Hui, School of Mathematics and Statistics at University of Glasgow, "The Impact of Market and Non-Market-Based Environmental Policy Instruments on Firms' Sustainable Technological Innovation: Evidence from Chinese Firms," Sustainability, vol. 15, no. 5, 5, Multidisciplinary Digital Publishing Institute, 01/15/2023, p. 4425

            Important:
            - Do not remove any information from the citation that was included in the submission.
            - Do not add any information to the citation that was not included in the submission.
            - Return only the reformatted citation without any additional text or explanations.
            - Always end your response with a new line character.
            """
        
        result = self.client.process_text(text, system_message)
        
        # Ensure the result ends with a newline
        if result and not result.endswith('\n'):
            result += '\n'
            
        return result

class TagWriter:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('tag_writer')
            
        if custom_prompt:
            log.info("Using custom tag writer prompt")
            system_message = custom_prompt
        else:
            # Default system message
            system_message = """
            Please summarize the text I've pasted in a single sentence or phrase, following the style of these examples:
    
            - Biden's barely holding Israel back from torching the Middle East. Leverage is working now but must be sustained.
            - The link alone turns the case---political weakness spurs global adversary testing.
            - It causes the plan to be ignored AND external war
            - Fights over the domestic agenda sap White House focus from managing foreign policy conflicts. Biden's personal touch is key to both.
            - Policy is a political decision justified by utilitarian consequentialist arguments. Courts do not make policy---they interpret law.
            - Current law permits inventors to patent novel applications of already patented technologies, but limits the enforceability of those patents via a judicially-crafted doctrine called obviousness-type double patenting, or OTDP. Inventors can circumvent OTDP restrictions by committing to link the expirations of their related patents through a document called a 'terminal disclaimer,' or TD.
            - Destroys courts AND claim processing. Litigation costs will spike to the hundreds of millions.
            - It's credible. The last plank has the judiciary make it permanent---that solves---makes the CP the durable law of the land
            - Links to them---Congress can always reverse itself---and so can courts, in antitrust
            - 'ITS'---means domestic law, NOT international
            - The CP's distinct---it's international, binding in the absence of domestic legislation
    
            Please provide a similar style summary that captures the key points concisely, using similar formatting including dashes (triple dashes only: --- , not -) and capitalization where appropriate. The phrase should start with a short label that clearly and consisely identifies the argument made in the excerpt. Return only the summary with no additional text.
            """
        
        return self.client.process_text(text, system_message)

class TextRepairer:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('repair_text')
            
        if custom_prompt:
            log.info("Using custom text repair prompt")
            system_message = custom_prompt
        else:
            # Default system message
            system_message = """
            You are a specialized text repair tool. Your task is to identify and fix common OCR and PDF text extraction errors while preserving the original meaning and content exactly. 
    
            Focus exclusively on these types of errors:
            1. Character substitutions and ligature issues (e.g., "fl" appearing as "ff", "fi" appearing as missing character glyph)
            2. Number/letter confusions (e.g., "0" for "O", "l" for "1", "rn" for "m"). Note that sometimes numbers should be preserved because they are footnotes. 
            3. Random line breaks or hyphenation (e.g., "re-\nsearch" should be "research")
            4. Extra or missing spaces (e.g., "thisis" should be "this is")
            5. Common punctuation errors (e.g., missing periods, commas appearing as periods)
            6. Other typical OCR errors that are clearly unintentional
    
            EXTREMELY IMPORTANT GUIDELINES:
            - Make NO substantive changes to the text's meaning or content
            - NEVER add, remove, or modify actual content
            - NEVER rewrite sentences or paragraphs for clarity or style
            - NEVER correct grammar, spelling, or word choice unless it's clearly an OCR error
            - If there is ANY uncertainty about a potential error, leave the text as is
            - Preserve all formatting except for the specific OCR errors mentioned above
            - Do not combine separate lines into paragraphs or add paragraph breaks
            - Do not add line breaks. If the original text has no spacing between paragraphs, that is how it should be returned.
    
            Your goal is to produce exactly what the original document contained before OCR errors were introduced. When in doubt about any change, always err on the side of minimal intervention.
    
            Return the repaired text with no additional commentary, introductions, or explanations. 
            """
        
        return self.client.process_text(text, system_message)

class Translator:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('translator')
            
        if custom_prompt:
            log.info("Using custom translator prompt")
            system_message = custom_prompt
        else:
            # Default system message
            system_message = """
            You are a professional translator. Your task is to translate the given text 
            into fluent, natural-sounding English while preserving the original meaning 
            and context. If the text is already in English, simply return it unchanged.
            
            Important guidelines:
            - Maintain the original tone and style
            - Preserve formatting and special characters
            - Keep proper nouns unchanged
            - Return only the translated text without explanations
            """
        
        return self.client.process_text(text, system_message)

class Explainer:
    def __init__(self, client, settings=None):
        self.client = client
        self.settings = settings
        
    def process(self, text):
        # Check if there's a custom prompt
        custom_prompt = None
        if self.settings:
            custom_prompt = self.settings.get_custom_prompt('explainer')
            
        if custom_prompt:
            log.info("Using custom explainer prompt")
            system_message = custom_prompt
        else:
            # Default system message
            system_message = """
            You are an expert explainer who takes complex text and explains it in clear, simple terms.
            Your task is to read the given text and provide a concise, straightforward explanation that:
            
            1. Identifies the main concepts and arguments
            2. Explains any jargon or technical terms in plain language
            3. Summarizes the key points in a way that's easy to understand
            4. Provides context if necessary for understanding
            
            Keep your explanation concise and to the point. Focus on clarity and understanding.
            Return only the explanation without any introductory phrases or concluding remarks.
            """

        return self.client.process_text(text, system_message)

# ----------------------------------------------------------------------
# Main Application
# ----------------------------------------------------------------------

class QualsCiteApp:
    def __init__(self):
        self.settings = Settings()
        self.api_client = None
        self.hotkey_manager = None
        self.tooltip = Tooltip()
        self.toast = ToastNotifier()
        
        # Processors
        self.quals_formatter = None
        self.cite_formatter = None
        self.tag_writer = None
        self.text_repairer = None  # Changed from self.tag_refiner
        self.translator = None
        
        # Tray icon
        self.tray_icon = None
        self.running = True
        
        # wxPython app
        self.wx_app = None
        
    def initialize(self):
        log.info(f"Initializing {APP_NAME} v{APP_VERSION}")
        
        # Initialize wxPython app
        self.wx_app = wx.App(False)
        log.debug("wxPython app initialized")
        
        # Check for first run
        if self.settings.is_first_run():
            message = "Welcome to Card Formatting Tools! This tool helps you quickly format qualifications, citations, explain complex text, and more. You'll need an Anthropic API key to get started."
            wx.MessageBox(message, "Welcome", wx.OK | wx.ICON_INFORMATION)
            self.settings.set_first_run(False)
            log.info("First run setup completed")
        
        # Check for API key
        api_key = self.settings.get_api_key()
        if not api_key:
            log.info("No API key found, prompting user")
            api_key = self.prompt_for_api_key()
            if not api_key:
                log.error("No API key provided")
                wx.MessageBox("API key is required to run this application.", "Error", wx.OK | wx.ICON_ERROR)
                return False
            log.info("API key obtained")
        
        # Initialize API client
        try:
            log.debug("Initializing API client")
            self.api_client = AnthropicClient(api_key, self.settings)
            
            # Initialize processors
            log.debug("Initializing text processors")
            self.quals_formatter = QualificationsFormatter(self.api_client, self.settings)
            self.cite_formatter = CitationFormatter(self.api_client, self.settings)
            self.tag_writer = TagWriter(self.api_client, self.settings)
            self.text_repairer = TextRepairer(self.api_client, self.settings)
            self.translator = Translator(self.api_client, self.settings)
            self.explainer = Explainer(self.api_client, self.settings)
            
            # Print confirmation message
            log.info("Card Formatting Tools initialized successfully!")
            log.info(f"Clod mode is {'enabled' if self.settings.is_clod_enabled() else 'disabled'}")
            
            # Register hotkeys
            log.debug("Registering hotkeys")
            self.hotkey_manager = HotkeyManager(self)
            if not self.hotkey_manager.register_all():
                log.error("Failed to register hotkeys")
                wx.MessageBox("Failed to register hotkeys. Please check if another application is using the same shortcuts.", 
                             "Error", wx.OK | wx.ICON_ERROR)
                return False
                
            # Create system tray icon
            log.debug("Creating system tray icon")
            self.create_tray_icon()
            
            log.info("Application initialization complete")
            return True
        except Exception as e:
            log.critical(f"Failed to initialize application: {str(e)}", exc_info=True)
            wx.MessageBox(f"Failed to initialize application: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            return False
    
    def prompt_for_api_key(self):
        # We already have a wx.App created in initialize()
        dialog = APIKeyDialog(None, self.settings)
        result = dialog.ShowModal()
        api_key = dialog.result
        dialog.Destroy()
        return api_key
        
    def create_tray_icon(self):
        """Creates and displays the system tray icon"""
        # Create a simple icon
        image = self.create_icon_image()
        
        # Create the menu with action callbacks that use wx.CallAfter
        menu = pystray.Menu(
            pystray.MenuItem('Settings', lambda: wx.CallAfter(self.show_settings_safe)),
            pystray.MenuItem('Help', lambda: wx.CallAfter(self.show_help_safe)),
            pystray.MenuItem('Exit', lambda: wx.CallAfter(self.exit_safe))
        )
        
        # Create the icon
        self.tray_icon = pystray.Icon("Card Formatting Tools", image, "Card Formatting Tools", menu)
        
        # Run in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def show_settings_safe(self):
        """Thread-safe method to show settings dialog"""
        dialog = SettingsDialog(None, self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def show_help_safe(self):
        """Thread-safe method to show help dialog"""
        dialog = HelpDialog(None, self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def exit_safe(self):
        """Thread-safe method to exit the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.running = False
        
    def create_icon_image(self):
        # Create a simple icon
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        drawing = ImageDraw.Draw(image)
        
        # Draw a simple icon - blue rectangle with '|' in white
        drawing.rectangle([(0, 0), (width, height)], fill=(41, 128, 185))
        drawing.text((width//4, height//4), "|", fill=(255, 255, 255))
        
        return image
        
    def show_notification(self, title, message):
        self.toast.show_toast(title, message)
        
    def show_tooltip(self, message, duration=2000):
        self.tooltip.show(message, duration)
    
    def show_settings(self, icon=None, item=None):
        # Use CallAfter to ensure this runs on the main thread
        wx.CallAfter(self.show_settings_safe)
        
    def show_help(self):
        # wx.App is already created in initialize()
        dialog = HelpDialog(None, self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def exit(self, icon=None, item=None):
        if icon:
            icon.stop()
        self.running = False
        self.tooltip.close()
        self.toast.close()
        
        # Clean up wx.App if it exists
        if self.wx_app:
            self.wx_app.ExitMainLoop()
            self.wx_app = None
        
    def copy_to_clipboard(self, text):
        pyperclip.copy(text)
        
    def get_from_clipboard(self):
        return pyperclip.paste()
        
    def execute_clod_activity(self, activity_msg, operation_func, success_msg, error_msg=None):
        if not self.api_client:
            log.error("API client not initialized")
            self.show_tooltip("API client not initialized")
            return
                
        log.debug(f"Executing activity: {activity_msg}")
        
        # Save the original hooks before we do anything
        original_hooks = keyboard._hooks.copy()
        
        # Create a temporary handler that blocks everything
        # but doesn't remove the existing hooks from memory
        temp_handler = lambda e: True
        keyboard.hook(temp_handler)
        
        try:
            # Send copy command with direct send_input to avoid keyboard hook
            keyboard.send('ctrl+c', do_press=True, do_release=True)
            time.sleep(0.2)  # Wait a bit for clipboard
            
            # Get clipboard content
            clipboard_content = self.get_from_clipboard()
            if not clipboard_content:
                # Re-enable keyboard by removing only our temporary hook
                keyboard.unhook(temp_handler)
                log.warning("Clipboard is empty")
                self.show_tooltip("Error: Clipboard is empty")
                return
            
            log.debug(f"Got clipboard content ({len(clipboard_content)} characters)")
            
            # Show activity message
            if self.settings.is_clod_enabled():
                activities = self.settings.get_clod_activities()
                activity = random.choice(activities)
                self.show_tooltip(f"{activity} Please wait.")
            else:
                self.show_tooltip(activity_msg)
                
            try:
                # Process content
                log.debug("Processing content with operation function")
                result = operation_func(clipboard_content)
                log.debug(f"Processing completed, result length: {len(result) if result else 0}")
                
                # Copy result to clipboard
                self.copy_to_clipboard(result)
                
                # Show success message
                if self.settings.is_clod_enabled():
                    signoffs = self.settings.get_clod_signoffs()
                    signoff = random.choice(signoffs)
                    self.show_tooltip(f"{success_msg} {signoff}")
                else:
                    self.show_tooltip(success_msg)
                    
                # Wait a moment before re-enabling keyboard
                time.sleep(0.3)
                
                log.info(f"Activity completed successfully: {activity_msg}")
                    
            except Exception as e:
                # Show error message
                error = error_msg or f"Error: {str(e)}"
                log.error(f"Error processing content: {str(e)}", exc_info=True)
                self.show_tooltip(error)
        except Exception as e:
            log.error(f"Error in execute_clod_activity: {str(e)}", exc_info=True)
            self.show_tooltip(f"Error: {str(e)}")
        finally:
            log.debug("Cleaning up keyboard hooks")
            # Remove ONLY our temporary handler
            keyboard.unhook(temp_handler)
            
            # Make sure the original hooks are still there
            # If some hooks were lost, restore them
            current_hooks = keyboard._hooks.copy()
            for hook in original_hooks:
                if hook not in current_hooks:
                    keyboard.hook(hook)
    
    def reformat_quals(self):
        log.debug("Calling reformat_quals")
        self.execute_clod_activity(
            "Reformatting qualifications. Please wait.",
            self.quals_formatter.process,
            "Formatting complete! Text copied to clipboard."
            # No paste_result parameter
        )
        
    def reformat_cite(self):
        # Store the initial window ID
        initial_win = get_active_window()
        
        # Save original global hook reference
        original_hooks = keyboard._hooks.copy()
        
        # Block keyboard temporarily without removing hooks
        keyboard._listener.suppress_event = lambda e: True
        
        try:
            # Send F12 key to open citation
            keyboard.send('f12', do_press=True, do_release=True)
            time.sleep(0.1)
            
            # Copy content
            keyboard.send('ctrl+c', do_press=True, do_release=True)
            time.sleep(0.2)
            
            # Get clipboard content
            clipboard_content = self.get_from_clipboard()
            if not clipboard_content:
                self.show_tooltip("Error: Clipboard is empty")
                return
            
            # Show activity message
            if self.settings.is_clod_enabled():
                activities = self.settings.get_clod_activities()
                activity = random.choice(activities)
                self.show_tooltip(f"{activity} Please wait.")
            else:
                self.show_tooltip("Reformatting citation. Please wait.")
                
            # Process content
            result = self.cite_formatter.process(clipboard_content)
            
            # Copy result to clipboard
            self.copy_to_clipboard(result)
            
            # Switch back to initial window
            if initial_win:
                activate_window(initial_win)
                time.sleep(0.1)
            
            # Send F2 key - this automatically pastes in Word
            keyboard.send('f2', do_press=True, do_release=True)
            time.sleep(0.1)
            
            # Show success message
            if self.settings.is_clod_enabled():
                signoffs = self.settings.get_clod_signoffs()
                signoff = random.choice(signoffs)
                self.show_tooltip(f"Citation formatting complete! Text pasted. {signoff}")
            else:
                self.show_tooltip("Citation formatting complete! Text pasted.")
        except Exception as e:
            # Show error message
            self.show_tooltip(f"Error: {str(e)}")
        finally:
            # Re-enable keyboard processing WITHOUT removing our hooks
            keyboard._listener.suppress_event = lambda e: False
            
            # Make sure our hooks are restored
            if keyboard._hooks != original_hooks:
                log.warning("Keyboard hooks changed during processing!")
                # Restore original hooks
                keyboard._hooks = original_hooks.copy()
        
    def write_tag(self):
        log.debug("Calling write_tag")
        self.execute_clod_activity(
            "Writing tag. Please wait.",
            self.tag_writer.process,
            "Tag complete! Text copied to clipboard."
            # No paste_result parameter
        )
        
    def repair_text(self):
        log.debug("Calling repair_text")
        self.execute_clod_activity(
            "Repairing text. Please wait.",
            self.text_repairer.process,
            "Text repair complete! Text copied to clipboard."
            # No paste_result parameter
        )
        
    def translate(self):
        log.debug("Calling translate")
        self.execute_clod_activity(
            "Translating text. Please wait.",
            self.translator.process,
            "Translation complete! Text copied to clipboard."
            # No paste_result parameter
        )

    def explain(self):
        log.debug("Calling explain")
        self.execute_clod_activity(
            "Explaining text. Please wait.",
            self.explainer.process,
            "Explanation complete! Text copied to clipboard."
            # No paste_result parameter
        )

# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------

def main():
    log.info(f"Starting {APP_NAME} v{APP_VERSION}")
    app = QualsCiteApp()
    
    if app.initialize():
        try:
            # Process wx events while keeping the main thread alive
            log.info("Entering main application loop")
            while app.running:
                # Allow wx to process events
                if app.wx_app:
                    app.wx_app.ProcessPendingEvents()
                time.sleep(0.1)
        except KeyboardInterrupt:
            log.info("Received keyboard interrupt, exiting")
            app.exit()
        except Exception as e:
            log.critical(f"Unhandled exception in main loop: {str(e)}", exc_info=True)
            app.exit()
    else:
        log.error("Application failed to initialize")
    
    log.info(f"{APP_NAME} shutting down")
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.critical(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
