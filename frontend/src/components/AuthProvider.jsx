import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); 

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const accessToken = localStorage.getItem("accessToken");
    if (storedUser && accessToken) {
      setUser(JSON.parse(storedUser));
    }else{
      setUser(null);
    }
    setLoading(false);
  }, []);

  const isAuthenticated = () => {
    return !!user && !!localStorage.getItem("accessToken");
  };

  const isFullyAuthenticated = () => isAuthenticated() && user?.face_verified;

  const logout = (manual = false) => {
    localStorage.clear();
    setUser(null);
    window.location.href = manual ? "/login" : "/login?expired=true";
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
    <AuthContext.Provider value={{ user, setUser, logout, isAuthenticated, isFullyAuthenticated, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
