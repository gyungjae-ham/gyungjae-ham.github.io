import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: "https://gyungjae-ham.github.io/",
    title: "무호흡냥냥펀치",
    description:
      "쉴 틈 없이 학습과 실무에 펀치를 날리는 백엔드 개발자의 기록장",
    author: "luca",
    profile: "https://github.com/gyungjae-ham",
    ogImage: "default-og.jpg",
    lang: "ko",
    timezone: "Asia/Seoul",
    dir: "ltr",
  },
  posts: {
    perPage: 4,
    perIndex: 4,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: true,
    showArchives: true,
    showBackButton: true,
    editPost: {
      enabled: true,
      url: "https://github.com/gyungjae-ham/gyungjae-ham.github.io/edit/main/",
    },
    search: "pagefind",
  },
  socials: [
    { name: "github", url: "https://github.com/gyungjae-ham" },
    { name: "linkedin", url: "https://www.linkedin.com/in/gyungjae-ham/" },
    { name: "mail", url: "mailto:gyeongjae.h.dev@gmail.com" },
  ],
  shareLinks: [
    { name: "x", url: "https://x.com/intent/post?url=" },
    { name: "telegram", url: "https://t.me/share/url?url=" },
    { name: "mail", url: "mailto:?subject=See%20this%20post&body=" },
  ],
});
