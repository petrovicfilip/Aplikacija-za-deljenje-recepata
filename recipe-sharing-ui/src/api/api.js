const API = import.meta.env.VITE_API_URL;

async function http(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || JSON.stringify(data);
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  // 204
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // users
  createUser: (username) =>
    http(`/users`, { method: "POST", body: JSON.stringify({ username }) }),

  listUsers: (skip = 0, limit = 50) =>
    http(`/users?skip=${skip}&limit=${limit}`),

  // recipes
  getRecipe: (id) => http(`/recipes/${encodeURIComponent(id)}`),

  popular: (skip = 0, limit = 20) =>
    http(`/recipes/popular?skip=${skip}&limit=${limit}`),

  search: (ingredients, skip = 0, limit = 20) => {
    const qs = ingredients
      .map((x) => `ingredients=${encodeURIComponent(x)}`)
      .join("&");
    return http(`/recipes/search?${qs}&skip=${skip}&limit=${limit}`);
  },

  byIds: (ids) =>
    http(`/recipes/by_ids`, { method: "POST", body: JSON.stringify({ ids }) }),

  likesCountForRecipe: (recipeId) =>
    http(`/recipes/${encodeURIComponent(recipeId)}/likes_count`),

  // likes
  like: (user_id, recipe_id) =>
    http(`/likes`, { method: "POST", body: JSON.stringify({ user_id, recipe_id }) }),

  unlike: (user_id, recipe_id) =>
    http(`/likes`, { method: "DELETE", body: JSON.stringify({ user_id, recipe_id }) }),

  likesCountForUser: (userId) =>
    http(`/likes/users/${encodeURIComponent(userId)}/count`),

  likesIdsPage: (userId, skip = 0, limit = 20) =>
    http(`/likes/users/${encodeURIComponent(userId)}?skip=${skip}&limit=${limit}`),

   getUser: (userId) => http(`/users/${encodeURIComponent(userId)}`),

  listUserRecipes: (userId, skip = 0, limit = 20) =>
    http(`/users/${encodeURIComponent(userId)}/recipes?skip=${skip}&limit=${limit}`),

  createRecipeForUser: (userId, payload) =>
    http(`/users/${encodeURIComponent(userId)}/recipes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listCategories: () => http(`/categories`),

  likesCountForUser: (userId) =>
  http(`/likes/users/${encodeURIComponent(userId)}/count`),

  likesIdsPage: (userId, skip = 0, limit = 20) =>
    http(`/likes/users/${encodeURIComponent(userId)}/ids?skip=${skip}&limit=${limit}`),

  byIds: (ids) =>
    http(`/recipes/by_ids`, { method: "POST", body: JSON.stringify({ ids }) }),
  
  updateRecipeForUser: (userId, recipeId, payload) =>
  http(`/users/${encodeURIComponent(userId)}/recipes/${encodeURIComponent(recipeId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),

  deleteRecipeForUser: (userId, recipeId) =>
    http(`/users/${encodeURIComponent(userId)}/recipes/${encodeURIComponent(recipeId)}`, {
      method: "DELETE",
    }),

  getRecipeLikesCount: (recipeId) => http(`/recipes/${encodeURIComponent(recipeId)}/likes_count`),

  likeRecipe: (payload) =>
    http(`/likes`, { method: "POST", body: JSON.stringify(payload) }),

  unlikeRecipe: (payload) =>
    http(`/likes`, { method: "DELETE", body: JSON.stringify(payload) }),

  likesIdsPage: (userId, skip=0, limit=20) =>
    http(`/likes/users/${encodeURIComponent(userId)}/ids?limit=${limit}&skip=${skip}`),

  likeExists: (userId, recipeId) =>
  http(`/likes/exists?user_id=${encodeURIComponent(userId)}&recipe_id=${encodeURIComponent(recipeId)}`),
  
  searchByCategory: (category, skip = 0, limit = 20) =>
    request(
      `/recipes/search_by_category?category=${encodeURIComponent(category)}&skip=${skip}&limit=${limit}`
    ),

  searchByDescription: (q, skip = 0, limit = 20) =>
    request(
      `/recipes/search_by_description?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`
    ),
};