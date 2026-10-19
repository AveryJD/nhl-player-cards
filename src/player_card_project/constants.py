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
UPDATE_DATE = 'September 1, 2026'

# Position to data folder name
POSITION_FOLDERS = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}

# The card data CSVs name each ranked attribute in plain words. These map the short attribute keys the card code uses to those labels.
SKATER_ATTRIBUTE_LABELS = {
    'tot': 'Total WAR', 'evo': 'ES Offense', 'evd': 'ES Defense', 'ppl': 'PP Offense', 'pkl': 'PK Defense',
    'fin': 'Finishing', 'gol': 'Goals', 'xgl': 'xGoals', 'ast': 'Assists', 'pen': 'Penalties', 'hit': 'Physicality',
    'ozs': 'O-Zone Starts', 'pdo': 'PDO (Luck)', 'tmt': 'Teammates', 'cmp': 'Competition',
}
GOALIE_ATTRIBUTE_LABELS = {
    'tot': 'Total WAR', 'evs': 'Even Strength', 'pkl': 'Penalty Kill', 'ldg': 'Low Danger', 'mdg': 'Med. Danger',
    'hdg': 'High Danger', 'rbd': 'Rebounds', 'tmd': 'Team Defense', 'gre': 'Great Starts', 'qal': 'Quality Starts',
    'bad': 'Bad Starts', 'awf': 'Awful Starts', 'wrk': 'Workload',
}

# Columns holding how many players were ranked (all players, or only those who qualified for power play / penalty kill)
TOTAL_PLAYERS_COLUMNS = {'all': 'All Players', 'ppl': 'PP Offense Players', 'pkl': 'PK Defense Players'}

# === NAMING ===
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
GRAPH_WHITE = (255/255, 255/255, 255/255)
GRAPH_BLACK = (0/255, 0/255, 0/255)
GRAPH_GRAY = (180/255, 180/255, 180/255)
GRAPH_DARK = (39/255, 39/255, 39/255)

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

# Rank components RBG values
ATTRIBUTE_COLORS = {
    'Total WAR':        (210, 110, 210),
    'ES Offense':       (255, 70, 70),
    'ES Defense':       (70, 70, 255),
    'Even Strength':    (255, 70, 70),
    'Penalty Kill':     (70, 70, 255),
}

# Graph component RBG values
PLOT_ATTRIBUTE_COLORS = {
    'tot_plot': (210/255, 110/255, 210/255),
    'evo_plot': (255/255, 70/255, 70/255),
    'evd_plot': (70/255, 70/255, 255/255),
    'evs_plot': (255/255, 70/255, 70/255),
    'pkl_plot': (70/255, 70/255, 255/255),
}
