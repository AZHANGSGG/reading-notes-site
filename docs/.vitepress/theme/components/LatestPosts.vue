<script setup>
import { withBase } from 'vitepress'
import { data as posts } from '../posts.data.js'

const latest = posts.slice(0, 8)
</script>

<template>
  <section class="latest-posts">
    <h2 class="lp-heading">最新</h2>

    <ul v-if="latest.length" class="lp-list">
      <li v-for="p in latest" :key="p.url" class="lp-item">
        <a :href="withBase(p.url)" class="lp-link">
          <time class="lp-date">{{ p.dateText }}</time>
          <span class="lp-body">
            <span class="lp-title">{{ p.title }}</span>
            <span v-if="p.excerpt" class="lp-excerpt">{{ p.excerpt }}</span>
            <span v-if="p.tags.length" class="lp-tags">
              <span v-for="t in p.tags" :key="t" class="lp-tag">{{ t }}</span>
            </span>
          </span>
        </a>
      </li>
    </ul>

    <p v-else class="lp-empty">文章正在迁入中，很快上线。</p>

    <p class="lp-more">
      <a :href="withBase('/posts/')">查看全部文章 →</a>
    </p>
  </section>
</template>

<style scoped>
.latest-posts {
  max-width: 720px;
  margin: 0 auto;
  padding: 1rem 24px 5rem;
}
.lp-heading {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--vp-c-text-3);
  letter-spacing: 0.08em;
  margin: 0 0 0.4rem;
  padding-bottom: 0.7rem;
  border-bottom: 1px solid var(--vp-c-divider);
}
.lp-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.lp-item + .lp-item {
  border-top: 1px solid var(--vp-c-divider);
}
.lp-link {
  display: flex;
  gap: 1.2rem;
  padding: 1.3rem 0.2rem;
  text-decoration: none;
}
.lp-date {
  flex: 0 0 4.6rem;
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
  padding-top: 0.45rem;
  font-variant-numeric: tabular-nums;
}
.lp-body {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.lp-title {
  font-family: var(--ds-serif);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  line-height: 1.45;
  transition: color 0.15s ease;
}
.lp-link:hover .lp-title {
  color: var(--vp-c-brand-1);
}
.lp-excerpt {
  font-size: 0.92rem;
  color: var(--vp-c-text-2);
  line-height: 1.75;
}
.lp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.2rem;
}
.lp-tag {
  font-size: 0.74rem;
  color: var(--vp-c-text-3);
}
.lp-tag::before {
  content: '#';
  opacity: 0.6;
}
.lp-empty {
  color: var(--vp-c-text-3);
  text-align: center;
  padding: 2rem 0;
}
.lp-more {
  margin-top: 1.8rem;
}
.lp-more a {
  font-weight: 500;
  color: var(--vp-c-brand-1);
  text-decoration: none;
}
@media (max-width: 640px) {
  .lp-link {
    flex-direction: column;
    gap: 0.4rem;
  }
  .lp-date {
    flex: none;
    padding-top: 0;
  }
}
</style>
