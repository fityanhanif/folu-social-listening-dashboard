import json, re, hashlib, shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / 'data'
ASSET_DIR = ROOT / 'assets'
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)

SRC = {
    'instagram_comments': Path('D:/Project_Portofolio/kemenhut_folu_scraping_final/instagram_kemenhut_folu_talks_deep_comments.csv'),
    'youtube_comments': Path('D:/Project_Portofolio/kemenhut_folu_scraping_final/youtube_kemenhut_folu_14_comments_title_date.csv'),
    'tiktok_posts': Path('C:/Users/lenovo/Downloads/kemenhut_folu_tiktok/tiktok_folu_posts_final.csv'),
    'tiktok_comments': Path('C:/Users/lenovo/Downloads/kemenhut_folu_tiktok/tiktok_folu_comments_final.csv'),
    'web_discourse': Path('D:/Project_Portofolio/kemenhut_folu_scraping_final/website_folu_net_sink_2030/website_kemenhut_folu_net_sink_2030_clean.csv'),
}
LOGO_SRC = Path('C:/Users/lenovo/Downloads/FOLU Talks Logo Coklat teks Coklat.jpg')

POS_TERMS = {
    'bagus','baik','mantap','keren','hebat','setuju','dukung','mendukung','semangat','terima kasih','terimakasih','sukses','hadir','bermanfaat','apresiasi','kolaborasi','lestari','adil','berkeadilan','solusi','jaga','menjaga','konservasi','rehabilitasi','restorasi','hijau','berkelanjutan','tulus','terbuka','top','good','great','excellent','amazing','love','idolaku','bantu','berhasil','siap','peduli','edukasi','percaya','inspiratif'
}
NEG_TERMS = {
    'gagal','buruk','jelek','bohong','omong kosong','pencitraan','korup','korupsi','bagi-bagi','jabatan','kontroversi','ambisi','deforestasi','banjir','bencana','rusak','merusak','kritik','masalah','konflik','mafia','tidak percaya','nggak percaya','ga percaya','gak percaya','parah','aneh','sulit','impossible','hoax','scam','tambang','penambangan','hutan lindung','perusahaan','ambil lahannya','dijual','tanda tanya','greenwashing','izin','krisis','emisi naik','tercemar'
}
QUESTION_TERMS = {'apa','apakah','bagaimana','kapan','dimana','di mana','kenapa','mengapa','siapa','berapa','?','gimana','boleh','bisakah'}
LOW_INFO = {'hadir','absen','ijin hadir','izin hadir','ok','oke','siap','mantap','terima kasih','thanks','makasih','🙏','👍','🔥','😍','hadirr','hadirrr'}

TOPIC_RULES = [
    ('Konflik lahan & hutan lindung', ['hutan lindung','lahan','tanah','perusahaan','kampung','tambang','penambangan','izin','kawasan hutan','konflik']),
    ('Deforestasi & tata kelola hutan', ['deforestasi','rusak','merusak','hutan','kawasan','mafia','rehabilitasi','restorasi']),
    ('Edukasi FOLU Net Sink 2030', ['folu','net sink','2030','emisi','karbon','carbon','ndc','gas rumah kaca']),
    ('Perubahan iklim & emisi', ['perubahan iklim','iklim','emisi','cuaca','pemanasan global','bencana','banjir']),
    ('Perhutanan sosial & ekonomi karbon', ['hutan sosial','perhutanan sosial','ekonomi karbon','berkeadilan','masyarakat','sertifikat']),
    ('Program lapangan & daerah', ['kopi','kth','bpdlh','papua','riau','siak','lampung','pelatihan','demplot','desa']),
    ('Dukungan & apresiasi', ['dukung','mantap','keren','terima kasih','apresiasi','semangat','sukses','idolaku']),
    ('Pertanyaan publik', ['?','apa','apakah','bagaimana','kenapa','gimana','kapan','boleh']),
]

RISK_RULES = [
    ('conflict_land_tenure', ['lahan','tanah','perusahaan','hutan lindung','ambil lahannya','izin','tambang','penambangan']),
    ('deforestation_criticism', ['deforestasi','rusak','merusak','kawasan hutan','mafia']),
    ('trust_greenwashing_risk', ['pencitraan','bohong','tidak percaya','ga percaya','gak percaya','greenwashing','tanda tanya']),
    ('climate_impact_concern', ['banjir','bencana','cuaca','emisi naik','pemanasan global']),
    ('unanswered_question', ['?','apa','apakah','bagaimana','kenapa','gimana','boleh']),
]

emoji_re = re.compile(r'[\U0001F300-\U0001FAFF]+', flags=re.UNICODE)
url_re = re.compile(r'https?://\S+|www\.\S+', flags=re.I)
mention_re = re.compile(r'@\w[\w.]*')
space_re = re.compile(r'\s+')


