import { createContext, useContext, useMemo, useState } from "react";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [residentId, setResidentId] = useState(
    localStorage.getItem("resident_id") || "RES_1001"
  );

  const value = useMemo(
    () => ({
      residentId,
      setResidentId: (id) => {
        localStorage.setItem("resident_id", id);
        setResidentId(id);
      },
    }),
    [residentId]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}



