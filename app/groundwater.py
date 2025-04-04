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
parquet_kataster_file = datapath / "bohrloch_kataster.parquet"
image_path = Path("images")

alt.data_transformers.disable_max_rows()

if not Path.exists(image_path):
    Path.mkdir(image_path)


class Groundwater:
    def __init__(self):
        self.waterlevels_df = pd.read_parquet(parquet_data_file)
        self.stations_df = pd.read_parquet(parquet_station_file)
        self.stations = self.get_station_dict()
        self.station_nrs = list(self.stations_df["stationnr"].unique())
        self.stations_df.set_index("stationnr", inplace=True)
        self.bohr_kataster_df = pd.read_parquet(datapath / "bohrloch_kataster.parquet")
        self.precipitation_df = pd.read_parquet(datapath / "precipitation.parquet")
        self.precipitation_df["stationnr"] = "Binningen"
        self.years = list(self.waterlevels_df["year"].unique())
        self.years.sort(reverse=True)
        self.years = [int(y) for y in self.years]
        self.min_year = self.years[0]
        self.max_year = self.years[-1]

    def get_station_dict(self):
        """
        Generates a dictionary mapping station names to their corresponding station numbers.

        This method processes the `stations_df` DataFrame by selecting the specified fields,
        removing duplicate entries, and ordering the data by station names. It then creates
        a dictionary where the keys are station names and the values are station numbers.

        Returns:
            dict: A dictionary with station names as keys and station numbers as values.
        """
        fields = ["stationname", "stationnr"]
        df = self.stations_df[fields].drop_duplicates()
        df = df.sort_values(by="stationname")
        station_dict = dict(zip(df["stationname"], df["stationnr"]))
        return station_dict

    def get_monthly_waterlevels_df(self, station_nr: str) -> pd.DataFrame:
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

    def get_bohrkaster_info_df(self, station_nr: str) -> pd.DataFrame:
        """
        Generates a DataFrame containing information about a specific station.

        This method retrieves the station information from the `stations_df` DataFrame
        for a given station number. It then formats the data into a DataFrame with the
        following columns:
            - 'Station Number': The station number.
            - 'Station Name': The station name.
            - 'Latitude': The latitude of the station.
            - 'Longitude': The longitude of the station.
            - 'Altitude': The altitude of the station.
            - 'Depth': The depth of the station.
            - 'Type': The type of station.

        Args:
            station_nr (int): The station number to retrieve the information for.

        Returns:
            pandas.DataFrame: A DataFrame containing the station information.
        """
        try:
            info = self.bohr_kataster_df[
                self.bohr_kataster_df["catnum45"] == station_nr
            ]
            info_df = pd.DataFrame(info).reset_index()
            # transpose this record
            info_df = info_df.T
            # html_table = info_df.reset_index().to_html(render_links=True, escape=False, index=False, header=False)
            return info_df.reset_index()
        except:
            print(station_nr)
            return pd.DataFrame()

    def get_station_name(self, station_nr: str) -> str:
        return self.stations_df.loc[station_nr, "stationname"]

    def get_years(self, station_nr):
        years = self.waterlevels_df[self.waterlevels_df["stationnr"] == station_nr][
            "year"
        ].unique()
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
            popup=f"Station: {station_nr}",  # Optional: shown on click
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(fmap)
        return fmap

    def get_plot_waterlevels_df(
        self, station_nr: str, year_range: list
    ) -> pd.DataFrame:
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
                - 'date': The format=x_axis_formatdate of the observation as a pandas.Timestamp.
                - 'day_in_year': The day of the year of the observation.
                - 'value': The observed value.
        """
        years = range(year_range[0], year_range[1] + 1)
        df = self.waterlevels_df[
            (self.waterlevels_df["stationnr"] == station_nr)
            & (self.waterlevels_df["year"].isin(years))
        ]
        df = df[["stationnr", "year", "month", "date", "day_in_year", "value"]]
        df["date"] = pd.to_datetime(df["date"])
        return df

    def get_report_waterlevels_image(
        self, data_df: pd.DataFrame, settings: dict
    ) -> str:
        chart = self.get_timeseries_chart_report(data_df, settings)
        # print(chart.to_json() )
        chart_path = image_path / settings["plot_name"]
        chart.save(chart_path)
        return str(chart_path)

    def get_timeseries_chart_report(self, data_df: pd.DataFrame, settings: dict) -> str:
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

    def get_timeseries_chart(self, data_df: pd.DataFrame, settings: dict) -> str:
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
            y_min = data_df[settings["y"]].min() - 1
            y_max = data_df[settings["y"]].max() + 1
            settings["y_domain"] = [y_min, y_max]

        start_date = data_df[settings["x"]].min()
        end_date = data_df[settings["x"]].max()
        duration = (end_date - start_date).days / 365
        if duration > 5:
            x_axis_format = "%Y"  # Display only the year
        else:
            x_axis_format = "%Y-%m"  # Display year and month
        chart = (
            alt.Chart(data_df)
            .mark_line()
            .encode(
                x=alt.X(
                    settings["x"],
                    scale=settings["x_domain"],
                    axis=alt.Axis(format=x_axis_format, title=""),
                ),
                y=alt.Y(
                    settings["y"],
                    title="Grundwasserstand m ü. NN",
                    scale=alt.Scale(domain=settings["y_domain"]),
                ),
                color=alt.Color(settings["color"], title=settings["color"]),
            )
            .properties(width=1000, height=400, title=settings["title"])
        ).interactive()
        return chart

    def get_precipitation_chart(
        self, data_df: pd.DataFrame, settings: dict
    ) -> alt.Chart:
        """
        Generates a bar chart for precipitation data using Altair.

        Args:
            data_df (pd.DataFrame): A pandas DataFrame with at least:
                - A datetime column (e.g., 'date')
                - A value column (e.g., 'precip_mm')
                - A grouping column (e.g., 'year')

            settings (dict): A dictionary with required keys:
                - 'x': str, column name for the x-axis (typically datetime)
                - 'y': str, column name for the precipitation values
                - 'color': str, column name for coloring (e.g., year)
                - 'title': str, chart title
                - 'plot_name': str, unused here but kept for compatibility
                Optional:
                - 'y_domain': list of [min, max] for y-axis

        Returns:
            alt.Chart: An interactive Altair bar chart object
        """

        # Ensure datetime on x-axis
        data_df[settings["x"]] = pd.to_datetime(data_df[settings["x"]])

        if "y_domain" not in settings:
            y_min = 0
            y_max = data_df[settings["y"]].max() + 10
            settings["y_domain"] = [y_min, y_max]

        start_date = data_df[settings["x"]].min()
        end_date = data_df[settings["x"]].max()
        duration = (end_date - start_date).days / 365
        x_axis_format = "%Y" if duration > 5 else "%Y-%m"

        chart = (
            alt.Chart(data_df)
            .mark_bar(width=2)
            .encode(
                x=alt.X(
                    settings["x"],
                    scale=settings["x_domain"],
                    type="temporal",
                    axis=alt.Axis(format=x_axis_format, title=""),
                ),
                y=alt.Y(
                    settings["y"],
                    title="Niederschlag (mm)",
                    scale=alt.Scale(domain=settings["y_domain"]),
                ),
                color=alt.Color(settings["color"], title=settings["color"]),
            )
            .properties(width=1600, height=400, title=settings["title"])
        ).interactive()

        return chart

    def get_station_min_max(self, station_nr: str):
        if station_nr is None:
            df = self.waterlevels_df
        else:
            df = self.waterlevels_df[self.waterlevels_df["stationnr"] == station_nr]
        return df["year"].min(), df["year"].max(), df["value"].min(), df["value"].max()

    def get_precipitation_df(self, year_range: list) -> pd.DataFrame:
        """
        Filters the precipitation data for a given range of years.

        Args:
            year_range (list): A list containing the start and end years of the range.

        Returns:
            pandas.DataFrame: A DataFrame containing the filtered precipitation data.
        """
        df = self.precipitation_df[
            self.precipitation_df["jahr"].between(year_range[0], year_range[1])
        ]
        return df
