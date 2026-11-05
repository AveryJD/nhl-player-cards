# ====================================================================================================
# GET PROJECT FILE LOCATION
# ====================================================================================================

import os

def find_project_dir(start_dir: str) -> str:
    """
    Traverse upward until a directory containing 'data' is found.

    :param start_dir: Directory where the search starts
    :return: Project root directory
    """

    project_dir = None
    while project_dir is None:
        potential_data_dir = os.path.join(start_dir, "data")

        if os.path.exists(potential_data_dir):
            project_dir = start_dir
        else:
            parent = os.path.dirname(start_dir)

            if parent == start_dir:
                raise FileNotFoundError('Could not find "data" folder')

            start_dir = parent
    return project_dir


# Directory of the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.environ.get('NHL_CARD_DATA_DIR')

# Root project directory
if DATA_DIR:
    PROJECT_DIR = os.path.dirname(DATA_DIR)
else:
    PROJECT_DIR = find_project_dir(CURRENT_DIR)
    DATA_DIR = os.path.join(PROJECT_DIR, "data")

# Card assets (fonts and team logos)
ASSETS_DIR = os.path.join(DATA_DIR, 'card_data', 'assets')


# ====================================================================================================
# CARD GENERATION CONSTANTS
# ====================================================================================================

# Date card data was updated on
UPDATE_DATE = 'Sep 1, 2026'

# Position to data folder name
POSITION_FOLDERS = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}

# Name shown on the card for each skater stat and how its value is displayed (the kinds are formatted in card_utils.format_stat_value)
SKATER_STAT_DISPLAY = {
    'tot': ('Overall (All Situations)', 'war'), 'evo': ('ES Offense', 'war'), 'evd': ('ES Defense', 'war'),
    'ppl': ('Power Play', 'war'), 'pkl': ('Penalty Kill', 'war'), 'fin': ('Finishing (All)', 'war'), 'pen': ('Penalties (All)', 'war'),
    'xgl': ('xGoals', 'count'), 'gol': ('Goals', 'count'), 'ast': ('Primary Assists', 'count'), 'hit': ('Hits', 'count'),
    'sho': ('Shots', 'count'), 'cfs': ('Corsi Share', 'percent'), 'xfs': ('xGoal Share', 'percent'), 'gfs': ('Goal Share', 'percent'),
    'shp': ('Shooting %', 'percent'), 'svp': ('Save %', 'percent'),
    'toi': ('5v5 Ice Time (Per Game)', 'toi'), 'ppt': ('5v4 Ice Time (Per Game)', 'toi'), 'pkt': ('4v5 Ice Time (Per Game)', 'toi'), 'tmt': ('Teammates', 'war'),
    'cmp': ('Opponents', 'war'),
}
# Special teams WAR shown (without a ranking) for players that do not qualify
SKATER_UNQUALIFIED_LABELS = {'ppl': 'Power Play (All)', 'pkl': 'Penalty Kill (All)'}
# Special teams ice times that are only ranked for players who qualify for the matching WAR
SKATER_QUALIFIED_BY = {'ppt': 'ppl', 'pkt': 'pkl'}

# Minimum minutes of ice time to be ranked in a season (same as the pipeline's SKATER_MIN_TOI and GOALIE_MIN_TOI)
SKATER_MIN_TOI = {
    '2026-2027': 100,    # Current season (max games any team has played)
    '2025-2026': 300,
    '2024-2025': 300,
    '2023-2024': 300,
    '2022-2023': 300,
    '2021-2022': 300,
    '2020-2021': 200,    # Season shortened due to COVID
    '2019-2020': 250,    # Season paused due to COVID
    '2018-2019': 300,
    '2017-2018': 300,
    '2016-2017': 300,
    '2015-2016': 300,
    '2014-2015': 300,
    '2013-2014': 300,
    '2012-2013': 200,    # Season shortened due to lockout
    '2011-2012': 300,
    '2010-2011': 300,
    '2009-2010': 300,
}

