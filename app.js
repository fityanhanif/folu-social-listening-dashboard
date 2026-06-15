const COLORS = {
  positive: '#9fd17a',
  negative: '#ff8d75',
  neutral: '#dfc18b'
};
const fmt = new Intl.NumberFormat('id-ID');
const pct = (value, total) => total ? `${Math.round((value / total) * 100)}%` : '0%';
const clean = (v) => (v === null || v === undefined || v === '' || Number.isNaN(v)) ? '-' : v;
const shortText = (s, n = 120) => (s || '').length > n ? (s || '').slice(0, n - 1) + '…' : (s || '');

function drawDonut(canvas, counts) {
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const cx = w * 0.32, cy = h * 0.52, r = Math.min(w, h) * 0.30;
  let start = -Math.PI / 2;
  ['positive','neutral','negative'].forEach(key => {
    const val = counts[key] || 0;
    const angle = total ? (val / total) * Math.PI * 2 : 0;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + angle);
    ctx.closePath();
    ctx.fillStyle = COLORS[key];
    ctx.fill();
    start += angle;
  });
  ctx.globalCompositeOperation = 'destination-out';
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.58, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#fff8ea';
  ctx.font = '800 30px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(fmt.format(total), cx, cy + 6);
  ctx.fillStyle = '#cdbb9d';
  ctx.font = '600 12px Inter, sans-serif';
  ctx.fillText('comments', cx, cy + 28);

  const items = [
    ['positive', counts.positive || 0, 'Positive'],
    ['neutral', counts.neutral || 0, 'Neutral'],
    ['negative', counts.negative || 0, 'Negative'],
  ];
  let y = 90;
  ctx.textAlign = 'left';
  items.forEach(([key, val, label]) => {
    ctx.fillStyle = COLORS[key];
    ctx.beginPath(); ctx.arc(w * 0.62, y - 5, 7, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#fff8ea'; ctx.font = '800 18px Inter, sans-serif';
    ctx.fillText(`${label}: ${fmt.format(val)}`, w * 0.65, y);
    ctx.fillStyle = '#cdbb9d'; ctx.font = '600 13px Inter, sans-serif';
    ctx.fillText(pct(val, total), w * 0.65, y + 22);
    y += 62;
  });
}

function renderBars(id, counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  document.getElementById(id).innerHTML = ['positive','neutral','negative'].map(k => `
    <div class="signal-row">
      <span>${k}</span>
      <div class="signal-track"><div class="signal-fill" style="width:${pct(counts[k] || 0, total)};background:${COLORS[k]}"></div></div>
      <b>${pct(counts[k] || 0, total)}</b>
    </div>`).join('');
}

function platformBreakdown(rows) {
  const map = {};
  rows.forEach(r => {
    map[r.platform] ||= {positive: 0, neutral: 0, negative: 0};
    const k = r.sentiment_family || 'neutral';
    map[r.platform][k] = (map[r.platform][k] || 0) + Number(r.count || 0);
  });
  document.getElementById('platformBreakdown').innerHTML = Object.entries(map).map(([platform, counts]) => {
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    return `<div class="platform-row">
      <header><span>${platform}</span><span>${fmt.format(total)} comments</span></header>
      <div class="stacked">
        <span style="width:${pct(counts.positive || 0, total)};background:${COLORS.positive}"></span>
        <span style="width:${pct(counts.neutral || 0, total)};background:${COLORS.neutral}"></span>
        <span style="width:${pct(counts.negative || 0, total)};background:${COLORS.negative}"></span>
      </div>
      <div class="legend">
        <span>Positive ${pct(counts.positive || 0, total)}</span>
        <span>Neutral ${pct(counts.neutral || 0, total)}</span>
        <span>Negative ${pct(counts.negative || 0, total)}</span>
      </div>
    </div>`;
  }).join('');
}

function renderTopics(rows) {
  const merged = {};
  rows.forEach(r => {
    merged[r.topic_cluster] ||= {count: 0, positive: 0, neutral: 0, negative: 0};
    merged[r.topic_cluster].count += Number(r.count || 0);
    merged[r.topic_cluster][r.sentiment_family || 'neutral'] += Number(r.count || 0);
  });
  const sorted = Object.entries(merged).sort((a,b) => b[1].count - a[1].count).slice(0, 9);
  document.getElementById('topicGrid').innerHTML = sorted.map(([topic, d]) => `
    <div class="topic-card">
      <strong>${topic}</strong>
      <div class="count">${fmt.format(d.count)}</div>
      <div class="legend"><span>+ ${d.positive}</span><span>0 ${d.neutral}</span><span>- ${d.negative}</span></div>
    </div>`).join('');
}

