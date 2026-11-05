# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD GENERATION
# ====================================================================================================

# Imports
import os
import numpy as np
import pandas as pd
import io
import ast
import cairosvg
from PIL import Image, ImageDraw, ImageFont
from player_card_project import card_utils as ch
from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR

# Load and cache fonts
BASIC_FONT_PATH = constants.BASIC_FONT_PATH
HEADING_FONT_PATH = constants.HEADING_FONT_PATH

FONT_CACHE = {
    'basic_28': ImageFont.truetype(BASIC_FONT_PATH, 28),
    'basic_36': ImageFont.truetype(BASIC_FONT_PATH, 36),
    'basic_38': ImageFont.truetype(BASIC_FONT_PATH, 38),
    'basic_42': ImageFont.truetype(BASIC_FONT_PATH, 42),
    'basic_34': ImageFont.truetype(BASIC_FONT_PATH, 34),
    'basic_46': ImageFont.truetype(BASIC_FONT_PATH, 46),
    'basic_50': ImageFont.truetype(BASIC_FONT_PATH, 50),
    'stat': ImageFont.truetype(BASIC_FONT_PATH, constants.STAT_FONT_SIZE),
    'title': ImageFont.truetype(HEADING_FONT_PATH, constants.TITLE_FONT_SIZE),
    'branding': ImageFont.truetype(BASIC_FONT_PATH, constants.BRANDING_FONT_SIZE),
    'heading_96': ImageFont.truetype(HEADING_FONT_PATH, 96),
}


def get_mode_colors(mode: str = 'light') -> dict:
    """
    Return the colors of a card style: the card background, the section background, the text, and the dot used on the stat bars.

    :param mode: A str determining the style of card ('light' or 'dark')
    :return: A dict of RGB colors for 'background', 'section', 'text', 'unqualified_bar', and 'graph_grid'
    """
    if mode == 'light':
        colors = {
            'background': constants.WHITE, 'section': constants.SECTION_LIGHT, 'text': constants.BLACK,
            'unqualified_bar': (190, 190, 190), 'graph_grid': (190, 190, 196),
        }
    else:
        colors = {
            'background': constants.DARK, 'section': constants.SECTION_DARK, 'text': constants.WHITE,
            'unqualified_bar': (95, 95, 95), 'graph_grid': (110, 110, 116),
        }

    return colors


