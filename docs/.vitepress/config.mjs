import { defineConfig } from 'vitepress'
import { generateSidebar } from './sidebar.mjs'

// ⚠️ 重要：base 路径
// 如果你的仓库名是 reading-notes-site → base: '/reading-notes-site/'
// 如果你的仓库名是 <你的用户名>.github.io → base: '/'
// 改成你自己的仓库名
const REPO_NAME = 'reading-notes-site'

export default defineConfig({
  lang: 'zh-CN',
  title: '懂叔的出海笔记',
  description: '从新加坡看中国企业出海：一个落地服务商的地缘、文化与落地实务笔记。',
  base: `/${REPO_NAME}/`,
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  sitemap: {
    hostname: 'https://azhangsgg.github.io/reading-notes-site/'
  },

  head: [
    ['link', { rel: 'icon', href: '/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#9a5b3d' }],
    ['meta', { name: 'author', content: '懂叔' }],
    ['meta', { name: 'keywords', content: '中国企业出海,新加坡公司注册,新马落地,马来西亚落地,跨文化管理,地缘政治,中美关系,AI出海,东南亚市场,家族办公室,FA融资,出海顾问,China going global,Singapore,Southeast Asia,cross-cultural management,geopolitics' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: '懂叔的出海笔记' }],
    ['meta', { property: 'og:description', content: '从新加坡看中国企业出海：地缘、文化与落地实务。' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
    ['meta', { property: 'og:site_name', content: '懂叔的出海笔记' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: '懂叔的出海笔记' }],
    ['meta', { name: 'twitter:description', content: '从新加坡看中国企业出海：地缘、文化与落地实务。' }],
  ],

  themeConfig: {
    logo: { src: '/logo.svg', width: 24, height: 24 },
    siteTitle: '懂叔',

    nav: [
      { text: '首页', link: '/' },
      { text: '文章', link: '/posts/' },
      { text: '读书', link: '/books/' },
      { text: '关于', link: '/about' },
    ],

    sidebar: generateSidebar(),

    footer: {
      message: '一个人的出海笔记 · 在新加坡',
      copyright: `© ${new Date().getFullYear()} 懂叔`
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            displayDetails: '显示详情',
            resetButtonTitle: '清除',
            backButtonTitle: '返回',
            noResultsText: '没有找到相关内容',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    outline: { level: [2, 3], label: '本页大纲' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdatedText: '最后更新',
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '目录',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到亮色',
    darkModeSwitchTitle: '切换到暗色',
  }
})
