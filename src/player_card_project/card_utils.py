# ====================================================================================================
# GENERAL HELPER FUNCTIONS FOR CARD GENERATION
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image, ImageChops, ImageDraw, ImageFont
import io
import ast
import os
import cairosvg
import requests
import numpy as np
import unicodedata
from datetime import datetime
from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR


def get_mode_colors(mode: str = 'light') -> dict:
    """
    Return the colors of a card style: the card background, the section background, the text, the grey of the stat bars, and the faint lines.

    :param mode: A str determining the style of card ('light' or 'dark')
    :return: A dict of RGB colors for 'background', 'section', 'text', 'unqualified_bar', and 'graph_grid'
    """
    if mode == 'light':
        colors = {
            'background': constants.WHITE, 'section': constants.SECTION_LIGHT, 'text': constants.BLACK,
            'unqualified_bar': (190, 190, 190),
            'graph_grid': (190, 190, 196),
        }
    else:
        colors = {
            'background': constants.DARK, 'section': constants.SECTION_DARK, 'text': constants.WHITE,
            'unqualified_bar': (95, 95, 95), 'graph_grid': (110, 110, 116),
        }

    return colors


def get_centered_text_top(font: ImageFont.ImageFont, lines_num: int, line_height: int, section_height: int) -> int:
    """
    Return the y position to draw the first line of a block of text so the block is centered vertically in a section, measured from the top of the
    first line's capital letters to the baseline of the last line.

    :param font: An ImageFont of the text's font
    :param lines_num: An int of how many lines the block has
    :param line_height: An int of the distance between the lines in pixels
    :param section_height: An int of the section's height in pixels
    :return: An int of the y position to draw the first line at
    """
    cap_top, baseline = font.getbbox('H')[1], font.getbbox('H')[3]
    block_height = (lines_num - 1) * line_height + baseline - cap_top
    result = round((section_height - block_height) / 2 - cap_top)
    return result


def get_stat_component_sizes(size: str) -> dict:
    """
    Return the fonts and sizes of a stat component's text and bar for a size of component.

    :param size: A str of the size of the component ('small' or 'large')
    :return: A dict with the names of the 'name_font', 'value_font' and 'percentile_font' (keys of the font cache), the 'bar_height' and 'edge_pad' (the space between the
        bar and the sides of the component), the 'bar_gap' (the space between the bottom of the stat's name and the top of its bar) and the 'percentile_stroke' (the extra stroke
        thickness of the percentile number on the bar), all in pixels
    """
    sizes = {
        'small': {'name_font': 'stat', 'value_font': 'stat', 'percentile_font': 'basic_42', 'bar_height': 46, 'edge_pad': 32, 'bar_gap': 16, 'percentile_stroke': 0.5},
        'large': {'name_font': 'stat', 'value_font': 'stat', 'percentile_font': 'basic_58', 'bar_height': 69, 'edge_pad': 39, 'bar_gap': 16, 'percentile_stroke': 0.5},
    }
    return sizes[size]


def get_bar_bottom(size: str, font_cache: dict) -> int:
    """
    Return how far down a stat component its gradient bar ends (the bar sits just below the stat name's capital letters).

    :param size: A str of the size of the component ('small' or 'large')
    :param font_cache: A dict of the fonts by name (the stat name's font is looked up in it)
    :return: An int of the y position of the bottom of the bar within the component
    """
    sizes = get_stat_component_sizes(size)
    name_font = font_cache[sizes['name_font']]
    return name_font.getbbox('H')[3] - name_font.getbbox('H')[1] + sizes['bar_gap'] + sizes['bar_height']


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


# Accent marks the heading font has no glyphs for, drawn as shapes (combining character: kind of mark)
HEADING_MARKS = {'\u0300': 'grave', '\u0301': 'acute', '\u0308': 'diaeresis', '\u030a': 'ring'}
APOSTROPHES = ("'", '\u2019')


def draw_heading_mark(draw: ImageDraw.ImageDraw, kind: str, center: float, cap_top: float, stroke: int, fill: tuple[int, int, int]) -> None:
    """
    Draws an accent mark above a letter of the heading font as blocky shapes sized to the font's stroke.

    :param draw: A PIL drawing to draw the mark on
    :param kind: A str of the mark ('grave', 'acute', 'diaeresis', or 'ring')
    :param center: A float of the x position the mark is centered on
    :param cap_top: A float of the y position of the top of the capital letters
    :param stroke: An int of the thickness of the font's strokes
    :param fill: A tuple of rgb values for the color of the mark
    :return: None
    """
    bottom = cap_top - round(stroke * 0.3)
    top = bottom - round(stroke * 0.95)
    if kind in ('acute', 'grave'):
        half, thick = round(stroke * 0.8), round(stroke * 1.1)
        if kind == 'acute':
            points = [(center - half, bottom), (center - half + thick, bottom), (center + half, top), (center + half - thick, top)]
        else:
            points = [(center + half, bottom), (center + half - thick, bottom), (center - half, top), (center - half + thick, top)]
        draw.polygon(points, fill=fill)
    elif kind == 'diaeresis':
        size, space = round(stroke * 0.9), round(stroke * 0.55)
        for left in (center - space / 2 - size, center + space / 2):
            draw.rectangle([left, top, left + size - 1, bottom - 1], fill=fill)
    else:
        # A square ring made from four bars
        half_width, ring_top, bar = round(stroke * 0.8), top - round(stroke * 0.2), round(stroke * 0.4)
        draw.rectangle([center - half_width, ring_top, center + half_width, ring_top + bar - 1], fill=fill)
        draw.rectangle([center - half_width, bottom - bar, center + half_width, bottom - 1], fill=fill)
        draw.rectangle([center - half_width, ring_top, center - half_width + bar - 1, bottom - 1], fill=fill)
        draw.rectangle([center + half_width - bar + 1, ring_top, center + half_width, bottom - 1], fill=fill)


