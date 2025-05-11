import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // să nu treacă ProtectedRoute înainte de verificare

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const logout = (manual = false) => {
    localStorage.clear();
    setUser(null);
    window.location.href = manual ? "/login" : "/login?expired=true";
  };

  const isAuthenticated = () => {
    return !!user && !!localStorage.getItem("accessToken");
  };

  // Dacă tokenurile se șterg din alt tab → logout
  useEffect(() => {
    const handleStorageChange = (event) => {
      if (
        (event.key === "accessToken" || event.key === "refreshToken") &&
        event.newValue === null
      ) {
        setTimeout(()=>{
            const newToken = localStorage.getItem("accessToken");
            if(!newToken){
              console.warn("Token missing after delay, logging out is happening.");
              setUser(null);
              window.location.href = "/login?expired=true";
            }else{
              console.info("Token is back, skip logout");
            }
        },300);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, logout, isAuthenticated, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
