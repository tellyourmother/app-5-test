# Streamlit NBA Player Stats Web App
# First, install dependencies:
# pip install nba_api pandas plotly streamlit

import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_player_id(player_name):
    nba_players = players.get_players()
    for player in nba_players:
        if player['full_name'].lower() == player_name.lower():
            return player['id']
    return None


def fetch_games(player_id, season, location=None, games=20):
    gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    df = gamelog.get_data_frames()[0]
    if location == 'Home':
        df = df[df['MATCHUP'].str.contains('vs.')]
    elif location == 'Away':
        df = df[df['MATCHUP'].str.contains('@')]
    df = df.head(games).iloc[::-1]
    df['PRA'] = df['PTS'] + df['REB'] + df['AST']
    return df


def create_interactive_graph(player_name, season, location, games=20):
    player_id = get_player_id(player_name)
    if not player_id:
        st.error(f"Player '{player_name}' not found.")
        return

    stats = ['PTS', 'REB', 'AST', 'PRA', 'MIN', 'FGA']

    df = fetch_games(player_id, season, location if location != 'Overall' else None, games)
    averages = df[stats].mean()

    fig = make_subplots(rows=3, cols=2, subplot_titles=stats)

    for i, stat in enumerate(stats):
        row = (i // 2) + 1
        col = (i % 2) + 1
        colors = ['green' if val > averages[stat] else 'gray' for val in df[stat]]

        bar = go.Bar(
            x=df['GAME_DATE'],
            y=df[stat],
            marker_color=colors,
            name=stat
        )

        line = go.Scatter(
            x=df['GAME_DATE'],
            y=[averages[stat]]*len(df),
            mode='lines',
            line=dict(color='red', dash='dash'),
            name=f'Avg {stat}',
            showlegend=False
        )

        fig.add_trace(bar, row=row, col=col)
        fig.add_trace(line, row=row, col=col)

    fig.update_layout(
        title=f"{player_name} - Last {games} {location} Games ({season})",
        height=1200,
        showlegend=False
    )

    st.plotly_chart(fig)


# Streamlit UI
st.title("NBA Player Recent Game Stats")

player_name = st.text_input("Enter NBA player name:", "LeBron James")
season = st.text_input("Enter season (e.g., '2024-25'):", "2024-25")
location = st.selectbox("Select game location:", ['Overall', 'Home', 'Away'])
games = st.slider("Select number of recent games:", 5, 30, 20)

if st.button("Show Stats"):
    create_interactive_graph(player_name, season, location, games)
