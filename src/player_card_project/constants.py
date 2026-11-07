# ====================================================================================================
# GET PROJECT FILE LOCATION
# ====================================================================================================

# Imports
import os

def find_project_dir(start_dir: str) -> str:
    """
    Traverse upward until a directory containing 'data' is found.

    :param start_dir: Directory where the search starts
    :return: Project root directory
    """

    project_dir = None
    while project_dir is None:
        potential_data_dir = os.path.join(start_dir, 'data')

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
    DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# Card assets (fonts and team logos)
ASSETS_DIR = os.path.join(DATA_DIR, 'card_data', 'assets')


# ====================================================================================================
# CARD GENERATION CONSTANTS
# ====================================================================================================

# Date card data was updated on
UPDATE_DATE = 'September 1, 2026'

# === NAMING ===
# Position to data folder name
POSITION_FOLDERS = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}

# Name shown on the card for each skater stat and how its value is displayed (the kinds are formatted in card_utils.format_stat_value)
SKATER_STAT_DISPLAY = {
    'tot': ('Overall (All Situations)', 'war'), 'evo': ('ES Offense', 'war'), 'evd': ('ES Defense', 'war'),
    'ppl': ('Power Play', 'war'), 'pkl': ('Penalty Kill', 'war'), 'fin': ('Finishing (All)', 'war'), 'pen': ('Penalties (All)', 'war'),
    'xgl': ('xGoals', 'count'), 'gol': ('Goals', 'count'), 'ast': ('Primary Assists', 'count'), 'hit': ('Hits', 'count'),
    'sho': ('Shots', 'count'), 'sfs': ('Shot Share', 'percent'), 'xfs': ('xGoal Share', 'percent'), 'gfs': ('Goal Share', 'percent'),
    'shp': ('Shooting %', 'percent'), 'svp': ('Save %', 'percent'),
    'toi': ('5v5 Ice Time', 'toi'), 'ppt': ('5v4 Ice Time', 'toi'), 'pkt': ('4v5 Ice Time', 'toi'), 'tmt': ('5v5 Teammates', 'war'),
    'cmp': ('5v5 Opponents', 'war'),
}
# Special teams WAR shown (without a ranking) for players that do not qualify
SKATER_UNQUALIFIED_LABELS = {'ppl': 'Power Play (All)', 'pkl': 'Penalty Kill (All)'}
# Special teams ice times that are only ranked for players who qualify for the matching WAR
SKATER_QUALIFIED_BY = {'ppt': 'ppl', 'pkt': 'pkl'}

# Player group names for the branding note, and the stat sections: (title, five attribute keys top to bottom, None leaves a slot blank)
POSITION_GROUP_NAMES = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}
SKATER_STAT_SECTIONS = [
    ('5v5 Individual', ['xgl', 'gol', 'sho', 'ast', 'hit']),
    ('5v5 On-Ice', ['xfs', 'gfs', 'sfs', 'shp', 'svp']),
    ('Deployment', ['tmt', 'cmp', 'toi', 'ppt', 'pkt']),
]
GOALIE_STAT_SECTIONS = [
    ('5v5 Saves', ['gsv', 'gsx', 'ldg', 'mdg', 'hdg']),
    ('5v5 Shots Faced', ['gag', 'tmd', 'lds', 'mds', 'hds']),
    ('Starts', ['wrk', 'gre', 'qal', 'bad', 'awf']),
]
# The title of the WAR section
WAR_SECTION_TITLE = 'Wins Above Replacement'

# Name shown on the card for each goalie stat and how its value is displayed
GOALIE_STAT_DISPLAY = {
    'tot': ('Overall (All Situations)', 'signed60'), 'evs': ('Even Strength', 'signed60'), 'pkl': ('Penalty Kill', 'signed60'), 'gpp': ('Power Play', 'signed60'),
    'gsv': ('Save %', 'save'), 'gag': ('Goals Against', 'negcount60'), 'gsx': ('GSAx', 'signed60'), 'ldg': ('LD GSAx', 'signed60'), 'mdg': ('MD GSAx', 'signed60'), 'hdg': ('HD GSAx', 'signed60'),
    'gre': ('Excellent Start %', 'rate'), 'qal': ('Quality Start %', 'rate'), 'bad': ('Bad Start %', 'rate'), 'awf': ('Awful Start %', 'rate'),
    'wrk': ('Game Start %', 'rate'), 'tmd': ('xGoals Against', 'negcount60'),
    'lds': ('LD Shots Against', 'negcount60'), 'mds': ('MD Shots Against', 'negcount60'), 'hds': ('HD Shots Against', 'negcount60'),
}

# Card data columns are named '{label} Score', '{label} Percentile', and '{label} History'
SKATER_ATTRIBUTE_LABELS = {key: display[0] for key, display in SKATER_STAT_DISPLAY.items()}
GOALIE_ATTRIBUTE_LABELS = {key: display[0] for key, display in GOALIE_STAT_DISPLAY.items()}

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

# === FONTS ===
BASIC_FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'basic.ttf')
HEADING_FONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'header.ttf')

# === COLORS ===
# Card color RGB values
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
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

# Stat bar gradient (red, purple, and blue)
STAT_GRADIENT_COLORS = [(255, 99, 99), (210, 110, 210), (99, 99, 255)]

