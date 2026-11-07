# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD GENERATION
# ====================================================================================================

# Imports
import os
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
    'basic_58': ImageFont.truetype(BASIC_FONT_PATH, 58),
    'stat': ImageFont.truetype(BASIC_FONT_PATH, 60),
    'title': ImageFont.truetype(HEADING_FONT_PATH, 76),
    'branding': ImageFont.truetype(BASIC_FONT_PATH, 41),
    'name': ImageFont.truetype(HEADING_FONT_PATH, 108),
    'header': ImageFont.truetype(BASIC_FONT_PATH, 60),
}


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
    colors = ch.get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    header_text_color = constants.WHITE
    header_shadow_color = constants.SECONDARY_COLORS.get(team)

    # Get banner variables
    name = player_row['Player']
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
        draft_str = f"{ch.get_ordinal(int(player_row['Overall Draft Position']))} ({int(player_row['Draft Year'])})"
    birth_country_str = constants.COUNTRY_NAMES.get(player_row['Birth Country'], player_row['Birth Country'])

    # Get stats variables
    games_played_str = str(int(player_row['Games Played']))
    if player_row['Position'] == 'G':
        stats_rows = [
            ('GP:', games_played_str), ('Record:', f"{int(player_row['Wins'])}-{int(player_row['Losses'])}-{int(player_row['OT Losses'])}"),
            ('SV%:', f"{float(player_row['Season Save %']):.1%}"), ('GSAx:', ch.format_signed(float(player_row['Season GSAx']))), ('WAR:', ch.format_signed(float(player_row['Season WAR']))),
        ]
    else:
        # The player's all situations TOI per game that season (MM:SS)
        toi_per_gp = float(player_row['TOI Per Game'])
        toi_minutes = int(toi_per_gp)
        toi_seconds = int((toi_per_gp - toi_minutes) * 60)
        stats_rows = [
            ('GP:', games_played_str), ('TOI/GP:', f'{toi_minutes}:{toi_seconds:02d}'),
            ('G-A-P:', f"{int(player_row['Season Goals'])}-{int(player_row['Season Assists'])}-{int(player_row['Season Points'])}"),
            ('xG:', f"{float(player_row['Season xGoals']):.2f}"), ('WAR:', ch.format_signed(float(player_row['Season WAR']))),
        ]

    # Create header section
    header_section_width = 1880
    header_section_height = 535
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=section_color)

    # Create draw object
    draw = ImageDraw.Draw(header_section)

    # Load fonts
    basic_font = FONT_CACHE['header']
    heading_font = FONT_CACHE['name']
    subheading_font = FONT_CACHE['title']

    # The header has the logo (and player) on the left, then the profile and the stats
    third_width = header_section_width / 3
    # The x position of the center of each column of header text (the logo is centered in the first third of the header)
    third_centers = [313, 940, 1567]
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

    # Draw banner (the name's capital letters, with their 4 pixel drop shadow, are centered in it)
    draw.rectangle([(0, 0), (header_section_width, 110)], fill=primary_team_color)
    name_cap_top, name_cap_bottom = heading_font.getbbox('H')[1], heading_font.getbbox('H')[3]
    name_y = round((110 - (name_cap_bottom - name_cap_top) - 4) / 2) - name_cap_top
    # Draw name and season drop shadow
    ch.draw_heading_text(draw, (36, name_y + 4), name, heading_font, header_shadow_color)
    ch.draw_righted_text(draw, season, heading_font, name_y + 4, header_section_width - 44, fill=header_shadow_color)
    # Draw name and season text
    ch.draw_heading_text(draw, (40, name_y), name, heading_font, header_text_color)
    ch.draw_righted_text(draw, season, heading_font, name_y, header_section_width - 40, fill=header_text_color)

    # Row y positions
    banner_height = 110
    row_pitch = 62
    title_to_first_row = 80
    title_cap_top = subheading_font.getbbox('H')[1]
    last_row_baseline = basic_font.getmetrics()[0]
    content_height = (title_to_first_row + 4 * row_pitch + last_row_baseline) - title_cap_top
    edge_space = (header_section_height - banner_height - content_height) // 2
    title_y = banner_height + edge_space - title_cap_top
    row_ys = [title_y + title_to_first_row + row_num * row_pitch for row_num in range(5)]

    # Draw profile and stats (labels and values both left aligned, centered as a block)
    profile_rows = [
        ('Position:', position_str), ('Age:', age_str), ('Size:', size_str), ('Draft:', draft_str), ('Country:', birth_country_str),
    ]
    label_gap = 26
    # Width in pixels of a typical widest value in the profile and season stats rows (the profile one is a little under the true widest so the block looks centered)
    profile_value_width = 340
    stats_value_width = 148
    # The labels of the goalie's season stats (skaters' season stats line up with them)
    goalie_stats_labels = ['GP:', 'Record:', 'SV%:', 'GSAx:', 'WAR:']
    # Skaters' season stats line up exactly where the goalies' do
    stats_label_width = max(basic_font.getlength(label) for label in goalie_stats_labels)
    for title, rows, center_x, label_width, value_width in [
        ('Profile', profile_rows, third_centers[1], max(basic_font.getlength(label) for label, _ in profile_rows), profile_value_width),
        ('Season Stats', stats_rows, third_centers[2], stats_label_width, stats_value_width),
    ]:
        ch.draw_centered_text(draw, title, subheading_font, title_y, x_center=center_x, fill=text_color)

        # Every card of a kind puts its labels and values in the same place, centered for the widest values in the data
        label_left = center_x - (label_width + label_gap + value_width) / 2
        value_x = label_left + label_width + label_gap
        for row_y, (label, value) in zip(row_ys, rows):
            draw.text(xy=(label_left, row_y), text=label, font=basic_font, fill=text_color)
            draw.text(xy=(value_x, row_y), text=value, font=basic_font, fill=text_color)

    return header_section


