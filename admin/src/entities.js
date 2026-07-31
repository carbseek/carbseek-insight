// Entity configs driving the generic CRUD UI.
// Field types: text | textarea | number | boolean | select | array | json
//   array  — textarea, one item per line, submitted as string[]
//   json   — textarea holding raw JSON, submitted as parsed value
const INDUSTRIES = ['化工', '电子电气', '汽车', '欧盟出口', '通用'];
const THEMES = ['碳足迹', '碳标签', 'LCA', 'CBAM', 'EPD', 'PCR', 'Scope3', '碳核算', '碳数据平台', '政策'];

export const ENTITIES = {
  evidence: {
    key: 'evidence',
    label: '证据池',
    api: '/api/evidence',
    pk: 'evidence_id',
    columns: [
      { key: 'evidence_id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'source', label: '来源' },
      { key: 'date', label: '日期' },
      { key: 'industry', label: '行业' },
      { key: 'evidence_type', label: '类型' },
      { key: 'credibility', label: '可信度' },
      { key: 'in_product_pool', label: '产品池', render: (v) => (v ? '✓' : '—') },
    ],
    fields: [
      { name: 'evidence_id', label: 'ID', type: 'text', required: true, placeholder: 'EV-2026-0001' },
      { name: 'title', label: '标题', type: 'text', required: true },
      { name: 'source', label: '来源', type: 'text' },
      { name: 'source_url', label: '来源链接', type: 'text' },
      { name: 'date', label: '日期', type: 'text', placeholder: 'YYYY-MM-DD' },
      { name: 'industry', label: '行业', type: 'select', options: INDUSTRIES },
      { name: 'theme', label: '主题', type: 'select', options: THEMES },
      { name: 'evidence_type', label: '证据类型', type: 'select', options: ['政策', '学术', '专利', '竞品', '行业应用', '新闻'] },
      { name: 'credibility', label: '可信度', type: 'select', options: ['高', '中', '低'] },
      { name: 'in_product_pool', label: '进入产品池', type: 'boolean' },
      { name: 'abstract', label: '摘要', type: 'textarea' },
      { name: 'key_evidence', label: '关键证据', type: 'textarea' },
      { name: 'agent_explanation', label: 'Agent 解读', type: 'textarea' },
      { name: 'opportunity_ids', label: '关联机会 ID', type: 'array', help: '每行一个，如 OP-2026-0001' },
    ],
  },

  opportunities: {
    key: 'opportunities',
    label: '机会池',
    api: '/api/opportunities',
    pk: 'opportunity_id',
    columns: [
      { key: 'opportunity_id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'industry', label: '行业' },
      { key: 'theme', label: '主题' },
      { key: 'evidence_grade', label: '等级' },
      { key: 'priority', label: '优先级' },
      { key: 'status', label: '状态' },
      { key: 'updated_at', label: '更新于' },
    ],
    fields: [
      { name: 'opportunity_id', label: 'ID', type: 'text', required: true, placeholder: 'OP-2026-0001' },
      { name: 'title', label: '标题', type: 'textarea', required: true },
      { name: 'industry', label: '行业', type: 'select', options: INDUSTRIES },
      { name: 'theme', label: '主题', type: 'select', options: THEMES },
      { name: 'source_count', label: '来源数量', type: 'number' },
      { name: 'evidence_grade', label: '证据等级', type: 'select', options: ['A', 'B', 'C', 'D'] },
      { name: 'business_value', label: '商业价值 (1-10)', type: 'number' },
      { name: 'tech_feasibility', label: '技术可行性 (1-10)', type: 'number' },
      { name: 'revenue_potential', label: '收入潜力', type: 'select', options: ['高', '中', '低'] },
      { name: 'suggested_owner', label: '建议负责人', type: 'text' },
      { name: 'status', label: '状态', type: 'select', options: ['待评审', '已立项', '已上线', '已归档'] },
      { name: 'priority', label: '优先级', type: 'select', options: ['P0', 'P1', 'P2'] },
      { name: 'created_at', label: '创建日期', type: 'text', placeholder: 'YYYY-MM-DD' },
      { name: 'updated_at', label: '更新日期', type: 'text', placeholder: 'YYYY-MM-DD' },
      { name: 'evidence_ids', label: '关联证据 ID', type: 'array', help: '每行一个，如 EV-2026-0001' },
      { name: 'description', label: '描述', type: 'textarea' },
      { name: 'impact_pro', label: '对 Pro 影响', type: 'textarea' },
      { name: 'impact_scan', label: '对 Scan 影响', type: 'textarea' },
      { name: 'impact_db', label: '对因子库影响', type: 'textarea' },
    ],
  },

  policies: {
    key: 'policies',
    label: '政策倒计时',
    api: '/api/policies',
    pk: 'id',
    autoId: true,
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'policy', label: '政策' },
      { key: 'issuing_body', label: '发布机构' },
      { key: 'deadline', label: '截止日期' },
      { key: 'days_left', label: '剩余天数' },
      { key: 'urgency', label: '紧急度' },
    ],
    fields: [
      { name: 'policy', label: '政策名称', type: 'text', required: true },
      { name: 'issuing_body', label: '发布机构', type: 'text' },
      { name: 'deadline', label: '截止日期', type: 'text', required: true, placeholder: 'YYYY-MM-DD' },
      { name: 'days_left', label: '剩余天数', type: 'number' },
      { name: 'urgency', label: '紧急度', type: 'select', options: ['critical', 'high', 'medium', 'low'] },
    ],
  },

  articles: {
    key: 'articles',
    label: '文章情报',
    api: '/api/articles',
    pk: 'article_id',
    columns: [
      { key: 'article_id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'source', label: '来源' },
      { key: 'source_type', label: '类型' },
      { key: 'industry', label: '行业' },
      { key: 'publish_date', label: '发布日期' },
      { key: 'relevance_score', label: '相关度' },
    ],
    fields: [
      { name: 'article_id', label: 'ID', type: 'text', required: true, placeholder: 'ART-2026-001' },
      { name: 'title', label: '标题', type: 'textarea', required: true },
      { name: 'summary', label: '摘要', type: 'textarea' },
      { name: 'source', label: '来源', type: 'text' },
      { name: 'source_type', label: '来源类型', type: 'select', options: ['industry', 'news', 'policy', 'academic', 'patent'] },
      { name: 'industry', label: '行业', type: 'text' },
      { name: 'publish_date', label: '发布日期', type: 'text', placeholder: 'YYYY-MM-DD' },
      { name: 'relevance_score', label: '相关度 (0-1)', type: 'number', step: '0.01' },
      { name: 'url', label: '链接', type: 'text' },
    ],
  },

  competitors: {
    key: 'competitors',
    label: '竞品动态',
    api: '/api/competitors',
    pk: 'id',
    autoId: true,
    // GET /api/competitors wraps rows in { demo, competitors }
    listFrom: (data) => data.competitors ?? [],
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'avatar', label: '头像' },
      { key: 'name', label: '名称' },
      { key: 'action', label: '动作' },
      { key: 'impact', label: '影响' },
    ],
    fields: [
      { name: 'avatar', label: '头像文字', type: 'text', placeholder: '如:宁德' },
      { name: 'name', label: '名称', type: 'text', required: true },
      { name: 'action', label: '动作', type: 'textarea' },
      { name: 'impact', label: '影响', type: 'textarea' },
    ],
  },

  trends: {
    key: 'trends',
    label: '行业趋势',
    api: '/api/trends',
    pk: 'industry',
    // GET /api/trends returns { 化工: {score,...}, ... } — flatten to rows
    listFrom: (data) =>
      Object.entries(data).map(([industry, v]) => ({ industry, ...v })),
    columns: [
      { key: 'industry', label: '行业' },
      { key: 'score', label: '热度分' },
      { key: 'change', label: '变化' },
      { key: 'top_theme', label: '最热主题' },
    ],
    fields: [
      { name: 'industry', label: '行业', type: 'text', required: true },
      { name: 'score', label: '热度分', type: 'number' },
      { name: 'change', label: '变化', type: 'number' },
      { name: 'top_theme', label: '最热主题', type: 'text' },
    ],
  },

  recommendations: {
    key: 'recommendations',
    label: '推荐配置',
    api: '/api/recommendations',
    pk: 'id',
    autoId: true,
    // GET /api/recommendations returns { 行业: [{id,type,name,desc}] } — flatten to rows
    listFrom: (data) =>
      Object.entries(data).flatMap(([industry, items]) =>
        items.map((it) => ({ industry, ...it })),
      ),
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'industry', label: '行业' },
      { key: 'type', label: '类型' },
      { key: 'name', label: '名称' },
      { key: 'desc', label: '说明' },
    ],
    fields: [
      { name: 'industry', label: '行业', type: 'text', required: true },
      { name: 'type', label: '类型', type: 'select', options: ['field', 'template', 'plugin'], required: true },
      { name: 'name', label: '名称', type: 'text', required: true },
      { name: 'desc', label: '说明', type: 'textarea' },
    ],
  },

  radar_items: {
    key: 'radar_items',
    label: '雷达条目',
    api: '/api/radar-items',
    pk: 'radar_id',
    columns: [
      { key: 'radar_id', label: 'ID' },
      { key: 'title', label: '标题' },
      { key: 'category', label: '分类' },
      { key: 'severity', label: '严重度' },
      { key: 'industry', label: '行业' },
      { key: 'date', label: '日期' },
      { key: 'action_required', label: '需行动', render: (v) => (v ? '✓' : '—') },
    ],
    fields: [
      { name: 'radar_id', label: 'ID', type: 'text', required: true, placeholder: 'RD-2026-W30-01' },
      { name: 'title', label: '标题', type: 'textarea', required: true },
      { name: 'category', label: '分类', type: 'select', options: ['政策变化', '竞品动作', '技术突破', '市场动态'] },
      { name: 'severity', label: '严重度', type: 'select', options: ['critical', 'high', 'medium', 'low'] },
      { name: 'industry', label: '行业', type: 'select', options: INDUSTRIES },
      { name: 'date', label: '日期', type: 'text', placeholder: 'YYYY-MM-DD' },
      { name: 'summary', label: '摘要', type: 'textarea' },
      { name: 'evidence_ids', label: '关联证据 ID', type: 'array', help: '每行一个，如 EV-2026-0001' },
      { name: 'action_required', label: '需要行动', type: 'boolean' },
    ],
  },

  reports: {
    key: 'reports',
    label: '周报',
    api: '/api/reports',
    pk: 'report_id',
    columns: [
      { key: 'report_id', label: 'ID' },
      { key: 'week_ending', label: '周截止日期' },
      { key: 'one_sentence_judgment', label: '一句话判断' },
    ],
    fields: [
      { name: 'report_id', label: 'ID', type: 'text', required: true, placeholder: 'WR-2026-W31' },
      { name: 'week_ending', label: '周截止日期', type: 'text', required: true, placeholder: 'YYYY-MM-DD' },
      { name: 'one_sentence_judgment', label: '一句话判断', type: 'textarea' },
      { name: 'impact_pro', label: '对 Pro 影响', type: 'textarea' },
      { name: 'impact_scan', label: '对 Scan 影响', type: 'textarea' },
      { name: 'impact_db', label: '对因子库影响', type: 'textarea' },
      { name: 'rd_suggestions', label: '研发建议', type: 'array', help: '每行一条' },
      { name: 'top_opportunities', label: '本周 Top 机会', type: 'json', help: 'JSON 数组,元素为机会对象' },
      { name: 'demo', label: '演示数据', type: 'boolean' },
    ],
  },

  intel_center: {
    key: 'intel_center',
    label: '情报中心',
    api: '/api/intel-center',
    single: true,
    fields: [
      { name: 'overall_status', label: '整体状态', type: 'text' },
      { name: 'update_frequency', label: '更新频率', type: 'text' },
      { name: 'demo', label: '演示数据', type: 'boolean' },
      { name: 'agents', label: 'Agents', type: 'json', help: 'JSON 数组,如 [{"icon":"📰","name":"...","status":"..."}]' },
      { name: 'stats', label: '统计卡片', type: 'json', help: 'JSON 数组,如 [{"value":24,"label":"...","color":"blue"}]' },
      { name: 'latest', label: '最新情报', type: 'json', help: 'JSON 数组,如 [{"title":"...","tag":"...","meta":"..."}]' },
    ],
  },
};

// Tab order for the entity management pages
export const ENTITY_TABS = [
  'evidence',
  'opportunities',
  'policies',
  'articles',
  'competitors',
  'trends',
  'recommendations',
  'radar_items',
  'reports',
  'intel_center',
];
