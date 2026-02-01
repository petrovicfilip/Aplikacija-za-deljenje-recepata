import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/api";
import styles from "../styles/RecipePage.module.css";
import formStyles from "../styles/ProfilePage.module.css";
import { useCurrentUser } from "../current_user/CurrentUserContext";


const HARD_USER_ID = "fc184998-e09e-451b-925b-2f496f279b50";

function Button({ variant = "primary", className = "", ...props }) {
  return (
    <button
      className={`${formStyles.btn} ${formStyles[`btn_${variant}`]} ${className}`}
      {...props}
    />
  );
}

function Input(props) {
  return <input className={formStyles.input} {...props} />;
}

function Textarea(props) {
  return <textarea className={formStyles.textarea} {...props} />;
}

function Select(props) {
  return <select className={formStyles.select} {...props} />;
}

function IngredientRow({ ing, onChange, onRemove, canRemove }) {
  return (
    <div className={formStyles.ingRow}>
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
            onChange({ ...ing, amount: null, unit: "" });
            return;
          }
          const n = Number(raw);
          const safe = Number.isFinite(n) ? Math.max(0, n) : 0;
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
          if (ing.amount === null || ing.amount === 0) return;
          onChange({ ...ing, unit: e.target.value });
        }}
      />

      <Button
        variant="ghost"
        className={formStyles.iconBtn}
        onClick={onRemove}
        disabled={!canRemove}
        title="Ukloni"
        type="button"
      >
        ✕
      </Button>
    </div>
  );
}


