import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
  return { name: "FamilyFoodOS", short_name: "FamilyFoodOS", lang: "ru",
    start_url: "/", display: "standalone", background_color: "#f5f7f3",
    theme_color: "#315c44", icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }] };
}
