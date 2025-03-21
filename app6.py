# Streamlit NBA Player Stats & XGBoost Predictions Web App
# First, install dependencies:
# pip install nba_api pandas plotly streamlit xgboost scikit-learn

import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split


def get_player_id(player_name):
    nba_players = players.get_players()
    for player in nba_players:
        if player['full_name'].lower() == player_name.lower():
            return player['id']
    return None


def fetch_games(player_id, season, location=None, games=30):
    gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    df = gamelog.get_data_frames()[0]
    if location == 'Home':
        df = df[df['MATCHUP'].str.contains('vs.')]
    elif location == 'Away':
        df = df[df['MATCHUP'].str.contains('@')]
    df = df.head(games).iloc[::-1]
    df['PRA'] = df['PTS'] + df['REB'] + df['AST']
    return df


def train_xgboost_predict(df, target_stat):
    features = ['MIN', 'FGA', 'FG3A', 'FTA', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TO', 'PF']
    df = df.dropna(subset=features + [target_stat])

    X = df[features]
    y = df[target_stat]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor()
    model.fit(X_train, y_train)

    latest_game_features = df[features].iloc[-1:].values
    prediction = model.predict(latest_game_features)[0]

    return prediction


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
            x=df['GAME_DATE'] + ' (' + df['MATCHUP'] + ')',
            y=df[stat],
            marker_color=colors,
            name=stat
        )

        line = go.Scatter(
            x=df['GAME_DATE'] + ' (' + df['MATCHUP'] + ')',
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

    st.subheader("XGBoost Predictions for Next Game")
    predictions = {}
    cols = st.columns(len(stats))

    for idx, stat in enumerate(stats):
        pred = train_xgboost_predict(df, stat)
        predictions[stat] = pred
        cols[idx].metric(label=stat, value=f"{pred:.2f}")


# Streamlit UI
st.title("NBA Player Recent Game Stats & XGBoost Predictions")

player_name = st.text_input("Enter NBA player name:", "LeBron James")
season = st.text_input("Enter season (e.g., '2023-24'):", "2023-24")
location = st.selectbox("Select game location:", ['Overall', 'Home', 'Away'])
games = st.slider("Select number of recent games:", 5, 30, 20)

if st.button("Show Stats & Predictions"):
    create_interactive_graph(player_name, season, location, games)
