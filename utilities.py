from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import streamlit as st
from pandas import DataFrame

DOMAIN = "https://letterboxd.com"


@st.cache_data
def transform_ratings(some_str):
    """
    transforms raw star rating into float value
    :param: some_str: actual star rating
    :rtype: returns the float representation of the given star(s)
    """
    stars = {
        "★": 1,
        "★★": 2,
        "★★★": 3,
        "★★★★": 4,
        "★★★★★": 5,
        "½": 0.5,
        "★½": 1.5,
        "★★½": 2.5,
        "★★★½": 3.5,
        "★★★★½": 4.5,
    }
    try:
        return stars[some_str]
    except:
        return -1


@st.cache_data
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
        encounter_error("")
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
                encounter_error("")
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

    df_film = pd.DataFrame(movies_dict)
    return df_film


@st.cache_data
def score_index(rating_x, liked_x, rating_y, liked_y):
    if (rating_x == rating_y) & (liked_x == liked_y):
        score = 2.0
    # both like but different ratings
    elif (liked_x == True) & (liked_x == liked_y):
        score = 2.0 - (abs(rating_x - rating_y) / 5)
    else:
        score = 1.0 - (abs(rating_x - rating_y) / 5)
    return score


@st.cache_data
def decade_year(year):
    return str(int(year / 10) * 10) + "s"


@st.cache_data
def classify_popularity(watched_by):
    if watched_by <= 10000:
        return "1 - very obscure"
    elif watched_by <= 100000:
        return "2 - obscure"
    elif watched_by <= 1000000:
        return "3 - popular"
    else:
        return "4 - very popular"


@st.cache_data
def classify_likeability(ltw_ratio):
    if ltw_ratio <= 0.1:
        return "1 - rarely likeable"
    elif ltw_ratio <= 0.2:
        return "2 - sometimes likeable"
    elif ltw_ratio <= 0.4:
        return "3 - often likeable"
    else:
        return "4 - usually likeable"


@st.cache_data
def classify_runtime(runtime):
    if pd.isnull(runtime) != True:
        if runtime < 30:
            return "less than 30m"
        elif runtime < 60:
            return "30m-1h"
        elif runtime < 90:
            return "1h-1h 30m"
        elif runtime < 120:
            return "1h 30m-2h"
        elif runtime < 150:
            return "2h-2h 30m"
        elif runtime < 180:
            return "2h 30m-3h"
        else:
            return "at least 3h"
    else:
        return np.nan


