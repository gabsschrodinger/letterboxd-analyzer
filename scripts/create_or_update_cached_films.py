import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

from pandas import DataFrame

DOMAIN = "https://letterboxd.com"
USERNAMES = [] # add usernames prior to run the script

def transform_ratings(start_str: str) -> float:
    stars = {
        "★": 1.0,
        "★★": 2.0,
        "★★★": 3.0,
        "★★★★": 4.0,
        "★★★★★": 5.0,
        "½": 0.5,
        "★½": 1.5,
        "★★½": 2.5,
        "★★★½": 3.5,
        "★★★★½": 4.5,
    }

    try:
        return stars[start_str]
    except:
        return -1

def decade_year(year: int) -> str:
    return str(int(year / 10) * 10) + "s"

def scrape_films(username):
    print("==== SCRAPING FOR USERNAME {} ====".format(username))
    movies_dict = {}
    movies_dict["id"] = []
    movies_dict["title"] = []
    movies_dict["rating"] = []
    movies_dict["liked"] = []
    movies_dict["link"] = []
    url = DOMAIN + "/" + username + "/films/"
    url_page = requests.get(url)
    if url_page.status_code != 200:
        raise Exception()
    soup = BeautifulSoup(url_page.content, "html.parser")

    # check number of pages
    li_pagination = soup.findAll("li", {"class": "paginate-page"})
    if len(li_pagination) == 0:
        ul = soup.find("ul", {"class": "poster-list"})
        if ul != None:
            movies = ul.find_all("li")
            for movie in movies:
                movies_dict["id"].append(movie.find("div")["data-film-id"])
                movies_dict["title"].append(movie.find("img")["alt"])
                movies_dict["rating"].append(
                    transform_ratings(
                        movie.find("p", {"class": "poster-viewingdata"})
                        .get_text()
                        .strip()
                    )
                )
                movies_dict["liked"].append(
                    movie.find("span", {"class": "like"}) != None
                )
                movies_dict["link"].append(movie.find("div")["data-target-link"])
    else:
        for i in range(int(li_pagination[-1].find("a").get_text().strip())):
            url = DOMAIN + "/" + username + "/films/page/" + str(i + 1)
            url_page = requests.get(url)
            if url_page.status_code != 200:
                raise Exception()
            soup = BeautifulSoup(url_page.content, "html.parser")
            ul = soup.find("ul", {"class": "poster-list"})
            if ul != None:
                movies = ul.find_all("li")
                for movie in movies:
                    movies_dict["id"].append(movie.find("div")["data-film-id"])
                    movies_dict["title"].append(movie.find("img")["alt"])
                    movies_dict["rating"].append(
                        transform_ratings(
                            movie.find("p", {"class": "poster-viewingdata"})
                            .get_text()
                            .strip()
                        )
                    )
                    movies_dict["liked"].append(
                        movie.find("span", {"class": "like"}) != None
                    )
                    movies_dict["link"].append(movie.find("div")["data-target-link"])

    return pd.DataFrame(movies_dict)

