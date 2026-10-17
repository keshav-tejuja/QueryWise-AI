import { Link } from "react-router-dom";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { useAuth } from "@/features/auth/AuthContext";
import { LoginForm } from "@/features/auth/LoginForm";

export function LoginPage() {
  const { login } = useAuth();
  return (
    <AuthLayout
      title="Sign in"
      description="Welcome back. Sign in to your workspace."
      footer={
        <>
          New to QueryWise?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <LoginForm onSubmit={login} />
    </AuthLayout>
  );
}