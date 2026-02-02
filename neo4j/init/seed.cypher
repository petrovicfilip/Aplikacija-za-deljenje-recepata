// ============================
// ============================
// MATCH (r:Recipe) WHERE r.id STARTS WITH "r-seed-"
// DETACH DELETE r;

// ============================
// CATEGORIES
// ============================
UNWIND [
  "uncategorized",
  "dorucak","uzina","rucak","vecera",
  "burger","pica","pasta","dezert",
  "salata","supa","rostilj",
  "piletina","svinjetina","riba",
  "vegetarijansko","vegansko",
  "keto","bez_glutena",
  "torte","kolaci","palacinke",
  "pecivo","sendvic",
  "italijanska","srpska","azijska","meksicka",
  "koktel", "sejk", "pice"
] AS name
MERGE (:Category {name: name});

// ============================
// USERS
// ============================
// ovo je default user, pa je pozeljno ne brisati ga
MERGE (filip:User {id: "fc184998-e09e-451b-925b-2f496f279b50"})
SET filip.username = "filip";

MERGE (ana:User {id: "11111111-1111-1111-1111-111111111111"})
SET ana.username = "ana";

MERGE (marko:User {id: "22222222-2222-2222-2222-222222222222"})
SET marko.username = "marko";

MERGE (milica:User {id: "33333333-3333-3333-3333-333333333333"})
SET milica.username = "milica";

MERGE (nikola:User {id: "44444444-4444-4444-4444-444444444444"})
SET nikola.username = "nikola";

MERGE (jelena:User {id: "55555555-5555-5555-5555-555555555555"})
SET jelena.username = "jelena";

// ============================
// INGREDIENTS
// ============================
UNWIND [
  "jaja","sir","so","biber","mleko","brasno","secer","kvasac","maslinovo ulje","puter",
  "testenina","pirinac","piletina","svinjetina","riba","tuna","paradajz","pelat","luk","beli luk",
  "paprika","krastavac","krompir","sargarepa","kupus","spanac","praziluk","pecurke","limun","jogurt",
  "pavlaka","kukuruz","pasulj","slanutak","avokado","susam","soja sos","sirce","med","senf"
] AS n
MERGE (:Ingredient {name: n});

// ============================
// 3 RUCNA RECEPTA
// ============================

// 1) Omlet (filip)
MATCH (u:User {id:"fc184998-e09e-451b-925b-2f496f279b50"})
MATCH (c:Category {name:"dorucak"})
MERGE (r:Recipe {id:"r-omlet-001"})
ON CREATE SET
  r.title = "Omlet",
  r.description = "Umuti jaja.\nIsprži na tiganju.\nDodaj sir po želji.",
  r.description_norm = toLower("Umuti jaja.\nIsprži na tiganju.\nDodaj sir po želji."),
  r.rating_sum = 0,
  r.rating_count = 0
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r
UNWIND [
  {name:"jaja", amount:3, unit:"kom"},
  {name:"sir", amount:50, unit:"g"},
  {name:"so", amount:1, unit:"prstohvat"}
] AS ing
MERGE (i:Ingredient {name: ing.name})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount = ing.amount, rel.unit = ing.unit;

// 2) Pasta (ana)
MATCH (u:User {id:"11111111-1111-1111-1111-111111111111"})
MATCH (c:Category {name:"pasta"})
MERGE (r:Recipe {id:"r-pasta-001"})
ON CREATE SET
  r.title = "Pasta sa belim lukom",
  r.description = "Skuvaj testeninu.\nNa maslinovom ulju proprži beli luk.\nPomešaj i posluži.",
  r.description_norm = toLower("Skuvaj testeninu.\nNa maslinovom ulju proprži beli luk.\nPomešaj i posluži."),
  r.rating_sum = 0,
  r.rating_count = 0
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r
UNWIND [
  {name:"testenina", amount:200, unit:"g"},
  {name:"beli luk", amount:2, unit:"cena"},
  {name:"maslinovo ulje", amount:2, unit:"kasike"}
] AS ing
MERGE (i:Ingredient {name: ing.name})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount = ing.amount, rel.unit = ing.unit;

// 3) Pica (marko)
MATCH (u:User {id:"22222222-2222-2222-2222-222222222222"})
MATCH (c:Category {name:"pica"})
MERGE (r:Recipe {id:"r-pica-001"})
ON CREATE SET
  r.title = "Brza pica",
  r.description = "Razvuci testo.\nDodaj sos i sir.\nPeci 10-12 min.",
  r.description_norm = toLower("Razvuci testo.\nDodaj sos i sir.\nPeci 10-12 min."),
  r.rating_sum = 0,
  r.rating_count = 0
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r
UNWIND [
  {name:"brasno", amount:300, unit:"g"},
  {name:"pelat", amount:150, unit:"g"},
  {name:"sir", amount:150, unit:"g"}
] AS ing
MERGE (i:Ingredient {name: ing.name})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount = ing.amount, rel.unit = ing.unit;