export default function RecipePage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const [likesCount, setLikesCount] = useState(0);
  const [liked, setLiked] = useState(false);
  const [likeBusy, setLikeBusy] = useState(false);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [categories, setCategories] = useState([]);

  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editCategory, setEditCategory] = useState("uncategorized");
  const [editIngredients, setEditIngredients] = useState([{ name: "", amount: null, unit: "" }]);
  const [savingEdit, setSavingEdit] = useState(false);
  const { userId } = useCurrentUser();



  async function toggleLike() {
    if (!data) return;
    setLikeBusy(true);
    setErr("");
    try {
      if (!liked) {
        await api.likeRecipe({ user_id: userId, recipe_id: data.id });
        setLiked(true);
        setLikesCount((x) => x + 1);
      } else {
        await api.unlikeRecipe({ user_id: userId, recipe_id: data.id });
        setLiked(false);
        setLikesCount((x) => Math.max(0, x - 1));
      }
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLikeBusy(false);
    }
  }
  

  const isMine = data?.created_by?.id === userId;

  async function onDelete() {
    if (!isMine) return;
    if (!confirm("Obrisati ovaj recept?")) return;

    setDeleteBusy(true);
    setErr("");
    try {
      await api.deleteRecipeForUser(userId, data.id);
      navigate("/profile");
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setDeleteBusy(false);
    }
  }

  async function loadCategories() {
  try {
    const data = await api.listCategories();
    setCategories(data.results || []);
  } catch {
    // nije kritično
  }
}

  function openEdit() {
    if (!data) return;
    setEditing(true);
    setEditTitle(data.title ?? "");
    setEditDescription(data.description ?? "");
    setEditCategory(data.category ?? "uncategorized");
    setEditIngredients(
      data.ingredients?.length
        ? data.ingredients.map((x) => ({
            name: x.name ?? "",
            amount: x.amount ?? null,
            unit: x.unit ?? "",
          }))
        : [{ name: "", amount: null, unit: "" }]
    );
  }

  function closeEdit() {
    setEditing(false);
  }

  async function saveEdit() {
    if (!data) return;
    setSavingEdit(true);
    setErr("");

    try {
      const payload = {
        title: editTitle.trim() ? editTitle.trim() : null,
        // "" = obriši, null = ne šalji -> mi šaljemo "" kad je prazno
        description: editDescription.trim() ? editDescription : "",
        category: editCategory,
        ingredients: editIngredients
          .map((x) => ({
            name: x.name?.trim(),
            amount: x.amount == null ? null : Math.max(0, x.amount),
            unit:
              x.amount != null && x.amount > 0 && x.unit?.trim()
                ? x.unit.trim()
                : null,
          }))
          .filter((x) => x.name),
      };

      await api.updateRecipeForUser(userId, data.id, payload);

      // reload recept
      const fresh = await api.getRecipe(data.id);
      setData(fresh);

      closeEdit();
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setSavingEdit(false);
    }
  }



  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const r = await api.getRecipe(id);
        loadCategories();

        setData(r);

        // likes count
        const lc = await api.getRecipeLikesCount(id); // { recipe_id, likes }
        setLikesCount(lc.likes);
        const ex = await api.likeExists(userId, id);
        // duplo da ga negiram da sigurno bude bool, msm nema potrebe al kao
        setLiked(!!ex.exists);
      } catch (e) {
        setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [id, userId]);

  if (loading) return <div className={styles.page}>Učitavanje…</div>;
  if (err) return <div className={styles.page}>Greška: {err}</div>;
  if (!data) return <div className={styles.page}>Nema podataka.</div>;

  return (
    <div className={styles.page}>
      <div className={styles.topbar}>
        <Link to="/profile" className={styles.back}>← Nazad</Link>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>{data.title}</h1>

          <div className={styles.headerRight}>
            <span className={styles.badge}>{data.category ?? "uncategorized"}</span>

            <button
              className={`${styles.likeBtn} ${liked ? styles.likeBtnActive : ""}`}
              onClick={toggleLike}
              disabled={likeBusy}
              title={liked ? "Ukloni like" : "Lajkuj"}
              type="button"
            >
              {liked ? "♥" : "♡"} <span className={styles.likeCount}>{likesCount}</span>
            </button>

            {isMine ? (
              <button
                className={styles.deleteBtn}
                onClick={openEdit}
                type="button"
                title="Izmeni recept"
              >
                ✎
              </button>
            ) : null}

            {isMine ? (
              <button
                className={styles.deleteBtn}
                onClick={onDelete}
                disabled={deleteBusy}
                type="button"
                title="Obriši recept"
              >
                {deleteBusy ? "Brisanje…" : "🗑"}
                
              </button>
            ) : null}
          </div>
        </div>


        {data.created_by ? (
          <div className={styles.meta}>
            Postavio: <strong>{data.created_by.username}</strong>{" "}
            <span className={styles.muted}>({data.created_by.id})</span>
          </div>
        ) : (
          <div className={styles.meta}>Postavio: <span className={styles.muted}>nepoznato</span></div>
        )}

        {data.description ? (
        <>
            <div className={styles.sectionTitle}>Priprema</div>
            <ul className={styles.list}>
            {data.description
                .split(/\r?\n/)
                .map((line) => line.trim())
                .filter(Boolean)
                .map((line, idx) => (
                <li key={idx}>{line}</li>
                ))}
            </ul>
        </>
        ) : (
        <>
            <div className={styles.sectionTitle}>Priprema</div>
            <div className={styles.muted}>Nema opisa.</div>
        </>
        )}


        <div className={styles.sectionTitle}>Sastojci</div>
        {data.ingredients?.length ? (
          <ul className={styles.list}>
            {data.ingredients.map((x, i) => (
              <li key={i}>
                <strong>{x.name}</strong>{" "}
                {x.amount != null || x.unit ? (
                  <span className={styles.muted}>
                    - {x.amount ?? ""} {x.unit ?? ""}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <div className={styles.muted}>Nema sastojaka.</div>
        )}
      </div>
      {editing ? (
        <div className={formStyles.modalBackdrop} onClick={closeEdit}>
          <div className={formStyles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={formStyles.modalHeader}>
              <div className={formStyles.modalTitle}>Izmeni recept</div>
              <Button variant="ghost" className={formStyles.iconBtn} onClick={closeEdit} type="button">
                ✕
              </Button>
            </div>

            <div className={formStyles.modalBody}>
              <div className={formStyles.form}>
                <div className={formStyles.field}>
                  <div className={formStyles.label}>Naslov</div>
                  <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                </div>

                <div className={formStyles.field}>
                  <div className={formStyles.label}>Opis</div>
                  <Textarea
                    rows={3}
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                  />
                  <div className={formStyles.hint}>Obriši opis tako što ostaviš prazno i sačuvaš.</div>
                </div>

                <div className={formStyles.field}>
                  <div className={formStyles.label}>Kategorija</div>
                  <Select value={editCategory} onChange={(e) => setEditCategory(e.target.value)}>
                    {(categories.length ? categories : ["uncategorized"]).map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className={formStyles.field}>
                  <div className={formStyles.labelRow}>
                    <div className={formStyles.label}>Sastojci</div>
                    <Button
                      variant="secondary"
                      type="button"
                      onClick={() =>
                        setEditIngredients((prev) => [...prev, { name: "", amount: null, unit: "" }])
                      }
                    >
                      + Dodaj
                    </Button>
                  </div>

                  <div className={formStyles.ingList}>
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

                <div className={formStyles.actions}>
                  <Button variant="secondary" onClick={closeEdit} type="button">
                    Otkaži
                  </Button>
                  <Button
                    onClick={saveEdit}
                    disabled={savingEdit || !editTitle.trim()}
                    type="button"
                  >
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