import ReviewCenter from "@/components/review-center";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ asset?: string }>;
}) {
  const { asset } = await searchParams;
  return <ReviewCenter initialAssetId={asset} />;
}