def draw_heading_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int]) -> None:
    """
    Draws text in the heading font, which has no apostrophe or accent glyphs. Those are drawn as shapes in the same blocky style.

    :param draw: A PIL drawing to draw the text on
    :param xy: A tuple of the x and y position of the text's top left corner
    :param text: A str of the text to draw
    :param font: An ImageFont of the heading font
    :param fill: A tuple of rgb values for the color of the text
    :return: None
    """
    x, y = xy
    cap_top = y + font.getbbox('H')[1]
    cap_height = font.getmask('H').getbbox()[3]
    stroke = font.getmask('-').getbbox()[3]

    # Split the text into letters with their marks, and apostrophes
    units = []
    for char in unicodedata.normalize('NFD', text):
        if char in HEADING_MARKS and units and units[-1][0] not in APOSTROPHES:
            units[-1][1].append(HEADING_MARKS[char])
        else:
            units.append((char, []))

    # Draw runs of plain letters together to keep their spacing, and the apostrophes and marks as shapes
    run = ''
    for char, marks in units:
        if char in APOSTROPHES or marks:
            draw.text((x, y), run, font=font, fill=fill)
            x += font.getlength(run)
            run = ''
            if char in APOSTROPHES:
                draw.rectangle([x + 3, cap_top, x + 3 + stroke - 1, cap_top + round(cap_height * 0.42)], fill=fill)
                x += stroke + 6
            else:
                draw.text((x, y), char, font=font, fill=fill)
                ink_left, _, ink_right, _ = font.getmask(char).getbbox()
                for kind in marks:
                    draw_heading_mark(draw, kind, x + (ink_left + ink_right) / 2, cap_top, stroke, fill)
                x += font.getlength(char)
        else:
            run += char
    draw.text((x, y), run, font=font, fill=fill)


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


def format_signed(value: float) -> str:
    """
    Format a number to two decimals with a + or - sign (zero gets no sign, so -0.00 and +0.00 both become 0.00).

    :param value: A float to format
    :return: A str of the formatted value
    """
    text = f'{value:+.2f}'
    return '0.00' if float(text) == 0 else text


