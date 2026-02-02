import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/api";
import styles from "../styles/SearchPage.module.css";

//
import { useCurrentUser } from "../current_user/CurrentUserContext";

function Card({ children, className = "", ...props }) {
  return (
    <div className={`${styles.card} ${className}`} {...props}>
      {children}
    </div>
  );
}

function Button({ variant = "primary", className = "", type = "button", ...props }) {
  return (
    <button
      type={type}
      className={`${styles.btn} ${styles[`btn_${variant}`]} ${className}`}
      {...props}
    />
  );
}

function parseIngs(text) {
  return text
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}


function Input(props) {
  return <input className={styles.input} {...props} />;
}

function Select(props) {
  return <select className={styles.select} {...props} />;
}

function Pill({ children, className = "" }) {
  return <span className={`${styles.pill} ${className}`}>{children}</span>;
}

function RecipeCard({ r, onClick }) {
  return (
    <Card className={styles.recipeCard} onClick={onClick}>
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
      ) : null}
    </Card>
  );
}

export default function SearchPage() {
  const navigate = useNavigate();

    const { userId } = useCurrentUser(); // string id
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
    let alive = true;

    async function loadUser() {
        if (!userId) {
        setCurrentUser(null);
        return;
        }
        try {
        const u = await api.getUser(userId);
        if (alive) setCurrentUser(u);
        } catch {
        if (alive) setCurrentUser(null);
        }
    }

    loadUser();
    return () => {
        alive = false;
    };
    }, [userId]);


  const [mode, setMode] = useState("category"); // "category" | "ingredients" | "description"

  // forme
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("uncategorized");

  const [ingText, setIngText] = useState("");
  const [ings, setIngs] = useState([]);

  const [descQ, setDescQ] = useState("");

  // rezultati pretrage
  const [results, setResults] = useState([]);
  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // preporuke
  const [reco, setReco] = useState([]);
  const [recoSkip, setRecoSkip] = useState(0);
  const [recoTotal, setRecoTotal] = useState(0);
  const [recoMode, setRecoMode] = useState(""); 
  const [recoLoading, setRecoLoading] = useState(false);

  const [err, setErr] = useState("");

  const limit = 20;
  const recoLimit = 10;

  const allLoaded = results.length >= total && total > 0;
  const recoAllLoaded = reco.length >= recoTotal && recoTotal > 0;

  const canSearch = useMemo(() => {
    if (mode === "category") return !!category;
    if (mode === "ingredients") return ings.length > 0;
    if (mode === "description") return descQ.trim().length > 0;
    return false;
  }, [mode, category, ings, descQ]);

  async function loadCategories() {
    try {
      const data = await api.listCategories();
      const list = data.results || [];
      setCategories(list);
      if (list.includes("uncategorized")) setCategory("uncategorized");
      else if (list.length) setCategory(list[0]);
    } catch {
        //...
    }
  }

  function addIngredientFromText() {
    const v = ingText.trim().toLowerCase();
    if (!v) return;
    setIngs((prev) => (prev.includes(v) ? prev : [...prev, v]));
    setIngText("");
  }

  function removeIng(name) {
    setIngs((prev) => prev.filter((x) => x !== name));
  }

  async function runSearch(reset = false) {
    if (!canSearch) return;

    let effectiveIngs = ings;

    if (mode === "ingredients" && effectiveIngs.length === 0) {
    const fromText = parseIngs(ingText);
    if (fromText.length) {
        effectiveIngs = fromText;
        setIngs(fromText);
        setIngText("");
    }
    }


    setErr("");
    setLoading(true);

    try {
      const pageSkip = reset ? 0 : skip;

      let data;
      if (mode === "category") {
        data = await api.searchByCategory(category, pageSkip, limit);
      } else if (mode === "ingredients") {
        data = await api.searchByIngredients(effectiveIngs, pageSkip, limit);
      } else {
        data = await api.searchByDescription(descQ, pageSkip, limit);
      }

      const got = data.results || [];
      setTotal(data.total ?? (reset ? got.length : total));
      setResults((prev) => (reset ? got : [...prev, ...got]));
      setSkip(pageSkip + limit);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

async function loadRecommendations(reset = false) {
  if (!userId) return;

  setRecoLoading(true);
  setErr("");
  try {
    const pageSkip = reset ? 0 : recoSkip;

    const data = await api.recommendForUser(userId, pageSkip, recoLimit);

    const got = Array.isArray(data) ? data : (data?.results ?? []);
    setReco((prev) => (reset ? got : [...prev, ...got]));
    setRecoMode(data?.mode ?? "");

    if (typeof data?.total === "number") setRecoTotal(data.total);

    setRecoSkip(pageSkip + recoLimit);
  } catch (e) {
    setErr(e.message || String(e));
  } finally {
    setRecoLoading(false);
  }
}



  useEffect(() => {
    setResults([]);
    setSkip(0);
    setTotal(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  // inicijalno
  useEffect(() => {
    loadCategories();
  }, []);

  // default: search po kategoriji
  useEffect(() => {
    if (mode === "category" && category) runSearch(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, category]);

  // preporuke za korisnika
  useEffect(() => {
    setReco([]);
    setRecoSkip(0);
    setRecoTotal(0);
    if (userId) loadRecommendations(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <div className={styles.kicker}>APLIKACIJA ZA DELJENJE RECEPATA</div>
          <h1 className={styles.title}>Pretraga</h1>
          <div className={styles.subtitle}>
            Pretraži recepte po kategoriji, sastojcima ili opisu.
          </div>
        </div>

        <div className={styles.headerRight}>
          <Pill>{loading ? "Pretraga…" : "Spremno"}</Pill>
          <Button variant="secondary" onClick={() => navigate("/profile")}>
            ← Profil
          </Button>
        </div>
      </header>

      {err ? (
        <div className={styles.alert}>
          <div className={styles.alertTitle}>Greška</div>
          <div className={styles.alertText}>{err}</div>
        </div>
      ) : null}

      <div className={styles.grid}>
        {/* search controls */}
        <div className={styles.left}>
          <Card className={styles.panel}>
            <div className={styles.panelTitle}>Pretraga</div>

            <div className={styles.segment}>
              <button
                className={`${styles.segmentBtn} ${mode === "category" ? styles.segmentActive : ""}`}
                onClick={() => setMode("category")}
                type="button"
              >
                Kategorija
              </button>
              <button
                className={`${styles.segmentBtn} ${mode === "ingredients" ? styles.segmentActive : ""}`}
                onClick={() => setMode("ingredients")}
                type="button"
              >
                Sastojci
              </button>
              <button
                className={`${styles.segmentBtn} ${mode === "description" ? styles.segmentActive : ""}`}
                onClick={() => setMode("description")}
                type="button"
              >
                Opis
              </button>
            </div>

            {mode === "category" ? (
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
            ) : null}

            {mode === "ingredients" ? (
              <div className={styles.field}>
                <div className={styles.label}>Sastojci</div>
                <div className={styles.row}>
                  <Input
                    value={ingText}
                    placeholder="npr. jaja"
                    onChange={(e) => setIngText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addIngredientFromText();
                      }
                    }}
                  />
                  <Button variant="secondary" type="button" onClick={addIngredientFromText}>
                    Dodaj
                  </Button>
                </div>

                {ings.length ? (
                  <div className={styles.chips}>
                    {ings.map((x) => (
                      <span key={x} className={styles.chip}>
                        {x}
                        <button className={styles.chipX} onClick={() => removeIng(x)} type="button">
                          ✕
                        </button>
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className={styles.hint}>Dodaj bar jedan sastojak.</div>
                )}
              </div>
            ) : null}

            {mode === "description" ? (
              <div className={styles.field}>
                <div className={styles.label}>Opis sadrži</div>
                <Input
                  value={descQ}
                  placeholder="npr. u rerni"
                  onChange={(e) => setDescQ(e.target.value)}
                />
              </div>
            ) : null}

            {mode !== "category" ? (
              <div className={styles.actions}>
                <Button
                  onClick={() => runSearch(true)}
                  disabled={!canSearch || loading}
                  className={styles.searchBtn}
                >
                  {loading ? "Tražim…" : "Pretraži"}
                </Button>
              </div>
            ) : null}

            <div className={styles.meta}>
              <div>
                Rezultati: <strong>{results.length}</strong>
                {total ? (
                  <>
                    {" "}
                    / <strong>{total}</strong>
                  </>
                ) : null}
              </div>
            </div>
          </Card>
        </div>

        {/* results */}
        <div className={styles.center}>
          <div className={styles.sectionHeader}>
            <div>
              <div className={styles.sectionTitle}>Rezultati</div>
              <div className={styles.sectionHint}>
                Klikni na recept da otvoriš detalje.
              </div>
            </div>

            <Button variant="ghost" onClick={() => runSearch(true)} disabled={loading || !canSearch}>
              ↻ Osveži
            </Button>
          </div>

          <div className={styles.list}>
            {results.map((r) => (
              <RecipeCard key={r.id} r={r} onClick={() => navigate(`/recipes/${r.id}`)} />
            ))}
          </div>

          <div className={styles.loadMoreWrap}>
            <Button
              onClick={() => runSearch(false)}
              disabled={loading || !canSearch || allLoaded}
              variant="secondary"
            >
              {allLoaded ? "Sve učitano" : loading ? "Učitavam…" : "Učitaj još"}
            </Button>
          </div>
        </div>

        {/* recommendations */}
        <div className={styles.right}>
          <Card className={styles.panel}>
            <div className={styles.panelTop}>
              <div>
                <div className={styles.panelTitle}>Preporučeno</div>
                <div className={styles.panelHint}>
                  {userId ? (
                    <>
                      za: <strong>{currentUser?.username}</strong>{" "} 
                      {recoMode ? <span className={styles.dim}>({recoMode})</span> : null}
                    </>
                  ) : (
                    <span className={styles.dim}>Izaberi korisnika u profilu.</span>
                  )}
                </div>
              </div>

              <Button
                variant="ghost"
                onClick={() => loadRecommendations(true)}
                disabled={!userId || recoLoading}
                title="Osveži"
              >
                ↻
              </Button>
            </div>

            <div className={styles.listSmall}>
              {reco.map((r) => (
                <div
                  key={r.id}
                  className={styles.recoItem}
                  onClick={() => navigate(`/recipes/${r.id}`)}
                  role="button"
                  tabIndex={0}
                >
                  <div className={styles.recoTitle}>{r.title}</div>
                  <div className={styles.recoMeta}>
                    <span className={styles.badgeSmall}>{r.category ?? "uncategorized"}</span>
                    {r.score != null ? <span className={styles.dim}>score: {r.score}</span> : null}
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.loadMoreWrap}>
              <Button
                onClick={() => loadRecommendations(false)}
                disabled={!userId || recoLoading || recoAllLoaded}
                variant="secondary"
              >
                {recoAllLoaded ? "Sve učitano" : recoLoading ? "Učitavam…" : "Učitaj još"}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
