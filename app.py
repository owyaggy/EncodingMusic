import pandas as pd
import plotly.express as px
import streamlit as st
# import os

# Also required:
# • A csv with all the event data returned by the SPARQL query
# • A csv with that matches the wikidata IDs for each composer to their nationality, from a previously-ran series of API
#   calls


def add_to_event_info(column_name: str, item: str, event_df, base_df, row):
    """adds a particular attribute to the sub-dataframe"""

    event_df[column_name] = base_df[base_df['event'] == row['event']][item]
    return event_df


def create_event_data(items_to_add, base_df, row):
    event_data = pd.DataFrame()
    for item in items_to_add:
        event_data = add_to_event_info(item, item, event_data, base_df, row)
    return event_data


def cleaner(x: pd.DataFrame, items_to_add: list):

    x['event_data'] = [create_event_data(items_to_add, x, row) for index, row in x.iterrows()]

    events = []
    for index, row in x.iterrows():

        # get rid of multiple rows for the same event
        if row['event'] in events:
            x = x.drop(index)
        else:
            events.append(row['event'])

    # creates a year column
    x['year'] = [int(date[:4]) for date in x['date']]

    x['genreLabel'] = x['genreLabel'].map(str.lower)

    return x


def create_event_frequency_list(df, lookup_range, column, specific_value, normalize=False):
    column_key = {'Genre': 'genreLabel', 'Nationality': 'nationalities', 'Work': 'workperformed', 'Composer': 'composer'}
    column = column_key[column]
    if column == 'genreLabel':
        specific_value = specific_value.lower()
    elif column in ('workperformed', 'composer'):
        specific_value = specific_value[specific_value.index('#') + 1:specific_value.index(')')]
    frequency_list = []
    for year in lookup_range:

        # if it has to do with works and not events (composer, nationality, etc)
        if column in df['event_data'][0].columns:

            # create smaller dataframe with events only in that year to simplify
            sub_df = df[df['year'] == year].copy()
            # print(sub_df['event_data'])

            # create a boolean column for whether the specific value can be found in a work performed at that event
            has_value = []

            # iterate through events in year
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
                        if f"{nation}" in important_column.to_string():
                            # mark that this nationality group is present for this event
                            any_nationality_present = True
                            # stop searching for matches in this event
                            break
                    # add the boolean storing whether this nationality group was present for this event
                    has_value.append(any_nationality_present)
                else:
                    # add the boolean storing whether the desired value was present for this event
                    has_value.append(f"{specific_value}" in important_column.to_string())

            if column == 'nationalities':
                sub_df[specific_value[0]] = has_value
            else:
                sub_df[specific_value] = has_value
            #             sub_df[specific_value] = [specific_value in sub_df['event_data'][index][column].to_list() for index, row in sub_df.iterrows()]

            # create the frequency list
            try:  # if the desired event has occurred in this year, add the number of times it occured
                if column == 'nationalities':
                    frequency_list.append(sub_df.value_counts(specific_value[0], normalize=normalize).to_dict()[True])
                else:
                    frequency_list.append(sub_df.value_counts(specific_value, normalize=normalize).to_dict()[True])
            except KeyError:  # if the desired event has not occurred in this year
                frequency_list.append(0)

        #             # remove the extra column
        #             sub_df.drop(columns=[specific_value])

        # if it has to do with events (genre, work, etc)
        else:
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
    """make a bar chart of the frequency of "specific_value", which is a value in "column" over "lookup_range" years"""
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
                 x = 'Years', y= 'frequency',
                 labels={'Years': 'Years', 'frequency': f'Performances of {column.title()}: {specific_value}'},
                 title=f'Performances of {column.title()}: {specific_value} by Year',
                )
    # Set width and height in pixels
    fig.update_layout(width=600, height=400)
    # If in notebook, use below code:
    # fig.show()
    # If in streamlit, use below code:
    st.plotly_chart(fig, theme=None, use_container_width=True)


