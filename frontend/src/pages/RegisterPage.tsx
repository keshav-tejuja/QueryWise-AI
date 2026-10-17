import { Link } from "react-router-dom";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { useAuth } from "@/features/auth/AuthContext";
import { RegisterForm } from "@/features/auth/RegisterForm";

export function RegisterPage() {
  const { register } = useAuth();
  return (
    <AuthLayout
      title="Create your account"
      description="Natural-language analytics for your PostgreSQL data."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <RegisterForm onSubmit={register} />
    </AuthLayout>
  );
}