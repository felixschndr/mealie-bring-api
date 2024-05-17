# Mealie Bring API Integration

The self-hosted recipe manager [Mealie](https://github.com/mealie-recipes/mealie) startet to support sending a recipe to
a Bring shopping list with this [PR](https://github.com/mealie-recipes/mealie/pull/3448). However, this requires the
Mealie instance to be publicly available (from the internet). Since many users want their self-hosted services to
*not* be available from the internet, I chose to create this integration.

This project provides the source code and a container image for a simple webserver. This webserver can run next to
the users Mealie instance (for example with `docker-compose`) and listen for requests.

## Architecture

### Without this project

1. The `Mealie instance` sends a `GET` request to the recipe to `API of bring` (
   See [Bring API docs](https://sites.google.com/getbring.com/bring-import-dev-guide/web-to-app-integration))
	- The link looks like
	  this `https://api.getbring.com/rest/bringrecipes/deeplink?url=<mealieinstance>g/home/r/<recipe>&source=web`
2. `Bring` then does a `GET` request to the `Mealie instance` and pulls the ingredients.
	- In order for this to work the `Mealie instance` has to be reachable from the public internet.
	- This opens an attack vector as anyone can access the `Mealie instance`.

### With this project

1. The `Mealie instance` sends a `POST` request to this `webserver` with the ingredients in its body
2. The `webserver` extracts the ingredients from the request and adds them directly to a list of the users choice via
   the `Bring API`

## Deployment

You can run this app in three simple ways. I prefer the third option.

### 1. Locally

1. Set your environment variables in the `.env` file
2. (Optional) Create and activate a virtual environment with `python -m venv .venv; source .venv/bin/activate`
3. Install the requirements with `pip install -r requirements.txt`
4. Run `python source/main.py`

### 2. As a container with `docker run`

1. Run `docker run mealie-api` and pass in your environment variables with `-e`

   Example: Run `docker run -e BRING_USERNAME=<your email> -e BRING_PASSWORD=<your password> -e BRING_LIST_NAME="<your
   list name>" mealie-api`

### 3. As a container with `docker-compose` (Preferred way)

1. Add this container to your existing docker-compose next to your Mealie instance or create a new docker-compose. 
   Take a look at the [example docker-compose](./docker-compose.yml.example).
2. Run `docker-compose up`