def add_nationalities(input_df):
    """Combines nationality data csv and carnegie hall data csv together"""
    input_df.insert(6, "nationalities", pd.Series(dtype=str))

    names_with_nationalities = pd.read_csv('Labs/CarnegieData/nationalities_new.csv')

    # Iterate through the dataframe, adding nationalities when possible
    for index in input_df.index:
        nationalities = names_with_nationalities.loc[
            names_with_nationalities['composer'] == input_df.loc[index, 'composer']]
        nationalities = nationalities['nationalities']
        nationalities = nationalities.get(nationalities.keys()[0])
        try:
            input_df.at[index, 'nationalities'] = nationalities
        except KeyError:
            print(input_df.loc[index])

    return input_df


def bar_chart(pickle_data, column, value, normalize=False):
    inner_df = pd.read_pickle(pickle_data)
    make_bar_chart(inner_df, column, value, normalize)


st.title("Analyzing Trends in Carnegie Hall Performance Data")

option = st.selectbox(
    "What attribute would you like to graph?",
    ("Genre", "Nationality", "Work", "Composer"),
    index=None,
    placeholder="Select attribute...",
    key='attribute'
)

if st.session_state.attribute:
    if st.session_state.attribute == 'Genre':
        genre_options = st.selectbox(
            'Select the genre:',
            [genre for genre in pd.read_csv('Labs/genreLabels_list.csv')['Genre']],
            index=None,
            placeholder="Select genre...",
            key='genreValue'
        )
    elif st.session_state.attribute == 'Nationality':
        nationality_options = st.multiselect(
            'Select the nationalities: *Composers who hold **any** of the chosen nationalities will be selected.*',
            [nation for nation in pd.read_csv('Labs/nationalities_list.csv')['Nation']],
            placeholder="Select nationalities...",
            key='nationalityValue'
        )
    elif st.session_state.attribute == 'Work':
        work_list = []
        works = pd.read_csv('Labs/works_list.csv')
        for item, row in works.iterrows():
            work_list.append(f"{row['title']} by {row['composerLabel']} (#{row['work'][row['work'].index('works/') + 6:]})")
        work_options = st.selectbox(
            'Select the work:',
            work_list,
            index=None,
            placeholder="Select work...",
            key='workValue'
        )
    elif st.session_state.attribute == 'Composer':
        composer_list = []
        composers = pd.read_csv('Labs/composers_list.csv')
        for item, row in composers.iterrows():
            composer_list.append(f"{row['composerLabel']} (#{row['composer'][row['composer'].index('names/') + 6:]})")
        composer_options = st.selectbox(
            'Select the composer:',
            composer_list,
            index=None,
            placeholder="Select composer...",
            key='composerValue'
        )
    else:
        st.write("You seem to have entered something incorrectly in the attribute input!")


def is_value_selected():
    """Returns True if the user has selected an attribute value, False if not"""
    for key, value in st.session_state.items():
        if value in (None, []):
            return False
    return True


def find_selected_value():
    for key, value in st.session_state.items():
        if 'genre' in key:
            return value
        elif 'nationality' in key:
            return value
        elif 'work' in key:
            return value
        elif 'composer' in key:
            return value


if is_value_selected():
    graph_options = st.selectbox(
        'Select the graph type:',
        ('Absolute Frequency', 'Relative Frequency'),
        index=None,
        placeholder="Select graph type...",
        key='graphType'
    )
    if st.session_state.graphType is None:
        st.write('Select the graph type to see your graph!')
    else:
        pickle = 'Labs/finalPickle.pkl'
        if st.session_state.graphType == 'Absolute Frequency':
            bar_chart(pickle, st.session_state.attribute, find_selected_value())
        elif st.session_state.graphType == 'Relative Frequency':
            bar_chart(pickle, st.session_state.attribute, find_selected_value(), normalize=True)
elif any(['genreValue' in st.session_state, 'nationalityValue' in st.session_state, 'workValue' in st.session_state, 'composerValue' in st.session_state]):
    st.write('After selecting a value, you can choose the type of graph you\'d like to see.')
else:
    st.write('Once you select an attribute, you can choose the specific value of that attribute you\'d like to graph!')




#options = st.multiselect(
#    'Select the nationalities:',
#    ['Green', 'Yellow', 'Red', 'Blue'],
#    ['Yellow', 'Red'])#
#
#pickle = 'Labs/testPickle.pkl'
#bar_chart(pickle, 'genreLabel', 'jazz')