def clean_text(x):
    if pd.isna(x): return ''
    s = str(x).replace('\r',' ').replace('\n',' ')
    s = url_re.sub(' ', s)
    s = mention_re.sub(' ', s)
    return space_re.sub(' ', s).strip()

def word_count(s):
    return len(re.findall(r'\b\w+\b', str(s), flags=re.UNICODE))

def count_terms(s, terms):
    sl = s.lower()
    return sum(1 for t in terms if t in sl)

def classify(text, source='social'):
    raw = text or ''
    s = raw.lower().strip()
    pos = count_terms(s, POS_TERMS)
    neg = count_terms(s, NEG_TERMS)
    is_q = any(q in s for q in QUESTION_TERMS)
    wc = word_count(raw)
    only_emoji = bool(emoji_re.fullmatch(raw.strip())) if raw.strip() else False
    low = s in LOW_INFO or wc <= 1 or only_emoji
    score = pos - neg
    if low:
        sentiment = 'neutral_low_information'
    elif neg > pos:
        sentiment = 'negative'
    elif pos > neg:
        sentiment = 'positive'
    elif is_q:
        sentiment = 'neutral_question'
    else:
        sentiment = 'neutral'
    if source == 'web':
        stance = 'media_discourse_not_direct_public_comment'
    elif low:
        stance = 'low_information'
    elif neg > pos:
        stance = 'critical_or_concern'
    elif pos > neg:
        stance = 'supportive_or_appreciative'
    elif is_q:
        stance = 'question_or_information_seeking'
    else:
        stance = 'neutral_or_unclear'
    emotion = 'concern' if neg > pos else 'appreciation' if pos > neg else 'curiosity' if is_q else 'low_information' if low else 'neutral'
    return sentiment, score, stance, emotion, low

def topic(text):
    s = (text or '').lower()
    hits = []
    for name, terms in TOPIC_RULES:
        if any(t in s for t in terms): hits.append(name)
    return hits[0] if hits else 'General/unclear', '; '.join(hits) if hits else 'General/unclear'

def risk_flags(text):
    s = (text or '').lower()
    flags = [name for name, terms in RISK_RULES if any(t in s for t in terms)]
    return '; '.join(flags) if flags else ''

def anon(v):
    if pd.isna(v) or str(v).strip() == '': return ''
    return 'user_' + hashlib.sha256(str(v).encode('utf-8')).hexdigest()[:10]

def safe_num(v):
    try:
        if pd.isna(v) or v == '': return None
        return float(v)
    except Exception:
        return None

def add_record(records, *, platform, content_type, topic_title, content_date, author, text, url, source_file, parent_metrics=None, comment_like=None, scope='public_social_comment'):
    text_clean = clean_text(text)
    sentiment, score, stance, emotion, low = classify(text_clean, 'web' if scope == 'media_or_web_discourse' else 'social')
    primary_topic, topic_list = topic(' '.join([str(topic_title or ''), text_clean]))
    flags = risk_flags(text_clean + ' ' + str(topic_title or ''))
    records.append({
        'analysis_scope': scope,
        'platform': platform,
        'content_type': content_type,
        'topic_title': topic_title or '',
        'content_date': content_date or '',
        'author_hash': anon(author),
        'text_for_sentiment': text_clean,
        'text_word_count': word_count(text_clean),
        'sentiment_label': sentiment,
        'sentiment_score': score,
        'emotion_label': emotion,
        'stance_label': stance,
        'topic_cluster': primary_topic,
        'topic_matches': topic_list,
        'risk_flags': flags,
        'is_low_information': bool(low),
        'comment_like_count': safe_num(comment_like),
        'post_like_count': safe_num((parent_metrics or {}).get('likes')),
        'post_comment_count': safe_num((parent_metrics or {}).get('comments')),
        'post_share_or_repost_count': safe_num((parent_metrics or {}).get('shares')),
        'post_view_count': safe_num((parent_metrics or {}).get('views')),
        'url': url or '',
        'source_file': source_file,
    })

records = []
posts = []

# Instagram comments
ig = pd.read_csv(SRC['instagram_comments'], encoding='utf-8-sig')
for _, r in ig.iterrows():
    add_record(records, platform='Instagram', content_type='comment', topic_title=r.get('caption_judul'), content_date=r.get('comment_created_at_utc') or r.get('tanggal'), author=r.get('comment_username'), text=r.get('isi_komentar'), url=r.get('url'), source_file=SRC['instagram_comments'].name, parent_metrics={'likes': r.get('like_count')}, comment_like=r.get('comment_like_count'))
