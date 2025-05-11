import axios from "axios";

//protect agains csrf token -> unauthorized requests from other sites
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      //"csrftoken="
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let isRefreshing= false;
let refreshSubs = [];

function onTokenRefreshed(newToken){
  refreshSubs.forEach((callback) => callback(newToken));
  refreshSubs = [];
}

function addRefreshSubscriber(callback){
  refreshSubs.push(callback);
}

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

//where to go
axiosInstance.interceptors.request.use(
  (config) => {
    const csrfToken = getCookie("csrftoken");
    const accessToken = localStorage.getItem("accessToken");

    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }

    if (accessToken) {
      config.headers["Authorization"] = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 429) {
      alert("Too many tries. Please try to login again later.");
      return Promise.reject(error);
    }

    if (error.response?.status === 400) {
      const message =
        error.response.data?.detail ||
        "The request is not valid. Please verify the input data.";
      alert(message);
      return Promise.reject(error);
    }

    // ✳️ LOGICĂ REFRESH TOKEN
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.warn("401 received – trying to refresh access token.");
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refreshToken");

      if (!refreshToken) {
        console.warn("⚠️ No refresh token found – redirecting to login.");
        window.location.href = "/login?expired=true";
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((newToken) => {
            originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
            resolve(axiosInstance(originalRequest));
          });
        });
      }

      isRefreshing = true;

      try {
        const res = await axios.post(
          `${import.meta.env.VITE_API_URL}token/refresh/`,
          { refresh: refreshToken }
        );
        
        const newAccessToken = res.data.access;
        const newRefreshToken = res.data.refresh;
        
        localStorage.setItem("accessToken", newAccessToken);
        
        if (newRefreshToken) {
          localStorage.setItem("refreshToken", newRefreshToken);
        }
        localStorage.setItem("accessToken", newAccessToken);

        axiosInstance.defaults.headers[
          "Authorization"
        ] = `Bearer ${newAccessToken}`;
        originalRequest.headers[
          "Authorization"
        ] = `Bearer ${newAccessToken}`;

        onTokenRefreshed(newAccessToken);
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        setTimeout(() => {
          console.error("Refresh token failed:", refreshError.response?.data || refreshError.message);
        }, 2000);
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login?expired=true";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);


export default axiosInstance;