GOALIE_MIN_TOI = {
    '2026-2027': 300,    # Current season (max games any team has played)
    '2025-2026': 600,
    '2024-2025': 600,
    '2023-2024': 600,
    '2022-2023': 600,
    '2021-2022': 600,
    '2020-2021': 400,    # Season shortened due to COVID
    '2019-2020': 500,    # Season paused due to COVID
    '2018-2019': 600,
    '2017-2018': 600,
    '2016-2017': 600,
    '2015-2016': 600,
    '2014-2015': 600,
    '2013-2014': 600,
    '2012-2013': 400,    # Season shortened due to lockout
    '2011-2012': 600,
    '2010-2011': 600,
    '2009-2010': 600,
}

# Player group names for the branding note, and the stat sections: (title, five attribute keys top to bottom, None leaves a slot blank)
POSITION_GROUP_NAMES = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}
SKATER_STAT_SECTIONS = [
    ('Individual', ['xgl', 'gol', 'ast', 'sho', 'hit']),
    ('On-Ice', ['xfs', 'gfs', 'cfs', 'shp', 'svp']),
    ('Deployment', ['tmt', 'cmp', 'toi', 'ppt', 'pkt']),
]
GOALIE_STAT_SECTIONS = [
    ('Goals Saved', ['gsv', 'gsx', 'ldg', 'mdg', 'hdg']),
    ('Shots Against', ['gag', 'tmd', 'lds', 'mds', 'hds']),
    ('Starts (Per Season)', ['wrk', 'gre', 'qal', 'bad', 'awf']),
]
# The title of the WAR section
WAR_SECTION_TITLE = 'Wins Above Replacement'

# Font sizes shared by every card (the largest that fit the longest text)
STAT_FONT_SIZE = 54
TITLE_FONT_SIZE = 69
BRANDING_FONT_SIZE = 38

# Games in a season that per-game rates are scaled to (2026-2027 onward has 84)
SEASON_LENGTH = 82
LONG_SEASON_LENGTH = 84
LONG_SEASON_START_YEAR = 2026

# Games that goalie rates are scaled to on the card (scores are stored per 60 minutes)
GOALIE_RATE_GAMES = 60

# Name shown on the card for each goalie stat and how its value is displayed
GOALIE_STAT_DISPLAY = {
    'tot': ('Overall (All Situations)', 'war60'), 'evs': ('Even Strength', 'war60'), 'pkl': ('Penalty Kill', 'war60'), 'gpp': ('Power Play', 'war60'),
    'gsv': ('Save %', 'save'), 'gag': ('Goals Against', 'negcount60'), 'gsx': ('GSAx', 'signed60'), 'ldg': ('LD GSAx', 'signed60'), 'mdg': ('MD GSAx', 'signed60'), 'hdg': ('HD GSAx', 'signed60'),
    'gre': ('Excellent Start %', 'rate'), 'qal': ('Quality Start %', 'rate'), 'bad': ('Bad Start %', 'rate'), 'awf': ('Awful Start %', 'rate'),
    'wrk': ('Game Start %', 'rate'), 'tmd': ('xGoals Against', 'negcount60'),
    'lds': ('LD Shots Against', 'negcount60'), 'mds': ('MD Shots Against', 'negcount60'), 'hds': ('HD Shots Against', 'negcount60'),
}

# Card data columns are named '{label} Score', '{label} Percentile', and '{label} History'
SKATER_ATTRIBUTE_LABELS = {key: display[0] for key, display in SKATER_STAT_DISPLAY.items()}
GOALIE_ATTRIBUTE_LABELS = {key: display[0] for key, display in GOALIE_STAT_DISPLAY.items()}

# === NAMING ===
# Birth country codes to full names (an unlisted code is shown as is)
COUNTRY_NAMES = {
    'AUS': 'Australia', 'AUT': 'Austria', 'BLR': 'Belarus', 'CAN': 'Canada', 'CHE': 'Switzerland', 'CZE': 'Czechia',
    'DEU': 'Germany', 'DNK': 'Denmark', 'EST': 'Estonia', 'FIN': 'Finland', 'FRA': 'France', 'GBR': 'Great Britain',
    'HUN': 'Hungary', 'ITA': 'Italy', 'JPN': 'Japan', 'KAZ': 'Kazakhstan', 'LTU': 'Lithuania', 'LVA': 'Latvia',
    'NLD': 'Netherlands', 'NOR': 'Norway', 'POL': 'Poland', 'RUS': 'Russia', 'SVK': 'Slovakia', 'SVN': 'Slovenia',
    'SWE': 'Sweden', 'UKR': 'Ukraine', 'USA': 'USA',
}

