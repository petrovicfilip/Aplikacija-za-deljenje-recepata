// ----------------------------
// CATEGORIES
// ----------------------------
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
  "italijansko","srpsko","azijsko","mexicko"
] AS name
MERGE (:Category {name: name});


// ----------------------------
// USERS
// ----------------------------
MERGE (u1:User {username: "filip"})
ON CREATE SET u1.id = "fc184998-e09e-451b-925b-2f496f279b50";

MERGE (u2:User {username: "ana"})
ON CREATE SET u2.id = "11111111-1111-1111-1111-111111111111";

MERGE (u3:User {username: "marko"})
ON CREATE SET u3.id = "22222222-2222-2222-2222-222222222222";


// ----------------------------
// RECIPES
// ----------------------------

// 1) Omlet (filip)
MATCH (u:User {id:"fc184998-e09e-451b-925b-2f496f279b50"})
MATCH (c:Category {name:"dorucak"})
MERGE (r:Recipe {id:"r-omlet-001"})
ON CREATE SET
  r.title = "Omlet",
  r.description = "Umuti jaja.\nIsprži na tiganju.\nDodaj sir po želji.",
  r.description_norm = toLower("Umuti jaja.\nIsprži na tiganju.\nDodaj sir po želji.")
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


//
MATCH (u:User {id:"11111111-1111-1111-1111-111111111111"})
MATCH (c:Category {name:"pasta"})
MERGE (r:Recipe {id:"r-pasta-001"})
ON CREATE SET
  r.title = "Pasta sa belim lukom",
  r.description = "Skuvaj testeninu.\nNa maslinovom ulju proprži beli luk.\nPomešaj i posluži.",
  r.description_norm = toLower("Skuvaj testeninu.\nNa maslinovom ulju proprži beli luk.\nPomešaj i posluži.")
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r
UNWIND [
  {name:"testenina", amount:200, unit:"g"},
  {name:"beli luk", amount:2, unit:"čena"},
  {name:"maslinovo ulje", amount:2, unit:"kašike"}
] AS ing
MERGE (i:Ingredient {name: ing.name})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount = ing.amount, rel.unit = ing.unit;


//
MATCH (u:User {id:"22222222-2222-2222-2222-222222222222"})
MATCH (c:Category {name:"pica"})
MERGE (r:Recipe {id:"r-pica-001"})
ON CREATE SET
  r.title = "Brza pica",
  r.description = "Razvuci testo.\nDodaj sos i sir.\nPeci 10-12 min.",
  r.description_norm = toLower("Razvuci testo.\nDodaj sos i sir.\nPeci 10-12 min.")
MERGE (u)-[:CREATED]->(r)
MERGE (r)-[:IN_CATEGORY]->(c)
WITH r
UNWIND [
  {name:"testo", amount:1, unit:"kom"},
  {name:"pelat", amount:150, unit:"g"},
  {name:"sir", amount:150, unit:"g"}
] AS ing
MERGE (i:Ingredient {name: ing.name})
MERGE (r)-[rel:HAS_INGREDIENT]->(i)
SET rel.amount = ing.amount, rel.unit = ing.unit;


// ----------------------------
// LIKES
// ----------------------------
MATCH (filip:User {id:"fc184998-e09e-451b-925b-2f496f279b50"})
MATCH (ana:User {id:"11111111-1111-1111-1111-111111111111"})
MATCH (marko:User {id:"22222222-2222-2222-2222-222222222222"})
MATCH (pasta:Recipe {id:"r-pasta-001"})
MATCH (pica:Recipe {id:"r-pica-001"})
MERGE (filip)-[:LIKES]->(pasta)
MERGE (ana)-[:LIKES]->(pica)
MERGE (marko)-[:LIKES]->(pasta);