@st.cache_data
def scrape_films_details(df_film, username):
    df_film = df_film[df_film["rating"] != -1].reset_index(drop=True)
    movies_rating = {}
    movies_rating["id"] = []
    movies_rating["avg_rating"] = []
    movies_rating["year"] = []
    movies_rating["watched_by"] = []
    movies_rating["liked_by"] = []
    movies_rating["runtime"] = []

    movies_actor = {}
    movies_actor["id"] = []
    movies_actor["actor"] = []
    movies_actor["actor_link"] = []

    movies_director = {}
    movies_director["id"] = []
    movies_director["director"] = []
    movies_director["director_link"] = []

    movies_genre = {}
    movies_genre["id"] = []
    movies_genre["genre"] = []

    movies_theme = {}
    movies_theme["id"] = []
    movies_theme["theme"] = []

    movies_country = {}
    movies_country["id"] = []
    movies_country["country"] = []

    movies_language = {}
    movies_language["id"] = []
    movies_language["language"] = []

    progress = 0
    bar = st.progress(progress)
    for link in df_film["link"]:
        progress = progress + 1
        print(
            "scraping details of {} [{}]".format(
                df_film[df_film["link"] == link]["title"].values[0], username
            )
        )

        with st.spinner(
            "scraping details of " + df_film[df_film["link"] == link]["title"].values[0]
        ):
            id_movie = df_film[df_film["link"] == link]["id"].values[0]
            url_movie = DOMAIN + link
            url_movie_page = requests.get(url_movie)
            if url_movie_page.status_code != 200:
                encounter_error("")
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
            movies_rating["id"].append(id_movie)
            movies_rating["avg_rating"].append(rating)
            movies_rating["year"].append(year)
            movies_rating["watched_by"].append(watched_by)
            movies_rating["liked_by"].append(liked_by)
            movies_rating["runtime"].append(runtime)

            # finding the actors
            if soup_movie.find("div", {"class": "cast-list"}) != None:
                for actor in soup_movie.find("div", {"class": "cast-list"}).findAll(
                    "a"
                ):
                    if actor.get_text().strip() != "Show All…":
                        movies_actor["id"].append(id_movie)
                        movies_actor["actor"].append(actor.get_text().strip())
                        movies_actor["actor_link"].append(actor["href"])

            # finding the directors
            if soup_movie.find("div", {"id": "tab-crew"}) != None:
                for director in (
                    soup_movie.find("div", {"id": "tab-crew"}).find("div").findAll("a")
                ):
                    movies_director["id"].append(id_movie)
                    movies_director["director"].append(director.get_text().strip())
                    movies_director["director_link"].append(director["href"])

            # finding the genres
            if soup_movie.find("div", {"id": "tab-genres"}) != None:
                for genre in (
                    soup_movie.find("div", {"id": "tab-genres"})
                    .find("div")
                    .findAll("a")
                ):
                    movies_genre["id"].append(id_movie)
                    movies_genre["genre"].append(genre.get_text().strip())

            # finding the themes
            if soup_movie.find("div", {"id": "tab-genres"}) != None:
                if "Themes" in str(soup_movie.find("div", {"id": "tab-genres"})):
                    for theme in (
                        soup_movie.find("div", {"id": "tab-genres"})
                        .findAll("div")[1]
                        .findAll("a")
                    ):
                        if theme.get_text().strip() != "Show All…":
                            movies_theme["id"].append(id_movie)
                            movies_theme["theme"].append(theme.get_text().strip())

            # finding the countries
            if soup_movie.find("div", {"id": "tab-details"}) != None:
                if "Countr" in str(soup_movie.find("div", {"id": "tab-details"})):
                    for country in (
                        soup_movie.find("div", {"id": "tab-details"})
                        .find("h3", string=lambda text: text and "Countr" in text)
                        .find_next_sibling("div")
                        .findAll("a")
                    ):
                        if country.get_text().strip() != "Show All…":
                            movies_country["id"].append(id_movie)
                            movies_country["country"].append(country.get_text().strip())

            # finding the languages
            if soup_movie.find("div", {"id": "tab-details"}) != None:
                if "Language" in str(soup_movie.find("div", {"id": "tab-details"})):
                    for language in (
                        soup_movie.find("div", {"id": "tab-details"})
                        .find("h3", string=lambda text: text and "Language" in text)
                        .find_next_sibling("div")
                        .findAll("a")
                    ):
                        if language.get_text().strip() != "Show All…":
                            movies_language["id"].append(id_movie)
                            movies_language["language"].append(
                                language.get_text().strip()
                            )

        bar.progress(progress / len(df_film))
    df_rating = pd.DataFrame(movies_rating)
    df_rating["decade"] = df_rating.apply(
        lambda row: decade_year(int(row["year"])), axis=1
    )
    df_actor = pd.DataFrame(movies_actor)
    df_director = pd.DataFrame(movies_director)
    df_genre = pd.DataFrame(movies_genre)
    df_theme = pd.DataFrame(movies_theme)
    df_country = pd.DataFrame(movies_country)
    df_language = pd.DataFrame(movies_language)

    return df_rating, df_actor, df_director, df_genre, df_theme, df_country, df_language


def add_standardized_calculations(
    df_weighted: DataFrame, field: str, default_num: int
) -> None:
    actual_num = min(default_num, len(df_weighted))

    initial_content = """
    Based on standardized calculations:
    """

    for i in range(actual_num):
        initial_content += f"\n{i + 1}. " + "{}"

    list_items = [
        df_weighted.sort_values("score", ascending=False)
        .reset_index(drop=True)
        .loc[i, field]
        for i in range(actual_num)
    ]

    st.markdown(initial_content.format(*list_items))
