import { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import styles from "../styles/ProfilePage.module.css";
import { useNavigate } from "react-router-dom";
import { useCurrentUser } from "../current_user/CurrentUserContext";
const HARD_USER_ID = "fc184998-e09e-451b-925b-2f496f279b50";

function Card({ children, className = "", ...props}) {
  return <div className={`${styles.card} ${className}`} {...props}>{children}</div>;
}

function Button({ variant = "primary", className = "", ...props }) {
  return (
    <button
      className={`${styles.btn} ${styles[`btn_${variant}`]} ${className}`}
      {...props}
    />
  );
}

function Input(props) {
  return <input className={styles.input} {...props} />;
}

function Textarea(props) {
  return <textarea className={styles.textarea} {...props} />;
}

function Select(props) {
  return <select className={styles.select} {...props} />;
}

function Pill({ children }) {
  return <span className={styles.pill}>{children}</span>;
}

function IngredientRow({ ing, onChange, onRemove, canRemove }) {
  return (
    <div className={styles.ingRow}>
      <Input
        placeholder="Naziv (npr. jaja)"
        value={ing.name}
        onChange={(e) => onChange({ ...ing, name: e.target.value })}
      />
      <Input
        placeholder="Količina"
        type="number"
        min="0"
        step="any"
        value={ing.amount ?? ""}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === "") {
            // ako obrise kolicinu, obrisi i unit
            onChange({ ...ing, amount: null, unit: "" });
            return;
          }

          const n = Number(raw);
          const safe = Number.isFinite(n) ? Math.max(0, n) : 0;

          // ako je 0 ili pozitivno
          onChange({ ...ing, amount: safe });
        }}
        onKeyDown={(e) => {
          if (e.key === "-" || e.key === "e" || e.key === "E") e.preventDefault();
        }}
      />

      <Input
        placeholder="Jedinica (g/ml/kom)"
        value={ing.unit ?? ""}
        disabled={ing.amount === null || ing.amount === 0}
        onChange={(e) => {
          // ne dozvoli upis jedinice ako nema kolicine
          if (ing.amount === null || ing.amount === 0) return;
          onChange({ ...ing, unit: e.target.value });
        }}
      />

      <Button
        variant="ghost"
        className={styles.iconBtn}
        onClick={onRemove}
        disabled={!canRemove}
        title="Ukloni"
      >
        ✕
      </Button>
    </div>
  );
}

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [skip, setSkip] = useState(0);
  const [recipesTotal, setRecipesTotal] = useState(0);
  const [categories, setCategories] = useState([]);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("uncategorized");
  const [ingredients, setIngredients] = useState([{ name: "", amount: null, unit: "" }]);

  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const [likedRecipes, setLikedRecipes] = useState([]);
  const [likesSkip, setLikesSkip] = useState(0);
  const [likesTotal, setLikesTotal] = useState(0);
  const [likesLoading, setLikesLoading] = useState(false);

  const [editing, setEditing] = useState(null); // ovde drzim recept koji editujem
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editCategory, setEditCategory] = useState("uncategorized");
  const [editIngredients, setEditIngredients] = useState([{ name: "", amount: null, unit: "" }]);

  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  const { userId, setUserId } = useCurrentUser();

  const [allUsers, setAllUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);


  const canCreate = useMemo(() => title.trim().length > 0, [title]);

  const recipesAllLoaded = recipes.length >= recipesTotal;


  async function loadUsers() {
    setUsersLoading(true);
    try {
      const data = await api.listUsers(0, 50);
      setAllUsers(data.results || []);
    } finally {
      setUsersLoading(false);
    }
  }

  async function onChangeUser(nextId) {
    setUserId(nextId);

    // reset svega vezanog za profil
    setUser(null);
    setRecipes([]);
    setSkip(0);
    setLikedRecipes([]);
    setLikesSkip(0);
    setLikesTotal(0);
    setRecipesTotal(0);


    // ucitaj sve ispočetka za novog usera
    try {
      const u = await api.getUser(nextId);
      setUser(u);

      const r = await api.listUserRecipes(nextId, 0, 20);
      setRecipes(r.results || []);
      setRecipesTotal(r.total ?? 0);
      setSkip(20);


      const page = await api.likesIdsPage(nextId, 0, 20);
      setLikesTotal(page.total ?? 0);
      const ids = page.recipe_ids || [];
      const details = ids.length ? await api.byIds(ids) : { results: [] };
      setLikedRecipes(details.results || []);
      setLikesSkip(20);
    } catch (e) {
      setErr(e.message || String(e));
    }
  }

  async function loadProfile(reset = false) {
    setLoading(true);
    setErr("");
    try {
      const u = await api.getUser(userId);
      setUser(u);

      const pageSkip = reset ? 0 : skip;
      const data = await api.listUserRecipes(userId, pageSkip, 20);
      console.log("listUserRecipes:", data);
      setRecipesTotal(data.total ?? 0);
      setRecipes((prev) => (reset ? data.results : [...prev, ...data.results]));
      setSkip(pageSkip + 20);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function loadCategories() {
    try {
      const data = await api.listCategories();
      const list = data.results || [];
      setCategories(list);
      if (list.includes("uncategorized")) setCategory("uncategorized");
    } catch {
      // nije kriticno
    }
  }

  async function onCreateRecipe() {
    setErr("");
    setCreating(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() ? description : null,
        category,
        ingredients: ingredients
          .map((x) => ({
            name: x.name?.trim(),
            amount: x.amount === null ? null : x.amount,
            unit: x.unit?.trim() ? x.unit.trim() : null,
          }))
          .filter((x) => x.name),
      };

      await api.createRecipeForUser(userId, payload);

      // reset forme
      setTitle("");
      setDescription("");
      setCategory("uncategorized");
      setIngredients([{ name: "", amount: null, unit: "" }]);

      // reload
      setRecipes([]);
      setSkip(0);
      await loadProfile(true);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setCreating(false);
    }
  }

  async function loadLikes(reset = false) {
    setLikesLoading(true);
    setErr("");
    try {
      const pageSkip = reset ? 0 : likesSkip;

      // 1) uzmi ids page
      const page = await api.likesIdsPage(userId, pageSkip, 20);
      // očekujemo: { total, skip, limit, recipe_ids }
      const ids = page.recipe_ids || [];
      setLikesTotal(page.total ?? 0);

      // 2) batch detalji
      const details = ids.length ? await api.byIds(ids) : { results: [] };

      setLikedRecipes((prev) => (reset ? details.results : [...prev, ...details.results]));
      setLikesSkip(pageSkip + 20);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLikesLoading(false);
    }
}

function openEdit(recipe) {
  setEditing(recipe);
  setEditTitle(recipe.title ?? "");
  setEditDescription(recipe.description ?? "");
  setEditCategory(recipe.category ?? "uncategorized");
  setEditIngredients(
    recipe.ingredients?.length
      ? recipe.ingredients.map((x) => ({
          name: x.name ?? "",
          amount: x.amount ?? null,
          unit: x.unit ?? "",
        }))
      : [{ name: "", amount: null, unit: "" }]
  );
}

function closeEdit() {
  setEditing(null);
}

async function saveEdit() {
  if (!editing) return;
  setSavingEdit(true);
  setErr("");

  try {
    const payload = {
      title: editTitle.trim() ? editTitle.trim() : null,
      description: editDescription.trim() ? editDescription : "", // "" = obriši, null = ne šalji (ali ti šalješ ovde)
      category: editCategory,
      ingredients: editIngredients
        .map((x) => ({
          name: x.name?.trim(),
          amount: x.amount === null ? null : x.amount,
          unit: x.unit?.trim() ? x.unit.trim() : null,
        }))
        .filter((x) => x.name),
    };

    await api.updateRecipeForUser(userId, editing.id, payload);

    closeEdit();
    setRecipes([]);
    setSkip(0);
    await loadProfile(true);
  } catch (e) {
    setErr(e.message || String(e));
  } finally {
    setSavingEdit(false);
  }
}

async function deleteRecipe(recipeId) {
  if (!confirm("Obrisati recept?")) return;
  setDeletingId(recipeId);
  setErr("");

  try {
    await api.deleteRecipeForUser(userId, recipeId);
    setRecipes([]);
    setSkip(0);
    await loadProfile(true);
  } catch (e) {
    setErr(e.message || String(e));
  } finally {
    setDeletingId(null);
  }
}


useEffect(() => {
  loadUsers();
  loadCategories();
  loadProfile(true);
  loadLikes(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);


  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <div className={styles.kicker}>Aplikacija za deljenje recepata</div>
          <h1 className={styles.title}>Profil korisnika</h1>
        </div>
        <div className={styles.headerRight}>
          {loading ? <Pill> "Učitavanje…" </Pill> : ""}
        </div>
      </header>

      {err ? (
        <div className={styles.alert}>
          <div className={styles.alertTitle}>Greška</div>
          {/* <div className={styles.alertText}>{err}</div> */}
        </div>
      ) : null}

      <div className={styles.grid}>
        {/* LEFT: user + create */}
        <div className={styles.colLeft}>
          <Card className={styles.userCard}>
            <div className={styles.userTop}>
              <div className={styles.avatar}>
                {(user?.username?.[0] || "U").toUpperCase()}
              </div>
              <div className={styles.userMeta}>
                <div className={styles.userLabel}>Korisnik</div>
                <div className={styles.userName}>
                  {user ? user.username : "Učitavanje…"}
                </div>
                <div className={styles.userId}>{userId}</div>
              </div>
            </div>
            {/*  lista korisnika */}
            <div className={styles.field}>
              <div className={styles.label}>Izaberi korisnika</div>
              <Select
                value={userId}
                onChange={(e) => onChangeUser(e.target.value)}
                disabled={usersLoading || !allUsers.length}
              >
                {allUsers.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username}
                  </option>
                ))}
              </Select>
            </div>
            
          </Card>
          <Card className={styles.formCard}>
            <div className={styles.cardHeader}>
              <div>
                <div className={styles.cardTitle}>Dodaj recept</div>
                <div className={styles.cardHint}>Brzo dodavanje sa sastojcima.</div>
              </div>
            </div>

            <div className={styles.form}>
              <div className={styles.field}>
                <div className={styles.label}>Naslov</div>
                <Input placeholder="npr. Omlet" value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>

              <div className={styles.field}>
                <div className={styles.label}>Opis (opciono)</div>
                <Textarea
                  placeholder="Kratak opis pripreme…"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className={styles.field}>
                <div className={styles.label}>Kategorija</div>
                <Select value={category} onChange={(e) => setCategory(e.target.value)}>
                  {categories.length ? (
                    categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="uncategorized">uncategorized</option>
                      <option value="pasta">pasta</option>
                      <option value="pica">pica</option>
                      <option value="dezert">dezert</option>
                    </>
                  )}
                </Select>
              </div>

              <div className={styles.field}>
                <div className={styles.labelRow}>
                  <div className={styles.label}>Sastojci</div>
                  <Button
                    variant="secondary"
                    type="button"
                    onClick={() => setIngredients((prev) => [...prev, { name: "", amount: null, unit: "" }])}
                  >
                    + Dodaj
                  </Button>
                </div>

                <div className={styles.ingList}>
                  {ingredients.map((ing, idx) => (
                    <IngredientRow
                      key={idx}
                      ing={ing}
                      canRemove={ingredients.length > 1}
                      onChange={(next) =>
                        setIngredients((prev) => prev.map((x, i) => (i === idx ? next : x)))
                      }
                      onRemove={() => setIngredients((prev) => prev.filter((_, i) => i !== idx))}
                    />
                  ))}
                </div>
              </div>

              <div className={styles.actions}>
                <Button
                  onClick={onCreateRecipe}
                  disabled={!canCreate || creating}
                  className={styles.createBtn}
                >
                  {creating ? "Kreiram…" : "Kreiraj recept"}
                </Button>
              </div>
            </div>
          </Card>
        </div>

