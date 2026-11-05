# ====================================================================================================
# GENERAL HELPER FUNCTIONS FOR CARD GENERATION
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import ast
import os
import cairosvg
import requests
import numpy as np
from datetime import datetime
from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR


def draw_centered_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        y_position: int,
        x_center: int = 1000,
        fill: tuple[int, int, int] = (0, 0, 0),
        stroke_width: int = 0,
        stroke_fill: tuple[int, int, int] = None,
    ) -> None:
    """
    Draws text that is centered on a PIL drawing.

    :param draw: A PIL drawing that will have the text centered on it
    :param text: A str of the text to be centered
    :param font: An ImageFont of the text's font
    :param y_position: An int of where the y position will be
    :param x_center: An int of where the center x position is (default is at 1000)
    :param fill: A tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :param stroke_width: An int outline thickness in pixels around the text (default is 0/no outline)
    :param stroke_fill: A tuple of rgb values for the outline color (default is None)
    :return: None
    """

    text_bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = x_center - (text_width // 2)
    draw.text((x_position, y_position), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def draw_righted_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    y_position: int,
    x_right: int,
    fill: tuple[int, int, int] = (0, 0, 0)
    ) -> None:
    """
    Draws text that right-aligned on a PIL drawing.

    :param draw: A PIL drawing that will have the text right-aligned on it
    :param text: A str of the text to be right-aligned
    :param font: An ImageFont of the text's font
    :param y_position: An int of where the y position will be
    :param x_right: An int of where the right most x position is
    :param fill: A tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :return: None
    """

    text_width = draw.textbbox((0, 0), str(text), font=font)[2] 
    x_position = x_right - text_width 
    draw.text((x_position, y_position), str(text), font=font, fill=fill)


def get_word_date(number_date: str) -> str:
    """
    Converts a date from number format to word format (Ex: 2001-02-03 -> Feb 3, 2001).

    :param number_date: A str of date in number format (YYYY-MM-DD)
    :return: A str of the date in word format (Month Day, Year)
    """
    date_obj = datetime.strptime(number_date, '%Y-%m-%d')
    word_date = f"{date_obj.strftime('%b')} {date_obj.day}, {date_obj.year}"

    return word_date


def get_player_headshot(season: str, team: str, player_id: float) -> Image.Image:
    """
    Fetch a player's headshot image based on the season, team, and player ID.
    
    :param season: A str representing the season ('YYYY-YYYY')
    :param team: A str of the team abbreviation to get the headshot for ('ABC')
    :param player_id: A float of the player ID to get the headshot for ('#######')
    :return: PIL Image object
    """

    season_clean = season.replace('-', '')
    if player_id is not None and not np.isnan(player_id):
        player_id_clean = str(int(player_id))
    else:
        player_id_clean = 000
    headshot_url = f"https://assets.nhle.com/mugs/nhl/{season_clean}/{team}/{player_id_clean}.png"

    try:
        response = requests.get(headshot_url, stream=True, timeout=5)
        response.raise_for_status()
        img_bytes = response.content
    except requests.RequestException:
        try:
            fallback_url = 'https://assets.nhle.com/mugs/nhl/default-skater.png'
            response = requests.get(fallback_url, stream=True, timeout=5)
            img_bytes = response.content
        except requests.RequestException:
            # Network unavailable
            img_bytes = None

    if img_bytes is None:
        # A blank transparent image
        img = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    else:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        img_data = img.getdata()
        img.putdata([
            (255, 255, 255, 0) if pixel[:2] == (255, 255, 255) else pixel
            for pixel in img_data
        ])

    return img


def get_attribute_column(player_row: pd.Series, attribute_key: str, suffix: str) -> str:
    """
    Return the card data column for an attribute, such as 'Total WAR Percentile' for key 'tot' and suffix 'Percentile'.
    Goalies have their own attribute labels, so the player's position picks the set.

    :param player_row: A series from the card data (needs a 'Position' value)
    :param attribute_key: The short attribute key used by the card code (e.g. 'tot', 'evo', 'ldg')
    :param suffix: 'Percentile', 'Rank', or 'History'
    :return: The column name in the card data
    """
    labels = constants.GOALIE_ATTRIBUTE_LABELS if player_row['Position'] == 'G' else constants.SKATER_ATTRIBUTE_LABELS
    result = f'{labels[attribute_key]} {suffix}'
    return result


def get_player_single_season(player_name: str, season: str, position: str) -> pd.DataFrame:
    """
    Return a Series of a player's card data for a single season.

    :param player_name: A str of the full name of the player to return the multiple seasons for ('First Last')
    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: A Series containing player stats for the given season
    """

    # Load the current season's card data
    season_data = data_io.load_card_data_csv(season, position)

    # Get player row
    player_season = season_data.loc[season_data['Player'] == player_name].copy()
    if player_season.empty:
        raise ValueError(f"{player_name} not found in {season} {position} card data.")
    player_season = player_season.iloc[0]

    return player_season



def get_ordinal(number: int) -> str:
    """
    Return a number with its ordinal suffix (Ex: 1 -> 1st, 22 -> 22nd, 113 -> 113th).

    :param number: An int to add the suffix to
    :return: A str of the number with its suffix
    """
    if 10 <= number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')

    result = f'{number}{suffix}'
    return result


def get_season_games(season: str) -> int:
    """
    Return the number of games per-game rates are scaled to for a season (82, or 84 from the 2026-2027 season on).

    :param season: A str representing the season ('YYYY-YYYY')
    :return: An int of the games in a season
    """
    if int(season.split('-')[0]) >= constants.LONG_SEASON_START_YEAR:
        season_games = constants.LONG_SEASON_LENGTH
    else:
        season_games = constants.SEASON_LENGTH

    return season_games


def format_stat_value(value: float, kind: str, season: str) -> str:
    """
    Format a stat's per-game value for display on the card (skater rates are scaled to the season length and goalie rates to GOALIE_RATE_GAMES games).

    :param value: A float of the stat's per-game value
    :param kind: A str of how the stat is displayed ('war', 'count', 'percent', 'toi', 'rate', 'save', 'war60', 'signed60', or 'negcount60')
    :param season: A str representing the season ('YYYY-YYYY')
    :return: A str of the formatted value
    """
    season_games = get_season_games(season)

    if kind == 'war':
        formatted = f'{value * season_games:+.2f}'
    elif kind == 'save':
        formatted = f'{value:.3f}'
    elif kind == 'war60':
        formatted = f'{value * constants.GOALIE_RATE_GAMES:+.2f}'
    elif kind == 'signed60':
        formatted = f'{value * constants.GOALIE_RATE_GAMES:+.2f}'
    elif kind == 'negcount60':
        formatted = f'{-value * constants.GOALIE_RATE_GAMES:.1f}'
    elif kind == 'count':
        formatted = f'{value * season_games:.1f}'
    elif kind == 'percent':
        formatted = f'{value / 100:.3f}'
    elif kind == 'rate':
        formatted = f'{abs(value):.3f}'
    else:
        minutes = int(value)
        seconds = int(round((value - minutes) * 60))
        if seconds == 60:
            minutes, seconds = minutes + 1, 0
        formatted = f'{minutes}:{seconds:02d}'

    return formatted


def get_stat_display(player_row: pd.Series, attribute_key: str) -> tuple[str, str]:
    """
    Return the name shown on the card for a stat and how its value is displayed (goalies and skaters have their own stats).

    :param player_row: A series from the card data (needs a 'Position' value)
    :param attribute_key: A str of the attribute key of the stat (e.g. 'gol' or 'ldg')
    :return: A tuple of the stat's name and the kind of value it displays
    """
    displays = constants.GOALIE_STAT_DISPLAY if player_row['Position'] == 'G' else constants.SKATER_STAT_DISPLAY
    result = displays[attribute_key]
    return result


def get_stat_summary(player_row: pd.Series, attribute_key: str) -> dict:
    """
    Return what a stat component displays: the player's percentile, formatted value, and place on the bar.
    A player who does not qualify for the stat gets None for the percentile and place (and for the value, except special teams WAR and ice time).

    :param player_row: A series from the card data
    :param attribute_key: A str of the attribute key of the stat (e.g. 'gol')
    :return: A dict with the player's 'percentile' (int), 'value' (str), and 'fraction' (float from 0 to 1 along the bar, the percentile divided by 100)
    """
    labels = constants.GOALIE_ATTRIBUTE_LABELS if player_row['Position'] == 'G' else constants.SKATER_ATTRIBUTE_LABELS
    label = labels[attribute_key]
    kind = get_stat_display(player_row, attribute_key)[1]
    score = player_row[f'{label} Score']

    if pd.isna(score):
        # Unranked special teams players still show their WAR, without a percentile
        unqualified_label = constants.SKATER_UNQUALIFIED_LABELS.get(attribute_key)
        if unqualified_label is not None and pd.notna(player_row[f'{unqualified_label} Score']):
            value = format_stat_value(player_row[f'{unqualified_label} Score'], kind, player_row['Season'])
            return {'percentile': None, 'value': value, 'fraction': None}
        return {'percentile': None, 'value': None, 'fraction': None}

    # Special teams ice time is not ranked for players who do not qualify for that WAR
    qualified_by = constants.SKATER_QUALIFIED_BY.get(attribute_key)
    if qualified_by is not None and pd.isna(player_row[f'{labels[qualified_by]} Percentile']):
        return {'percentile': None, 'value': format_stat_value(score, kind, player_row['Season']), 'fraction': None}

    # The bar runs from the 0th to the 100th percentile
    percentile = int(player_row[f'{label} Percentile'])

    result = {
        'percentile': percentile,
        'value': format_stat_value(score, kind, player_row['Season']),
        'fraction': percentile / 100,
    }
    return result


def get_gradient_colors(fractions: np.ndarray) -> np.ndarray:
    """
    Return the colors of the stat bar gradient (red to purple to blue) at places along the bar. The red and blue ends hold their full color for a
    stretch before blending toward purple.

    :param fractions: An array of places along the bar, from 0 (the left end) to 1 (the right end)
    :return: An array of RGB colors, one per place
    """
    red, purple, blue = constants.STAT_GRADIENT_COLORS
    solid = constants.STAT_GRADIENT_SOLID_FRACTION
    colors = np.array([red, red, purple, blue, blue], dtype=float)
    positions = np.array([0, solid, 0.5, 1 - solid, 1])
    result = np.stack([np.interp(fractions, positions, colors[:, channel]) for channel in range(3)], axis=-1)
    return result


def make_gradient_bar(width: int, height: int) -> Image.Image:
    """
    Make a pill shaped bar that goes from red to purple to blue (the colours used on the website).

    :param width: An int of the bar's width in pixels
    :param height: An int of the bar's height in pixels
    :return: An RGBA image of the gradient bar
    """
    gradient = get_gradient_colors(np.linspace(0, 1, width)).astype(np.uint8)
    gradient = np.repeat(gradient[np.newaxis, :, :], height, axis=0)
    bar = Image.fromarray(gradient, 'RGB').convert('RGBA')

    mask = Image.new('L', (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (width - 1, height - 1)], radius=height // 2, fill=255)
    bar.putalpha(mask)

    return bar


def paste_rounded(
        card: Image.Image,
        section: Image.Image,
        position: tuple[int, int],
        radius: int,
        corners: tuple[bool, bool, bool, bool] = (True, True, True, True),
    ) -> None:
    """
    Paste a section onto the card with rounded corners (any corner can be left square).

    :param card: The card image the section is pasted onto
    :param section: The section image to paste
    :param position: A tuple of the (x, y) position of the section's top left corner
    :param radius: An int of the corner radius in pixels
    :param corners: A tuple of whether the top left, top right, bottom right, and bottom left corners are rounded (default is all of them)
    :return: None
    """
    scale = 4
    mask = Image.new('L', (section.width * scale, section.height * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (mask.width - 1, mask.height - 1)], radius=radius * scale, fill=255, corners=corners)
    mask = mask.resize(section.size, Image.Resampling.BOX)

    card.paste(section, position, mask)


def load_team_logo(team: str, mode: str, width: int) -> Image.Image:
    """
    Load a team's logo resized to a width (keeping its proportions).

    :param team: A str of the team abbreviation ('ABC')
    :param mode: A str determining the style of the logo ('light' or 'dark')
    :param width: An int of the logo's width in pixels
    :return: An RGBA image of the team logo
    """
    with open(os.path.join(constants.ASSETS_DIR, 'team_logos', f'{team}_{mode}.svg'), 'rb') as f:
        svg_bytes = f.read()
    team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert('RGBA')

    logo_height = int(team_logo.height * width / team_logo.width)
    team_logo = team_logo.resize((width, logo_height), Image.Resampling.LANCZOS)

    return team_logo


def make_team_logo_strip(teams: list, mode: str, width: int, height: int) -> Image.Image:
    """
    Make the logo for a season. Each logo is cropped to its visible part and scaled as large as fits in the width and height. A player that played for
    multiple teams gets one logo split like a pie into an equal slice for each team, in the order they were played for, starting at the top and going
    counterclockwise (Ex: two teams are the left half of the first team's logo next to the right half of the second team's).

    :param teams: A list of team abbreviations played for in the season, in order
    :param mode: A str determining the style of the logos ('light' or 'dark')
    :param width: An int of the logo's width in pixels
    :param height: An int of the logo's height in pixels
    :return: An RGBA image of the logo
    """
    teams_num = len(teams)

    # Find each pixel's team slice (at a larger size for smooth edges)
    scale = 4
    y_grid, x_grid = np.mgrid[0:height * scale, 0:width * scale]
    x_offset = (x_grid + 0.5) - width * scale / 2
    y_offset = (y_grid + 0.5) - height * scale / 2
    # Angle counterclockwise from straight up, from 0 to 360 degrees
    angles = np.degrees(np.arctan2(-x_offset, -y_offset)) % 360
    slice_nums = np.minimum((angles / (360 / teams_num)).astype(int), teams_num - 1)

    logo_strip = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    for i, team in enumerate(teams):
        team_logo = load_team_logo(team, mode, 800)
        team_logo = team_logo.crop(team_logo.getchannel('A').point(lambda value: 255 if value > 8 else 0).getbbox())
        logo_scale = min(width / team_logo.width, height / team_logo.height)
        team_logo = team_logo.resize((round(team_logo.width * logo_scale), round(team_logo.height * logo_scale)), Image.Resampling.LANCZOS)

        # Center the logo on a canvas the size of the whole logo so every team's slice lines up
        canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        canvas.paste(team_logo, ((width - team_logo.width) // 2, (height - team_logo.height) // 2), team_logo)

        # Keep only this team's slice of its logo
        slice_mask = Image.fromarray(((slice_nums == i) * 255).astype(np.uint8), 'L').resize((width, height), Image.Resampling.BOX)
        slice_logo = canvas.copy()
        slice_logo.putalpha(Image.fromarray(np.minimum(np.array(canvas.getchannel('A')), np.array(slice_mask))))
        logo_strip.alpha_composite(slice_logo)

    return logo_strip


def get_attribute_history(player_row: pd.Series, attribute_key: str) -> list:
    """
    Return a skater's percentile for an attribute in each of the last five seasons (oldest first). A season the player was not ranked in is None.

    :param player_row: A series from the card data
    :param attribute_key: A str of the attribute key (e.g. 'tot', 'ppl')
    :return: A list of five percentiles (int or None)
    """
    history = player_row[get_attribute_column(player_row, attribute_key, 'History')]
    if isinstance(history, str):
        history = ast.literal_eval(history)

    result = [None if value is None or pd.isna(value) else int(value) for value in history]
    return result


def draw_percentile_chart(
        card_image: Image.Image,
        x: int,
        y: int,
        width: int,
        height: int,
        values: list,
        line_color: tuple[int, int, int],
        grid_color: tuple[int, int, int],
        dot_radius: int,
        line_width: int,
        grid_width: float = 1.5,
        inset: int = None,
    ) -> tuple[list, list]:
    """
    Draw a small chart of a player's percentile in each of five seasons: faint lines at the 0, 25, 50, 75, and 100 percentiles and the player's line
    and dots over them (a season without a percentile leaves a gap).

    :param card_image: The image the chart is drawn onto
    :param x: An int of the chart's left edge
    :param y: An int of the chart's top edge
    :param width: An int of the chart's width in pixels
    :param height: An int of the chart's height in pixels
    :param values: A list of five percentiles (int or None), oldest season first
    :param line_color: A tuple of rgb values for the player's line and dots
    :param grid_color: A tuple of rgb values for the percentile lines
    :param dot_radius: An int of the radius of the dots in pixels
    :param line_width: An int of the player's line width in pixels
    :param grid_width: A float of the width of the percentile lines in pixels (default is 1.5)
    :param inset: An int of how far the first and last seasons are from the ends of the chart (default is a little more than a dot's radius)
    :return: A tuple of a list of the x position of each season and a list of the y positions of the 0, 25, 50, 75, and 100 lines on the card image
    """

    # Draw at a larger size so the lines and dots are smooth
    scale = 4
    layer = Image.new('RGBA', (width * scale, height * scale), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)

    top, bottom = dot_radius + 2, height - dot_radius - 2
    percentile_y = lambda percentile: bottom - (bottom - top) * percentile / 100
    for percentile in (0, 25, 50, 75, 100):
        layer_draw.line([(0, percentile_y(percentile) * scale), (width * scale, percentile_y(percentile) * scale)], fill=grid_color + (255,), width=int(grid_width * scale))

    if inset is None:
        inset = dot_radius + 6
    season_xs = [inset + (width - 2 * inset) * i / 4 for i in range(5)]
    seasons = [(i, value) for i, value in enumerate(values) if value is not None]

    # Connect seasons that are next to each other
    for (i, value), (next_i, next_value) in zip(seasons, seasons[1:]):
        if next_i - i == 1:
            layer_draw.line(
                [(season_xs[i] * scale, percentile_y(value) * scale), (season_xs[next_i] * scale, percentile_y(next_value) * scale)],
                fill=line_color + (255,), width=int(line_width * scale),
            )
    for i, value in seasons:
        layer_draw.ellipse(
            [(season_xs[i] - dot_radius) * scale, (percentile_y(value) - dot_radius) * scale, (season_xs[i] + dot_radius) * scale, (percentile_y(value) + dot_radius) * scale],
            fill=line_color + (255,),
        )

    layer = layer.resize((width, height), Image.Resampling.BOX)
    card_image.paste(layer, (x, y), layer)

    result = ([x + season_x for season_x in season_xs], [y + percentile_y(percentile) for percentile in (0, 25, 50, 75, 100)])
    return result
