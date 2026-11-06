import { cookies } from "next/headers";
import Workspace from "@/components/workspace";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jar = await cookies();
  const role =
    jar.get("fairmodel-persona")?.value === "studio_demo" ? "studio" : "artist";
  return <Workspace initialRole={role}>{children}</Workspace>;
}
