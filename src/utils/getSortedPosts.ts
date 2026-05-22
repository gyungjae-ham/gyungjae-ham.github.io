import type { CollectionEntry } from "astro:content";
import { postFilter } from "./postFilter";

/**
 * Returns posts that are eligible to be shown to users, sorted by `pubDatetime`
 * descending (most recently published first). `modDatetime` is used only as a
 * "last revised" marker shown in the article view, not for list ordering.
 *
 * Note: filtering respects drafts and scheduled posts via `postFilter()`.
 */
export function getSortedPosts(posts: CollectionEntry<"posts">[]) {
  return posts
    .filter(postFilter)
    .sort(
      (a, b) =>
        Math.floor(new Date(b.data.pubDatetime).getTime() / 1000) -
        Math.floor(new Date(a.data.pubDatetime).getTime() / 1000)
    );
}
