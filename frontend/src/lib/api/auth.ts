import { request, setAccessToken } from "./client";
import type { TokenResponse, User } from "./types";

export const authApi = {
  register: (input: { email: string; password: string; display_name: string }) =>
    request<User>("/auth/register", { method: "POST", body: input, auth: false }),

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const data = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    setAccessToken(data.access_token);
    return data;
  },

  logout: async (): Promise<void> => {
    try {
      await request<void>("/auth/logout", { method: "POST", auth: false });
    } finally {
      setAccessToken(null);
    }
  },
};