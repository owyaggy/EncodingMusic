# EncodingMusic
### Music 255
### Professor Freedman
### Creative Encoding Project - Vivek and Owen

#### About

Our project is a Streamlit app that allows a user to reveal various trends in the Carnegie Hall performance
data. The user can select an attribute (genre, nationality, work, or composer) and a value for that
attribute. For instance, a value for genre would be 'jazz', a value for nationality would be 'United States
of America', a value for work would be "Roxanne by Sting," and a value for composer would "Wolfgang Amadeus
Mozart."

For nationality, problems may arise when searching for a "German" composer, for instance, because composers
born before the creation of the modern German state may be given a nationality on Wikidata such as
"Kingdom of Germany." Therefore, our application allows the user to select multiple nationalities to search
for, so they can search for all composers with either "Germany" or "Kingdom of Germany" nationality.

Searches are done for exact matches within the Carnegie Hall Data. Therefore, if there are several works
or composers with the same name, the user can select the exact one they mean. All values can be selected
through a search box, avoiding the problem of typos or exact matches with attribute names.

The user can choose between an absolute frequency graph and a relative frequency graph. Absolute frequency
shows either:
* For genre: The number of events in a given year with the desired genre.
* For nationality, composer, and work: The number of events in a year in which a work was performed that
contains the desired attribute.

Relative frequency graph show the same statistic, but as a proportion (0-1) of the total events in a
given year.

#### Instructions

To run this app, run the command:
`python -m streamlit run app.py`
Alternatively, run:
`streamlit run app.py`

#### Troubleshooting

When running the app, *make sure your current working directory is*
`CarnegieDataProject`