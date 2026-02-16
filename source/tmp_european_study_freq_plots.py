import plotly.express as px
import logging
import pandas as pd
import sys
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name='mylogger')

def change_extension(file_path, new_extension):
    base_name, _ = os.path.splitext(file_path)
    new_file_path = base_name + "." + new_extension
    return new_file_path

def plot_countries(my_f_dict, location, my_title, max_colour, plot_file_name):
    """
    Scope is quite limited, just europe or world
    had to hard code the ranges in to get the filters to approximate useful

    :param my_f_dict:
    :param location:
    :param my_title:
    :param max_colour:
    :param plot_file_name:
    :return:
    """
    logger.info(f"inside plot_countries")
    logger.debug(f"\n{my_f_dict}")
    df = pd.DataFrame(my_f_dict.items(), columns=['country', 'count'])
    logger.debug(f"\n{df}")
    database = px.data.gapminder().query('year == 2007')

    df = pd.merge(database, df, how='inner', on='country')
    url = ("https://raw.githubusercontent.com/python-visualization/folium/master/examples/data")

    my_title = ""

    geojson_file = f"{url}/world-countries.json"
    # see https://github.com/python-visualization/folium/tree/main/examples
    if location == 'europe':
        scope = location
    else:
        scope = "world"

    fig = px.choropleth(
                        df,
                        title=my_title,
                        locations="country",  # "iso_alpha",
                        locationmode="country names",  # "ISO-3",
                        geojson=geojson_file,
                        scope=scope,
                        range_color=(0, max_colour),
                        color="count",
                        color_continuous_scale="Viridis"  # color-blind friendly, perceptually uniform
                        )
    fig.update_geos(projection_scale=1.5)

    # fig.show()
    logger.info(f"\nWriting {plot_file_name}")
    fig.write_image(plot_file_name)
    plot_file_name = change_extension(plot_file_name, "png")
    logger.info(f"\nPlot also saved as {plot_file_name}.png")
    fig.write_image(plot_file_name)


def largest_value(my_struct):
    for key, value in my_struct.items():
        return max(value, largest_value(value)) if isinstance(value, dict) else value

# Data for Reported eDNA related ALL readrun in Europe Frequencies
country_record_count_dict = {'United Kingdom': 26092, 'Germany': 12896, 'France': 12488, 'Sweden': 11285, 'Spain': 10300, 'Norway': 8961, 'Denmark': 6681, 'Switzerland': 6440, 'Italy': 6295, 'Netherlands': 5933, 'Finland': 5482, 'Portugal': 4910, 'Greece': 4283, 'Russia': 3859, 'Belgium': 1749, 'Croatia': 1586, 'Czech Republic': 1551, 'Svalbard': 1545, 'Austria': 1490, 'Slovenia': 1140, 'Ireland': 1096, 'Bulgaria': 926, 'Estonia': 832, 'Hungary': 823, 'Romania': 765, 'Poland': 706, 'Iceland': 551, 'Latvia': 462, 'Cyprus': 292, 'Montenegro': 290, 'Ukraine': 286, 'Belarus': 214, 'Lithuania': 144, 'Serbia': 126, 'North Macedonia': 109, 'Albania': 89, 'Slovakia': 11, 'Moldova': 9, 'Guernsey': 4, 'Jan Mayen': 4, 'Bosnia and Herzegovina': 2, 'Luxembourg': 2, 'Monaco': 2}

logger.info(f"largest_value={largest_value(country_record_count_dict)}")


print("The following are all the countries in Europe, with their respective counts (Readrun):")
print(country_record_count_dict)

my_title_readrun = "Reported eDNA related ALL in Europe Study Frequencies"
my_plot_file_readrun = "ena_study_european_countries.svg"
plot_countries(country_record_count_dict, 'europe', my_title_readrun, largest_value(country_record_count_dict), my_plot_file_readrun)

# Data for Reported eDNA related ALL in Europe Study Frequencies
country_study_count_dict = {'United Kingdom': 339, 'Spain': 329, 'Germany': 314, 'France': 313, 'Sweden': 236, 'Russia': 224, 'Italy': 198, 'Norway': 191, 'Greece': 157, 'Denmark': 157, 'Netherlands': 154, 'Finland': 105, 'Switzerland': 93, 'Portugal': 80, 'Svalbard': 62, 'Croatia': 61, 'Bulgaria': 59, 'Ireland': 52, 'Austria': 45, 'Belgium': 43, 'Romania': 42, 'Czech Republic': 33, 'Poland': 32, 'Hungary': 28, 'Iceland': 28, 'Slovenia': 27, 'Estonia': 19, 'Ukraine': 14, 'Montenegro': 13, 'Serbia': 12, 'Albania': 11, 'Lithuania': 10, 'Cyprus': 8, 'Latvia': 6, 'Slovakia': 5, 'North Macedonia': 3, 'Luxembourg': 2, 'Jan Mayen': 2, 'Guernsey': 2, 'Bosnia and Herzegovina': 2, 'Monaco': 1, 'Moldova': 1, 'Belarus': 1}

print("\nThe following are all the countries in Europe, with their respective counts (Study):")
print(country_study_count_dict)
logger.info(f"largest_value={largest_value(country_study_count_dict)}")

my_title_study = "Reported eDNA related ALL readrun in Europe Study Frequencies"
my_plot_file_study = "ena_readrun_study_countries.svg"
plot_countries(country_study_count_dict, 'europe', my_title_study, largest_value(country_study_count_dict), my_plot_file_study)

logger.info("Finished plotting both readrun and study frequencies.")
