// Unique constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT user_username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;

CREATE CONSTRAINT recipe_id_unique IF NOT EXISTS
FOR (r:Recipe) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT ingredient_name_unique IF NOT EXISTS
FOR (i:Ingredient) REQUIRE i.name IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

// Fulltext index (description_norm)
CREATE FULLTEXT INDEX recipeDescNormIndex IF NOT EXISTS
FOR (r:Recipe)
ON EACH [r.description_norm];
