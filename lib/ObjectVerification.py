import os
import sys

run_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(run_path, ".."))

from lib.Objects import Song, Genre, Charter


def verify_song(song):
    none = type(None)
    try:
        assert isinstance(song,                Song)
        assert isinstance(song._id,           (int, none))
        assert isinstance(song.title_orig,     str)
        assert isinstance(song.title_eng,      str)
        assert isinstance(song.subtitle_orig, (str, none))
        assert isinstance(song.subtitle_eng,  (str, none))
        assert isinstance(song.artist_orig,    str)
        assert isinstance(song.artist_eng,     str)
        assert isinstance(song.source_orig,   (str, none))
        assert isinstance(song.source_eng,    (str, none))
        assert isinstance(song.charter,        Charter)
        assert isinstance(song.genre,          Genre)
        assert isinstance(song.bpm,            float)
        assert isinstance(song.vetted,         bool)
        assert isinstance(song.d_kantan,      (int, none))
        assert isinstance(song.d_futsuu,      (int, none))
        assert isinstance(song.d_muzukashii,  (int, none))
        assert isinstance(song.d_oni,         (int, none))
        assert isinstance(song.d_ura,         (int, none))
        assert isinstance(song.comments,      (str, none))
        assert isinstance(song.video_link,    (str, none))
        assert isinstance(song.path,           str)
        assert isinstance(song.md5_orig,       str)
        assert isinstance(song.md5_eng,        str)

        assert len(song.title_orig)  > 0
        assert len(song.title_eng)   > 0
        assert len(song.artist_orig) > 0
        assert len(song.artist_eng)  > 0
        assert len(song.path)        > 0
        assert len(song.md5_orig)    == 32
        assert len(song.md5_eng)     == 32
        # Note: Agreement was made that a +1 to the difficulty cap is allowed
        #       to signify "This is even harder than normal"
        assert song.d_kantan     == None or -1 < song.d_kantan     < 7
        assert song.d_futsuu     == None or -1 < song.d_futsuu     < 9
        assert song.d_muzukashii == None or -1 < song.d_muzukashii < 10
        assert song.d_oni        == None or -1 < song.d_oni        < 12
        assert song.d_ura        == None or -1 < song.d_ura        < 12
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)
        return False


def verify_genre(genre):
    none = type(None)
    try:
        assert isinstance(genre,           Genre)
        assert isinstance(genre._id,      (int, none))
        assert isinstance(genre.name_eng,  str)
        assert isinstance(genre.name_jp,   str)
        assert isinstance(genre.genre,     str)
        assert len(genre.name_eng) > 0
        assert len(genre.name_jp)  > 0
        assert len(genre.genre)    > 0
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)
        return False


def verify_charter(charter):
    none = type(None)
    try:
        assert isinstance(charter,       Charter)
        assert isinstance(charter._id,   (int, none))
        assert isinstance(charter.name,   str)
        assert isinstance(charter.image, (bytes, none))
        assert isinstance(charter.about, (str, none))
        assert isinstance(charter.staff,  bool)
        assert len(charter.name) > 0
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)
        return False

