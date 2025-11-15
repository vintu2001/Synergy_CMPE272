// frontend/testcase/test-utils.jsx
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UserProvider } from "../src/context/UserContext.jsx";

export function renderWithProviders(ui, { route = "/", initialEntries } = {}) {
  const Wrapper = ({ children }) => (
    <MemoryRouter initialEntries={initialEntries ?? [route]}>
      <UserProvider>{children}</UserProvider>
    </MemoryRouter>
  );

  return render(ui, { wrapper: Wrapper });
}
