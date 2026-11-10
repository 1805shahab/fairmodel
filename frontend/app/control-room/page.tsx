import { redirect } from "next/navigation";

export default function ControlRoomPage() {
  // Keep old bookmarks working without exposing a second, fictional product.
  redirect("/dashboard");
}
