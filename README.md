# PickMyShot

Build a golf hole and visualize the optimal path from tee to pin.

## Description

This program allows a user to build a custom golf hole, input their available clubs and respective carry distances and vizualize the optimal path that they should take to get to the hole. The frontend was built using Dash with HMTL and CSS while the backend is in Python. To determine the optimal path, a custom A* Search algorithm is used, placing different weights on factors that could affect a shot (shot distance, lie, wind, number of obstacles, proximity of endpoint to a hazard) and using distance to the pin as the heuristic function.

## Getting Started

### Installing

1. Install Anaconda. Installation instructions can be found [here](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
2. Clone this repository or download using Code -> Download ZIP and unpack the .zip file.
3. Open the Anaconda Prompt and enter
   ```
   conda env create -f environment.yml
   ```
   to create a new environment named "pickmyshot" with the required dependencies.

### Executing program

1. Open the Anaconda Prompt and activate the environment
   ```
   conda activate pickmyshot
   ```
2. Navigate to the project's folder.
3. Run the app using
   ```
   python app.py
   ```
4. Open a browser and enter "localhost:8050" in the search bar.

## Author

Jack Quirion 
<jquir073@uottawa.ca>