// ============================
// GENERISI 120 RECEPATA
// ============================
WITH
  ["dorucak","uzina","rucak","vecera","burger","pica","pasta","dezert","salata","supa","rostilj",
   "piletina","svinjetina","riba","vegetarijansko","vegansko","keto","bez_glutena","italijanska","srpska","azijska","meksicka"] AS cats,
  [
    "jaja","sir","so","biber","mleko","brasno","secer","kvasac","maslinovo ulje","puter",
    "testenina","pirinac","piletina","svinjetina","riba","tuna","paradajz","pelat","luk","beli luk",
    "paprika","krastavac","krompir","sargarepa","kupus","spanac","praziluk","pecurke","limun","jogurt",
    "pavlaka","kukuruz","pasulj","slanutak","avokado","susam","soja sos","sirce","med","senf"
  ] AS ings,
  [
    "fc184998-e09e-451b-925b-2f496f279b50",
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
    "33333333-3333-3333-3333-333333333333",
    "44444444-4444-4444-4444-444444444444",
    "55555555-5555-5555-5555-555555555555"
  ] AS user_ids
UNWIND range(1, 120) AS n
WITH n, cats, ings, user_ids,
     cats[(n-1) % size(cats)] AS cat,
     user_ids[(n-1) % size(user_ids)] AS uid
MATCH (u:User {id: uid})
MATCH (c:Category {name: cat})
MERGE (r:Recipe {id: "r-seed-" + toString(n)})
ON CREATE SET
  r.title = replace(cat, "_", " ") + " #" + toString(n),
  r.description = "Koraci:\n1) Pripremi sastojke.\n2) Kuvaj/peci 10-20 min.\n3) Posluzi.",
  r.description_norm = toLower("Koraci:\n1) Pripremi sastojke.\n2) Kuvaj/peci 10-20 min.\n3) Posluzi."),
  r.rating_sum = 0,
  r.rating_count = 0
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r, n, ings
WITH r, n,
     [
       ings[n % size(ings)],
       ings[(n+7) % size(ings)],
       ings[(n+13) % size(ings)],
       ings[(n+21) % size(ings)]
     ] AS sel
UNWIND range(0, size(sel)-1) AS idx
WITH r, sel[idx] AS ingName, idx
MERGE (i:Ingredient {name: ingName})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount =
      CASE idx
        WHEN 0 THEN 2
        WHEN 1 THEN 150
        WHEN 2 THEN 1
        ELSE 50
      END,
    rel.unit =
      CASE idx
        WHEN 0 THEN "kom"
        WHEN 1 THEN "g"
        WHEN 2 THEN "prstohvat"
        ELSE "g"
      END;

// ============================
// LIKES
// ============================
UNWIND range(1, 120) AS n
MATCH (r:Recipe {id: "r-seed-" + toString(n)})
MATCH (u:User)
WITH r, n, collect(u) AS users
UNWIND range(0, size(users)-1) AS ui
WITH r, users[ui] AS u, n, ui
WHERE ((n + ui) % 4) <> 0
MERGE (u)-[:LIKES]->(r);

// Malo lajkova i za 3 rucna recepta
MATCH (u:User), (r:Recipe)
WHERE r.id IN ["r-omlet-001","r-pasta-001","r-pica-001"]
WITH u, r
WHERE substring(toString(u.id), 0, 1) <> "0" // samo da ne bude bas svi za sve (deterministicki filter)
MERGE (u)-[:LIKES]->(r);

// ============================
// RATINGS
// ============================
UNWIND range(1, 120) AS n
MATCH (r:Recipe {id: "r-seed-" + toString(n)})
MATCH (u:User)
WITH r, n, collect(u) AS users
UNWIND range(0, size(users)-1) AS ui
WITH r, users[ui] AS u, n, ui
WHERE ((n + ui) % 3) <> 0
MERGE (u)-[rt:RATED]->(r)
ON CREATE SET
  rt.value = 1 + ((n + ui) % 5),
  rt.createdAt = datetime();

// Par ocena za rucne recepte
MATCH (filip:User {id:"fc184998-e09e-451b-925b-2f496f279b50"})
MATCH (ana:User {id:"11111111-1111-1111-1111-111111111111"})
MATCH (marko:User {id:"22222222-2222-2222-2222-222222222222"})
MATCH (omlet:Recipe {id:"r-omlet-001"})
MATCH (pasta:Recipe {id:"r-pasta-001"})
MATCH (pica:Recipe {id:"r-pica-001"})
MERGE (filip)-[r1:RATED]->(pasta) ON CREATE SET r1.value=5, r1.createdAt=datetime()
MERGE (ana)-[r2:RATED]->(omlet)  ON CREATE SET r2.value=4, r2.createdAt=datetime()
MERGE (marko)-[r3:RATED]->(pica) ON CREATE SET r3.value=3, r3.createdAt=datetime();

// ============================
// (rating_sum i rating_count) ZA SVE RECEPTE
// ============================
MATCH (r:Recipe)
OPTIONAL MATCH (:User)-[rt:RATED]->(r)
WITH r, collect(rt.value) AS vals
SET r.rating_sum = reduce(s = 0, v IN vals | s + v),
    r.rating_count = size(vals);