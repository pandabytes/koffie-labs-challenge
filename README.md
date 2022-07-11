# Koffie Labs Challenge

Link: https://github.com/KoffieLabs/backend-challenge

# Set up environment
This project uses [conda](https://docs.conda.io/en/latest/miniconda.html) to manage the Python environment. The required packages are documented in `koffie_labs.yml`.
To create an environment to run this project, run this command `conda env create -f koffie_labs.yml`.

# Run the app
Once the environment has been set up, do the following steps to run the app:
1. Cd to `src`
1. Run `uvicorn main:app`
1. The app is now running at `http://127.0.0.1:8000`
1. Go to `http://127.0.0.1:8000/docs` to see the API documentation via Swagger UI
    * You can use the Swagger UI to interact with the APIs