<div className={styles.colRight}>
  <div className={styles.rightGrid}>
    {/* PANEL 1: Moji recepti */}
    <div className={styles.panel}>
      <div className={styles.sectionHeader}>
        <div>
          <div className={styles.sectionTitle}>Moji recepti</div>
          <div className={styles.sectionHint}>
            Ukupno: <strong>{recipesTotal}</strong> • Prikazano: <strong>{recipes.length}</strong>
          </div>
        </div>
        <Button variant="ghost" onClick={() => loadProfile(true)} disabled={loading}>
          ↻ Osveži
        </Button>
      </div>

      <div className={styles.recipes}>
        {recipes.map((r) => (
          <Card key={r.id} 
            className={styles.recipeCard}
              onClick={() => navigate(`/recipes/${r.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && navigate(`/recipes/${r.id}`)
              }>
            <div className={styles.recipeTop}>
              <div className={styles.recipeTitle}>{r.title}</div>

                <div className={styles.recipeActions}>
                  <span className={styles.badge}>{r.category ?? "uncategorized"}</span>

                  <Button
                    variant="ghost"
                    className={styles.iconBtn}
                    type="button"
                    title="Izmeni"
                    onClick={(e) => { e.stopPropagation(); openEdit(r); }}
                  >
                    ✎
                  </Button>

                  <Button
                    variant="ghost"
                    className={styles.iconBtn}
                    type="button"
                    title="Obriši"
                    disabled={deletingId === r.id}
                    onClick={(e) => { e.stopPropagation(); deleteRecipe(r.id); }}
                  >
                    🗑
                  </Button>
                </div>
              </div>

            {r.description ? <div className={styles.recipeDesc}>{r.description}</div> : null}

            {r.ingredients?.length ? (
              <div className={styles.recipeIngs}>
                {r.ingredients.map((x, i) => (
                  <span key={i} className={styles.ingChip}>
                    {x.name}
                    {x.amount != null || x.unit ? (
                      <span className={styles.ingChipMeta}>
                        {" "}
                        • {x.amount ?? ""}{x.unit ?? ""}
                      </span>
                    ) : null}
                  </span>
                ))}
              </div>
            ) : (
              <div className={styles.emptyIngs}>Nema sastojaka.</div>
            )}
          </Card>
        ))}
      </div>

      <div className={styles.loadMoreWrap}>
        <Button
          onClick={() => loadProfile(false)}
          disabled={loading || recipesAllLoaded}
          variant="secondary"
        >
          {loading ? "Učitavam…" : recipesAllLoaded ? "Nema više" : "Učitaj još"}
        </Button>
      </div>
    </div>

    {/* PANEL 2: Lajkovani recepti */}
    <div className={styles.panel}>
      <div className={styles.sectionHeader}>
        <div>
          <div className={styles.sectionTitle}>Lajkovani recepti</div>
          <div className={styles.sectionHint}>
            Ukupno: <strong>{likesTotal}</strong> • Prikazano: <strong>{likedRecipes.length}</strong>
          </div>
        </div>
        <Button variant="ghost" onClick={() => loadLikes(true)} disabled={likesLoading}>
          ↻ Osveži
        </Button>
      </div>

              <div className={styles.recipes}>
                {likedRecipes.map((r) => (
                  <Card key={r.id} 
                    className={styles.recipeCard}
                      onClick={() => navigate(`/recipes/${r.id}`)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === "Enter" && navigate(`/recipes/${r.id}`)
                      }>
                    <div className={styles.recipeTop}>
                      <div className={styles.recipeTitle}>{r.title}</div>
                      <span className={styles.badge}>{r.category ?? "uncategorized"}</span>
                    </div>

                    {r.description ? <div className={styles.recipeDesc}>{r.description}</div> : null}

                    {r.ingredients?.length ? (
                      <div className={styles.recipeIngs}>
                        {r.ingredients.map((x, i) => (
                          <span key={i} className={styles.ingChip}>
                            {x.name}
                            {x.amount != null || x.unit ? (
                              <span className={styles.ingChipMeta}>
                                {" "}
                                • {x.amount ?? ""}{x.unit ?? ""}
                              </span>
                            ) : null}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <div className={styles.emptyIngs}>Nema sastojaka.</div>
                    )}
                  </Card>
                ))}
              </div>

              <div className={styles.loadMoreWrap}>
                <Button
                  onClick={() => loadLikes(false)}
                  disabled={likesLoading || likedRecipes.length >= likesTotal}
                  variant="secondary"
                >
                  {likesLoading
                    ? "Učitavam…"
                    : likedRecipes.length >= likesTotal
                    ? "Nema više"
                    : "Učitaj još"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
      {editing ? (
  <div className={styles.modalBackdrop} onClick={closeEdit}>
    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
      <div className={styles.modalHeader}>
        <div className={styles.modalTitle}>Izmeni recept</div>
        <Button variant="ghost" className={styles.iconBtn} onClick={closeEdit}>✕</Button>
      </div>
      <div className={styles.modalBody}>
        <div className={styles.form}>
          <div className={styles.field}>
            <div className={styles.label}>Naslov</div>
            <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
          </div>

          <div className={styles.field}>
            <div className={styles.label}>Opis</div>
            <Textarea rows={3} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
            <div className={styles.hint}>Obriši opis tako što ostaviš prazno i sačuvaš.</div>
          </div>

          <div className={styles.field}>
            <div className={styles.label}>Kategorija</div>
            <Select value={editCategory} onChange={(e) => setEditCategory(e.target.value)}>
              {(categories.length ? categories : ["uncategorized"]).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </Select>
          </div>

          <div className={styles.field}>
            <div className={styles.labelRow}>
              <div className={styles.label}>Sastojci</div>
              <Button
                variant="secondary"
                type="button"
                onClick={() => setEditIngredients((prev) => [...prev, { name: "", amount: null, unit: "" }])}
              >
                + Dodaj
              </Button>
            </div>

            <div className={styles.ingList}>
              {editIngredients.map((ing, idx) => (
                <IngredientRow
                  key={idx}
                  ing={ing}
                  canRemove={editIngredients.length > 1}
                  onChange={(next) =>
                    setEditIngredients((prev) => prev.map((x, i) => (i === idx ? next : x)))
                  }
                  onRemove={() => setEditIngredients((prev) => prev.filter((_, i) => i !== idx))}
                />
              ))}
            </div>
          </div>

          <div className={styles.actions}>
            <Button variant="secondary" onClick={closeEdit} type="button">
              Otkaži
            </Button>
            <Button onClick={saveEdit} disabled={savingEdit || !editTitle.trim()} type="button">
              {savingEdit ? "Čuvam…" : "Sačuvaj"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
) : null}
    </div>
  );
}