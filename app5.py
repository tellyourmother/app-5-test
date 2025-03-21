import streamlit as st
import pandas as pd
import plotly.express as px
from nba_api.stats.endpoints import playergamelog, leaguedashplayerstats
from nba_api.stats.static import players
from PIL import Image
import requests
import io

# Function to get player ID
def get_player_id(player_name):
    player_dict = players.get_players()
    for player in player_dict:
        if player['full_name'].lower() == player_name.lower():
            return player['id']
    return None

# Function to fetch game log data
def get_player_game_log(player_id, season="2023-24"):
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    df = game_log.get_data_frames()[0]
    df = df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'FG_PCT', 'MIN']]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df.sort_values('GAME_DATE')
    return df

# Function to fetch defensive matchup data
def get_defensive_matchup(team_abbr):
    league_stats = leaguedashplayerstats.LeagueDashPlayerStats(season="2023-24").get_data_frames()[0]
    guards = league_stats[league_stats['PLAYER_POSITION'].isin(["G", "PG", "SG"])]
    team_avg = guards[guards['TEAM_ABBREVIATION'] == team_abbr]['PTS'].mean()
    return round(team_avg, 1) if not pd.isna(team_avg) else "N/A"

# Function to fetch team logos
def get_team_logo(team_abbr):
    team_logos = {
        "ATL": "https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg",
        "BOS": "https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg",
        "CHA": "https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg",
        "CHI": "https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg",
        "CLE": "https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg",
        "GSW": "https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg",
        "LAL": "https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg",
        "MIA": "https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg",
        "MIL": "https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg",
        "NYK": "https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg",
        "PHI": "https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg",
        "PHX": "https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg",
    }
    return team_logos.get(team_abbr, "")

# Streamlit UI
st.title("NBA Player Performance Dashboard")

# User Input: Player Name
player_name = st.text_input("Enter Player Name:", "Stephen Curry")

# User Input: Season Selection
season = st.selectbox("Select Season:", [f"{year}-{year+1}" for year in range(2000, 2024)], index=23)

# Fetch player ID
player_id = get_player_id(player_name)

if player_id:
    # Get player game logs
    df = get_player_game_log(player_id, season)

    if df.empty:
        st.error("No game data found for this player in the selected season.")
    else:
        # Get last matchup team
        team_abbr = df.iloc[-1]['MATCHUP'].split()[-1]
        def_avg = get_defensive_matchup(team_abbr)
        logo_url = get_team_logo(team_abbr)

        # Display Team Logo
        if logo_url:
            response = requests.get(logo_url)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                st.image(img, caption=f"Opponent: {team_abbr}", width=100)

        # Display Season Game Log
        st.subheader("Season Game Log")
        fig1 = px.bar(df, x="PTS", y="GAME_DATE", orientation="h", color="PTS", title=f"{player_name} - {season} Season")
        st.plotly_chart(fig1)

        # Display Minutes Trend
        st.subheader("Minutes Trend")
        fig2 = px.line(df, x="GAME_DATE", y="MIN", markers=True, line_shape="spline", title="Minutes Played Per Game")
        st.plotly_chart(fig2)

        # Display Defensive Matchup
        st.subheader("Defensive Matchup")
        fig3 = px.pie(names=["Opponent Guards Avg", "League Best"], values=[def_avg, 43], hole=0.6, title=f"Defense - {team_abbr}")
        st.plotly_chart(fig3)

        # Display Shooting Stats
        st.subheader("Shooting % / Rebounds / Assists Per Game")
        fig4 = px.bar(df, x="GAME_DATE", y=["FG_PCT", "REB", "AST"], title="Shooting Efficiency & Contributions")
        st.plotly_chart(fig4)

else:
    st.error("Player not found! Please check the spelling and try again.")
