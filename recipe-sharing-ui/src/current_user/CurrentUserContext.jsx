import { createContext, useContext, useMemo, useState } from "react";

const CurrentUserCtx = createContext(null);
const LS_KEY = "recipe_sharing_current_user_id";

export function CurrentUserProvider({ children, defaultUserId }) {
  const [userId, setUserIdState] = useState(() => {
    return localStorage.getItem(LS_KEY) || defaultUserId || "";
  });

  const setUserId = (nextId) => {
    setUserIdState(nextId);
    localStorage.setItem(LS_KEY, nextId);
  };

  const value = useMemo(() => ({ userId, setUserId }), [userId]);
  return <CurrentUserCtx.Provider value={value}>{children}</CurrentUserCtx.Provider>;
}

export function useCurrentUser() {
  const ctx = useContext(CurrentUserCtx);
  if (!ctx) throw new Error("useCurrentUser must be used within CurrentUserProvider");
  return ctx;
}