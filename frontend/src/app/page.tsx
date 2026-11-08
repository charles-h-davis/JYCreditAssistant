import { redirect } from "next/navigation";

/**
 * The app has no route that makes sense at `/`, so send people to the dashboard.
 * `RequireAuth` inside the (app) group bounces them to /sign-in when signed out.
 */
export default function Home() {
  redirect("/dashboard");
}