# IG post-level unique
for url, g in ig.groupby('url'):
    rr = g.iloc[0]
    posts.append({'platform':'Instagram','source_account':'@kemenhut','post_type':'post/reel','date':rr.get('tanggal',''),'title_or_caption':rr.get('caption_judul',''),'url':url,'likes':safe_num(rr.get('like_count')),'comments':len(g),'shares':None,'views':None,'relevance':'FOLU Talks Instagram scrape'})

# YouTube comments
if SRC['youtube_comments'].exists():
    yt = pd.read_csv(SRC['youtube_comments'], encoding='utf-8-sig')
    for _, r in yt.iterrows():
        add_record(records, platform='YouTube', content_type='comment', topic_title=r.get('video_title'), content_date=r.get('comment_time_text') or r.get('video_created_or_published_date'), author=r.get('comment_author'), text=r.get('comment_text'), url=r.get('video_url'), source_file=SRC['youtube_comments'].name, comment_like=r.get('comment_like_count'))
    for url, g in yt.groupby('video_url'):
        rr = g.iloc[0]
        posts.append({'platform':'YouTube','source_account':'@Kemenhut_RI','post_type':'stream/video','date':rr.get('video_created_or_published_date',''),'title_or_caption':rr.get('video_title',''),'url':url,'likes':None,'comments':len(g),'shares':None,'views':None,'relevance':'FOLU Talks YouTube streams scrape'})

# TikTok posts and comments
tp = pd.read_csv(SRC['tiktok_posts'], encoding='utf-8-sig', dtype={'video_id':str})
for _, r in tp.iterrows():
    posts.append({'platform':'TikTok','source_account':'@'+str(r.get('creator_username','')).lstrip('@'),'post_type':r.get('post_type',''),'date':r.get('upload_date_iso',''),'title_or_caption':clean_text(r.get('caption',''))[:500],'url':r.get('url',''),'likes':safe_num(r.get('like_count')),'comments':safe_num(r.get('comment_count')),'shares':safe_num(r.get('share_or_repost_count')),'views':safe_num(r.get('view_count')),'relevance':'FOLU keyword / Net Sink related TikTok discovery'})

tc = pd.read_csv(SRC['tiktok_comments'], encoding='utf-8-sig', dtype={'video_id':str})
for _, r in tc.iterrows():
    add_record(records, platform='TikTok', content_type='comment', topic_title=r.get('post_caption'), content_date=r.get('comment_create_time_iso') or r.get('post_upload_date'), author=r.get('comment_author'), text=r.get('comment_text'), url=r.get('post_url'), source_file=SRC['tiktok_comments'].name, parent_metrics={'likes':r.get('post_like_count'),'comments':r.get('post_comment_count'),'shares':r.get('post_share_or_repost_count'),'views':r.get('post_view_count')}, comment_like=r.get('comment_like_count'))

# Web discourse, separate from public social comments
web = pd.read_csv(SRC['web_discourse'], encoding='utf-8-sig')
for _, r in web.iterrows():
    add_record(records, platform='Website/Media', content_type='article_excerpt', topic_title=r.get('title'), content_date=r.get('published_date'), author=r.get('domain'), text=r.get('summary_or_relevant_excerpt'), url=r.get('url'), source_file=SRC['web_discourse'].name, scope='media_or_web_discourse')

comments = pd.DataFrame(records)
posts_df = pd.DataFrame(posts).drop_duplicates('url')
comments['platform'] = comments['platform'].fillna('Unknown')
comments['sentiment_family'] = comments['sentiment_label'].replace({'neutral_low_information':'neutral','neutral_question':'neutral'})
meaningful = comments[(comments['analysis_scope']=='public_social_comment') & (comments['is_low_information']==False) & (comments['text_word_count']>=2)].copy()
social = comments[comments['analysis_scope']=='public_social_comment'].copy()

# summaries
def group_count(df, cols):
    return df.groupby(cols, dropna=False).size().reset_index(name='count').sort_values('count', ascending=False)

platform_summary = group_count(social, ['platform','sentiment_family'])
topic_summary = group_count(meaningful, ['topic_cluster','sentiment_family'])
risk_rows = []
for _, r in meaningful.iterrows():
    if r['risk_flags']:
        for f in str(r['risk_flags']).split('; '):
            risk_rows.append({'platform': r['platform'], 'risk_flag': f, 'url': r['url'], 'text_for_sentiment': r['text_for_sentiment'], 'sentiment_family': r['sentiment_family']})
risk_df = pd.DataFrame(risk_rows)
risk_summary = group_count(risk_df, ['risk_flag','platform']) if len(risk_df) else pd.DataFrame(columns=['risk_flag','platform','count'])

