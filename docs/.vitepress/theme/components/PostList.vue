<script setup>
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import { data as posts } from '../posts.data.js'

const active = ref('全部')

const allTags = computed(() => {
  const s = new Set()
  posts.forEach((p) => p.tags.forEach((t) => s.add(t)))
  return ['全部', ...Array.from(s)]
})

const filtered = computed(() =>
  active.value === '全部'
    ? posts
    : posts.filter((p) => p.tags.includes(active.value))
)

const byYear = computed(() => {
  const groups = {}
  filtered.value.forEach((p) => {
    const y = (p.date || '').slice(0, 4) || '其他'
    ;(groups[y] = groups[y] || []).push(p)
  })
  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map((y) => ({ year: y, posts: groups[y] }))
})
</script>

<template>
  <div class="post-list">
    <div class="pl-tagbar">
      <button
        v-for="t in allTags"
        :key="t"
        :class="['pl-tagbtn', { active: active === t }]"
        @click="active = t"
      >
        {{ t }}
      </button>
    </div>

    <div v-for="g in byYear" :key="g.year" class="pl-year-group">
      <div class="pl-year">{{ g.year }}</div>
      <ul class="pl-list">
        <li v-for="p in g.posts" :key="p.url" class="pl-item">
          <a :href="withBase(p.url)" class="pl-link">
            <time class="pl-date">{{ p.dateText }}</time>
            <span class="pl-body">
              <span class="pl-title">{{ p.title }}</span>
              <span v-if="p.excerpt" class="pl-excerpt">{{ p.excerpt }}</span>
            </span>
          </a>
        </li>
      </ul>
    </div>

    <p v-if="!filtered.length" class="pl-empty">这个标签下还没有文章。</p>
  </div>
</template>

<style scoped>
.post-list {
  margin-top: 1.5rem;
}
.pl-tagbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 2rem;
}
.pl-tagbtn {
  font-size: 0.82rem;
  color: var(--vp-c-text-2);
  background: transparent;
  border: 1px solid var(--vp-c-divider);
  border-radius: 999px;
  padding: 0.25rem 0.85rem;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pl-tagbtn:hover {
  border-color: var(--vp-c-brand-2);
  color: var(--vp-c-brand-1);
}
.pl-tagbtn.active {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}
.pl-year {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--vp-c-text-3);
  letter-spacing: 0.05em;
  margin: 2rem 0 0.2rem;
}
.pl-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.pl-item + .pl-item {
  border-top: 1px solid var(--vp-c-divider);
}
.pl-link {
  display: flex;
  gap: 1.2rem;
  padding: 1.3rem 0.2rem;
  text-decoration: none !important;
}
.pl-date {
  flex: 0 0 4.6rem;
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
  padding-top: 0.45rem;
  font-variant-numeric: tabular-nums;
}
.pl-body {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.pl-title {
  font-family: var(--ds-serif);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  line-height: 1.45;
  transition: color 0.15s ease;
}
.pl-link:hover .pl-title {
  color: var(--vp-c-brand-1);
}
.pl-excerpt {
  font-size: 0.92rem;
  color: var(--vp-c-text-2);
  line-height: 1.75;
}
.pl-empty {
  color: var(--vp-c-text-3);
  text-align: center;
  padding: 3rem 0;
}
@media (max-width: 640px) {
  .pl-link {
    flex-direction: column;
    gap: 0.4rem;
  }
  .pl-date {
    flex: none;
    padding-top: 0;
  }
}
</style>
