# ====================================================================================================
# FUNCTIONS FOR LOADING AND SAVING DIFFERENT FILES
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image
import os
from player_card_project import constants

DATA_DIR = constants.DATA_DIR
PROJECT_DIR = constants.PROJECT_DIR


def get_prev_season(cur_season: str) -> str:
    """
    Return the str for the previous season from a given season's str.

    :param cur_season: A str of the current season ('YYYY-YYYY')
    :return: A str of the season previous to the current season
    """
    start_year, end_year = map(int, cur_season.split("-"))
    prev_season = f"{start_year - 1}-{end_year - 1}"

    return prev_season


def load_card_data_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player card data CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: The DataFrame of the loaded card data
    """

    if position not in ('D', 'G'):
        position = 'F'
    pos_folder = constants.POSITION_FOLDERS[position]

    file_name = f'{season}_{position}_card_data.csv'
    # Card data lives in data/card_data/player_card_data/<position>/ (the layout the stats collection project writes)
    file_path = os.path.join(DATA_DIR, 'card_data', 'player_card_data', pos_folder, file_name)

    card_data_df = pd.read_csv(file_path)
    return card_data_df


def save_card(card: Image, season: str, team: str, position: str, file_name: str) -> None:
    """
    Save a card PNG to a specified folder.

    :param card: The card image to save
    :param season: A str representing the season ('YYYY-YYYY')
    :param team: The team folder inside the year folder to save to
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param file_name: Name of the card to save
    :return: None
    """
    save_dir = os.path.join(PROJECT_DIR, 'player_cards', season, team, position)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file_name)

    card.save(save_path, 'PNG')
    print(f"Saved {file_name}")