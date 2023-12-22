import os

import pandas as pd
import plotly.express as px
import streamlit as st


# REQUIRES a pickle file


def create_event_frequency_list(df, lookup_range, column, specific_value, normalize=False):
    """
    Given a lookup_range of years, and a specific_value in a column to look for, this function
    returns a list of frequencies of that specific_value per year.

    Note that specific_value must appear in column.

    Setting the normalize parameter to True will instead return a list of the proportions
    count(specific_value)/total number of performances per year
    """

    # converts user inputs into column names in df
    column_key = {'Genre': 'genreLabel', 'Nationality': 'nationalities', 'Work': 'workperformed',
                  'Composer': 'composer'}
    column = column_key[column]

    # cleaning work to make sure everything matches up
    if column == 'genreLabel':
        specific_value = specific_value.lower()
    elif column in ('workperformed', 'composer'):
        specific_value = specific_value[specific_value.index('#') + 1:specific_value.index(')')]

    frequency_list = []

    for year in lookup_range:

        # if it has to do with works and not events (composer, nationality, etc.)
        if column in df['event_data'][0].columns:

            # create smaller dataframe with events only in that year to simplify
            sub_df = df[df['year'] == year].copy()

            # create a boolean column for whether the specific value can be found in a work performed at that event
            has_value = []

            # iterate through events in specific year
            for index, row in sub_df.iterrows():
                # isolate the entry in the column for the current event
                important_column = sub_df['event_data'][index][column]

                # check if the desired value is present in the column entry
                # for nationalities, need to check if any of the desired nations are present in the column
                if column == 'nationalities':
                    # assume not present
                    any_nationality_present = False
                    # iterate through nations
                    for nation in specific_value:
                        # if a matching nation is found
                        if nation in important_column.to_string():
                            # mark that this nationality group is present for this event
                            any_nationality_present = True
                            # stop searching for matches in this event
                            break
                    # add the boolean storing whether this nationality group was present for this event
                    has_value.append(any_nationality_present)
                else:
                    # add the boolean storing whether the desired value was present for this event
                    has_value.append(f"/{specific_value}" in important_column.to_string())

            if column == 'nationalities':
                sub_df[specific_value[0]] = has_value
            else:
                sub_df[specific_value] = has_value

            # create the frequency list
            try:  # if the desired event has occurred in this year, add the number of times it occurred
                if column == 'nationalities':
                    frequency_list.append(sub_df.value_counts(specific_value[0], normalize=normalize).to_dict()[True])
                else:
                    frequency_list.append(sub_df.value_counts(specific_value, normalize=normalize).to_dict()[True])
            except KeyError:  # if the desired event has not occurred in this year
                frequency_list.append(0)

        # if it has to do with events (genre, work, etc)
        else:
            # get a dictionary of the frequencies
            attribute_counts = df[df['year'] == year].value_counts(column, normalize=normalize)

            # getting the count for the specific value
            try:
                if column == 'nationalities':
                    frequency_list.append(attribute_counts[specific_value[0]])
                else:
                    frequency_list.append(attribute_counts[specific_value])
            except KeyError:
                frequency_list.append(0)

    return frequency_list


def make_bar_chart(df, column, specific_value, normalize=False, lookup_range=(0, 0)):
    """
    make a bar chart of the frequency of "specific_value", which is a value in "column" over "lookup_range" years

    Note: if normalize=True it will instead return a bar chart of proportions
    """
    # Create a DataFrame for bar chart

    # years is the x-axis
    # this first if statement allows you to make the chart for a subset of the years
    if lookup_range != (0, 0):
        years = []
        for year in range(lookup_range[0], lookup_range[1] + 1):
            years.append(year)

    else:
        years = list(set(df['year'].to_list()))

    # list of frequencies
    frequency = create_event_frequency_list(df, years, column, specific_value, normalize)

    bar_data = {'Years': years,
                'frequency': frequency}
    df_bar = pd.DataFrame(bar_data)

    # The barchart with Plotly Express specifying the source df, the columns to use as x and y axes,
    # labels to use for those axes, and an overall title for the figure

    fig = px.bar(df_bar,
                 x='Years', y='frequency',
                 labels={'Years': 'Years', 'frequency': f'Performances of {column.title()}: {specific_value}'},
                 title=f'Performances of {column.title()}: {specific_value} by Year',
                 )
    # Set width and height in pixels
    fig.update_layout(width=600, height=400)

    # If in streamlit, use below code:
    st.plotly_chart(fig, theme=None, use_container_width=True)
    # If in notebook, use fig.show() instead


def bar_chart(pickle_data, column, value, normalize=False):
    """Helper function that passes user input from Streamlit into the bar chart creator function"""
    # convert data from stored .pkl format to pandas dataframe
    inner_df = pd.read_pickle(pickle_data)
    # make the bar chart
    make_bar_chart(inner_df, column, value, normalize)


