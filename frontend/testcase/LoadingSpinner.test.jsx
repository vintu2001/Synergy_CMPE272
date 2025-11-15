// frontend/testcase/components/LoadingSpinner.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LoadingSpinner from "../../src/components/LoadingSpinner.jsx";

describe("LoadingSpinner", () => {
  it("renders with default label", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders with a custom label", () => {
    render(<LoadingSpinner label="Fetching data" />);
    expect(screen.getByText("Fetching data")).toBeInTheDocument();
  });
});