def format_stat_value(value: float, kind: str, rate_games: int) -> str:
    """
    Format a stat's per-game value for display on the card (skater rates are scaled to the games in the season and goalie rates to 60 minute rates, both given by rate_games).

    :param value: A float of the stat's per-game value
    :param kind: A str of how the stat is displayed ('war', 'count', 'percent', 'toi', 'rate', 'save', 'signed60', or 'negcount60')
    :param rate_games: An int of the games the card's rates are scaled to (from the card data)
    :return: A str of the formatted value
    """
    if kind == 'war':
        formatted = format_signed(value * rate_games)
    elif kind == 'save':
        formatted = f'{value * 100:.1f}%'
    elif kind == 'signed60':
        formatted = format_signed(value * rate_games)
    elif kind == 'negcount60':
        formatted = f'{-value * rate_games:.1f}'
    elif kind == 'count':
        formatted = f'{value * rate_games:.1f}'
    elif kind == 'percent':
        formatted = f'{value:.1f}%'
    elif kind == 'rate':
        formatted = f'{abs(value) * 100:.1f}%'
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
    Return what a stat component displays: the stat's name, the player's percentile, and the formatted value.
    A player who does not qualify for the stat gets None for the percentile (and for the value, except special teams WAR and ice time).

    :param player_row: A series from the card data
    :param attribute_key: A str of the attribute key of the stat (e.g. 'gol')
    :return: A dict with the stat's 'name' (str), the player's 'percentile' (int) and the 'value' (str)
    """
    labels = constants.GOALIE_ATTRIBUTE_LABELS if player_row['Position'] == 'G' else constants.SKATER_ATTRIBUTE_LABELS
    label = labels[attribute_key]
    name, kind = get_stat_display(player_row, attribute_key)
    score = player_row[f'{label} Score']

    if pd.isna(score):
        # Unranked special teams players still show their WAR, without a percentile
        unqualified_label = constants.SKATER_UNQUALIFIED_LABELS.get(attribute_key)
        if unqualified_label is not None and pd.notna(player_row[f'{unqualified_label} Score']):
            value = format_stat_value(player_row[f'{unqualified_label} Score'], kind, player_row['Rate Games'])
            return {'name': name, 'percentile': None, 'value': value}
        return {'name': name, 'percentile': None, 'value': None}

    # Special teams ice time is not ranked for players who do not qualify for that WAR
    qualified_by = constants.SKATER_QUALIFIED_BY.get(attribute_key)
    if qualified_by is not None and pd.isna(player_row[f'{labels[qualified_by]} Percentile']):
        return {'name': name, 'percentile': None, 'value': format_stat_value(score, kind, player_row['Rate Games'])}

    percentile = int(player_row[f'{label} Percentile'])

    result = {'name': name, 'percentile': percentile, 'value': format_stat_value(score, kind, player_row['Rate Games'])}
    return result


def get_gradient_colors(fractions: np.ndarray, solid_fraction: float) -> np.ndarray:
    """
    Return the colors of the stat bar gradient (red to purple to blue) at places along the bar. The red and blue ends hold their full color for a
    stretch before blending toward purple.

    :param fractions: An array of places along the bar, from 0 (the left end) to 1 (the right end)
    :param solid_fraction: A float of the share of the bar at each end that stays solid red or blue
    :return: An array of RGB colors, one per place
    """
    red, purple, blue = constants.STAT_GRADIENT_COLORS
    solid = solid_fraction
    colors = np.array([red, red, purple, blue, blue], dtype=float)
    positions = np.array([0, solid, 0.5, 1 - solid, 1])
    result = np.stack([np.interp(fractions, positions, colors[:, channel]) for channel in range(3)], axis=-1)
    return result


def make_percentile_bar(
        width: int, height: int, fraction: float, track_color: tuple, label: str = None, label_font: ImageFont.ImageFont = None, label_stroke: int = 0,
        *, solid_fraction: float, min_fill: float, end_hold: float, label_gap: float,
) -> Image.Image:
    """
    Make a pill shaped percentile bar: a grey track filled from the left with the red to purple to blue gradient up to the percentile, with the percentile
    written in white at the end of the fill. The smallest fill (0) is a small rounded lens, and the end of the fill holds its percentile's color for a stretch.
    A bar with no percentile is all grey with N/A in the middle.

    :param width: An int of the bar's width in pixels
    :param height: An int of the bar's height in pixels
    :param fraction: A float of the percentile from 0 to 1 (None for no percentile)
    :param track_color: An RGB tuple of the color of the unfilled part of the bar
    :param label: A str of the percentile to write at the end of the fill
    :param label_font: The font of the label
    :param label_stroke: An int of the extra stroke thickness of the label in pixels
    :param solid_fraction: A float of the share of the bar at each end of the gradient that stays solid red or blue
    :param min_fill: A float of the smallest fill of the bar (0 percentile) as a share of the bar's height
    :param end_hold: A float of how far the end of the fill holds its percentile's color, as a share of the bar's height
    :param label_gap: A float of the space between the percentile number and the end of the fill, as a share of the bar's height
    :return: An RGBA image of the percentile bar
    """
    track = Image.new('L', (width, height), 0)
    ImageDraw.Draw(track).rounded_rectangle([(0, 0), (width - 1, height - 1)], radius=height // 2, fill=255)
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    bar.paste(Image.new('RGBA', (width, height), track_color + (255,)), (0, 0), track)

    if fraction is None:
        label_xy, label_anchor, label = (width / 2, height / 2), 'mm', 'N/A'
    else:
        # The fill is a pill. One narrower than the bar is tall is a lens: the bar's rounded left end overlapped with a mirrored rounded right end
        min_fill_width = round(min_fill * height)
        fill_width = round(min_fill_width + fraction * (width - min_fill_width))
        if fill_width >= height:
            mask = Image.new('L', (fill_width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (fill_width - 1, height - 1)], radius=height // 2, fill=255)
        else:
            left_end = Image.new('L', (height, height), 0)
            ImageDraw.Draw(left_end).ellipse([(0, 0), (height - 1, height - 1)], fill=255)
            right_end = Image.new('L', (height, height), 0)
            ImageDraw.Draw(right_end).ellipse([(fill_width - height, 0), (fill_width - 1, height - 1)], fill=255)
            mask = ImageChops.multiply(left_end, right_end).crop((0, 0, fill_width, height))

        # The gradient is stretched so it reaches the percentile's color a stretch before the end of the fill, which holds that color
        hold = min(end_hold * height, 0.35 * fill_width)
        fractions = np.minimum(np.arange(fill_width) / max(fill_width - hold, 1), 1) * fraction
        fill = np.repeat(get_gradient_colors(fractions, solid_fraction).astype(np.uint8)[np.newaxis, :, :], height, axis=0)
        bar.paste(Image.fromarray(fill, 'RGB').convert('RGBA'), (0, 0), mask)
        label_xy, label_anchor = (fill_width - label_gap * height, height / 2), 'rm'

    if label:
        ImageDraw.Draw(bar).text(
            label_xy, label, font=label_font, fill=constants.WHITE + (255,), anchor=label_anchor, stroke_width=label_stroke, stroke_fill=constants.WHITE + (255,),
        )

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