# Specific position full names
POSITION_NAMES = {
    'C': 'Center', 'L': 'Left Wing', 'R': 'Right Wing', 'D': 'Defense', 'G': 'Goalie'
}

# Handedness full names
HANDEDNESS_NAMES = {
    'L': 'Left', 'R': 'Right',
}

# Symbols to be replaced in player names for the header
SYMBOLS_TO_REPLACE = {
    'ä': 'a',
    'á': 'a',
    'à': 'a',
    'â': 'a',
    'é': 'e',
    'è': 'e',
    'ê': 'e',
    'ë': 'e',
    'ï': 'i',
    'í': 'i',
    'ì': 'i',
    'î': 'i',
    'ö': 'o',
    'ó': 'o',
    'ò': 'o',
    'ô': 'o',
    'ø': 'o',
    'ü': 'u',
    'ñ': 'n',
    'ç': 'c',
    'ý': 'y',
}

# === FONTS ===
BASIC_FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'basic.ttf')
HEADING_FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'header.ttf')

# === COLORS ===
# Card color RGB values
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK = (39, 39, 39)
SECTION_LIGHT = (236, 236, 236)
SECTION_DARK = (54, 54, 54)

# Team primary color RBG values
PRIMARY_COLORS = {
    'ANA': (252, 76, 2),    'ARI': (140, 38, 51),   'BOS': (252, 181, 20),
    'BUF': (0, 48, 135),    'CGY': (210, 0, 28),    'CAR': (206, 17, 38),
    'CHI': (207, 10, 44),   'COL': (111, 38, 61),   'CBJ': (0, 38, 84),
    'DAL': (0, 104, 71),    'DET': (206, 17, 38),   'EDM': (252, 76, 0),
    'FLA': (200, 16, 46),   'LAK': (162,170,173),   'MIN': (2, 73, 48),
    'MTL': (175, 30, 45),   'NSH': (255, 184, 28),  'NJD': (206, 17, 38),
    'NYI': (244, 125, 48),  'NYR': (0, 56, 168),    'OTT': (218, 26, 50),
    'PHI': (247, 73, 2),    'PIT': (252, 181, 20),  'SJS': (0, 109, 117),
    'SEA': (153, 217, 217), 'STL': (0, 47, 135),    'TBL': (0, 40, 104),
    'TOR': (0, 32, 91),     'VAN': (0, 32, 91),     'UTA': (105, 179, 231),
    'VGK': (185, 151, 91),  'WSH': (4, 30, 66),     'WPG': (4, 30, 66),
    'ATL': (4, 30, 66),     'PHX': (140, 38, 51),
}

# Team secondary color RGB values
SECONDARY_COLORS = {
    'ANA': (185, 151, 91),  'ARI': (21,71,52),      'BOS': (17, 17, 17),
    'BUF': (255, 184, 28),  'CGY': (250, 175, 25),  'CAR': (0, 0, 0),
    'CHI': (0, 0, 0),       'COL': (35, 97, 146),   'CBJ': (206,17,38),
    'DAL': (143, 143, 140), 'DET': (0, 0, 0),       'EDM': (4, 30, 66),
    'FLA': (4,30,66),       'LAK': (17, 17, 17),    'MIN': (175, 35, 36),
    'MTL': (25, 33, 104),   'NSH': (4,30,66),       'NJD': (0, 0, 0),
    'NYI': (0,83,155),      'NYR': (206,17,38),     'OTT': (0, 0, 0),
    'PHI': (0, 0, 0),       'PIT': (0, 0, 0),       'SJS': (0, 0, 0),
    'SEA': (0, 22, 40),     'STL': (252, 181, 20),  'TBL': (0, 0, 0),
    'TOR': (0, 0, 0),       'VAN': (0, 132, 61),    'UTA': (0, 0, 0),
    'VGK': (51,63,72),      'WSH': (200, 16, 46),   'WPG': (172,22,44),
    'ATL': (184, 97, 37),   'PHX': (21,71,52),
}

# Stat bar gradient (low to high), the same red, purple, and blue as the website
STAT_GRADIENT_COLORS = [(255, 99, 99), (210, 110, 210), (99, 99, 255)]
# Share of the bar at each end that stays solid red or blue
STAT_GRADIENT_SOLID_FRACTION = 0.12

