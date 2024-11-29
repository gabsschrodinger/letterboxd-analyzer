import streamlit as st
from htbuilder import div, big, h2, styles
from htbuilder.units import rem
import altair as alt
import pandas as pd
from utilities import (
    scrape_films_details,
    scrape_films,
    DOMAIN,
    classify_popularity,
    classify_likeability,
    classify_runtime,
    add_standardized_calculations,
)
from pathlib import Path
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"
st.set_page_config(
    page_icon="📽️",
    page_title="Letterboxd Analysis",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state,
)
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


sections = ["Analyze Profile"]
selected_sect = st.sidebar.selectbox("Choose mode", sections)

if selected_sect == sections[0]:
    st.title("📽️ Letterboxd Profile Analyzer")
    st.write(
        "See how you rate your movies, what movies you like, the genres, the actors and directors of those movies 🍿."
    )

    username = st.text_input("Letterboxd Username")
    row_button = st.columns((6, 1, 1, 6))
    submit = row_button[1].button("Submit")

    # scraping process
    df_film = scrape_films(username)
    df_film = df_film[df_film["rating"] != -1].reset_index(drop=True)
    st.write("You have {0} movies to scrape".format(len(df_film)))
    df_rating, df_actor, df_director, df_genre, df_theme, df_country, df_language = (
        scrape_films_details(df_film, username)
    )

    st.write("---")
    st.markdown(
        "<h1 style='text-align:center;'>👤 {0}'s Profile Analysis</h1>".format(
            username
        ),
        unsafe_allow_html=True,
    )
    st.write("")
    row_df = st.columns(3)
    with row_df[0]:
        st.markdown(
            div(
                style=styles(
                    text_align="center",
                    padding=(rem(1), 0, rem(2), 0),
                )
            )(
                h2(style=styles(font_size=rem(2), padding=0))("👁️ Rated Movies"),
                big(style=styles(font_size=rem(5), font_weight=600, line_height=1))(
                    len(df_film)
                ),
            ),
            unsafe_allow_html=True,
        )
    with row_df[1]:
        st.markdown(
            div(
                style=styles(
                    text_align="center",
                    padding=(rem(1), 0, rem(2), 0),
                )
            )(
                h2(style=styles(font_size=rem(2), padding=0))("❤️ Liked Movies"),
                big(style=styles(font_size=rem(5), font_weight=600, line_height=1))(
                    len(df_film[df_film["liked"] == True])
                ),
            ),
            unsafe_allow_html=True,
        )
    with row_df[2]:
        st.markdown(
            div(
                style=styles(
                    text_align="center",
                    padding=(rem(1), 0, rem(2), 0),
                )
            )(
                h2(style=styles(font_size=rem(2), padding=0))("⭐ Average Ratings"),
                big(style=styles(font_size=rem(5), font_weight=600, line_height=1))(
                    round(df_film["rating"].mean(), 2)
                ),
            ),
            unsafe_allow_html=True,
        )

    df_rating["runtime_group"] = df_rating.apply(
        lambda row: classify_runtime(row["runtime"]), axis=1
    )
    df_rating["ltw_ratio"] = df_rating["liked_by"] / df_rating["watched_by"]
    df_rating["popularity"] = df_rating.apply(
        lambda row: classify_popularity(row["watched_by"]), axis=1
    )
    df_rating["likeability"] = df_rating.apply(
        lambda row: classify_likeability(row["ltw_ratio"]), axis=1
    )
    df_rating_merged = pd.merge(df_film, df_rating, left_on="id", right_on="id")
    df_rating_merged["rating"] = df_rating_merged["rating"].astype(float)
    df_rating_merged["avg_rating"] = df_rating_merged["avg_rating"].astype(float)
    df_rating_merged["difference"] = (
        df_rating_merged["rating"] - df_rating_merged["avg_rating"]
    )
    df_rating_merged["difference_abs"] = abs(df_rating_merged["difference"])

    st.write("")
    row_year = st.columns(2)

    with row_year[0]:
        st.subheader("When were Your Movies Released?")
        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("year:O", axis=alt.Axis(labelAngle=90)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
        st.markdown(
            """
        Looks like the average release date is around **{}**, with your oldest movie being **[{}]({})** ({}) and your latest being **[{}]({})** ({}).
        Your movies mostly were released in {}.
        """.format(
                round(df_rating_merged["year"].astype(float).mean()),
                df_rating_merged["title"].values[-1],
                DOMAIN + df_rating_merged["link"].values[-1],
                df_rating_merged["year"].values[-1],
                df_rating_merged["title"].values[0],
                DOMAIN + df_rating_merged["link"].values[0],
                df_rating_merged["year"].values[0],
                df_rating_merged["year"].value_counts().index[0],
            )
        )

    with row_year[1]:
        st.subheader("Which Decade were Your Movies Released in?")
        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("decade", axis=alt.Axis(labelAngle=0)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
        liked = ""
        if df_rating_merged[df_rating_merged["liked"] == True].shape[0] != 0:
            liked = """Your favorite decade is probably **{}** since your liked movies mostly were released in that decade, with
            {} movies.""".format(
                df_rating_merged[df_rating_merged["liked"] == True]["decade"]
                .value_counts()
                .index[0],
                df_rating_merged[df_rating_merged["liked"] == True]["decade"]
                .value_counts()
                .values[0],
            )
        st.markdown(
            """
        You mostly rated movies that were released in the **{}**, you rated {} movies from that decade.
        {}
        """.format(
                df_rating_merged["decade"].value_counts().index[0],
                df_rating_merged["decade"].value_counts().values[0],
                liked,
            )
        )

    st.write("")
    st.subheader("How Long are Your Movies?")
    row_runtime = st.columns((2, 1))
    with row_runtime[0]:

        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged.loc[df_rating_merged["runtime"].notna()])
            .mark_bar(tooltip=True)
            .encode(
                alt.X(
                    "runtime_group",
                    axis=alt.Axis(labelAngle=0),
                    sort=[
                        "less than 30m",
                        "30m-1h",
                        "1h-1h 30m",
                        "1h 30m-2h",
                        "2h-2h 30m",
                        "2h 30m-3h",
                        "at least 3h",
                    ],
                ),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
    with row_runtime[1]:
        st.markdown(
            """
        The average runtime of your movies is **{:.2f}** minutes. Your shortest movie is **[{}]({})** with **{:.0f}** minutes, and the longest is
                    **[{}]({})** with **{:.0f}** minutes.
        """.format(
                df_rating_merged["runtime"].mean(),
                df_rating_merged.loc[
                    df_rating_merged["runtime"] == df_rating_merged["runtime"].min(),
                    "title",
                ].values[0],
                DOMAIN
                + df_rating_merged.loc[
                    df_rating_merged["runtime"] == df_rating_merged["runtime"].min(),
                    "link",
                ].values[0],
                df_rating_merged["runtime"].min(),
                df_rating_merged.loc[
                    df_rating_merged["runtime"] == df_rating_merged["runtime"].max(),
                    "title",
                ].values[0],
                DOMAIN
                + df_rating_merged.loc[
                    df_rating_merged["runtime"] == df_rating_merged["runtime"].max(),
                    "link",
                ].values[0],
                df_rating_merged["runtime"].max(),
            )
        )
        with st.expander("Shortest Movies"):
            st.dataframe(
                df_rating_merged.sort_values("runtime")
                .reset_index(drop=True)
                .shift()[1:]
                .head()[["title", "runtime"]],
                use_container_width=True,
            )
        with st.expander("Longest Movies"):
            st.dataframe(
                df_rating_merged.sort_values("runtime", ascending=False)
                .reset_index(drop=True)
                .shift()[1:]
                .head()[["title", "runtime"]],
                use_container_width=True,
            )
    st.write("")

    row_rating = st.columns(2)

    with row_rating[0]:
        st.subheader("How Do You Rate Your Movies?")
        st.write("")
        df_film["rating"] = df_film["rating"].astype(str)
        st.altair_chart(
            alt.Chart(df_film)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("rating", axis=alt.Axis(labelAngle=0)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )

        if df_rating_merged["difference"].mean() > 0:
            ave_rat = "higher"
        else:
            ave_rat = "lower"

        st.markdown(
            """
        It looks like on average you rated movies **{}** than the average Letterboxd user, **by about {} points**.
        You differed from the crowd most on the movie **[{}]({})** where you rated the movie {} stars while the general users rated the movie {}.
        """.format(
                ave_rat,
                abs(round(df_rating_merged["difference"].mean(), 2)),
                df_rating_merged[
                    df_rating_merged["difference_abs"]
                    == df_rating_merged["difference_abs"].max()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["difference_abs"]
                    == df_rating_merged["difference_abs"].max()
                ]["link"].values[0],
                df_rating_merged[
                    df_rating_merged["difference_abs"]
                    == df_rating_merged["difference_abs"].max()
                ]["rating"].values[0],
                df_rating_merged[
                    df_rating_merged["difference_abs"]
                    == df_rating_merged["difference_abs"].max()
                ]["avg_rating"].values[0],
            )
        )
        with st.expander("Movies You Under Rated"):
            st.dataframe(
                df_rating_merged.sort_values("difference")
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["rating", "avg_rating", "liked", "title"]],
                use_container_width=True,
            )
        with st.expander("Movies You Over Rated"):
            st.dataframe(
                df_rating_merged.sort_values("difference", ascending=False)
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["rating", "avg_rating", "liked", "title"]],
                use_container_width=True,
            )

    with row_rating[1]:
        st.subheader("How Do Letterboxd Users Rate Your Movies?")
        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("avg_rating", bin=True, axis=alt.Axis(labelAngle=0)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
        st.markdown(
            """
        Here is the distribution of average rating by other Letterboxd users for the movies that you've rated. Your movie with the lowest average
        rating is **[{}]({})** ({}) with {}, the highest is **[{}]({})** ({}) with {}.
        """.format(
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].min()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].min()
                ]["link"].values[0],
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].min()
                ]["year"].values[0],
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].min()
                ]["avg_rating"].values[0],
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].max()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].max()
                ]["link"].values[0],
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].max()
                ]["year"].values[0],
                df_rating_merged[
                    df_rating_merged["avg_rating"]
                    == df_rating_merged["avg_rating"].max()
                ]["avg_rating"].values[0],
            )
        )
        with st.expander("Lowest Rated Movies"):
            st.dataframe(
                df_rating_merged.sort_values("avg_rating")
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["rating", "avg_rating", "liked", "title"]],
                use_container_width=True,
            )
        with st.expander("Highest Rated Movies"):
            st.dataframe(
                df_rating_merged.sort_values("avg_rating", ascending=False)
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["rating", "avg_rating", "liked", "title"]],
                use_container_width=True,
            )

    st.write("")

    row_popularity = st.columns(2)
    with row_popularity[0]:
        st.subheader("How Popular are Your Movies?")
        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("popularity", axis=alt.Axis(labelAngle=0)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
        popular = ""
        if df_rating_merged["popularity"].value_counts().index[0] == "3 - popular":
            popular = "As expected, you mostly rated movies that are popular among Letterboxd users."
        else:
            popular = "Wow, you have a very unique taste because you mostly don't watch popular movies."
        st.markdown(
            """
        {} Your most obscure movie is **[{}]({})** with just **{:,} users watched**, your most popular movie is **[{}]({})** with **{:,} users watched**.
        """.format(
                popular,
                df_rating_merged[
                    df_rating_merged["watched_by"]
                    == df_rating_merged["watched_by"].min()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["watched_by"]
                    == df_rating_merged["watched_by"].min()
                ]["link"].values[0],
                df_rating_merged["watched_by"].min(),
                df_rating_merged[
                    df_rating_merged["watched_by"]
                    == df_rating_merged["watched_by"].max()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["watched_by"]
                    == df_rating_merged["watched_by"].max()
                ]["link"].values[0],
                df_rating_merged["watched_by"].max(),
            )
        )
        with st.expander("Popularity classification"):
            st.markdown(
                """
            Popularity is determined by number of watches.
            - <= 10,000 -> very obscure
            - 10,101 - 100,000 -> obscure
            - 100,001 - 1,000,000 -> popular
            - \> 1,000,000 -> very popular
            """
            )
        with st.expander("Least Popular Movies"):
            st.dataframe(
                df_rating_merged.sort_values("watched_by")
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["watched_by", "liked", "title"]],
                use_container_width=True,
            )
        with st.expander("Most Popular Movies"):
            st.dataframe(
                df_rating_merged.sort_values("watched_by", ascending=False)
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["watched_by", "liked", "title"]],
                use_container_width=True,
            )
    with row_popularity[1]:
        st.subheader("How Likeable are Your Movies?")
        st.write("")
        st.altair_chart(
            alt.Chart(df_rating_merged)
            .mark_bar(tooltip=True)
            .encode(
                alt.X("likeability", axis=alt.Axis(labelAngle=0)),
                y="count()",
                color=alt.Color(
                    "liked",
                    scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
                ),
            ),
            use_container_width=True,
        )
        unlikeable = ""
        if (
            df_rating_merged[
                (df_rating_merged["likeability"] == "1 - rarely likeable")
                & (df_rating_merged["liked"] == True)
            ].shape[0]
            > 0
        ):
            if (
                df_rating_merged[
                    (df_rating_merged["likeability"] == "1 - rarely likeable")
                    & (df_rating_merged["liked"] == True)
                ].shape[0]
                > 1
            ):
                unlikeable = "Wow, you liked movies that are rarely likeable, you really followed your heart and don't care what others think."
            else:
                unlikeable = """
                Wow, you liked a movie that is rarely likeable, it's **[{}]({}) ({}\% users liked)**, you must have a genuine opinion on this movie.
                """.format(
                    df_rating_merged[
                        (df_rating_merged["likeability"] == "1 - rarely likeable")
                        & (df_rating_merged["liked"] == True)
                    ]["title"].values[0],
                    DOMAIN
                    + df_rating_merged[
                        (df_rating_merged["likeability"] == "1 - rarely likeable")
                        & (df_rating_merged["liked"] == True)
                    ]["link"].values[0],
                    round(
                        df_rating_merged[
                            (df_rating_merged["likeability"] == "1 - rarely likeable")
                            & (df_rating_merged["liked"] == True)
                        ]["ltw_ratio"].values[0]
                        * 100,
                        2,
                    ),
                )
        mostly = ""
        if (
            df_rating_merged["likeability"].value_counts().index[0]
            == "3 - often likeable"
        ):
            mostly = "You mostly rated movies that are often likeable, it possibly means that your movies are mostly good movies."
        elif (
            df_rating_merged[
                df_rating_merged["likeability"] == "1 - rarely likeable"
            ].shape[0]
            + df_rating_merged[
                df_rating_merged["likeability"] == "2 - sometimes likeable"
            ].shape[0]
        ) > (
            df_rating_merged[
                df_rating_merged["likeability"] == "3 - often likeable"
            ].shape[0]
            + df_rating_merged[
                df_rating_merged["likeability"] == "4 - usually likeable"
            ].shape[0]
        ):
            mostly = "You mostly rated movies that are less likeable, it possibly means that you've been watching bad movies all this time."
        st.markdown(
            """
        {} {} Your most likeable movie is **[{}]({})** with **{}\% users liked**, your least likeable movie is **[{}]({})** with just **{}\% users liked**.
        """.format(
                unlikeable,
                mostly,
                df_rating_merged[
                    df_rating_merged["ltw_ratio"] == df_rating_merged["ltw_ratio"].max()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["ltw_ratio"] == df_rating_merged["ltw_ratio"].max()
                ]["link"].values[0],
                round(df_rating_merged["ltw_ratio"].max() * 100, 2),
                df_rating_merged[
                    df_rating_merged["ltw_ratio"] == df_rating_merged["ltw_ratio"].min()
                ]["title"].values[0],
                DOMAIN
                + df_rating_merged[
                    df_rating_merged["ltw_ratio"] == df_rating_merged["ltw_ratio"].min()
                ]["link"].values[0],
                round(df_rating_merged["ltw_ratio"].min() * 100, 2),
            )
        )
        with st.expander("Likeability classification"):
            st.markdown(
                """
            Likeability is determined by number of likes to number of watches ratio.
            - <= 0.1 -> rarely likeable
            - 0.1 - 0.2 -> sometimes likeable
            - 0.2 - 0.4 -> often likeable
            - \> 0.4 -> usually likeable
            """
            )
        with st.expander("Least Likeable Movies"):
            st.dataframe(
                df_rating_merged.sort_values("ltw_ratio")
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["ltw_ratio", "title", "liked"]],
                use_container_width=True,
            )
        with st.expander("Most Likeable Movies"):
            st.dataframe(
                df_rating_merged.sort_values("ltw_ratio", ascending=False)
                .reset_index(drop=True)
                .shift()[1:]
                .head(5)[["ltw_ratio", "title", "liked"]],
                use_container_width=True,
            )

    df_director_merged = pd.merge(df_film, df_director, left_on="id", right_on="id")
    df_actor_merged = pd.merge(df_film, df_actor, left_on="id", right_on="id")

    df_temp = df_director["director"].value_counts().reset_index()

    df_director_merged["rating"] = df_director_merged["rating"].astype(float)
    df_temp_2 = df_director_merged.groupby(["director", "director_link"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()

    df_temp = pd.merge(df_temp_2, df_temp, left_on="director", right_on="director")
    df_temp = df_temp.sort_values(
        ["count", "liked", "rating"], ascending=False
    ).reset_index(drop=True)
    df_temp = df_temp[df_temp["count"] != 1]
    scaled = scaler.fit_transform(df_temp[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp[["director"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )
    df_temp = df_temp[
        df_temp["director"].isin(
            df_weighted.sort_values("score", ascending=False)
            .head(20)["director"]
            .tolist()
        )
    ]

    st.write("")
    st.subheader("Your Top Directors")
    row_director = st.columns((2, 1))
    with row_director[0]:
        st.write("")
        base = alt.Chart(
            df_director_merged[df_director_merged["director"].isin(df_temp["director"])]
        ).encode(
            alt.X(
                "director",
                sort=df_temp["director"].tolist(),
                axis=alt.Axis(labelAngle=90),
            )
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "director",
                    sort=df_temp["director"].tolist(),
                    axis=alt.Axis(labelAngle=90),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )

        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_director[1]:
        if df_temp["liked"].max() != 0:
            if (
                df_temp[df_temp["rating"] == df_temp["rating"].max()][
                    "director"
                ].values[0]
                != df_temp[df_temp["liked"] == df_temp["liked"].max()][
                    "director"
                ].values[0]
            ):
                st.markdown(
                    """
                You rated **{}** movies that were directed by **[{}]({})**. Your favorite director is probably **[{}]({})** which you
                gave average rating of **{}**, or **[{}]({})** which you liked **{}** of his/her movies.
                """.format(
                        df_temp["count"].values[0],
                        df_temp["director"].values[0],
                        DOMAIN + df_temp["director_link"].values[0],
                        df_temp[df_temp["rating"] == df_temp["rating"].max()][
                            "director"
                        ].values[0],
                        DOMAIN
                        + df_temp[df_temp["rating"] == df_temp["rating"].max()][
                            "director_link"
                        ].values[0],
                        round(df_temp["rating"].max(), 2),
                        df_temp[df_temp["liked"] == df_temp["liked"].max()][
                            "director"
                        ].values[0],
                        DOMAIN
                        + df_temp[df_temp["liked"] == df_temp["liked"].max()][
                            "director_link"
                        ].values[0],
                        df_temp["liked"].max(),
                    )
                )
            else:
                st.markdown(
                    """
                You rated **{}** movies that were directed by **[{}]({})**. Your favorite director is probably **[{}]({})** which you
                gave average rating of **{}** and liked **{}** of his/her movies.
                """.format(
                        df_temp["count"].values[0],
                        df_temp["director"].values[0],
                        DOMAIN + df_temp["director_link"].values[0],
                        df_temp[df_temp["rating"] == df_temp["rating"].max()][
                            "director"
                        ].values[0],
                        DOMAIN
                        + df_temp[df_temp["rating"] == df_temp["rating"].max()][
                            "director_link"
                        ].values[0],
                        round(df_temp["rating"].max(), 2),
                        df_temp["liked"].max(),
                    )
                )
        else:
            st.markdown(
                """
            You rated **{}** movies that were directed by **[{}]({})**. Your favorite director is probably **[{}]({})** which you
                gave average rating of **{}**.
            """.format(
                    df_temp["count"].values[0],
                    df_temp["director"].values[0],
                    DOMAIN + df_temp["director_link"].values[0],
                    df_temp[df_temp["rating"] == df_temp["rating"].max()][
                        "director"
                    ].values[0],
                    DOMAIN
                    + df_temp[df_temp["rating"] == df_temp["rating"].max()][
                        "director_link"
                    ].values[0],
                    round(df_temp["rating"].max(), 2),
                )
            )

        add_standardized_calculations(df_weighted, "director", 5)

    list_weights = []
    movie_ids = df_actor["id"].unique()
    for movie_id in movie_ids:
        n_actor = df_actor.loc[df_actor["id"] == movie_id].shape[0]
        for i in range(n_actor):
            weight = 1 - i / n_actor
            list_weights.append(weight)
    df_actor["weights"] = list_weights
    df_temp_w = df_actor.groupby(["actor", "actor_link"], as_index=False)[
        "weights"
    ].sum()
    df_temp = df_actor["actor"].value_counts().reset_index()
    df_actor_merged["rating"] = df_actor_merged["rating"].astype(float)
    df_temp_2 = df_actor_merged.groupby(["actor", "actor_link"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()
    df_temp = pd.merge(df_temp_2, df_temp, left_on="actor", right_on="actor")

    df_temp = pd.merge(
        df_temp,
        df_temp_w,
        left_on=["actor", "actor_link"],
        right_on=["actor", "actor_link"],
    )
    df_temp = df_temp.sort_values(
        ["count", "liked", "rating"], ascending=False
    ).reset_index(drop=True)
    df_temp = df_temp[df_temp["count"] != 1]
    df_temp["liked_weighted"] = df_temp["liked"].astype(int) * df_temp["weights"]
    scaled = scaler.fit_transform(
        df_temp[["weights", "liked_weighted", "rating"]].values
    )
    df_weighted = pd.DataFrame(scaled, columns=["weights", "liked_weighted", "rating"])
    df_weighted = pd.merge(
        df_temp[["actor"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["weights"] + df_weighted["liked_weighted"] + df_weighted["rating"]
    )
    df_temp = df_temp[
        df_temp["actor"].isin(
            df_weighted.sort_values("score", ascending=False).head(20)["actor"].tolist()
        )
    ]

    st.write("")
    st.subheader("Your Top Actors")
    row_actor = st.columns((2, 1))
    with row_actor[0]:
        st.write("")

        base = alt.Chart(
            df_actor_merged[df_actor_merged["actor"].isin(df_temp["actor"])]
        ).encode(
            alt.X("actor", sort=df_temp["actor"].tolist(), axis=alt.Axis(labelAngle=90))
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "actor",
                    sort=df_temp["actor"].tolist(),
                    axis=alt.Axis(labelAngle=90),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )
        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_actor[1]:
        if df_temp["liked"].max() != 0:
            st.markdown(
                """
            You rated **{}** movies starring **[{}]({})**. Your favorite actor is probably **[{}]({})** which you liked **{}** of
            his/her movies.
            """.format(
                    df_temp["count"].values[0],
                    df_temp["actor"].values[0],
                    DOMAIN + df_temp["actor_link"].values[0],
                    df_temp[df_temp["liked"] == df_temp["liked"].max()]["actor"].values[
                        0
                    ],
                    DOMAIN
                    + df_temp[df_temp["liked"] == df_temp["liked"].max()][
                        "actor_link"
                    ].values[0],
                    df_temp["liked"].max(),
                )
            )
        else:
            st.markdown(
                """
            You rated **{}** movies starring **[{}]({})**.
            """.format(
                    df_temp["count"].values[0],
                    df_temp["actor"].values[0],
                    DOMAIN + df_temp["actor_link"].values[0],
                )
            )
        st.markdown(
            """
        Based on standardized and weighted calculations:
        1. {}
        2. {}
        3. {}
        4. {}
        5. {}
        6. {}
        7. {}
        8. {}
        9. {}
        10. {}
        """.format(
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[0, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[1, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[2, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[3, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[4, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[5, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[6, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[7, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[8, "actor"],
                df_weighted.sort_values("score", ascending=False)
                .reset_index(drop=True)
                .loc[9, "actor"],
            )
        )
    st.write("")
    st.subheader("Genres Breakdown")
    row_genre = st.columns((2, 1))
    df_genre_merged = pd.merge(df_film, df_genre, left_on="id", right_on="id")
    df_temp = df_genre["genre"].value_counts().reset_index()
    df_temp = df_temp[df_temp["count"] > df_film.shape[0] / 100].reset_index(drop=True)
    df_genre_merged["rating"] = df_genre_merged["rating"].astype(float)
    df_temp_2 = df_genre_merged.groupby(["genre"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()
    df_temp = pd.merge(df_temp_2, df_temp, left_on="genre", right_on="genre")
    df_temp = df_temp.sort_values("count", ascending=False).reset_index(drop=True)
    scaled = scaler.fit_transform(df_temp[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp[["genre"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )

    with row_genre[0]:

        st.write("")

        base = alt.Chart(
            df_genre_merged[df_genre_merged["genre"].isin(df_temp["genre"])]
        ).encode(
            alt.X("genre", sort=df_temp["genre"].tolist(), axis=alt.Axis(labelAngle=90))
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X("genre", sort=df_temp["genre"].tolist()),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )

        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_genre[1]:
        liked = ""
        if df_temp["liked"].max() != 0:
            liked = "You mostly liked **{}** movies with {} movies.".format(
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["genre"].values[0],
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["liked"].values[0],
            )
        st.markdown(
            """
        Seems like you're not a great fan of **{}** movies, you gave average rating of {} on that genre.
        You really gave good ratings on **{}** movies, with average rating of {}.
        You mostly rated **{}** movies with {} movies. {}
        """.format(
                df_temp[df_temp["rating"] == df_temp["rating"].min()]["genre"].values[
                    0
                ],
                round(
                    df_temp[df_temp["rating"] == df_temp["rating"].min()][
                        "rating"
                    ].values[0],
                    2,
                ),
                df_temp[df_temp["rating"] == df_temp["rating"].max()]["genre"].values[
                    0
                ],
                round(
                    df_temp[df_temp["rating"] == df_temp["rating"].max()][
                        "rating"
                    ].values[0],
                    2,
                ),
                df_temp[df_temp["count"] == df_temp["count"].max()]["genre"].values[0],
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["count"].values[0],
                liked,
            )
        )

        add_standardized_calculations(df_weighted, "genre", 5)

    df_genre_combination = pd.DataFrame(columns=df_genre_merged.columns)
    for i in range(len(df_temp["genre"].tolist())):
        for j in range(i + 1, len(df_temp["genre"].tolist())):
            df_ha = df_genre_merged[
                (df_genre_merged["genre"] == df_temp["genre"].tolist()[i])
                | (df_genre_merged["genre"] == df_temp["genre"].tolist()[j])
            ]
            if len(df_ha) != 0:
                df_ha["genre"] = (
                    df_temp["genre"].tolist()[i] + " & " + df_temp["genre"].tolist()[j]
                )
                df_ha = df_ha[df_ha.duplicated("id")]
                df_genre_combination = pd.concat(
                    [df_genre_combination, df_ha]
                ).reset_index(drop=True)

    df_temp_comb = df_genre_combination["genre"].value_counts().reset_index()
    df_genre_combination["rating"] = df_genre_combination["rating"].astype(float)
    df_genre_combination["liked"] = df_genre_combination["liked"].astype(int)
    df_temp_comb_2 = df_genre_combination.groupby(["genre"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_genre_combination["liked"] = df_genre_combination["liked"].astype(bool)
    df_temp_comb_2 = df_temp_comb_2.reset_index()

    df_temp_comb = pd.merge(
        df_temp_comb_2, df_temp_comb, left_on="genre", right_on="genre"
    )
    df_temp_comb = df_temp_comb.sort_values("count", ascending=False).reset_index(
        drop=True
    )
    scaled = scaler.fit_transform(df_temp_comb[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp_comb[["genre"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )
    n_genre = df_temp_comb.iloc[min(19, len(df_temp_comb) - 1)]["count"]
    df_temp_comb = df_temp_comb[df_temp_comb["count"] >= n_genre]

    st.subheader("Top Genre Combinations Breakdown")
    row_genre_comb = st.columns((2, 1))
    with row_genre_comb[0]:
        st.write("")
        base = alt.Chart(
            df_genre_combination[
                df_genre_combination["genre"].isin(df_temp_comb["genre"])
            ]
        ).encode(
            alt.X(
                "genre",
                sort=df_temp_comb["genre"].tolist(),
                axis=alt.Axis(labelAngle=90),
            )
        )
        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp_comb)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "genre",
                    axis=alt.Axis(title="genre combination"),
                    sort=df_temp_comb["genre"].tolist(),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )
        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_genre_comb[1]:
        top_2 = ""
        if (
            pd.DataFrame(df_temp_comb["genre"][0].split(" & "))
            .isin(df_temp.iloc[:2]["genre"].tolist())
            .sum()[0]
            == 0
        ):
            top_2 = """
            It's a little bit surprising that your mostly rated genre combination (**{}**) is not your top 2 genres (**{} & {}**).
            """.format(
                df_temp_comb["genre"][0], df_temp["genre"][0], df_temp["genre"][1]
            )
        elif (
            pd.DataFrame(df_temp_comb["genre"][0].split(" & "))
            .isin(df_temp.iloc[:2]["genre"].tolist())
            .sum()[0]
            == 1
        ):
            top_2 = "Well, it's no surprise that your mostly rated genre combination (**{}**) consists of one of your top 2 genres (**{}**).".format(
                df_temp_comb["genre"][0],
                df_temp.iloc[:2][
                    df_temp.iloc[:2]["genre"].isin(
                        df_temp_comb["genre"][0].split(" & ")
                    )
                ]["genre"].values[0],
            )
        elif (
            pd.DataFrame(df_temp_comb["genre"][0].split(" & "))
            .isin(df_temp.iloc[:2]["genre"].tolist())
            .sum()[0]
            == 2
        ):
            top_2 = "Well, it's no surprise that your mostly rated genre combination consists of your top 2 genres (**{}**).".format(
                df_temp_comb["genre"][0]
            )
        st.markdown(
            """It's a common thing that a movie is categorized into more than 1 genre, so we'll look deeper into the genre combinations
        to get a better understanding of your movies.
        """
        )

        low = ""
        if (
            pd.DataFrame(
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].min()][
                    "genre"
                ]
                .values[0]
                .split(" & ")
            )
            .isin(
                df_temp[df_temp["rating"] == df_temp["rating"].min()][
                    "genre"
                ].values.tolist()
            )
            .sum()[0]
            != 0
        ):
            low = """Once again, **{}** movies are definitely not your cup of tea, even when it's combined with other genre, the combination of **{}**
            has the lowest average rating ({}) compared to your other top genre combinations.
            """.format(
                df_temp[df_temp["rating"] == df_temp["rating"].min()]["genre"].values[
                    0
                ],
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].min()][
                    "genre"
                ].values[0],
                round(df_temp_comb["rating"].min(), 2),
            )
        else:
            low = """Genre combination with the lowest average rating you gave among your other top genre combinations is **{}** with {}.
            """.format(
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].min()][
                    "genre"
                ].values[0],
                round(df_temp_comb["rating"].min(), 2),
            )

        high = ""
        if (
            pd.DataFrame(
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].max()][
                    "genre"
                ]
                .values[0]
                .split(" & ")
            )
            .isin(
                df_temp[df_temp["rating"] == df_temp["rating"].max()][
                    "genre"
                ].values.tolist()
            )
            .sum()[0]
            != 0
        ):
            high = """You seem to have a lot appreciation for **{}** movies, the combination of **{}**
            has the highest average rating ({}) compared to your other top genre combinations.
            """.format(
                df_temp[df_temp["rating"] == df_temp["rating"].max()]["genre"].values[
                    0
                ],
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].max()][
                    "genre"
                ].values[0],
                round(df_temp_comb["rating"].max(), 2),
            )
        else:
            high = """You gave the highest average rating to **{}** movies with {}.
            """.format(
                df_temp_comb[df_temp_comb["rating"] == df_temp_comb["rating"].max()][
                    "genre"
                ].values[0],
                round(df_temp_comb["rating"].max(), 2),
            )

        st.markdown("{} {} {}".format(top_2, low, high))
        add_standardized_calculations(df_weighted, "genre", 5)

    df_theme_merged = pd.merge(df_film, df_theme, left_on="id", right_on="id")

    df_temp = df_theme["theme"].value_counts().reset_index()
    df_theme_merged["rating"] = df_theme_merged["rating"].astype(float)
    df_temp_2 = df_theme_merged.groupby(["theme"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()
    df_temp = pd.merge(df_temp_2, df_temp, left_on="theme", right_on="theme")
    df_temp = df_temp.sort_values(
        ["count", "liked", "rating"], ascending=False
    ).reset_index(drop=True)
    scaled = scaler.fit_transform(df_temp[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp[["theme"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )
    n_theme = df_temp.iloc[min(19, len(df_temp) - 1)]["count"]
    df_temp = df_temp[df_temp["count"] >= n_theme]

    st.write("")
    st.subheader("Top Themes")
    row_theme = st.columns((2, 1))
    with row_theme[0]:
        st.write("")
        base = alt.Chart(
            df_theme_merged[df_theme_merged["theme"].isin(df_temp["theme"])]
        ).encode(
            alt.X("theme", sort=df_temp["theme"].tolist(), axis=alt.Axis(labelAngle=90))
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "theme",
                    sort=df_temp["theme"].tolist(),
                    axis=alt.Axis(labelAngle=90),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )
        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_theme[1]:
        liked = ""
        if df_temp["liked"].max() != 0:
            if (
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["theme"].values[0]
                == df_temp[df_temp["count"] == df_temp["count"].max()]["theme"].values[
                    0
                ]
            ):
                liked = liked = "Your most watched and liked theme is **{}**.".format(
                    df_temp[df_temp["liked"] == df_temp["liked"].max()]["theme"].values[
                        0
                    ]
                )
            else:
                liked = "Your most liked theme is **{}**.".format(
                    df_temp[df_temp["liked"] == df_temp["liked"].max()]["theme"].values[
                        0
                    ]
                )
        ratings = """
        You don't seem to enjoy movies with **{}** theme since you rated it the lowest. Conversely, you gave relatively high ratings on movies with **{}** theme.
        """.format(
            df_temp[df_temp["rating"] == df_temp["rating"].min()]["theme"].values[0],
            df_temp[df_temp["rating"] == df_temp["rating"].max()]["theme"].values[0],
        )

        st.markdown("{} {}".format(liked, ratings))
        add_standardized_calculations(df_weighted, "theme", 5)

    df_country_merged = pd.merge(df_film, df_country, left_on="id", right_on="id")

    df_temp = df_country["country"].value_counts().reset_index()
    df_country_merged["rating"] = df_country_merged["rating"].astype(float)
    df_temp_2 = df_country_merged.groupby(["country"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()
    df_temp = pd.merge(df_temp_2, df_temp, left_on="country", right_on="country")
    df_temp = df_temp.sort_values(
        ["count", "liked", "rating"], ascending=False
    ).reset_index(drop=True)
    scaled = scaler.fit_transform(df_temp[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp[["country"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )
    n_country = df_temp.iloc[min(19, len(df_temp) - 1)]["count"]
    df_temp = df_temp[df_temp["count"] >= n_country]

    st.write("")
    st.subheader("Top countries")
    row_country = st.columns((2, 1))
    with row_country[0]:
        st.write("")
        base = alt.Chart(
            df_country_merged[df_country_merged["country"].isin(df_temp["country"])]
        ).encode(
            alt.X(
                "country",
                sort=df_temp["country"].tolist(),
                axis=alt.Axis(labelAngle=90),
            )
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "country",
                    sort=df_temp["country"].tolist(),
                    axis=alt.Axis(labelAngle=90),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )
        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_country[1]:
        liked = ""
        if df_temp["liked"].max() != 0:
            if (
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["country"].values[0]
                == df_temp[df_temp["count"] == df_temp["count"].max()][
                    "country"
                ].values[0]
            ):
                liked = liked = "Your most watched and liked country is **{}**.".format(
                    df_temp[df_temp["liked"] == df_temp["liked"].max()][
                        "country"
                    ].values[0]
                )
            else:
                liked = "Your most liked country is **{}**.".format(
                    df_temp[df_temp["liked"] == df_temp["liked"].max()][
                        "country"
                    ].values[0]
                )
        ratings = """
        You don't seem to enjoy movies from **{}** since you rated it the lowest. Conversely, you gave relatively high ratings on movies from **{}**.
        """.format(
            df_temp[df_temp["rating"] == df_temp["rating"].min()]["country"].values[0],
            df_temp[df_temp["rating"] == df_temp["rating"].max()]["country"].values[0],
        )

        st.markdown("{} {}".format(liked, ratings))
        add_standardized_calculations(df_weighted, "country", 5)

    df_language_merged = pd.merge(df_film, df_language, left_on="id", right_on="id")

    df_temp = df_language["language"].value_counts().reset_index()
    df_language_merged["rating"] = df_language_merged["rating"].astype(float)
    df_temp_2 = df_language_merged.groupby(["language"]).agg(
        {"liked": "sum", "rating": "mean"}
    )
    df_temp_2 = df_temp_2.reset_index()
    df_temp = pd.merge(df_temp_2, df_temp, left_on="language", right_on="language")
    df_temp = df_temp.sort_values(
        ["count", "liked", "rating"], ascending=False
    ).reset_index(drop=True)
    scaled = scaler.fit_transform(df_temp[["count", "liked", "rating"]].values)
    df_weighted = pd.DataFrame(scaled, columns=["count", "liked", "rating"])
    df_weighted = pd.merge(
        df_temp[["language"]], df_weighted, left_index=True, right_index=True
    )
    df_weighted["score"] = (
        df_weighted["count"] + df_weighted["liked"] + df_weighted["rating"]
    )
    n_language = df_temp.iloc[min(19, len(df_temp) - 1)]["count"]
    df_temp = df_temp[df_temp["count"] >= n_language]

    st.write("")
    st.subheader("Top languages")
    row_language = st.columns((2, 1))
    with row_language[0]:
        st.write("")
        base = alt.Chart(
            df_language_merged[df_language_merged["language"].isin(df_temp["language"])]
        ).encode(
            alt.X(
                "language",
                sort=df_temp["language"].tolist(),
                axis=alt.Axis(labelAngle=90),
            )
        )

        area = base.mark_bar(tooltip=True).encode(
            alt.Y("count()", axis=alt.Axis(title="Count of Records")),
            color=alt.Color(
                "liked",
                scale=alt.Scale(domain=[True, False], range=["#ff8000", "#00b020"]),
            ),
        )
        line = (
            alt.Chart(df_temp)
            .mark_line(interpolate="monotone")
            .encode(
                alt.X(
                    "language",
                    sort=df_temp["language"].tolist(),
                    axis=alt.Axis(labelAngle=90),
                ),
                alt.Y(
                    "rating",
                    axis=alt.Axis(title="Average Rating", titleColor="#40bcf4"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(value="#40bcf4"),
            )
        )
        st.altair_chart(
            alt.layer(area, line).resolve_scale(y="independent"),
            use_container_width=True,
        )
    with row_language[1]:
        liked = ""
        if df_temp["liked"].max() != 0:
            if (
                df_temp[df_temp["liked"] == df_temp["liked"].max()]["language"].values[
                    0
                ]
                == df_temp[df_temp["count"] == df_temp["count"].max()][
                    "language"
                ].values[0]
            ):
                liked = liked = (
                    "Your most watched and liked language is **{}**.".format(
                        df_temp[df_temp["liked"] == df_temp["liked"].max()][
                            "language"
                        ].values[0]
                    )
                )
            else:
                liked = "Your most liked language is **{}**.".format(
                    df_temp[df_temp["liked"] == df_temp["liked"].max()][
                        "language"
                    ].values[0]
                )
        ratings = """
        You don't seem to enjoy movies in **{}** since you rated it the lowest. Conversely, you gave relatively high ratings on movies in **{}**.
        """.format(
            df_temp[df_temp["rating"] == df_temp["rating"].min()]["language"].values[0],
            df_temp[df_temp["rating"] == df_temp["rating"].max()]["language"].values[0],
        )

        st.markdown("{} {}".format(liked, ratings))

        add_standardized_calculations(df_weighted, "language", 5)