def make_header_section(player_row: pd.Series, mode: str = 'light') -> Image:
    """
    Creates the header section of a player card as a PIL Image. The header includes a team colored banner with the player's name and season, 
    the team logo, the player's headshot, and the player's profile and stats (skaters and goalies have their own stats).

    :param player_row: A Series containing player data
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the header section
    """

    # Get the player's team
    team = player_row['Team']

    # Get color variables
    colors = get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    header_text_color = constants.WHITE
    header_shadow_color = constants.SECONDARY_COLORS.get(team)

    # Get banner variables
    name = player_row['Player']
    header_name = name
    for symbol, replacement in constants.SYMBOLS_TO_REPLACE.items():
        header_name = header_name.replace(symbol, replacement)
    season = player_row['Season']

    # Get profile variables
    player_id = player_row['Player ID']
    position_name = constants.POSITION_NAMES.get(player_row.get('Specific Position'))
    handedness = constants.HANDEDNESS_NAMES.get(player_row.get('Shoots Catches'))
    if player_row['Position'] == 'G':
        position_str = f'{position_name} (Catches {handedness})'
    else:
        position_str = f'{position_name} (Shoots {handedness})'
    age = int(player_row['Age'])
    birth_date = ch.get_word_date(player_row['Date of Birth'])
    age_str = f'{age} ({birth_date})'
    height_in = int(player_row['Height (in)'])
    size_str = f"{height_in // 12}\'{height_in % 12}\", {int(player_row['Weight (lbs)'])} lbs"
    if pd.isna(player_row['Overall Draft Position']):
        draft_str = 'Undrafted'
    else:
        draft_str = (
            f"{ch.get_ordinal(int(player_row['Draft Round']))} Rd, {ch.get_ordinal(int(player_row['Overall Draft Position']))} Ovr "
            f"({int(player_row['Draft Year'])})"
        )
    birth_country_str = constants.COUNTRY_NAMES.get(player_row['Birth Country'], player_row['Birth Country'])

    # Get stats variables
    games_played_str = str(int(player_row['Games Played']))
    if player_row['Position'] == 'G':
        stats_rows = [
            ('Games Played:', games_played_str), ('W-L-OTL:', f"{int(player_row['Wins'])}-{int(player_row['Losses'])}-{int(player_row['OT Losses'])}"),
            ('Save %:', f"{float(player_row['Season Save %']):.3f}"), ('GSAx:', f"{float(player_row['Season GSAx']):+.2f}"), ('WAR:', f"{float(player_row['Season WAR']):+.2f}"),
        ]
    else:
        # The player's all situations TOI per game that season (MM:SS)
        toi_per_gp = float(player_row['TOI Per Game'])
        toi_minutes = int(toi_per_gp)
        toi_seconds = int((toi_per_gp - toi_minutes) * 60)
        stats_rows = [
            ('Games Played:', games_played_str), ('TOI Per Game:', f'{toi_minutes}:{toi_seconds:02d}'),
            ('G-A-P:', f"{int(player_row['Season Goals'])}-{int(player_row['Season Assists'])}-{int(player_row['Season Points'])}"),
            ('xG:', f"{float(player_row['Season xGoals']):.2f}"), ('WAR:', f"{float(player_row['Season WAR']):+.2f}"),
        ]

    # Create header section
    header_section_width = 1880
    header_section_height = 535
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=section_color)

    # Create draw object
    draw = ImageDraw.Draw(header_section)

    # Load fonts
    basic_font = FONT_CACHE['basic_50']
    heading_font = FONT_CACHE['heading_96']
    subheading_font = FONT_CACHE['title']

    # The header is split into thirds: logo and player, profile, and stats
    third_width = header_section_width / 3
    third_centers = [int(third_width * (third_num + 0.5)) for third_num in range(3)]
    left_center_x = third_centers[0]
    body_top = 110
    body_height = header_section_height - body_top

    # Crop the logo and scale it to fit the first third
    logo_margin = 12
    team_logo = ch.load_team_logo(team, mode, 1600)
    team_logo = team_logo.crop(team_logo.getchannel('A').point(lambda value: 255 if value > 8 else 0).getbbox())
    logo_scale = min((third_width - 80) / team_logo.width, (body_height - 2 * logo_margin) / team_logo.height)
    team_logo = team_logo.resize((round(team_logo.width * logo_scale), round(team_logo.height * logo_scale)), Image.Resampling.LANCZOS)
    logo_y = body_top + (body_height - team_logo.height) // 2
    header_section.paste(team_logo, (left_center_x - team_logo.width // 2, logo_y), team_logo)

    # Crop the player and scale them to fit, bottom-aligned with the header
    head_gap = 24
    headshot_img = ch.get_player_headshot(season, team, player_id)
    bbox = headshot_img.getchannel('A').point(lambda value: 255 if value > 8 else 0).getbbox()
    if bbox:
        headshot_img = headshot_img.crop(bbox)
        headshot_scale = min((body_height - head_gap) / headshot_img.height, (third_width - 80) / headshot_img.width)
        headshot_img = headshot_img.resize(
            (round(headshot_img.width * headshot_scale), round(headshot_img.height * headshot_scale)), Image.Resampling.LANCZOS
        )
        header_section.paste(headshot_img, (left_center_x - headshot_img.width // 2, header_section_height - headshot_img.height), headshot_img)

    # Draw banner
    draw.rectangle([(0, 0), (header_section_width, 110)], fill=primary_team_color)
    # Draw name and season drop shadow
    draw.text(xy=(36, 10), text=header_name, font=heading_font, fill=header_shadow_color)
    ch.draw_righted_text(draw, season, heading_font, 10, header_section_width - 44, fill=header_shadow_color)
    # Draw name and season text
    draw.text(xy=(40, 6), text=header_name, font=heading_font, fill=header_text_color)
    ch.draw_righted_text(draw, season, heading_font, 6, header_section_width - 40, fill=header_text_color)

    # Row y positions
    banner_height = 110
    row_pitch = 62
    title_to_first_row = 88
    title_cap_top = subheading_font.getbbox('H')[1]
    last_row_baseline = basic_font.getmetrics()[0]
    content_height = (title_to_first_row + 4 * row_pitch + last_row_baseline) - title_cap_top
    edge_space = (header_section_height - banner_height - content_height) // 2
    title_y = banner_height + edge_space - title_cap_top
    row_ys = [title_y + title_to_first_row + row_num * row_pitch for row_num in range(5)]

    # Draw profile and stats (labels right aligned, values left aligned)
    profile_rows = [
        ('Position:', position_str), ('Age:', age_str), ('Size:', size_str), ('Draft:', draft_str), ('Birth Country:', birth_country_str),
    ]
    label_gap = 26
    for title, rows, center_x in [('Profile', profile_rows, third_centers[1]), ('Season Stats', stats_rows, third_centers[2])]:
        ch.draw_centered_text(draw, title, subheading_font, title_y, x_center=center_x, fill=text_color)

        label_right = center_x - label_gap / 2
        value_x = center_x + label_gap / 2
        for row_y, (label, value) in zip(row_ys, rows):
            ch.draw_righted_text(draw, label, basic_font, row_y, label_right, fill=text_color)
            draw.text(xy=(value_x, row_y), text=value, font=basic_font, fill=text_color)

    return header_section


# The fonts and sizes of a stat component's text, bar, and dot for each size of component
STAT_COMPONENT_SIZES = {
    'small': {'name_font': 'stat', 'value_font': 'stat', 'percentile_font': 'basic_36', 'percentile_font_100': 'basic_36', 'bar_height': 22, 'dot_radius': 27},
    'medium': {'name_font': 'stat', 'value_font': 'stat', 'percentile_font': 'basic_42', 'percentile_font_100': 'basic_42', 'bar_height': 24, 'dot_radius': 32},
    'large': {'name_font': 'stat', 'value_font': 'stat', 'percentile_font': 'basic_50', 'percentile_font_100': 'basic_50', 'bar_height': 32, 'dot_radius': 39},
}


# The space between the bottom of a stat component's name and the top of its dot
STAT_BAR_GAP = 16

# The thickness in pixels of the ring in the section's color around a stat component's dot
STAT_DOT_RING_WIDTH = 6

# Extra stroke thickness of the percentile number in the dot
STAT_PERCENTILE_STROKE = 0.5


def get_bar_bottom(size: str) -> int:
    """
    Return how far down a stat component its gradient bar ends (the bar sits just below the stat name's capital letters).

    :param size: A str of the size of the component ('small', 'medium', or 'large')
    :return: An int of the y position of the bottom of the bar within the component
    """
    sizes = STAT_COMPONENT_SIZES[size]
    name_font = FONT_CACHE[sizes['name_font']]
    bar_center_y = name_font.getbbox('H')[3] - name_font.getbbox('H')[1] + STAT_BAR_GAP + sizes['dot_radius']
    bar_bottom = bar_center_y + sizes['bar_height'] // 2
    return bar_bottom


def make_stat_component(player_row: pd.Series, attribute_key: str, width: int, height: int, mode: str = 'light', size: str = 'small') -> Image:
    """
    Creates a stat component: the stat name and value above a gradient bar with a dot at the player's percentile.

    :param player_row: A Series containing player data
    :param attribute_key: A str representing the attribute key of the stat (e.g. 'gol')
    :param width: An int of the component's width in pixels
    :param height: An int of the component's height in pixels
    :param mode: A str determining the style of card ('light' or 'dark')
    :param size: A str of the size of the component's text and bar ('small', 'medium', or 'large')
    :return: An Image of the stat component
    """

    # Get color variables
    colors = get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']
    attribute_color = text_color

    # Get attribute name and the player's percentile, value, and place on the bar
    attribute_name = ch.get_stat_display(player_row, attribute_key)[0]
    stat = ch.get_stat_summary(player_row, attribute_key)

    # Get size variables
    sizes = STAT_COMPONENT_SIZES[size]
    name_font = FONT_CACHE[sizes['name_font']]
    value_font = FONT_CACHE[sizes['value_font']]
    # A three digit percentile (100) uses a smaller font so it fits inside the dot
    percentile_str = str(stat['percentile'])
    percentile_font = FONT_CACHE[sizes['percentile_font_100' if len(percentile_str) == 3 else 'percentile_font']]
    bar_height = sizes['bar_height']
    dot_radius = sizes['dot_radius']

    # Create stat component
    stat_component = Image.new("RGB", (width, height), color=section_color)

    # Get row y positions
    name_top = name_font.getbbox('H')[1]
    bar_center_y = name_font.getbbox('H')[3] - name_top + STAT_BAR_GAP + dot_radius
    bar_y = bar_center_y - bar_height // 2
    name_baseline_y = name_font.getmetrics()[0] - name_top

    # Draw the bar and dot at a larger size so their edges are smooth
    scale = 4
    shapes = Image.new('RGBA', (width * scale, height * scale), (0, 0, 0, 0))
    bar_left, bar_right = dot_radius, width - dot_radius
    if stat['fraction'] is not None:
        bar = ch.make_gradient_bar((bar_right - bar_left) * scale, bar_height * scale)
    # A player that does not qualify for the stat has a grey bar
    else:
        bar = Image.new('RGBA', ((bar_right - bar_left) * scale, bar_height * scale), (0, 0, 0, 0))
        ImageDraw.Draw(bar).rounded_rectangle([(0, 0), (bar.width - 1, bar.height - 1)], radius=bar.height // 2, fill=colors['unqualified_bar'])
    shapes.paste(bar, (bar_left * scale, bar_y * scale), bar)

    if stat['fraction'] is not None:
        # Keep the dot inside the bar's ends
        dot_x = bar_left + dot_radius + stat['fraction'] * (bar_right - bar_left - 2 * dot_radius)
        # Fill the dot with the bar's color at its position, with a ring in the section's color
        dot_color = tuple(int(value) for value in ch.get_gradient_colors(np.array([(dot_x - bar_left) / (bar_right - bar_left)]))[0])
        dot_draw = ImageDraw.Draw(shapes)
        for radius, fill in [(dot_radius, section_color), (dot_radius - STAT_DOT_RING_WIDTH, dot_color)]:
            dot_draw.ellipse(
                [((dot_x - radius) * scale, (bar_center_y - radius) * scale), ((dot_x + radius) * scale, (bar_center_y + radius) * scale)], fill=fill,
            )
        # The percentile is drawn at the larger size too, so its stroke can be a fraction of a pixel
        percentile_font_large = ImageFont.truetype(BASIC_FONT_PATH, percentile_font.size * scale)
        dot_draw.text(
            (dot_x * scale, bar_center_y * scale), percentile_str, font=percentile_font_large, fill=text_color + (255,), anchor='mm',
            stroke_width=round(STAT_PERCENTILE_STROKE * scale), stroke_fill=text_color + (255,),
        )
    # Scale back down (BOX avoids the halo LANCZOS leaves)
    shapes = shapes.resize((width, height), Image.Resampling.BOX)
    stat_component.paste(shapes, (0, 0), shapes)

    # Create draw object
    draw = ImageDraw.Draw(stat_component)

    # Draw attribute name (lined up with the bar's left edge)
    name_left_offset = draw.textbbox((0, 0), attribute_name, font=name_font)[0]
    draw.text(xy=(bar_left - name_left_offset, -name_top), text=attribute_name, font=name_font, fill=attribute_color)

    # Draw the value beside the stat name (on its baseline, ending at the right end of the bar)
    draw.text(xy=(bar_right, name_baseline_y), text=stat['value'] or 'N/A', font=value_font, fill=text_color, anchor='rs')

    return stat_component


def make_war_section(player_row: pd.Series, mode: str = 'light', war_section_height: int = 765) -> Image:
    """
    Creates the WAR section of a player card as a PIL Image. The left side has the overall WAR stat component with a chart of the player's overall WAR
    percentile each season (with the team logos of each season below it), and the right side has the WAR component stat components (in two columns
    for skaters and stacked for goalies), each with a small chart of the player's percentile for that component each season.

    :param player_row: A Series containing player data
    :param mode: A str determining the style of card ('light' or 'dark')
    :param war_section_height: An int of the section's height in pixels
    :return: An Image of the WAR section
    """

    # Get color variables
    colors = get_mode_colors(mode)
    text_color = colors['text']
    grid_color = colors['graph_grid']

    # Create WAR section
    war_section_width = 1880
    war_section = Image.new("RGB", (war_section_width, war_section_height), color=colors['section'])

    # Create draw object
    draw = ImageDraw.Draw(war_section)

    # Get the seasons shown (the last five, oldest first)
    seasons = [player_row['Season']]
    for _ in range(4):
        seasons.append(data_io.get_prev_season(seasons[-1]))
    seasons.reverse()

    # Add the overall WAR stat component and chart on the left of the section
    top_padding, bottom_padding, left_top_padding = 30, 22, 112
    two_thirds_x = round(war_section_width * 2 / 3)
    bar_left_x, bar_right_x, number_gap = 62, (two_thirds_x - 62 if player_row['Position'] == 'G' else 878), 12
    large_dot_radius = STAT_COMPONENT_SIZES['large']['dot_radius']
    overall_component = make_stat_component(player_row, 'tot', bar_right_x - bar_left_x + 2 * large_dot_radius, 144, mode, size='large')
    war_section.paste(overall_component, (bar_left_x - large_dot_radius, left_top_padding))

    # Draw the title centered over the left side
    ch.draw_centered_text(draw, text=constants.WAR_SECTION_TITLE, font=FONT_CACHE['title'], y_position=14, x_center=(bar_left_x + bar_right_x) // 2, fill=text_color)

    # Add the overall WAR chart
    plot_x = bar_left_x + round(draw.textlength('100', font=FONT_CACHE['basic_34'])) + number_gap
    plot_y, plot_width, plot_height = left_top_padding + 166, bar_right_x - plot_x, war_section_height - left_top_padding - 340
    # Inset the seasons by half a logo so the labels and logos stay within the chart
    logo_width, logo_height = 96, 70
    season_xs, line_ys = ch.draw_percentile_chart(
        war_section, plot_x, plot_y, plot_width, plot_height, ch.get_attribute_history(player_row, 'tot'),
        line_color=text_color, grid_color=grid_color, dot_radius=13, line_width=6, grid_width=2, inset=logo_width // 2,
    )
    for percentile, line_y in zip((0, 25, 50, 75, 100), line_ys):
        draw.text((plot_x - 12, line_y), str(percentile), font=FONT_CACHE['basic_34'], fill=grid_color, anchor='rm')
    for season_x, season in zip(season_xs, seasons):
        ch.draw_centered_text(draw, f'{season[2:4]}-{season[7:9]}', FONT_CACHE['basic_46'], y_position=plot_y + plot_height + 14, x_center=int(season_x), fill=text_color)

    # Add the team logos for each season on the graph
    teams_history = ast.literal_eval(player_row['All Teams History'])
    overall_history = ch.get_attribute_history(player_row, 'tot')
    for season_x, teams, percentile in zip(season_xs, teams_history, overall_history):
        if not teams or percentile is None:
            continue
        team_logo = ch.make_team_logo_strip(teams, mode, logo_width, logo_height)
        war_section.paste(team_logo, (int(season_x - logo_width // 2), plot_y + plot_height + 64), team_logo)

    if player_row['Position'] == 'G':
        # Add the WAR components in one column, each with a small percentile chart
        size, bar_bottom = 'small', get_bar_bottom('small')
        sizes = STAT_COMPONENT_SIZES[size]
        component_bar_left, component_bar_right = bar_right_x + 104, war_section_width - bar_left_x
        component_width = component_bar_right - component_bar_left + 2 * sizes['dot_radius']
        component_x = component_bar_left - sizes['dot_radius']
        component_height = bar_bottom + sizes['dot_radius'] + 2
        chart_gap = sizes['dot_radius'] - sizes['bar_height'] // 2 + 2
        block_gap = 40
        block_height = (war_section_height - top_padding - bottom_padding - 2 * block_gap) / 3
        chart_height = round(block_height - bar_bottom - chart_gap)
        row_pitch = block_height + block_gap
        for row_num, attribute_key in enumerate(['evs', 'pkl', 'gpp']):
            row_y = round(top_padding + row_num * row_pitch)
            component = make_stat_component(player_row, attribute_key, component_width, component_height, mode, size=size)
            war_section.paste(component, (component_x, row_y))
            ch.draw_percentile_chart(
                war_section, component_x + sizes['dot_radius'], row_y + bar_bottom + chart_gap, component_width - 2 * sizes['dot_radius'], chart_height,
                ch.get_attribute_history(player_row, attribute_key), line_color=text_color, grid_color=grid_color, dot_radius=5, line_width=3,
            )
    else:
        # Add the WAR components in two columns, each with a small percentile chart
        component_height, chart_gap = 120, 12
        bar_bottom = get_bar_bottom('small')
        small_dot_radius = STAT_COMPONENT_SIZES['small']['dot_radius']
        block_gap = 40
        block_height = (war_section_height - top_padding - bottom_padding - 2 * block_gap) / 3
        chart_height = round(block_height - bar_bottom - chart_gap)
        row_pitch = block_height + block_gap
        component_rows = [('evo', 'evd'), ('ppl', 'pkl'), ('fin', 'pen')]
        for row_num, row_keys in enumerate(component_rows):
            row_y = round(top_padding + row_num * row_pitch)
            for col_num, attribute_key in enumerate(row_keys):
                component_x = 960 + col_num * 450
                component = make_stat_component(player_row, attribute_key, 410, component_height, mode, size='small')
                war_section.paste(component, (component_x, row_y))
                ch.draw_percentile_chart(
                    war_section, component_x + small_dot_radius, row_y + bar_bottom + chart_gap, 410 - 2 * small_dot_radius, chart_height,
                    ch.get_attribute_history(player_row, attribute_key),
                    line_color=text_color, grid_color=grid_color, dot_radius=5, line_width=3,
                )

    return war_section


def make_stat_group_section(player_row: pd.Series, title: str, attribute_keys: list, width: int, height: int, mode: str = 'light') -> Image:
    """
    Creates a section of a player card that holds a title and a column of stat components (Ex: the individual stats).

    :param player_row: A Series containing player data
    :param title: A str of the section's title
    :param attribute_keys: A list of the attribute keys of the stat components to show, from top to bottom (None leaves that slot blank)
    :param width: An int of the section's width in pixels
    :param height: An int of the section's height in pixels
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the stat group section
    """

    # Get color variables
    colors = get_mode_colors(mode)

    # Create stat group section
    group_section = Image.new("RGB", (width, height), color=colors['section'])

    # Create draw object
    draw = ImageDraw.Draw(group_section)

    # Draw title
    ch.draw_centered_text(draw, text=title, font=FONT_CACHE['title'], y_position=14, x_center=width // 2, fill=colors['text'])

    # Draw stat components, spread evenly down the section (a blank slot, None, is left empty)
    component_height, top_padding, bottom_padding = 130, 112, 22
    component_pitch = (height - top_padding - bottom_padding - component_height) / (len(attribute_keys) - 1)
    for component_num, attribute_key in enumerate(attribute_keys):
        if attribute_key is None:
            continue
        component = make_stat_component(player_row, attribute_key, width - 80, component_height, mode, size='medium')
        group_section.paste(component, (40, top_padding + round(component_num * component_pitch)))

    return group_section


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


def make_branding_section(player_row: pd.Series, mode: str = 'light') -> Image:
    """
    Creates the branding section Image for a player card. The branding section contains the data notes on the left (wrapping before they reach the website and socials), my website and socials
    stacked to the left of the logo, and the logo on the right.

    :param player_row: A Series containing player data
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of branding section
    """

    # Get color variables
    colors = get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']

    # Get the number of games the data is scaled to and the updated date
    season_games = ch.get_season_games(player_row['Season'])
    update_date = constants.UPDATE_DATE

    # Create branding section
    branding_section_width = 1880
    branding_section_height = 125
    branding_section = Image.new("RGB", (branding_section_width, branding_section_height), color=section_color)

    # Create draw image
    draw = ImageDraw.Draw(branding_section)

    # Add logo (the logo's knocked out areas are the section's color)
    with open(os.path.join(constants.ASSETS_DIR, 'images', 'analyticswithavery_logo.svg'), 'r') as f:
        svg_text = f.read()
    svg_text = svg_text.replace('<rect width="1000" height="1000" fill="#272727"/>', '')
    svg_text = svg_text.replace('#272727', '#{:02x}{:02x}{:02x}'.format(*section_color))
    logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_text.encode(), output_width=1000, output_height=1000))).convert('RGBA')
    logo = logo.crop(logo.getbbox())
    logo_height = 98
    logo = logo.resize((int(logo.width * logo_height / logo.height), logo_height), Image.Resampling.LANCZOS)
    # The logo is on the right side
    logo_x = branding_section_width - 30 - logo.width
    branding_section.paste(logo, (logo_x, (branding_section_height - logo_height) // 2), logo)

    # Get the font and the line height
    basic_font = FONT_CACHE['branding']
    line_height = round(constants.BRANDING_FONT_SIZE * 1.1)
    text_left = 40

    # Website and socials text, to the left of the logo
    contact_lines = ['Website: analyticswithavery.com', 'Socials: @analyticswavery']
    contact_width = max(draw.textlength(line, font=basic_font) for line in contact_lines)
    contact_x = logo_x - 40 - contact_width
    contact_top = get_centered_text_top(basic_font, 2, line_height, branding_section_height)
    for line_num, line in enumerate(contact_lines):
        draw.text(xy=(contact_x, contact_top + line_num * line_height), text=line, font=basic_font, fill=text_color)

    # Data notes text (wraps before the website and socials)
    min_minutes = (constants.GOALIE_MIN_TOI if player_row['Position'] == 'G' else constants.SKATER_MIN_TOI)[player_row['Season']]
    group_name = constants.POSITION_GROUP_NAMES[player_row['Position']]
    per_rate = f'{constants.GOALIE_RATE_GAMES} game' if player_row['Position'] == 'G' else f'{season_games} game'
    data_notes = (
        f'Data is weighted over the past 3 seasons. Data is 5v5 and adjusted to a per {per_rate} rate unless otherwise stated. '
        f'Percentiles compare {group_name} with at least {min_minutes} minutes. '
        f'All data and images from the NHL. Updated {update_date}.'
    )
    text_max_width = contact_x - 40 - text_left
    lines = ['']
    for word in data_notes.split(' '):
        candidate = f'{lines[-1]} {word}'.strip()
        if draw.textlength(candidate, font=basic_font) <= text_max_width or not lines[-1]:
            lines[-1] = candidate
        else:
            lines.append(word)
    data_top = get_centered_text_top(basic_font, len(lines), line_height, branding_section_height)
    for line_num, line in enumerate(lines):
        draw.text(xy=(text_left, data_top + line_num * line_height), text=line, font=basic_font, fill=text_color)

    return branding_section


def make_card(player_cur_season: pd.Series, mode: str = 'light') -> Image:
    """
    Generate a full card image from a player's card data. The card has a header section, a WAR section, three stat sections (individual, on-ice, and
    deployment for skaters, and shot danger, starts, and team for goalies), and a branding section.

    :param player_cur_season: A Series containing the player's card data for the season
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the player card
    """

    # Get color variables
    colors = get_mode_colors(mode)

    # Create player card
    card_width = 2000
    card_height = 2500
    player_card = Image.new('RGB', (card_width, card_height), color=colors['background'])

    # Spacing between sections and the section corner radius
    spacing = 30
    margin = spacing * 2
    radius = 38

    # Add header section
    header_section = make_header_section(player_cur_season, mode)
    header_y = margin
    # Round only the card's top and bottom corners
    ch.paste_rounded(player_card, header_section, (margin, header_y), radius, corners=(True, True, False, False))

    # Add WAR section
    # The WAR section is shorter than the stat group sections
    war_section_height = 730
    stat_section_height = 900
    war_section = make_war_section(player_cur_season, mode, war_section_height)
    war_y = header_y + header_section.height + spacing
    ch.paste_rounded(player_card, war_section, (margin, war_y), radius, corners=(False, False, False, False))

    # Add the three stat group sections side by side
    group_sections = constants.GOALIE_STAT_SECTIONS if player_cur_season['Position'] == 'G' else constants.SKATER_STAT_SECTIONS
    groups_y = war_y + war_section.height + spacing
    groups_width = card_width - 2 * margin
    group_x = margin
    for group_num, (title, attribute_keys) in enumerate(group_sections):
        # Split the width evenly (any leftover pixels go to the first sections)
        width = (groups_width - 2 * spacing) // 3 + (1 if group_num < (groups_width - 2 * spacing) % 3 else 0)
        group_section = make_stat_group_section(player_cur_season, title, attribute_keys, width, stat_section_height, mode)
        ch.paste_rounded(player_card, group_section, (group_x, groups_y), radius, corners=(False, False, False, False))
        group_x += width + spacing

    # Add branding section
    branding_section = make_branding_section(player_cur_season, mode)
    branding_y = groups_y + stat_section_height + spacing
    ch.paste_rounded(player_card, branding_section, (margin, branding_y), radius, corners=(False, False, True, True))

    return player_card


def make_player_card(player_name: str, season: str, position: str, mode: str='light', save: bool=True,) -> Image:
    """
    Generate and save a full player card image for a given player and season.

    Cards include a header section, WAR section, three stat sections, and a branding section. The card is saved as a PNG image in a directory
    specific to the season.

    :param player_name: A str of the full name of the player (e.g. 'Auston Matthews')
    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :param save: A bool of whether to save the card (default is True)
    :return: An Image of the player card
    """

    # Get the player's current season data
    player_cur_season = ch.get_player_single_season(player_name, season, position)

    # Get the player's team
    team = player_cur_season['Team']

    # Make the card
    player_card = make_card(player_cur_season, mode)

    pos_file = constants.POSITION_FOLDERS[position]

    player_card = player_card.convert('RGB')

    file_name = f"{season}_{team}_{position}_{player_name.replace(' ', '_')}_{mode}.png"

    if save:
        data_io.save_card(player_card, season, team, pos_file, file_name)

    print(f'========== {team} {position} {player_name} ({mode}) card created for the {season} season! ==========')

    return player_card
