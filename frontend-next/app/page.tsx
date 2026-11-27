import Editor from "../features/exclusions/editor";
export const dynamic = "force-dynamic";
export default async function Page({ searchParams }: { searchParams: Promise<{ household?: string }> }) {
  const { household } = await searchParams;
  const id = typeof household === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(household) ? household : "";
  return <Editor key={id} householdId={id}/>;
}
