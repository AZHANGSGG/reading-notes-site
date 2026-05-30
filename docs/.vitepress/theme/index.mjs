import DefaultTheme from 'vitepress/theme'
import { h, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'
import mediumZoom from 'medium-zoom'
import LatestPosts from './components/LatestPosts.vue'
import PostList from './components/PostList.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  // 首页 hero 下方插入「最新文章」列表
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'home-features-after': () => h(LatestPosts),
    })
  },
  enhanceApp({ app }) {
    // 供 /posts/ 列表页在 markdown 里使用 <PostList />
    app.component('PostList', PostList)
  },
  setup() {
    const route = useRoute()
    const initZoom = () => {
      mediumZoom('.slides-grid img, .vp-doc img:not(.no-zoom)', {
        background: 'rgba(20, 14, 10, 0.92)',
        margin: 24,
      })
    }
    onMounted(() => initZoom())
    watch(
      () => route.path,
      () => nextTick(() => initZoom())
    )
  },
}
