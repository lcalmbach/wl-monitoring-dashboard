from pathlib import Path
import pandas as pd
import altair as alt
import calendar
import folium

datapath = Path("app") / "data"
identifier = "100064"
csv_file = datapath / f"{identifier}.csv"
parquet_data_file = datapath / "100064_final.parquet"
parquet_station_file = datapath / "100064_stations.parquet"
image_path = Path("images")

if not Path.exists(image_path):
    Path.mkdir(image_path)

class Groundwater:
    def __init__(self):
        self.waterlevels_df = pd.read_parquet(parquet_data_file)
        self.stations_df = pd.read_parquet(parquet_station_file)
        self.stations = self.stations_df["stationnr"].unique()
        self.stations_df.set_index("stationnr", inplace=True)
        self.years = list(self.waterlevels_df["year"].unique())
        self.years.sort(reverse=True)
        self.years = [int(y) for y in self.years]
        self.min_year = self.years[0]
        self.max_year = self.years[-1]


    def get_monthly_waterlevels_df(self, station_nr:str)->pd.DataFrame:
        """
        Generate a DataFrame containing monthly average values for a specific station.

        This method filters the data for a given station number, calculates the monthly 
        average values, and formats the data into a pivoted table with years as rows 
        and months as columns. The values are formatted to two decimal places, and 
        missing values are replaced with a dash ("-").

        Args:
            station_nr (int): The station number to filter the data for.

        Returns:
            pandas.DataFrame: A DataFrame where each row represents a year, each column 
            (except the first) represents a month (abbreviated), and the values are the 
            monthly averages formatted as strings. Missing values are represented as "-".
        """
        df = self.waterlevels_df[self.waterlevels_df["stationnr"] == station_nr]
        df = (
            df[["year", "month", "value"]]
            .groupby(["year", "month"])
            .mean()
            .reset_index()
        )
        df_pivoted = df.pivot(
            index="year", columns="month", values="value"
        ).reset_index()
        months = [calendar.month_abbr[month] for month in range(1, 13)]
        df_pivoted.columns = ["year"] + months
        for month in months:
            df_pivoted[month] = df_pivoted[month].map("{:.2f}".format)
        df_pivoted = df_pivoted.fillna("-")
        df_pivoted[months].replace("nan", "-")

        return df_pivoted

    def get_station_name(self, station_nr: str)->str:
        return self.stations_df.loc[station_nr, "stationname"]

    def get_years(self, station_nr):
        years = self.waterlevels_df[self.waterlevels_df["stationnr"] == station_nr]['year'].unique()
        years = sorted(list(years), reverse=True)
        return years
    
    def get_station_coords(self, station_nr: str):
        coords = self.stations_df.loc[station_nr, ["lat", "lon"]].tolist()
        return [float(c) for c in coords]
    
    def get_map(self, station_nr: str):
        coords = self.get_station_coords(station_nr)
        fmap = folium.Map(location=coords, zoom_start=14)
        folium.Marker(
            location=coords,
            tooltip=self.get_station_name(station_nr),  # Optional: shown on hover
            popup=f"Station: {station_nr}",           # Optional: shown on click
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(fmap)
        return fmap


    def get_plot_waterlevels_df(self, station_nr: str, years: list)->pd.DataFrame:
        """
        Filters and processes a DataFrame to retrieve plot values for a specific station 
        and a set of years.

        Args:
            station_nr (int): The station number to filter the data.
            years (list of int): A list of years to include in the filtered data.

        Returns:
            pandas.DataFrame: A DataFrame containing the filtered and processed data 
            with the following columns:
                - 'year': The year of the observation.
                - 'month': The month of the observation.
                - 'date': The date of the observation as a pandas.Timestamp.
                - 'day_in_year': The day of the year of the observation.
                - 'value': The observed value.
        """
        df = self.waterlevels_df[
            (self.waterlevels_df["stationnr"] == station_nr)
            & (self.waterlevels_df["year"].isin(years))
        ]
        df = df[["year", "month", "date", "day_in_year", "value"]]
        df["date"] = pd.to_datetime(df["date"])
        return df

    def get_report_waterlevels_image(self, data_df: pd.DataFrame, settings: dict)->str:
        chart = self.get_timeseries_chart_report(data_df, settings)
        # print(chart.to_json() )
        chart_path = image_path / settings["plot_name"]
        chart.save(chart_path)
        return str(chart_path)

    def get_timeseries_chart_report(self, data_df: pd.DataFrame, settings: dict)->str:
        """
        Generates a time series chart using Altair and saves it as an image.

        Args:
            data_df (pd.DataFrame): A pandas DataFrame containing the data to be plotted.
                It must include the following columns:
                - 'day_in_year': Numeric values representing the day of the year.
                - 'value': Numeric values representing the measurement values.
                - 'year': Categorical values representing the year.

            settings (dict): A dictionary containing the chart settings. It must include:
                - 'title' (str): The title of the chart.
                - 'plot_name' (str): The name of the file to save the chart.
                Optional:
                - 'y_domain' (list): A list with two numeric values specifying the y-axis domain.
                  If not provided, it will be calculated based on the data.

        Returns:
            str: The file path of the saved chart image.

        Notes:
            - The x-axis represents the day of the year, with labels displayed at 30-day intervals.
            - The y-axis represents the measurement values, with an optional domain specified in `settings`.
            - The chart is color-coded by year.
            - The chart is saved as an image file at the specified path in `settings["plot_name"]`.
        """
        # show altair plot df_plot with date as x and value as y
        if "y_domain" not in settings:
            y_min = data_df["value"].min() - 1
            y_max = data_df["value"].max() + 1
            settings["y_domain"] = [y_min, y_max]

        chart = (
            alt.Chart(data_df)
            .mark_line()
            .encode(
                x=alt.X(
                    "day_in_year:Q",
                    axis=alt.Axis(
                        values=[
                            str(d) for d in range(1, 366, 30)
                        ],  # must be strings for Nominal axis
                        labelAngle=0,
                    ),
                ),
                y=alt.Y(
                    "value:Q",
                    title="Messwert",
                    scale=alt.Scale(domain=settings["y_domain"]),
                ),
                color=alt.Color("year:N", title="Jahr"),
            )
            .properties(width=1600, height=400, title=settings["title"])
        )
        return chart

    def get_timeseries_chart(self, data_df: pd.DataFrame, settings: dict)->str:
        """
        Generates a time series chart using Altair and saves it as an image.

        Args:
            data_df (pd.DataFrame): A pandas DataFrame containing the data to be plotted.
                It must include the following columns:
                - 'day_in_year': Numeric values representing the day of the year.
                - 'value': Numeric values representing the measurement values.
                - 'year': Categorical values representing the year.

            settings (dict): A dictionary containing the chart settings. It must include:
                - 'title' (str): The title of the chart.
                - 'plot_name' (str): The name of the file to save the chart.
                Optional:
                - 'y_domain' (list): A list with two numeric values specifying the y-axis domain.
                  If not provided, it will be calculated based on the data.

        Returns:
            str: The file path of the saved chart image.

        Notes:
            - The x-axis represents the day of the year, with labels displayed at 30-day intervals.
            - The y-axis represents the measurement values, with an optional domain specified in `settings`.
            - The chart is color-coded by year.
            - The chart is saved as an image file at the specified path in `settings["plot_name"]`.
        """
        # show altair plot df_plot with date as x and value as y
        if "y_domain" not in settings:
            y_min = data_df["value"].min() - 1
            y_max = data_df["value"].max() + 1
            settings["y_domain"] = [y_min, y_max]

        chart = (
            alt.Chart(data_df)
            .mark_line()
            .encode(
                x=alt.X(
                    settings['x'],
                    title="",
                ),
                y=alt.Y(
                    settings['y'],
                    title="Grundwasserstand m ü. NN",
                    scale=alt.Scale(domain=settings["y_domain"]),
                ),
                color=alt.Color("year:N", title="Jahr"),
            )
            .properties(width=1600, height=400, title=settings["title"])
        )
        return chart
    
    def get_station_min_max(self, station_nr: str):
        if station_nr is None:
            df = self.waterlevels_df
        else:
            df = self.waterlevels_df[self.waterlevels_df["stationnr"] == station_nr]
        return df["year"].min(), df["year"].max(), df["value"].min(), df["value"].max()