import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "@/lib/api/client";
import { LoginForm } from "./LoginForm";

it("shows validation errors and does not submit an empty form", async () => {
  const onSubmit = vi.fn();
  render(<LoginForm onSubmit={onSubmit} />);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(screen.getByText("Email is required.")).toBeInTheDocument();
  expect(screen.getByText("Enter your password.")).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

it("submits the trimmed email and the password", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<LoginForm onSubmit={onSubmit} />);
  await userEvent.type(screen.getByLabelText(/email/i), "  a@b.co ");
  await userEvent.type(screen.getByLabelText(/password/i), "secret-password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(onSubmit).toHaveBeenCalledWith("a@b.co", "secret-password");
});

it("disables the button while the request is pending", async () => {
  let resolve: () => void = () => {};
  const onSubmit = vi.fn(() => new Promise<void>((r) => (resolve = r)));
  render(<LoginForm onSubmit={onSubmit} />);
  await userEvent.type(screen.getByLabelText(/email/i), "a@b.co");
  await userEvent.type(screen.getByLabelText(/password/i), "secret-password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(screen.getByRole("button", { name: /sign in/i })).toBeDisabled();
  resolve();
});

it("displays the server's error message", async () => {
  const onSubmit = vi
    .fn()
    .mockRejectedValue(new ApiError(401, "invalid_credentials", "Invalid email or password."));
  render(<LoginForm onSubmit={onSubmit} />);
  await userEvent.type(screen.getByLabelText(/email/i), "a@b.co");
  await userEvent.type(screen.getByLabelText(/password/i), "wrong-password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
});