# Top comments representative
top_comments = meaningful.copy()
top_comments['abs_score'] = top_comments['sentiment_score'].abs()
top_comments = top_comments.sort_values(['abs_score','comment_like_count','post_comment_count'], ascending=False).head(40)

# Overall metrics
metrics = {
    'processed_at': datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S %z'),
    'posts_total': int(len(posts_df)),
    'social_comments_total': int(len(social)),
    'meaningful_comments_total': int(len(meaningful)),
    'web_discourse_rows': int((comments['analysis_scope']=='media_or_web_discourse').sum()),
    'platforms': sorted(social['platform'].dropna().unique().tolist()),
    'sentiment_counts': social['sentiment_family'].value_counts().to_dict(),
    'meaningful_sentiment_counts': meaningful['sentiment_family'].value_counts().to_dict(),
    'risk_comment_rows': int(len(risk_df)),
    'source_status': {
        'instagram': 'BYOB + Instagram API/session scrape available from prior task; comments included.',
        'youtube': 'YouTube streams/comments dataset included from prior scrape.',
        'tiktok': 'BYOB discovery worked; Obscura attempted but returned blank/eval null on TikTok; fallback extractor/API/session used; comments included.',
        'website': 'BYOB verified seeds + Obscura bulk text; zero-byte PPID pages excluded during cleaning.',
    }
}

# JSON payload for dashboard
sentiment_by_platform = platform_summary.to_dict('records')
topic_records = topic_summary.to_dict('records')
risk_records = risk_summary.to_dict('records')
post_records = posts_df.sort_values(['comments','likes','views'], ascending=False, na_position='last').head(30).fillna('').to_dict('records')
comment_records = top_comments[['platform','content_date','topic_cluster','sentiment_label','stance_label','risk_flags','comment_like_count','post_comment_count','text_for_sentiment','url']].fillna('').to_dict('records')

dashboard = {
    'metrics': metrics,
    'sentiment_by_platform': sentiment_by_platform,
    'topics': topic_records,
    'risks': risk_records,
    'top_posts': post_records,
    'representative_comments': comment_records,
    'recommendations': [
        'Prioritaskan explainer FOLU Net Sink 2030 yang menjawab pertanyaan publik dengan bahasa non-teknis.',
        'Pisahkan komunikasi edukasi iklim dari isu konflik lahan, karena komentar kritis banyak muncul pada lahan/hutan lindung/perusahaan.',
        'Gunakan format short video Q&A untuk menjawab komentar bertipe question_or_information_seeking.',
        'Perkuat proof-of-work program lapangan: perhutanan sosial, kopi, KTH, dan cerita daerah cenderung lebih mudah dipahami publik.',
        'Monitoring risiko greenwashing/deforestasi harus rutin karena sentiment negatif kecil tapi reputationally sensitive.'
    ]
}

# Save files
comments.to_csv(DATA_DIR / 'folu_all_sources_sentiment.csv', index=False, encoding='utf-8-sig')
social.to_csv(DATA_DIR / 'folu_social_comments_sentiment.csv', index=False, encoding='utf-8-sig')
meaningful.to_csv(DATA_DIR / 'folu_meaningful_social_comments.csv', index=False, encoding='utf-8-sig')
posts_df.to_csv(DATA_DIR / 'folu_posts_master.csv', index=False, encoding='utf-8-sig')
risk_df.to_csv(DATA_DIR / 'folu_risk_flags.csv', index=False, encoding='utf-8-sig')
with pd.ExcelWriter(DATA_DIR / 'folu_social_listening_report.xlsx', engine='openpyxl') as w:
    posts_df.to_excel(w, sheet_name='posts_master', index=False)
    social.to_excel(w, sheet_name='comments_master', index=False)
    meaningful.to_excel(w, sheet_name='meaningful_comments', index=False)
    platform_summary.to_excel(w, sheet_name='sentiment_by_platform', index=False)
    topic_summary.to_excel(w, sheet_name='sentiment_by_topic', index=False)
    risk_summary.to_excel(w, sheet_name='risk_summary', index=False)
    top_comments.drop(columns=['abs_score'], errors='ignore').to_excel(w, sheet_name='representative_comments', index=False)
    pd.DataFrame([metrics]).to_excel(w, sheet_name='metadata', index=False)
(DATA_DIR / 'dashboard_data.json').write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding='utf-8')

if LOGO_SRC.exists():
    shutil.copy2(LOGO_SRC, ASSET_DIR / 'folu-logo.jpg')

print(json.dumps({
    'outputs': [str(p) for p in [DATA_DIR/'folu_social_listening_report.xlsx', DATA_DIR/'dashboard_data.json', DATA_DIR/'folu_social_comments_sentiment.csv', DATA_DIR/'folu_posts_master.csv']],
    **metrics
}, ensure_ascii=False, indent=2))
