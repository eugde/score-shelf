import os

TABLES = ["tracks", "composers", "interpreters", "genres", "collections", "collections_tracks"]

#The colums to be selected from the joined tables in the database
ENTRY_COLS_SORTED = [   "tracks.track_id",
                        "tracks.track_name",
                        "tracks.year",
                        "interpreters.interpreter_name",
                        "composers.composer_name",
                        "genres.genre_name",
                        "tracks.media_location",
                        "tracks.sheet_location",
                        "tracks.thumbnail_location"]

#Trivial names to reference the columns in ENTRY_COLS_SORTED
ENTRY_COLS_NAMES = ["id",
                    "Track",
                    "Jahr",
                    "Intepret",
                    "Komponist",
                    "Genre",
                    "Medien",
                    "Noten",
                    "Thumbnail"]

TRACK_INSERT_COLS = ["track_name", "year", "interpreter_id", "composer_id",
                     "genre_id", "media_location", "sheet_location", "thumbnail_location"]

JOIN_COLS = "tracks NATURAL LEFT JOIN interpreters NATURAL LEFT JOIN composers NATURAL LEFT JOIN genres"

TRACKS_COLS = [("track_id", "INTEGER PRIMARY KEY"),
               ("track_name", "TEXT"),
               ("year", "INTEGER"),
               ("interpreter_id",
                    "INTEGER REFERENCES interpreters(interpreter_id) ON DELETE SET NULL ON UPDATE CASCADE"),
               ("composer_id",
                    "INTEGER REFERENCES composers(composer_id) ON DELETE SET NULL ON UPDATE CASCADE"),
               ("genre_id",
                    "INTEGER REFERENCES genres(genre_id) ON DELETE SET NULL ON UPDATE CASCADE"),
               ("media_location", "TEXT"),
               ("sheet_location", "TEXT"),
               ("thumbnail_location", "TEXT")]

COMPOSERS_COLS = [("composer_id", "INTEGER PRIMARY KEY"),
                  ("composer_name", "TEXT")]

INTERPRETERS_COLS = [("interpreter_id", "INTEGER PRIMARY KEY"),
                     ("interpreter_name", "TEXT")]

GENRES_COLS = [("genre_id", "INTEGER PRIMARY KEY"),
               ("genre_name", "TEXT")]

COLLECTIONS_COLS = [("collection_id", "INTEGER PRIMARY KEY"),
                    ("collection_name", "TEXT")]

COLLECTIONS_TRACKS_COLS = [("track_id",
                                    "INTEGER REFERENCES tracks(track_id) ON DELETE CASCADE ON UPDATE CASCADE"),
                           ("collection_id",
                                    "INTEGER REFERENCES collections(collection_id) ON DELETE CASCADE ON UPDATE CASCADE")]

FOREIGN_KEYS = {"composer_id": "composer_name", "interpreter_id": "interpreter_name", "genre_id": "genre_name"}
RELATIONS = {"tracks": ["composers", "interpreters", "genres"]}