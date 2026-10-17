import { validateDisplayName, validateEmail, validatePassword } from "./validation";

describe("validateEmail", () => {
  it("requires a value", () => expect(validateEmail("  ")).toBe("Email is required."));
  it("rejects malformed addresses", () => {
    expect(validateEmail("nope")).toBe("Enter a valid email address.");
    expect(validateEmail("a@b")).toBe("Enter a valid email address.");
  });
  it("accepts a normal address", () => expect(validateEmail("a@b.co")).toBeUndefined());
});

describe("validatePassword", () => {
  it("requires a value", () => expect(validatePassword("")).toBe("Password is required."));
  it("enforces minimum length", () =>
    expect(validatePassword("123456789")).toBe("Use at least 10 characters."));
  it("enforces maximum length", () =>
    expect(validatePassword("x".repeat(129))).toBe("Use at most 128 characters."));
  it("accepts a valid password", () => expect(validatePassword("1234567890")).toBeUndefined());
});

describe("validateDisplayName", () => {
  it("requires non-blank text", () => expect(validateDisplayName("   ")).toBe("Name is required."));
  it("accepts a name", () => expect(validateDisplayName("Keshav")).toBeUndefined());
});