def make_stat_component(name: str, value: str, percentile: int, width: int, height: int, mode: str = 'light', size: str = 'small') -> Image:
    """
    Creates a stat component: the stat name and value above a bar filled with a gradient up to the percentile (written on the bar). A stat with no percentile
    gets a grey bar marked N/A, and a stat with no value shows N/A as its value.

    :param name: A str of the stat's name
    :param value: A str of the stat's value (None if it has none)
    :param percentile: An int of the percentile of the stat (None if it has none)
    :param width: An int of the component's width in pixels
    :param height: An int of the component's height in pixels
    :param mode: A str determining the style of card ('light' or 'dark')
    :param size: A str of the size of the component's text and bar ('small' or 'large')
    :return: An Image of the stat component
    """

    # Get color variables
    colors = ch.get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']

    # Get size variables
    sizes = ch.get_stat_component_sizes(size)
    name_font = FONT_CACHE[sizes['name_font']]
    value_font = FONT_CACHE[sizes['value_font']]
    percentile_font = FONT_CACHE[sizes['percentile_font']]
    bar_height = sizes['bar_height']
    edge_pad = sizes['edge_pad']
    bar_gap = sizes['bar_gap']
    percentile_stroke = sizes['percentile_stroke']
    percentile_str = None if percentile is None else str(percentile)
    fraction = None if percentile is None else percentile / 100

    # Create stat component
    stat_component = Image.new("RGB", (width, height), color=section_color)

    # Get row y positions
    name_top = name_font.getbbox('H')[1]
    bar_y = name_font.getbbox('H')[3] - name_top + bar_gap
    name_baseline_y = name_font.getmetrics()[0] - name_top

    # Draw the bar at a larger size so its edges are smooth (the percentile is drawn at the larger size too, so its stroke can be a fraction of a pixel)
    scale = 4
    shapes = Image.new('RGBA', (width * scale, height * scale), (0, 0, 0, 0))
    bar_left, bar_right = edge_pad, width - edge_pad
    percentile_font_large = ImageFont.truetype(BASIC_FONT_PATH, percentile_font.size * scale)
    # The design of the stat bar: the share of the gradient at each end that stays solid red or blue, the smallest fill (0 percentile) as a share of the bar's height,
    # how far the end of the fill holds its percentile's color (a share of the bar's height), and the space between the percentile number and the end of the fill (a share of the bar's height)
    solid_fraction, min_fill, end_hold, label_gap = 0.12, 0.8, 1.2, 0.2
    bar = ch.make_percentile_bar(
        (bar_right - bar_left) * scale, bar_height * scale, fraction, colors['unqualified_bar'], percentile_str, percentile_font_large,
        round(percentile_stroke * scale),
        solid_fraction=solid_fraction, min_fill=min_fill, end_hold=end_hold, label_gap=label_gap,
    )
    shapes.paste(bar, (bar_left * scale, bar_y * scale), bar)
    # Scale back down (BOX avoids the halo LANCZOS leaves)
    shapes = shapes.resize((width, height), Image.Resampling.BOX)
    stat_component.paste(shapes, (0, 0), shapes)

    # Create draw object
    draw = ImageDraw.Draw(stat_component)

    # Draw the stat's name (lined up with the bar's left edge)
    name_left_offset = draw.textbbox((0, 0), name, font=name_font)[0]
    draw.text(xy=(bar_left - name_left_offset, -name_top), text=name, font=name_font, fill=text_color)

    # Draw the value beside the stat name (on its baseline, ending at the right end of the bar)
    draw.text(xy=(bar_right, name_baseline_y), text=value or 'N/A', font=value_font, fill=text_color, anchor='rs')

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
    colors = ch.get_mode_colors(mode)
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
    large_edge_pad = ch.get_stat_component_sizes('large')['edge_pad']
    overall_stat = ch.get_stat_summary(player_row, 'tot')
    overall_component = make_stat_component(overall_stat['name'], overall_stat['value'], overall_stat['percentile'], bar_right_x - bar_left_x + 2 * large_edge_pad, 144, mode, size='large')
    war_section.paste(overall_component, (bar_left_x - large_edge_pad, left_top_padding))

    # Draw the title centered over the left side
    ch.draw_centered_text(draw, text=constants.WAR_SECTION_TITLE, font=FONT_CACHE['title'], y_position=14, x_center=(bar_left_x + bar_right_x) // 2, fill=text_color)

    # Add the overall WAR chart
    plot_x = bar_left_x + round(draw.textlength('100', font=FONT_CACHE['basic_34'])) + number_gap
    # The chart starts just below the overall bar and ends where it always has, above the season labels and logos
    plot_y = left_top_padding + ch.get_bar_bottom('large', FONT_CACHE) + 26
    plot_width, plot_height = bar_right_x - plot_x, war_section_height - 174 - plot_y
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
        size, bar_bottom = 'small', ch.get_bar_bottom('small', FONT_CACHE)
        sizes = ch.get_stat_component_sizes(size)
        component_bar_left, component_bar_right = bar_right_x + 104, war_section_width - bar_left_x
        component_width = component_bar_right - component_bar_left + 2 * sizes['edge_pad']
        component_x = component_bar_left - sizes['edge_pad']
        component_height = bar_bottom + 2
        chart_gap = 8
        block_gap = 28
        block_height = (war_section_height - top_padding - bottom_padding - 2 * block_gap) / 3
        chart_height = round(block_height - bar_bottom - chart_gap)
        row_pitch = block_height + block_gap
        for row_num, attribute_key in enumerate(['evs', 'pkl', 'gpp']):
            row_y = round(top_padding + row_num * row_pitch)
            stat = ch.get_stat_summary(player_row, attribute_key)
            component = make_stat_component(stat['name'], stat['value'], stat['percentile'], component_width, component_height, mode, size=size)
            war_section.paste(component, (component_x, row_y))
            ch.draw_percentile_chart(
                war_section, component_x + sizes['edge_pad'], row_y + bar_bottom + chart_gap, component_width - 2 * sizes['edge_pad'], chart_height,
                ch.get_attribute_history(player_row, attribute_key), line_color=text_color, grid_color=grid_color, dot_radius=5, line_width=3,
            )
    else:
        # Add the WAR components in two columns, each with a small percentile chart
        component_height, chart_gap = 120, 8
        bar_bottom = ch.get_bar_bottom('small', FONT_CACHE)
        small_edge_pad = ch.get_stat_component_sizes('small')['edge_pad']
        block_gap = 28
        block_height = (war_section_height - top_padding - bottom_padding - 2 * block_gap) / 3
        chart_height = round(block_height - bar_bottom - chart_gap)
        row_pitch = block_height + block_gap
        component_rows = [('evo', 'evd'), ('ppl', 'pkl'), ('fin', 'pen')]
        for row_num, row_keys in enumerate(component_rows):
            row_y = round(top_padding + row_num * row_pitch)
            for col_num, attribute_key in enumerate(row_keys):
                component_x = 950 + col_num * 450
                stat = ch.get_stat_summary(player_row, attribute_key)
                component = make_stat_component(stat['name'], stat['value'], stat['percentile'], 430, component_height, mode, size='small')
                war_section.paste(component, (component_x, row_y))
                ch.draw_percentile_chart(
                    war_section, component_x + small_edge_pad, row_y + bar_bottom + chart_gap, 430 - 2 * small_edge_pad, chart_height,
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
    colors = ch.get_mode_colors(mode)

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
        stat = ch.get_stat_summary(player_row, attribute_key)
        component = make_stat_component(stat['name'], stat['value'], stat['percentile'], width - 80, component_height, mode, size='small')
        group_section.paste(component, (40, top_padding + round(component_num * component_pitch)))

    return group_section


def make_branding_section(player_row: pd.Series, mode: str = 'light') -> Image:
    """
    Creates the branding section Image for a player card. The branding section contains the data notes on the left (wrapping before they reach the website and socials), my website and socials
    stacked to the left of the logo, and the logo on the right.

    :param player_row: A Series containing player data
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of branding section
    """

    # Get color variables
    colors = ch.get_mode_colors(mode)
    section_color = colors['section']
    text_color = colors['text']

    # Get the number of games the data is scaled to and the updated date
    rate_games = player_row['Rate Games']
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
    line_height = round(FONT_CACHE['branding'].size * 1.1)
    text_left = 40

    # Website and socials text, to the left of the logo
    contact_lines = ['Website: analyticswithavery.com', 'Socials: @analyticswavery']
    contact_width = max(draw.textlength(line, font=basic_font) for line in contact_lines)
    contact_x = logo_x - 40 - contact_width
    contact_top = ch.get_centered_text_top(basic_font, 2, line_height, branding_section_height)
    for line_num, line in enumerate(contact_lines):
        draw.text(xy=(contact_x, contact_top + line_num * line_height), text=line, font=basic_font, fill=text_color)

    # Data notes text (wraps before the website and socials)
    min_minutes = player_row['Min TOI']
    group_name = constants.POSITION_GROUP_NAMES[player_row['Position']]
    per_rate = f'{rate_games} game'
    data_notes = (
        f'Data is adjusted to a per {per_rate} rate and weighted over the past 3 seasons. '
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
    data_top = ch.get_centered_text_top(basic_font, len(lines), line_height, branding_section_height)
    for line_num, line in enumerate(lines):
        draw.text(xy=(text_left, data_top + line_num * line_height), text=line, font=basic_font, fill=text_color)

    return branding_section


def make_player_card(player_name: str, season: str, position: str, mode: str='light', save: bool=True,) -> Image:
    """
    Generate and save a full player card image for a given player and season.

    Cards include a header section, WAR section, three stat sections (individual, on-ice, and deployment for skaters, and shot danger, starts, and team for goalies),
    and a branding section. The card is saved as a PNG image in a directory specific to the season.

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

    # Get color variables
    colors = ch.get_mode_colors(mode)

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

    pos_file = constants.POSITION_FOLDERS[position]

    player_card = player_card.convert('RGB')

    file_name = f"{season}_{team}_{position}_{player_name.replace(' ', '_')}_{mode}.png"

    if save:
        data_io.save_card(player_card, season, file_name, team, pos_file)

    print(f'========== {team} {position} {player_name} ({mode}) card created for the {season} season! ==========')

    return player_card
