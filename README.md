# Mealie Bring API Integration

The self-hosted recipe manager [Mealie](https://github.com/mealie-recipes/mealie) startet to support sending a recipe to a Bring shopping list with this [PR](https://github.com/mealie-recipes/mealie/pull/3448). However, this requires the Mealie instance to be publicly available (from the internet). Since many users want their self-hosted services to **not** be available from the internet, I chose to create this integration.

This project provides the source code and a container image for a simple webserver which listens for requests by the Mealie instance and adds the ingredients of a recipe to a specified Bring shopping list.

## Architecture

### Without this project

1. The `Mealie instance` sends a `GET` request to the recipe to `API of bring`
   (See [Bring API docs](https://sites.google.com/getbring.com/bring-import-dev-guide/web-to-app-integration)).
	- The link looks like
	  this `https://api.getbring.com/rest/bringrecipes/deeplink?url=<mealieinstance>g/home/r/<recipe>&source=web`.
2. `Bring` then does a `GET` request to the `Mealie instance` and pulls the ingredients.
	- In order for this to work the `Mealie instance` has to be reachable from the public internet.
	- This opens an attack vector as anyone can access the `Mealie instance`.

### With this project

1. The `client` (e.g. your phone or PC) sends a `POST` request to the `Mealie instance` instructing it to trigger the adding of the ingredients.
2. The `Mealie instance` sends a `POST` request to this `webserver` with the ingredients in its body. An example for such a request can be found in the [tests](test/conftest.py).
3. The `webserver` extracts the ingredients from the request and adds them directly to a list of the users choice via the [`Bring API`](https://github.com/miaucl/bring-api).

This integration runs entirely local and does **not** require any service to be exposed to the Internet.

## Deployment

Deployment can be done in three simple steps:
1. Figure out the environment variables you want/need to set
2. Choose a deployment option
3. Configure Mealie

### Environment variables

No matter which deployment option you chose, you must set up some environment variables:

| Variable name         | Description                                                                                                                                                                                                                                                                                | Required | Default                           | Example                        |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|-----------------------------------|--------------------------------|
| `BRING_USERNAME`      | The email address of your bring account                                                                                                                                                                                                                                                    |   Yes    | -                                 | `myuser@myemailprovider.com`   |
| `BRING_PASSWORD`      | The password of your bring account                                                                                                                                                                                                                                                         |   Yes    | -                                 | `my super secret password`     |
| `BRING_LIST_NAME`     | The exact name of the list you want to add the ingredients to, supports special characters                                                                                                                                                                                                 |   Yes    | -                                 | `My shopping list with spaces` |
| `LOG_LEVEL`           | The loglevel the application logs at                                                                                                                                                                                                                                                       |    No    | `INFO`                            | `DEBUG`                        |
| `HTTP_HOST`           | The address the application tries to attach to, leave this empty to listen on all interfaces, leave this empty if you are using Docker                                                                                                                                                     |    No    | `0.0.0.0`                         | `192.168.1.5`                  |
| `HTTP_PORT`           | The port the application listens on, change this if needed if you run the application locally, leave this empty if you are using Docker                                                                                                                                                    |    No    | `8742`                            | `1234`                         |
| `HTTP_BASE_PATH`      | The path the application listens on. Use this if you use the app behind a reverse proxy and have setup a path (e.g. set this to `/bring` if the application shall listen on `<mealie>.<yourdomain>.tld/bring`)                                                                             |    No    | `""`                              | `/bring`                       |

Ensure to quote your environment variables. Without quotes your password might not be read properly if it contains symbols such as `<`, `&` or `;`.

> [!IMPORTANT]  
> The environment variable `IGNORED_INGREDIENTS` was deprecated
in [PR24](https://github.com/felixschndr/mealie-bring-api/pull/24) and is now ignored. If you are using it, migrate to the new way of configuring which ingredients shall be ignored as seen below.

#### Ignoring ingredients

It is possible to define ingredients that shall never be added to the shopping list. These are ingredients you always have at home (e.g., salt and pepper).

To do so
1. Open the `Data Management` (under `<your mealie domain>/group/data/foods/`).
2. Search for the ingredient you don't want to be added to the shopping list.
3. Click on the edit button.
4. Enable the checkbox `On Hand`.

   ![](assets/images/food_on_hand.png)

### Deployment options

You can run this app in three simple ways. I prefer the third option. Depending on the deployment option you chose
you can ignore some environment variables (e.g. `HTTP_HOST` and `HTTP_PORT`).

#### 1. Locally

1. Copy the contents `./assets/env.example` to `./.env` and adjust the environment variables to your needs.
2. Install the requirements with `poetry install`.
3. Run `python source/main.py`.

#### 2. As a container with `docker run`

1. Run `docker run mealie-api` and pass in your environment variables with `-e`.
	- You *can* (not must) specify a different port than the default (`8742`) with `-p 1234:8742`.
	- Example:
	   ```bash
	   docker run \
	       -e BRING_USERNAME="myuser@myemailprovider.com" \
	       -e BRING_PASSWORD="my super secret password" \
	       -e BRING_LIST_NAME="My shopping list with spaces" \
	       -p 1234:8742 \
	       ghcr.io/felixschndr/mealie-bring-api:latest
	   ```

#### 3. As a container with `docker-compose` (Preferred way)

1. Add this container to your existing docker-compose next to your Mealie instance or create a new docker-compose
   and adjust the environment variables to your needs.
   Take a look at the [example docker-compose](./assets/docker-compose-example.yml).
2. Run `docker-compose up`.

### Setup in Mealie

After deploying the container, there is one simple step you have to do in Mealie: You have to set up the link between 
Mealie and this project.

1. Head over to `http(s)://<your-mealie-instance>/group/data/recipe-actions` (e.g., 
`http://localhost:1234/group/data/recipe-actions`) while being logged in as an administrator.

   ![actions before adding](./assets/images/actions_before_adding.png)
2. Click on `Create` to create a new `action`.
3. Give it any title (e.g. `Bring` or `Add ingredients to Bring`). This will be visible for the users.

   ![adding action](./assets/images/adding_action.png)
4. For the `URL` input the address where this project is running on followed by a `/` (e.g. `http://<ip-of-server>:8742/` or `https://mealie-bring-api.yourlocaldomain.com/` if you are using a reverse proxy)
5. Change the `Type` to `POST`
6. Save

   ![actions after adding](./assets/images/actions_after_adding.png)
7. Try it out 🎉

### Usage in Mealie

1. Head over to a recipe of your choice.
2. Click on the three little dots.
3. Click on `Recipe Actions`
4. Chose your new action (e.g. `Bring`)

   ![executing](./assets/images/executing.png)
5. That's it!
   - You should now see the ingredients in your list
   - You should see some output in the logfile
   ```text
   mealie_bring_api | [2024-05-18 13:38:41,090] [LoggerMixin] [INFO] [Received recipe "Apple crumble" from "https://mealie-bring-api.yourlocaldomain.com"]
   mealie_bring_api | [2024-05-18 13:38:45,373] [LoggerMixin] [INFO] [Added all ingredients to Bring]
   ```

## Maintenance

You can check whether the webserver is still alive by sending a `GET` request to `/status` and check if you get a `200` 
status code:
```bash
$ curl -I https://mealie-bring-api.yourlocaldomain.com/status
HTTP/2 200
server: openresty
date: Mon, 20 May 2024 12:27:56 GMT
content-type: text/html; charset=utf-8
content-length: 2
strict-transport-security: max-age=63072000; preload
```
or
```bash
$ curl -s -o /dev/null -w "%{http_code}" https://mealie-bring-api.yourlocaldomain.com/status
200
```
