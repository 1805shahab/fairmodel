import UsagePassport from "@/components/usage-passport";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <UsagePassport id={id} />;
}
