import {
  APP_BUILD_DATE,
  APP_VERSION,
  formatBuildDate,
} from '../../utils/appMeta.js'

const DEFAULT_SUPPORT_EMAIL = ''
const DEFAULT_FEEDBACK_EMAIL = ''
const DEFAULT_BD_EMAIL = ''

function buildDateText() {
  return formatBuildDate(APP_BUILD_DATE)
}

function resolveSourceList(source, fallback) {
  return Array.isArray(source) && source.length ? source : fallback
}

const NON_AD_PAYMENT_MARKERS = /赞助|捐赠|打赏|sponsor|donat(?:e|ion)|tip\s*jar/i

function isFakeLocalEmail(value) {
  const text = String(value || '').trim().toLowerCase()
  return text.includes('@') && text.split('@').at(-1)?.endsWith('.local')
}

function isNonAdPaymentCard(item) {
  return NON_AD_PAYMENT_MARKERS.test([
    item?.label,
    item?.title,
    item?.desc,
    item?.placeholderText,
    item?.actionText,
    item?.actionValue,
  ].map(value => String(value || '')).join(' '))
}

function sanitizeCommunityCards(cards) {
  return (Array.isArray(cards) ? cards : []).filter(item => item)
}

function sanitizeLegalDocs(legalDocs) {
  const result = { ...(legalDocs || {}) }
  for (const key of ['supportEmail', 'feedbackEmail', 'businessEmail']) {
    if (isFakeLocalEmail(result[key])) result[key] = ''
  }
  return result
}

export function createDefaultAboutContent() {
  const releaseDate = buildDateText()
  return {
    heroTitle: '智鱼云',
    heroBadgeText: '商业运营服务',
    heroDescription: '智鱼云提供账号运营、自动化、广告投放与反馈协作能力，帮助团队集中管理闲鱼业务流程。',
    serviceStatusText: '核心运营能力在线；广告服务按配置启用',
    logs: [
      {
        v: `v${APP_VERSION}`,
        t: releaseDate,
        tone: 'major',
        d: '当前版本已完成账号登录、系统配置整合与广告投放服务接入；未配置的广告能力会明确显示为不可用。',
        sections: [
          { t: '登录与账号', d: '使用账号密码登录模式，扫码登录仅用于闲鱼店铺授权，避免误连到外部旧环境。' },
          { t: '系统配置', d: '通用模型、向量模型、RAG 知识库与高德地图配置已统一收敛到系统配置页。' },
          { t: '广告投放', d: '广告套餐、申请、支付与展示均通过服务端统一处理，浏览器不会暴露敏感令牌。' },
        ],
        tags: ['账号登录', '系统配置整合', '广告投放', '客户反馈'],
      },
    ],
    supports: [
      {
        label: '反馈建议',
        desc: '提交内容进入反馈队列，便于维护团队统一跟进处理。',
        icon: 'aboutSupportFeedback',
        tone: 'violet',
        actionType: 'route',
        actionValue: 'feedback',
        actionMessage: '正在前往反馈建议...',
      },
      {
        label: '广告合作',
        desc: '查看广告套餐、提交投放申请并完成支付；未配置时入口会明确禁用操作。',
        icon: 'aboutSupportWeb',
        tone: 'blue',
        actionType: 'route',
        actionValue: 'ad-application',
        actionMessage: '正在前往广告合作...',
      },
      {
        label: '系统配置',
        desc: '统一管理通用模型、向量模型、RAG 知识库与高德地图配置。',
        icon: 'aboutSupportDoc',
        tone: 'green',
        actionType: 'route',
        actionValue: 'settings-system',
        actionMessage: '正在前往系统配置...',
      },
      {
        label: '商务联系',
        desc: '当前平台未配置商务联系人，请由平台运营方补充真实入口。',
        icon: 'aboutSupportChat',
        tone: 'orange',
        actionType: 'toast',
        actionValue: '平台运营方尚未配置商务联系方式。',
      },
    ],
    communityCards: [
      {
        label: '交流群',
        title: '微信群二维码',
        desc: '用于平台自行维护的版本通知、使用答疑、投放交流与功能建议收集。',
        placeholderText: '社群',
        hint: '配置后可扫码',
        tone: 'blue',
        actionType: 'toast',
        actionText: '配置后可扫码',
        actionValue: '当前平台尚未配置交流二维码，请联系平台负责人。',
      },
      {
        label: '联系方式',
        title: '商务合作联系方式',
        desc: '平台运营方配置真实且有人值守的联系方式后才会在这里展示。',
        value: '',
        hint: '当前未配置',
        tone: 'green',
        actionType: 'toast',
        actionText: '不可用',
        actionValue: '平台运营方尚未配置商务联系方式。',
      },
    ],
    links: [
      { label: '用户协议', icon: 'aboutShield', actionText: '查看', actionType: 'legal', actionValue: 'terms' },
      { label: '隐私政策', icon: 'aboutEye', actionText: '查看', actionType: 'legal', actionValue: 'privacy' },
      { label: '版本说明', icon: 'refresh', actionText: '查看', actionType: 'toast', actionValue: `当前版本 v${APP_VERSION} 已包含账号登录、系统配置整合与广告投放服务。` },
      { label: '导出诊断日志', icon: 'download', actionText: '导出', actionType: 'download', actionValue: 'diagnostics' },
    ],
    legalDocs: {
      termsUrl: '',
      privacyUrl: '',
      supportEmail: DEFAULT_SUPPORT_EMAIL,
      feedbackEmail: DEFAULT_FEEDBACK_EMAIL,
      businessEmail: DEFAULT_BD_EMAIL,
    },
  }
}

