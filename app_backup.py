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

    return x


def create_event_frequency_list(df, lookup_range, column, specific_value):
    frequency_list = []
    for year in lookup_range:

        # if it has to do with works and not events (composer, nationality, etc)
        if column in df['event_data'][0].columns:

            # create smaller dataframe with events only in that year to simplify
            sub_df = df[df['year'] == year].copy()
            # print(sub_df['event_data'])

            # create a boolean column for whether the specific value can be found in a work performed at that event
            has_value = []

            # iterate through events in specific year
            for index, row in sub_df.iterrows():
                # isolate the entry in the column for the current event
                important_column = sub_df['event_data'][index][column]

                # check if the desired value is present in the column entry
                has_value.append(f"{specific_value}" in important_column.to_string())
                if not True in has_value:
                    print('column: ', type(important_column), important_column)
                    print('search key: ', specific_value)
                    print('#' * 50)

            sub_df[specific_value] = has_value
            # sub_df[specific_value] = [specific_value in sub_df['event_data'][index][column].to_list() for index,
            # row in sub_df.iterrows()]

            # create the frequency list
            try:  # if the desired event has occurred in this year, add the number of times it occured
                frequency_list.append(sub_df.value_counts(specific_value).to_dict()[True])
            except KeyError:  # if the desired event has not occurred in this year
                frequency_list.append(0)

        #             # remove the extra column
        #             sub_df.drop(columns=[specific_value])

        # if it has to do with events (genre, work, etc)
        else:
            attribute_counts = df[df['year'] == year].value_counts(column)

            # getting the count for the specific value
            try:
                frequency_list.append(attribute_counts[specific_value])
            except KeyError:
                frequency_list.append(0)

    return frequency_list


def make_bar_chart(df, column, specific_value, lookup_range=(0, 0)):
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
    frequency = create_event_frequency_list(df, years, column, specific_value)

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


def bar_chart(pickle_data, column, value):
    inner_df = pd.read_pickle(pickle_data)
    make_bar_chart(inner_df, column, value)


#

#options = st.multiselect(
#    'Select the nationalities:',
#    ['Green', 'Yellow', 'Red', 'Blue'],
#    ['Yellow', 'Red'])#
#
#pickle = 'Labs/testPickle.pkl'
#bar_chart(pickle, 'genreLabel', 'jazz')

############################################################

# the pickle
pickle = 'Labs/testPickle.pkl'

choices = {"Genre": "genreLabel", "Composer": "composerName", "Work": "workperformed", "Nationality": "nationalities"}

genres = ["rock music", "genre"]
composers = ["Brian Wilson", "Wolfgang Amadeus Mozart"]
works = ["Good Vibrations"]
nationalities = ["United States of America", "Kingdom of Russia", "Soviet Union"]

# select box for the attribute category
option = st.selectbox("What event attribute would you like to graph?", tuple(choices.keys()), index=None,
                          placeholder="Select attribute...",)

if 'category' not in st.session_state:
    st.session_state['category'] = option
elif 'lookup' not in st.session_state:
    st.write(st.session_state['category'])
    lookup = "failure"
    if st.session_state['category'] == "Genre":
        lookup = st.selectbox(f"What genre would you like to graph?", genres, index=None,
                              placeholder="Select genre...", )
    elif st.session_state['category'] == "Composer":
        lookup = st.selectbox(f"What composer would you like to graph?", composers, index=None,
                              placeholder="Select composer...", )
    elif st.session_state['category'] == "Work":
        lookup = st.selectbox(f"What work would you like to graph?", works, index=None, placeholder="Select work...", )
    elif st.session_state['category'] == "Nationality":
        lookup = st.selectbox(f"What nationality would you like to graph?", nationalities, index=None,
                              placeholder="Select nationality...", )
    st.session_state['lookup'] = lookup
elif 'kind' not in st.session_state:
    kind = st.selectbox(
        f"Would you like to graph abolute numbers or proportions? For example, would you like to graph the total "
        f"number of works performed by Mozart per year (Absolute) or the proportion of Carnegie Hall performances "
        f"that included a piece by Mozart (Proportion)",
        ("Absolute", "Proportion"), index=None, placeholder="Select method of graphing...", )
    st.session_state['kind'] = kind
else:
    if st.session_state['kind'] == 'Absolute':
        # code that makes the graph including
        bar_chart(pickle, choices[st.session_state['category']], st.session_state['lookup'])
    elif st.session_state['kind'] == 'Proportion':
        pass
        # code that makes the graph including
        # make_percentage_bar_chart(name_of_df, choices[st.session_state['option']], st.session_state['lookup'])


#st.write('You selected:', option)