# IPL Akinator

IPL Akinator is a web-based mind-reading game built with Python. Think of any IPL cricket player from 2008 to 2024, answer a series of questions, and watch the machine guess your player!

The application features a sleek, premium dark-mode interface and utilizes a custom scoring engine based on player statistics and characteristics to narrow down a pool of 788 IPL players.

## Features

- **Mind-Reading Engine**: Asks intelligent, dynamically selected questions based on entropy to guess your player in 20 questions or fewer.
- **Large Dataset**: Covers 788 IPL players from the 2008 to 2024 seasons.
- **Premium UI**: A beautiful, responsive frontend built with Streamlit, custom CSS, and modern typography (Cinzel & DM Sans).
- **RESTful Backend**: Powered by FastAPI, keeping the core game logic separated from the user interface.
- **Player Profiles**: Retrieves player photos dynamically and falls back to beautifully styled initials if no photo is found.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **API Requests**: `requests` (for Wikipedia summaries and internal API communication)

## Dataset

The dataset powering this game was custom-engineered for this project. The base statistics and player data were sourced from the [IPL Dataset 2008-2025 on Kaggle](https://www.kaggle.com/datasets/chaitu20/ipl-dataset2008-2025), and further refined to extract the specific attributes and behavioral tags needed for the Akinator engine.

## How the Engine Works

The core intelligence of the game (`engine.py`) operates on a custom-built vector space and scoring algorithm:

1. **Vector Space**: All 788 players are mapped across 27 binary features (e.g., `is_opener`, `is_finisher`, `won_orange_cap`, `played_for_csk`). True values map to 1.0, and False to 0.0.
2. **Dynamic Questioning (Entropy)**: To minimize the number of questions needed, the engine calculates the "entropy" (information gain) for each unasked feature among the top 30 candidates. It dynamically selects the question that best splits the remaining candidates in half.
3. **Scoring Algorithm**: As you answer, the engine updates scores for every player:
   - **Match**: +3.0 points for matching a trait.
   - **Negative Match**: +1.5 points for correctly lacking a trait.
   - **Contradiction Penalty**: -5.0 points. If a player reaches 3 contradictions, a compounding penalty drops them out of the likely pool.

## Project Structure

- `app.py`: The Streamlit frontend application.
- `api.py`: The FastAPI backend handling session state and game logic.
- `engine.py`: The core Akinator logic, vector space generation, and scoring mechanism.
- `ipl_master_players_final.csv`: The dataset containing player attributes and statistics.
- `dataset_refiner/`: Contains the notebook used to engineer and refine the dataset from Kaggle.
- `maintestengine/`: The main prototype of the Akinator engine built before the UI was developed.
- `run.sh`: A shell script to easily spin up both the frontend and backend.
- `requirements.txt`: Python dependencies.

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### 1. Clone the repository (if applicable) or navigate to the project directory
```bash
cd iplakinator
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

The easiest way to run the application is using the provided bash script, which starts the backend and frontend simultaneously:

```bash
chmod +x run.sh
./run.sh
```

### Running Manually

If you prefer to run them separately:

1. **Start the FastAPI Backend**:
   ```bash
   uvicorn api:app --reload --port 8000
   ```

2. **Start the Streamlit Frontend** (in a new terminal window):
   ```bash
   streamlit run app.py
   ```

The Streamlit app will typically be available at `http://localhost:8501`.

## How to Play
1. Click **Begin** on the home screen.
2. Think of an IPL player.
3. Answer the questions presented by clicking **Yes**, **No**, or **Not sure**.
4. After up to 20 questions (or when the engine is confident enough), the game will present its best guesses!

## Contributing
Contributions are welcome! If you'd like to improve the dataset, refine the scoring engine, or enhance the UI:
1. Fork the repository.
2. Create a feature branch .
3. Commit your changes .
4. Push to the branch .
5. Open a Pull Request.

## Acknowledgments
- Player images are dynamically fetched via the [Wikipedia API](https://en.wikipedia.org/api/rest_v1/).
- Fallback avatar generation provided by [UI Avatars](https://ui-avatars.com/).
- Built with [Streamlit](https://streamlit.io/) and [FastAPI](https://fastapi.tiangolo.com/).

## License
Feel free to use and modify for your own projects.
