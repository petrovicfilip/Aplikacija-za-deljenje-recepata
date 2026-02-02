# Aplikacija-za-deljenje-recepata
Aplikacija za deljenje recepata za predmet Napredne baze podataka

# Pokretanje projekta
Nakon kloniranja projekta, pre svega treba u root folderu projekta napraviti .env fajl i u njega nalepiti sadrzaj iz .env.example fajla.
Zatim izvrsiti komandu: **docker compose up --build**
Sacekati da se sve izbilduje i da se izvrse skripte iz ./neo4j/init (constraints i test podaci..)
Proveriti da je sve u redu:
  - API docs (Swagger): http://localhost:8000/docs - moguce je testirati api i odavde
  - Neo4j Browser: http://localhost:7474
  - Bolt: bolt://localhost:7687

# Pokretanje UI dela
Preci u folder /recipe-sharing-ui.
Izvrsiti komande:
  **npm install**
  **npm run dev**
UI se pokrece na portu 5173.
Projekat se zaustavlja i kontejneri se brisu komandom:
**docker compose down -v**

# Kratak opis i napomene
Ne preporucuje se brisanje korisnika filip (id: fc184998-e09e-451b-925b-2f496f279b50) jer je setovan u UI delu kao default korisnik. Autentifikacija i autorizacija nisu uradjene, jer nisu neophodne za demonstraciju i testiranje neo4j funkcionalnosti u ovom projektu.
Bitne stavke, ukratko:
- CRUD za recepte, korisnike, ocene
- Like sistem
- Rating sa agregacijom na receptu
- Pretraga po sastojcima / opisu / kategoriji sa paginacijom
- Preporuceni recepti za korisnika
- Pretraga po opisu koristi ugradjeni Lucene analizator u neo4j. Kako nema analizatora za srpski koriscen je default analizator, a parsiranje je custom odradjeno f-jom sr_norm_latin.
- Kategorije su fiksne i dodaju se kroz seed.cypher i pokrivaju veliki opseg recepata.
