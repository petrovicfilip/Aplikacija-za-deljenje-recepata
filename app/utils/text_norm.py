import unicodedata
import re

# da normalizujem description jer cu koristiti indeks (Lucene u Neo4j ali nema za srpski) za pretragu po opisu recepta
def sr_norm_latin(s: str) -> str:
    s = (s or "").strip().lower()
    #  čćšđž -> ccsdz
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # ocisti interpunkciju
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
