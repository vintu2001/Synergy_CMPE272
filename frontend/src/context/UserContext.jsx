import { createContext, useContext, useMemo, useState } from "react";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [residentIdState, setResidentIdState] = useState(
    typeof window !== "undefined" ? localStorage.getItem("resident_id") || "" : ""
  );
  const [residentNameState, setResidentNameState] = useState(
    typeof window !== "undefined" ? localStorage.getItem("resident_name") || "" : ""
  );

  const value = useMemo(
    () => ({
      residentId: residentIdState,
      residentName: residentNameState,
      setResidentId: (id) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("resident_id", id);
        }
        setResidentIdState(id);
      },
      setResidentName: (name) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("resident_name", name);
        }
        setResidentNameState(name);
      },
      setResidentProfile: ({ id, name }) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("resident_id", id);
          localStorage.setItem("resident_name", name);
        }
        setResidentIdState(id);
        setResidentNameState(name);
      },
    }),
    [residentIdState, residentNameState]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}