function renderRisks(rows) {
  const merged = {};
  rows.forEach(r => { merged[r.risk_flag] = (merged[r.risk_flag] || 0) + Number(r.count || 0); });
  const sorted = Object.entries(merged).sort((a,b) => b[1] - a[1]);
  document.getElementById('riskList').innerHTML = sorted.map(([risk, count]) => `
    <div class="risk-item"><b>${risk.replaceAll('_',' ')}</b><span>${fmt.format(count)} mentions</span></div>
  `).join('');
}

function renderTable(rows) {
  const headers = ['Platform','Account','Type','Date','Engagement','Caption / Title','URL'];
  const body = rows.slice(0, 15).map(r => `<tr>
    <td>${r.platform}</td>
    <td>${r.source_account || '-'}</td>
    <td>${r.post_type || '-'}</td>
    <td>${r.date || '-'}</td>
    <td>❤ ${clean(r.likes)}<br>💬 ${clean(r.comments)}<br>↗ ${clean(r.shares)}<br>▶ ${clean(r.views)}</td>
    <td>${shortText(r.title_or_caption, 150)}</td>
    <td><a href="${r.url}" target="_blank" rel="noopener">Open</a></td>
  </tr>`).join('');
  document.getElementById('topPostsTable').innerHTML = `<thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody>`;
}

function renderComments(rows) {
  document.getElementById('commentsList').innerHTML = rows.slice(0, 14).map(r => `
    <article class="comment-card">
      <div class="comment-meta">
        <span>${r.platform}</span>
        <span>·</span>
        <span>${r.topic_cluster}</span>
        <span class="badge ${r.sentiment_label}">${r.sentiment_label}</span>
        ${r.risk_flags ? `<span>⚠ ${r.risk_flags}</span>` : ''}
      </div>
      <p>${r.text_for_sentiment}</p>
      <div class="comment-meta"><span>${r.content_date || ''}</span><span>Likes: ${clean(r.comment_like_count)}</span><a href="${r.url}" target="_blank" rel="noopener">source</a></div>
    </article>
  `).join('');
}

async function init() {
  const res = await fetch('data/dashboard_data.json');
  const data = await res.json();
  const m = data.metrics;
  const counts = {
    positive: Number(m.sentiment_counts.positive || 0),
    neutral: Number(m.sentiment_counts.neutral || 0),
    negative: Number(m.sentiment_counts.negative || 0)
  };
  const total = m.social_comments_total || Object.values(counts).reduce((a,b)=>a+b,0);
  document.getElementById('overallSignal').innerHTML = `
    <span class="signal-metric positive"><small>Positive</small>${pct(counts.positive, total)}</span>
    <span class="signal-metric negative"><small>Negative</small>${pct(counts.negative, total)}</span>
  `;
  document.getElementById('overallNarrative').textContent = `${fmt.format(m.social_comments_total)} komentar publik dianalisis. Sinyal terbesar masih neutral/question/low-information, dengan negative cluster kecil tapi penting untuk isu lahan, deforestasi, dan trust.`;
  renderBars('overallBars', counts);
  drawDonut(document.getElementById('sentimentCanvas'), counts);
  document.getElementById('kpiGrid').innerHTML = [
    ['Posts', m.posts_total], ['Social comments', m.social_comments_total], ['Meaningful comments', m.meaningful_comments_total], ['Risk mentions', m.risk_comment_rows]
  ].map(([label, val]) => `<div class="kpi-card"><span>${label}</span><strong>${fmt.format(val)}</strong></div>`).join('');
  platformBreakdown(data.sentiment_by_platform);
  renderTopics(data.topics);
  renderRisks(data.risks);
  renderTable(data.top_posts);
  renderComments(data.representative_comments);
  document.getElementById('recommendations').innerHTML = data.recommendations.map(x => `<li>${x}</li>`).join('');
  document.getElementById('sourceStatus').innerHTML = Object.entries(m.source_status).map(([k,v]) => `<div class="method-item"><b>${k}</b>${v}</div>`).join('');
  document.getElementById('processedAt').textContent = `Processed ${m.processed_at}`;
}

init().catch(err => {
  console.error(err);
  document.body.insertAdjacentHTML('afterbegin', `<div style="padding:16px;background:#5b1b12;color:white">Dashboard data failed to load: ${err.message}</div>`);
});
