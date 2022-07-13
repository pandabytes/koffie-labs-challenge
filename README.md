# Koffie Labs Challenge

Link: https://github.com/KoffieLabs/backend-challenge

# Set up environment
This project uses [conda](https://docs.conda.io/en/latest/miniconda.html) to manage the Python environment. The required packages are documented in `koffie_labs.yml`.
To set up the environment to run this project, do these steps:
1. Run this command `conda env create -f koffie_labs.yml` to create the environment with the necessary packages
1. Run this command `conda activate koffie_labs` to make the `koffie_labs` environment active
1. Now the environment is ready for the project to run

# Run the app
Once the environment has been set up, do the following steps to run the app:
1. Run `uvicorn koffie.main:app`
1. The app is now running at `http://127.0.0.1:8000`
1. Go to `http://127.0.0.1:8000/docs` to see the API documentation via Swagger UI
    * You can use the Swagger UI to interact with the APIs

# Run tests
This project uses [pytest](https://docs.pytest.org/en/7.1.x/contents.html) to run tests. To run the tests, simply run `pytest` in the terminal.