export function mergeAboutContent(payload = {}) {
  const defaults = createDefaultAboutContent()
  const communityCards = sanitizeCommunityCards(
    Array.isArray(payload.communityCards) ? payload.communityCards : defaults.communityCards
  )
  return {
    ...defaults,
    ...payload,
    heroTitle: payload.heroTitle || defaults.heroTitle,
    heroBadgeText: payload.heroBadgeText || defaults.heroBadgeText,
    heroDescription: payload.heroDescription || defaults.heroDescription,
    serviceStatusText: payload.serviceStatusText || defaults.serviceStatusText,
    logs: Array.isArray(payload.logs) ? payload.logs : defaults.logs,
    supports: Array.isArray(payload.supports) ? payload.supports : defaults.supports,
    communityCards,
    links: Array.isArray(payload.links) ? payload.links : defaults.links,
    legalDocs: sanitizeLegalDocs({
      ...defaults.legalDocs,
      ...(payload.legalDocs || {}),
    }),
  }
}

export function getAboutLogs(content = {}) {
  const fallbackLogs = createDefaultAboutContent().logs
  const source = resolveSourceList(content.logs, fallbackLogs)
  return source.map((item, index) => ({
    v: item?.v || `v${APP_VERSION}`,
    t: item?.t || buildDateText(),
    tone: item?.tone || (index === 0 ? 'major' : 'minor'),
    d: item?.d || '',
    sections: Array.isArray(item?.sections) ? item.sections : [],
    tags: Array.isArray(item?.tags) ? item.tags : [],
  }))
}

export function getAboutSupports(content = {}) {
  const fallbackSupports = createDefaultAboutContent().supports
  const source = resolveSourceList(content.supports, fallbackSupports)
  return source.map(item => {
    const fakeMailto = item?.actionType === 'mailto' && isFakeLocalEmail(item?.actionValue)
    return {
      label: item?.label || '支持入口',
      desc: item?.desc || '',
      icon: item?.icon || 'aboutSupportDoc',
      tone: item?.tone || 'blue',
      actionType: fakeMailto ? 'toast' : (item?.actionType || ''),
      actionValue: fakeMailto ? '平台运营方尚未配置真实联系方式。' : (item?.actionValue || ''),
      actionMessage: item?.actionMessage || '',
    }
  })
}

export function getAboutCommunityCards(content = {}) {
  const fallbackCards = createDefaultAboutContent().communityCards
  const source = sanitizeCommunityCards(resolveSourceList(content.communityCards, fallbackCards))
  return source.map(item => ({
    label: item?.label || '支持',
    title: item?.title || '社区卡片',
    desc: item?.desc || '',
    imageUrl: item?.imageUrl || '',
    imageAlt: item?.imageAlt || item?.title || 'community',
    placeholderText: item?.placeholderText || '',
    value: item?.value || '',
    hint: item?.hint || '',
    tone: item?.tone || 'blue',
    actionType: item?.actionType || '',
    actionText: item?.actionText || '',
    actionValue: item?.actionValue || '',
    actionMessage: item?.actionMessage || '',
  }))
}

export function getAboutLinks(content = {}) {
  const fallbackLinks = createDefaultAboutContent().links
  const source = resolveSourceList(content.links, fallbackLinks)
  return source.map(item => ({
    label: item?.label || '相关链接',
    icon: item?.icon || 'aboutEye',
    actionText: item?.actionText || '查看',
    actionType: item?.actionType || '',
    actionValue: item?.actionValue || '',
    actionMessage: item?.actionMessage || '',
  }))
}