# Main Streamlit APP
st.title("Analyzing Trends in Carnegie Hall Performance Data")

# prompts user to select attribute
option = st.selectbox(
    "What attribute would you like to graph?",
    ("Genre", "Nationality", "Work", "Composer"),
    index=None,
    placeholder="Select attribute...",
    key='attribute'
)

# if the user has selected an attribute
if st.session_state.attribute:
    # if genre selected
    if st.session_state.attribute == 'Genre':
        # ask user to choose genre from list derived from previously created csv
        genre_options = st.selectbox(
            'Select the genre:',
            [genre for genre in pd.read_csv('Data/genreLabels_list.csv')['Genre']],
            index=None,
            placeholder="Select genre...",
            key='genreValue'
        )
    # if nationality selected
    elif st.session_state.attribute == 'Nationality':
        # ask user to choose nationality from list derived from previously created csv listing all nationalities
        nationality_options = st.multiselect(
            'Select the nationalities: *Composers who hold **any** of the chosen nationalities will be selected.*',
            [nation for nation in pd.read_csv('Data/nationalities_list.csv')['Nation']],
            placeholder="Select nationalities...",
            key='nationalityValue'
        )
    # if work selected
    elif st.session_state.attribute == 'Work':
        # create a list of all the works for the user to select from
        work_list = []
        # fetch the csv with the list of all works
        works = pd.read_csv('Data/works_list.csv')
        # iterate through all the works from the csv
        for item, row in works.iterrows():
            # add the work to the selection list, combining with "by {composer} (#{carnegie work id})"
            # if they have a named composer, show the composer name
            if len(row['composerLabel']) != 0:
                work_list.append(
                    f"{row['title']} by {row['composerLabel']} (#{row['work'][row['work'].index('works/') + 6:]})")
            # if they have no named composer, show Unknown instead
            else:
                work_list.append(
                    f"{row['title']} by Unknown (#{row['work'][row['work'].index('works/') + 6:]})")
        # ask user to choose work from the created list of options
        work_options = st.selectbox(
            'Select the work:',
            work_list,
            index=None,
            placeholder="Select work...",
            key='workValue'
        )
    # if composer selected
    elif st.session_state.attribute == 'Composer':
        # create a list of all the composers for the user to select from
        composer_list = []
        # fetch the csv with the list of all composers
        composers = pd.read_csv('Data/composers_list.csv')
        # iterate through all the composers from the csv
        for item, row in composers.iterrows():
            # add the composer to the selection list, combining with "(#{carnegie composer id})"
            composer_list.append(f"{row['composerLabel']} (#{row['composer'][row['composer'].index('names/') + 6:]})")
        # ask user to choose composer from the created list of options
        composer_options = st.selectbox(
            'Select the composer:',
            composer_list,
            index=None,
            placeholder="Select composer...",
            key='composerValue'
        )
    # should be unreachable - if user selects an attribute not among genre, nationality, work, or composer:
    else:
        st.write("You seem to have entered something incorrectly in the attribute input!")


def is_value_selected():
    """Returns True if the user has selected an attribute value, False if not"""
    for key, value in st.session_state.items():
        if 'graph' not in key and value in (None, []):
            return False
    return True


def find_selected_value():
    """Returns the user's selected attribute value after determining which attribute was selected"""
    for key, value in st.session_state.items():
        if 'genre' in key:
            return value
        elif 'nationality' in key:
            return value
        elif 'work' in key:
            return value
        elif 'composer' in key:
            return value


# if the user has selected an attribute value
if is_value_selected():
    # ask the user to choose between absolute and relative frequency for the graph
    graph_options = st.selectbox(
        'Select the graph type:',
        ('Absolute Frequency', 'Relative Frequency'),
        index=None,
        placeholder="Select graph type...",
        key='graphType'
    )
    # if user has not yet chosen graph type
    if st.session_state.graphType is None:
        st.write('Select the graph type to see your graph!')
    # if user has chosen graph type
    else:
        # set the file path for the .pkl file containing all event data
        pickle = 'Data/event_data.pkl'
        # if absolute frequency selected, create corresponding bar chart
        if st.session_state.graphType == 'Absolute Frequency':
            bar_chart(pickle, st.session_state.attribute, find_selected_value())
        # if relative frequency selected, create corresponding bar chart
        elif st.session_state.graphType == 'Relative Frequency':
            bar_chart(pickle, st.session_state.attribute, find_selected_value(), normalize=True)
# if the user has not selected an attribute value, but has selected an attribute
elif any(['genreValue' in st.session_state, 'nationalityValue' in st.session_state, 'workValue' in st.session_state,
          'composerValue' in st.session_state]):
    # give prompt to select value
    st.write('After selecting a value, you can choose the type of graph you\'d like to see.')
# if attribute has not been selected
else:
    # give prompt to select attribute
    st.write('Once you select an attribute, you can choose the specific value of that attribute you\'d like to graph!')
