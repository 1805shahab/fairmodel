import LicenseDetail from "@/components/license-detail";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <LicenseDetail id={id} />;
}