def scrape_films_details(df_film):
    df_film = df_film[df_film["rating"] != -1].reset_index(drop=True)
    movies_data = {}
    movies_data["id"] = []
    movies_data["title"] = []
    movies_data["link"] = []
    movies_data["avg_rating"] = []
    movies_data["year"] = []
    movies_data["watched_by"] = []
    movies_data["liked_by"] = []
    movies_data["runtime"] = []

    movies_data["actors"] = []

    movies_data["directors"] = []

    movies_data["genres"] = []

    movies_data["themes"] = []

    movies_data["countries"] = []

    movies_data["languages"] = []

    for link in df_film["link"]:
        print("scraping details of {}".format(df_film[df_film["link"] == link]["title"].values[0]))

        id_movie = df_film[df_film["link"] == link]["id"].values[0]
        url_movie = DOMAIN + link
        url_movie_page = requests.get(url_movie)
        if url_movie_page.status_code != 200:
            raise Exception()
        soup_movie = BeautifulSoup(url_movie_page.content, "html.parser")
        for sc in soup_movie.findAll("script"):
            if sc.string != None:
                if "ratingValue" in sc.string:
                    rating = sc.string.split("ratingValue")[1].split(",")[0][2:]
                if "releaseYear" in sc.string:
                    year = (
                        sc.string.split("releaseYear")[1]
                        .split(",")[0][2:]
                        .replace('"', "")
                    )
        url_stats = DOMAIN + "/csi" + link + "stats"
        url_stats_page = requests.get(url_stats)
        soup_stats = BeautifulSoup(url_stats_page.content, "html.parser")
        watched_by = int(
            soup_stats.findAll("li")[0]
            .find("a")["title"]
            .replace("\xa0", " ")
            .split(" ")[2]
            .replace(",", "")
        )
        liked_by = int(
            soup_stats.findAll("li")[2]
            .find("a")["title"]
            .replace("\xa0", " ")
            .split(" ")[2]
            .replace(",", "")
        )
        try:
            runtime = int(
                soup_movie.find("p", {"class": "text-link text-footer"})
                .get_text()
                .strip()
                .split("\xa0")[0]
            )
        except:
            runtime = np.nan
        movies_data["id"].append(id_movie)
        movies_data["title"].append(df_film[df_film["link"] == link]["title"].values[0])
        movies_data["link"].append(link)
        movies_data["avg_rating"].append(rating)
        movies_data["year"].append(year)
        movies_data["watched_by"].append(watched_by)
        movies_data["liked_by"].append(liked_by)
        movies_data["runtime"].append(runtime)

        # finding the actors
        if soup_movie.find("div", {"class": "cast-list"}) != None:
            actors = []
            for actor in soup_movie.find("div", {"class": "cast-list"}).findAll("a"):
                if actor.get_text().strip() != "Show All…":
                    actor_data = {
                        "actor": actor.get_text().strip(),
                        "actor_link": actor["href"]
                    }
                    actors.append(actor_data)

            movies_data["actors"].append(actors)
        else:
            movies_data["actors"].append([])

        # finding the directors
        if soup_movie.find("div", {"id": "tab-crew"}) != None:
            directors = []
            for director in (
                soup_movie.find("div", {"id": "tab-crew"}).find("div").findAll("a")
            ):
                director_data = {
                    "director": director.get_text().strip(),
                    "director_link": director["href"]
                }
                directors.append(director_data)

            movies_data["directors"].append(directors)
        else:
            movies_data["directors"].append([])

        # finding the genres
        if soup_movie.find("div", {"id": "tab-genres"}) != None:
            genres = []
            for genre in (
                soup_movie.find("div", {"id": "tab-genres"})
                .find("div")
                .findAll("a")
            ):
                genres.append(genre.get_text().strip())

            movies_data["genres"].append(genres)
        else:
            movies_data["genres"].append([])

        # finding the themes
        if soup_movie.find("div", {"id": "tab-genres"}) != None:
            if "Themes" in str(soup_movie.find("div", {"id": "tab-genres"})):
                themes = []
                for theme in (
                    soup_movie.find("div", {"id": "tab-genres"})
                    .findAll("div")[1]
                    .findAll("a")
                ):
                    if theme.get_text().strip() != "Show All…":
                        themes.append(theme.get_text().strip())

                movies_data["themes"].append(themes)
            else:
                movies_data["themes"].append([])
        else:
            movies_data["themes"].append([])

        # finding the countries
        if soup_movie.find("div", {"id": "tab-details"}) != None:
            if "Countr" in str(soup_movie.find("div", {"id": "tab-details"})):
                countries = []
                for country in (
                    soup_movie.find("div", {"id": "tab-details"})
                    .find("h3", string=lambda text: text and "Countr" in text)
                    .find_next_sibling("div")
                    .findAll("a")
                ):
                    if country.get_text().strip() != "Show All…":
                        countries.append(country.get_text().strip())

                movies_data["countries"].append(countries)
            else:
                movies_data["countries"].append([])
        else:
            movies_data["countries"].append([])

        # finding the languages
        if soup_movie.find("div", {"id": "tab-details"}) != None:
            if "Language" in str(soup_movie.find("div", {"id": "tab-details"})):
                languages = []
                for language in (
                    soup_movie.find("div", {"id": "tab-details"})
                    .find("h3", string=lambda text: text and "Language" in text)
                    .find_next_sibling("div")
                    .findAll("a")
                ):
                    if language.get_text().strip() != "Show All…":
                        languages.append(language.get_text().strip())

                movies_data["languages"].append(languages)
            else:
                movies_data["languages"].append([])
        else:
            movies_data["languages"].append([])

    return pd.DataFrame(movies_data)

today = date.today()

final_df: DataFrame = None

for username in USERNAMES:
    if final_df is None:
        films_df = scrape_films(username)
        final_df = scrape_films_details(films_df)
    else:
        new_films_df = scrape_films(username)
        new_films_df = new_films_df[~new_films_df['id'].isin(final_df['id'])]
        new_final_df = scrape_films_details(new_films_df)
        new_final_df = new_final_df[~new_final_df['id'].isin(final_df['id'])]

        final_df = pd.concat([final_df, new_final_df], ignore_index=True)


final_df['last_modified_date'] = today

final_df.to_parquet(f"cached_films_{today.strftime('%y-%m-%d')}.parquet", engine="pyarrow")

print(f"DataFrame saved to cached_films_{today.strftime('%y-%m-%d')}.parquet")