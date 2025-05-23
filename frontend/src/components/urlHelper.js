export const getFullUrl = (path) => {
  const apiUrl = import.meta.env.VITE_API_URL || "https://localhost:8000/api/";
  const cleanBase = apiUrl.replace(/\/+api\/?$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  return `${cleanBase}${cleanPath}`;
};
