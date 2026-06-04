import streamlit as st
from transformers import pipeline
from datetime import datetime
from streamlit_option_menu import option_menu
import re
import html
import emoji
import emot
import unicodedata

# ==========================================
# 1. PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="MindPulse | Dashboard", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .stApp { font-family: 'Inter', sans-serif; }
    
    .badge {
        padding: 6px 14px; border-radius: 20px; font-size: 14px; font-weight: 700;
        display: inline-flex; align-items: center; gap: 6px; 
    }
    .badge-depression { background-color: #F3E8FF; color: #7E22CE; border: 1px solid #D8B4FE; }
    .badge-anxiety { background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
    .badge-lonely { background-color: #E0F2FE; color: #2563EB; border: 1px solid #93C5FD; }
    .badge-mentalhealth { background-color: #DCFCE7; color: #16A34A; border: 1px solid #86EFAC; }
    .badge-suicidewatch { background-color: #FCE7F3; color: #BE185D; border: 1px solid #F9A8D4; }

    .comment-block { 
        padding: 10px 12px; background: rgba(128,128,128,0.05); 
        border-radius: 8px; margin-bottom: 4px;
        border-left: 3px solid #818CF8;
    }
    .comment-meta { font-size: 12px; font-weight: bold; margin-bottom: 4px; }
    .comment-time { font-weight: normal; opacity: 0.6; margin-left: 8px; }
    .comment-text { font-size: 14px; opacity: 0.9; }

    .stButton button { 
        width: auto !important; 
        min-width: 85px !important;
        border-radius: 8px; 
        padding: 4px 16px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .comment-like-btn button { padding: 2px 5px !important; min-height: 0px !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1.5 NLP PREPROCESSING PIPELINE
# ==========================================
# Initialize emot parser for text-based emoticons
emot_obj = emot.core.emot()

# Manual mapping for common emoticons missed by the emot library
MANUAL_EMOTICON_MAP = {
    r'<\s*3': 'love heart',
    r':\s*\)': 'happy smile',
    r':-\s*\)': 'happy smile',
    r'\(\s*:': 'happy smile',
    r'\(-:': 'happy smile',
    r';\s*\)': 'wink smile',
    r';-\s*\)': 'wink smile',
    r'=\s*\)': 'happy smile',
    r':\s*\((?![A-Za-z0-9-])': 'sad face',
    r':-\s*\((?![A-Za-z0-9-])': 'sad face',
    r'\)\s*:': 'sad face',
    r';\s*\((?![A-Za-z0-9-])': 'crying sad face',
    r';-\s*\((?![A-Za-z0-9-])': 'crying sad face',
    r'=\s*\((?![A-Za-z0-9-])': 'sad face',
    r":\s*['‘’ʼ`´′＇]\s*\(": 'crying sad face',
    r":\s*['‘’ʼ`´′＇]\s*[cC]\b": 'crying sad face',
    r":\s*['‘’ʼ`´′＇]\s*\)": 'tears of happiness face',
    r":\s*['‘’ʼ`´′＇]\s*[dD]\b": 'crying laughing face',
    r'\bxD\b': 'laughing face',
    r'\bxd\b': 'laughing face',
    r'\bXd\b': 'laughing face',
    r'\bXD\b': 'laughing face',
    r':\s*[pP]\b': 'playful face',
    r':-\s*[pP]\b': 'playful face',
    r';\s*[pP]\b': 'playful face',
    r';-\s*[pP]\b': 'playful face',
    r'\bxP\b': 'playful face',
    r'\bXP\b': 'playful face',
    r':\s*/': 'skeptical uneasy face',
    r':-\s*/': 'skeptical uneasy face',
    r'/\s*:': 'skeptical uneasy face',
    r'\bDx\b': 'distressed face',
    r'\bDX\b': 'distressed face',
    r'x\s*\)': 'happy smile',
    r'x\s*\(': 'sad face',
    r'\)\s*;': 'crying sad face',
    r'\(\s*;': 'wink smile',
    r'\(\s*=': 'happy smile',
    r'\)\s*=': 'sad face',
    r':\s*-?\s*\)': 'happy smile',
    r';\s*-?\s*\)': 'wink smile',
    r'=\s*-?\s*\)': 'happy smile',
    r':\s*-?\s*\((?![A-Za-z0-9-])': 'sad face',
    r';\s*-?\s*\((?![A-Za-z0-9-])': 'crying sad face',
    r'=\s*-?\s*\((?![A-Za-z0-9-])': 'sad face',
    r'\(\s*-?\s*:': 'happy smile',
    r'\(\s*-?\s*;': 'wink smile',
    r'\(\s*-?\s*=': 'happy smile',
    r'\)\s*-?\s*:': 'sad face',
    r'\)\s*-?\s*;': 'crying sad face',
    r'\)\s*-?\s*=': 'sad face',
    r':\s*-?\s*/': 'skeptical uneasy face',
    r';\s*-?\s*/': 'skeptical uneasy face',
    r'/\s*-?\s*:': 'skeptical uneasy face',
    r'/\s*-?\s*;': 'skeptical uneasy face',
    r':\s*-?\s*[pP]\b': 'playful face',
    r';\s*-?\s*[pP]\b': 'playful face',
    r'=\s*-?\s*[pP]\b': 'playful face',
    r":\s*[\'’]\s*\)": "tears of happiness face",
    r"=\s*[\'’]\s*\)": "crying sad face",
    r":\s*[\'’]\s*/": "crying uneasy face",
    r":\s*[\'’]\s*\|": "uneasy face",
    r";\s*[\'’]\s*\(": "crying sad face",
    r":-D": "big happy smile",
    r":[vV]\b": "playful face",
    r":[cC]\b": "sad face",
    r":[sS]\b": "confused uneasy face",
    r":[dD]\b": "big happy smile",
    r";c\b": "crying sad face",
    r";3\b": "playful cute face",
    r";[vV];": "crying face",
    r";[wW];": "crying face",
    r"<\s*3": "love heart",
    r"[xX]\.x": "dizzy face",
    r"x-x": "dizzy face",
    r"T-T": "crying face",
    r"u\.u": "sad disappointed face",
    r"u-u": "sad disappointed face",
    r"v\.v": "sad disappointed face",
    r"U\.U": "sad disappointed face",
    r"[oO]\.o": "confused face",
    r"0-o": "confused face",
    r"\^\s*\^": "happy cute face",
    r"¯\s*\([^)]*ツ[^)]*\)\s*/¯": "shrug face",
    r"\(◍•ᴗ•◍\)": "happy cute face",
    r"｡◕‿◕｡": "happy cute face",
    r"ಠ╭╮ಠ": "disappointed face",
    r"\(´ー｀\)": "relieved face",
    r"༎ຶ‿༎ຶ": "crying face",
    r"\(´;︵;\s*\)": "crying sad face",
    r"\(´-﹏-\s*；\)/": "sad worried face",
    r"\(╯︵╰\)": "sad face",
    r"\(-\s*-メ\)": "annoyed face",
    r"•́\s*‿\s*,•̀": "sad pleading face",
    r'\^\s*-\s*\^': 'happy smile',
    r'\^\s*\.\s*\^': 'happy smile',
    r'-\s*\.\s*-': 'annoyed face',
    r"=\s*['‘’ʼ`´′＇]\s*\)": 'crying smile face',
    r':-\s*[xX]\b': 'sealed lips face',
    r'<\s*/\s*3': 'broken heart',
    r'\^\s*[-_.]?\s*\^': 'happy smile',
    r':\s*\^\s*\(': 'sad face',
    r':\s*\^\s*\)': 'happy smile',
    r':\s*\^\s*[dD]\b': 'happy grin',
    r':\s*\^\s*\|': 'neutral face',
    r"=\s*[oO]\b": 'surprised face',
    r';\s*-\s*;': 'crying face',
    r'=\s*\.\s*=': 'annoyed face',
    r'<\s*\.\s*<': 'side eye face',
}

UNICODE_SYMBOL_PATTERN = re.compile(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]')

def normalize_emotion_symbols(text):
    text = str(text)
    text = emoji.demojize(text, language='en')
    text = re.sub(r':([a-zA-Z0-9_+\-]+):', r' \1 ', text)
    text = text.replace('_', ' ')
    for pattern, meaning in MANUAL_EMOTICON_MAP.items():
        text = re.sub(pattern, f' {meaning} ', text, flags=re.IGNORECASE)
    emoticon_result = emot_obj.emoticons(text)
    if emoticon_result.get('flag'):
        values = emoticon_result.get('value', [])
        meanings = emoticon_result.get('mean', [])
        pairs = sorted(zip(values, meanings), key=lambda x: len(x[0]), reverse=True)
        for value, meaning in pairs:
            cleaned_meaning = re.sub(r'[^A-Za-z0-9\s]', ' ', str(meaning))
            cleaned_meaning = re.sub(r'\s+', ' ', cleaned_meaning).strip()
            text = re.sub(re.escape(value), f' {cleaned_meaning} ', text)
    return text

def final_residual_emoticon_cleanup(text):
    text = str(text)
    residual_map = {
        r":\s*['‘’ʼ`´′＇]\s*\)": "tears of happiness face",
        r":\s*-?\s*\((?![A-Za-z0-9-])": "sad face",
        r";\s*-?\s*\((?![A-Za-z0-9-])": "crying sad face",
        r"=\s*-?\s*\((?![A-Za-z0-9-])": "sad face",
        r"(?<![A-Za-z0-9]):\s*/(?![A-Za-z0-9])": "skeptical uneasy face",
        r"\(´;︵;\s*\)": "crying sad face",
    }
    for pattern, meaning in residual_map.items():
        text = re.sub(pattern, f" {meaning} ", text, flags=re.IGNORECASE)
    return text

def convert_leftover_unicode_symbols(text):
    def replace_symbol(match):
        symbol = match.group(0)
        symbol_name = unicodedata.name(symbol, '')
        if not symbol_name:
            return ' '
        return ' ' + symbol_name.lower().replace('-', ' ') + ' '
    return UNICODE_SYMBOL_PATTERN.sub(replace_symbol, text)

def repeated_html_unescape(text, max_iter=3):
    text = str(text)
    for _ in range(max_iter):
        new_text = html.unescape(text)
        if new_text == text:
            break
        text = new_text
    return text

def clean_reddit_text(text, lowercase=True, remove_punctuation=False):
    text = str(text)
    text = repeated_html_unescape(text)
    text = re.sub(r'(?:x200b|u200b|\\u200b|&#x200b;)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'[\u200b\u200c\u200d\ufe0e\ufe0f]', ' ', text)
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhttps?\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'(?<![A-Za-z0-9])/?u/[A-Za-z0-9_-]+', ' USER ', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<![A-Za-z0-9])/?r/[A-Za-z0-9_-]+', ' SUBREDDIT ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:removed|deleted|view poll)\]', ' ', text, flags=re.IGNORECASE)
    text = normalize_emotion_symbols(text)
    text = convert_leftover_unicode_symbols(text)
    text = re.sub(r'&[A-Za-z]+;', ' ', text)
    text = re.sub(r'[\[\]]', ' ', text)
    text = re.sub(r'[*_`~>#]+', ' ', text)
    text = re.sub(r'\\+', ' ', text)
    text = re.sub(r'\(\s*\)', ' ', text)
    text = re.sub(r'\[\s*\]', ' ', text)
    text = re.sub(r'\{\s*\}', ' ', text)
    text = re.sub(r'\(\s*[^A-Za-z0-9]+\s*\)', ' ', text)
    text = re.sub(r'\[\s*[^A-Za-z0-9]+\s*\]', ' ', text)
    text = re.sub(r'\{\s*[^A-Za-z0-9]+\s*\}', ' ', text)
    text = final_residual_emoticon_cleanup(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ==========================================
# 2. STATE MANAGEMENT & HELPERS
# ==========================================
@st.cache_resource
def load_model():
    try:
        # Replace "your-username" with your actual Hugging Face username!
        return pipeline("text-classification", model="ben9899/mindpulse-mentalbert")
    except Exception as e:
        # This will print the error to your app if it fails to load, helping us debug!
        st.error(f"Model loading failed: {e}") 
        return None

classifier = load_model()

def map_label(raw_label):
    label = raw_label.lower()
    if "sadness" in label or "depression" in label: return "Depression", "badge-depression", "😔"
    elif "fear" in label or "anxiety" in label: return "Anxiety", "badge-anxiety", "😰"
    elif "anger" in label or "suicide" in label: return "Suicide Watch", "badge-suicidewatch", "🚨"
    elif "lonely" in label: return "Loneliness", "badge-lonely", "😶"
    else: return "Mental Health", "badge-mentalhealth", "🫂"

def current_time_str():
    return datetime.now().strftime("%I:%M %p")

# Added mock confidence levels
    # Expanded session state with real RMHD data and mock comments
if 'feed' not in st.session_state:
    st.session_state.feed = [
        {
            "id": "post_sw_1", "user": "Anon_821", "time": "Just now", 
            "text": "2022. Just another year to be miserable. Might as well end it here in 2021.", 
            "label": "Suicide Watch", "css": "badge-suicidewatch", "emoji": "🚨", "confidence": 0.717,
            "likes": 2, "is_liked": False, "reposts": 0, "is_reposted": False,
            "comments": [
                {"user": "AutoMod", "time": "Just now", "text": "If you or someone you know is struggling, please reach out for help immediately. You can dial 988 or text HOME to 741741 to reach the Crisis Text Line. You are not alone and help is available.", "likes": 12, "is_liked": False},
                {"user": "CaringSoul", "time": "Just now", "text": "Please stay. We are here and we are listening. What is happening right now?", "likes": 5, "is_liked": False}
            ]
        },
        {
            "id": "post_anx_1", "user": "Runner_99", "time": "20 mins ago", 
            "text": "I feel like I panic so hard If I don't eat well enough before or immediately after a run. If I eat too much or unhealthy though, I also panic. Anyone else?", 
            "label": "Anxiety", "css": "badge-anxiety", "emoji": "😰", "confidence": 0.978,
            "likes": 45, "is_liked": False, "reposts": 3, "is_reposted": False,
            "comments": [
                {"user": "HealthNut", "time": "15 mins ago", "text": "Yes! Blood sugar spikes and drops can trigger physiological responses that perfectly mimic anxiety attacks. It happens to me too.", "likes": 18, "is_liked": False},
                {"user": "TrackStar", "time": "5 mins ago", "text": "I get this exactly. I found that half a banana 30 mins before is the perfect safe middle ground. Hang in there!", "likes": 8, "is_liked": False}
            ]
        },
        {
            "id": "post_dep_1", "user": "Tired_01", "time": "1 hr ago", 
            "text": "I want to feel notmal. I am tired and sick of everyday struggles. I have no one nothing in my life", 
            "label": "Depression", "css": "badge-depression", "emoji": "😔", "confidence": 0.352,
            "likes": 89, "is_liked": False, "reposts": 12, "is_reposted": False,
            "comments": [
                {"user": "BlueSky", "time": "45 mins ago", "text": "I hear you. The exhaustion is so heavy sometimes. Just taking it one hour at a time is enough for today.", "likes": 24, "is_liked": False}
            ]
        },
        {
            "id": "post_lon_2", "user": "John Doe", "time": "1 hr ago", 
            "text": "Online and in real life nobody notices me and nobody cares and it just makes me feel sad", 
            "label": "Loneliness", "css": "badge-lonely", "emoji": "😶", "confidence": 0.617,
            "likes": 23, "is_liked": False, "reposts": 1, "is_reposted": False,
            "comments": [
                {"user": "BestFriend", "time": "50 mins ago", "text": "We are always here buddy", "likes": 2, "is_liked": False}
            ]
        },
        {
            "id": "post_mh_2", "user": "User564", "time": "2 hrs ago", 
            "text": "I have always talked to myself, not in the arguing multiple personality type of way, but just openly fielding my thoughts and talking it over. It's helps me visualize and break down my thoughts about certain decisions and such. Is this crazy or normal? I'm not losing arguments with myself or anything like that.", 
            "label": "Mental Health", "css": "badge-mentalhealth", "emoji": "🌱", "confidence": 0.954,
            "likes": 30, "is_liked": False, "reposts": 2, "is_reposted": False,
            "comments": [
                {"user": "User587", "time": "2 hrs ago", "text": "It's a healthy way to process your thoughts and emotions.", "likes": 20, "is_liked": False}
            ]
        },
        {
            "id": "post_mh_1", "user": "HealingJourney", "time": "3 hrs ago", 
            "text": "therapy today at two , wish me luck", 
            "label": "Anxiety", "css": "badge-anxiety", "emoji": "😰", "confidence": 0.422,
            "likes": 156, "is_liked": False, "reposts": 4, "is_reposted": False,
            "comments": [
                {"user": "Dr_Smith", "time": "2 hrs ago", "text": "The hardest part is simply showing up. Proud of you for taking this step!", "likes": 40, "is_liked": False},
                {"user": "Sunshine", "time": "1 hr ago", "text": "Good luck! You've got this. Let us know how it goes if you feel up to it.", "likes": 15, "is_liked": False}
            ]
        },
        {
            "id": "post_lon_1", "user": "Echo_Chamber", "time": "5 hrs ago", 
            "text": "I am alone, at home, during new years and it sucks to be not a part of anything anywhere :(", 
            "label": "Loneliness", "css": "badge-lonely", "emoji": "😶", "confidence": 0.861,
            "likes": 34, "is_liked": False, "reposts": 1, "is_reposted": False,
            "comments": [
                {"user": "NightOwl", "time": "4 hrs ago", "text": "Hey, I'm around. We can always hangout together", "likes": 6, "is_liked": False}
            ]
        }
    ]

# Callbacks
def toggle_like(post_idx):
    if st.session_state.feed[post_idx]["is_liked"]:
        st.session_state.feed[post_idx]["likes"] -= 1
        st.session_state.feed[post_idx]["is_liked"] = False
    else:
        st.session_state.feed[post_idx]["likes"] += 1
        st.session_state.feed[post_idx]["is_liked"] = True

def toggle_repost(post_idx):
    if st.session_state.feed[post_idx].get("is_reposted", False):
        st.session_state.feed[post_idx]["reposts"] -= 1
        st.session_state.feed[post_idx]["is_reposted"] = False
    else:
        st.session_state.feed[post_idx]["reposts"] += 1
        st.session_state.feed[post_idx]["is_reposted"] = True

def add_comment(post_idx, comment_text):
    if comment_text.strip():
        new_comment = {
            "user": "You", "time": current_time_str(), "text": comment_text.strip(),
            "likes": 0, "is_liked": False 
        }
        st.session_state.feed[post_idx]["comments"].append(new_comment)

def toggle_comment_like(post_idx, comment_idx):
    if st.session_state.feed[post_idx]["comments"][comment_idx].get("is_liked", False):
        st.session_state.feed[post_idx]["comments"][comment_idx]["likes"] -= 1
        st.session_state.feed[post_idx]["comments"][comment_idx]["is_liked"] = False
    else:
        current_likes = st.session_state.feed[post_idx]["comments"][comment_idx].get("likes", 0)
        st.session_state.feed[post_idx]["comments"][comment_idx]["likes"] = current_likes + 1
        st.session_state.feed[post_idx]["comments"][comment_idx]["is_liked"] = True


# ==========================================
# 3. REUSABLE UI COMPONENT (Single Column Layout)
# ==========================================
def render_post_card(idx, post):
    """Draws a post card seamlessly integrating the classification label and confidence."""
    
    # Optional: We wrap the card in columns to prevent it from stretching too wide on massive screens
    _, center_col, _ = st.columns([1, 8, 1])
    
    with center_col:
        with st.container(border=True): 
            
            # Format the confidence percentage to 1 decimal place (e.g., 94.2%)
            conf_pct = f"{post.get('confidence', 0) * 100:.1f}%"
            
            # Header Row: Avatar & Name on the left, Classification Badge on the right
            post_html = f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                
                <div style="display: flex; align-items: center;">
                    <div style="background-color: #818CF8; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; flex-shrink: 0;">
                        {post['user'][0].upper()}
                    </div>
                    <div style="line-height: 1.2;">
                        <div style="font-weight: bold; font-size: 15px;">{post['user']}</div>
                        <div style="font-size: 12px; opacity: 0.6;">{post['time']}</div>
                    </div>
                </div>
                
                <div class="{post['css']} badge" style="margin-bottom: 0px; padding: 4px 10px; font-size: 13px;">
                    <span>{post['emoji']}</span>
                    <span>{post['label']}</span>
                    <span style="opacity: 0.7; font-size: 11px; margin-left: 2px;">({conf_pct})</span>
                </div>
                
            </div>
            
            <div style="font-size: 16px; margin-bottom: 20px;">
                {post['text']}
            </div>
            """
            
            # THE FIX: Replace the newlines to prevent the Markdown code block bug!
            st.markdown(post_html.replace('\n', ''), unsafe_allow_html=True)
            
            # Interactive Buttons (Like, Repost)
            act1, act2, _ = st.columns([2, 2, 14])
            
            heart_icon = "❤️" if post['is_liked'] else "🤍"
            act1.button(f"{heart_icon} {post['likes']}", key=f"like_{post['id']}_pg_{page}", on_click=toggle_like, args=(idx,))
            
            repost_icon = "🔄" if post.get('is_reposted', False) else "🔄"
            act2.button(f"{repost_icon} {post.get('reposts', 0)}", key=f"repost_{post['id']}_pg_{page}", on_click=toggle_repost, args=(idx,))
            
            # Comments Section
            with st.expander(f"💬 View/Add Comments ({len(post['comments'])})", expanded=False):
                if len(post['comments']) > 0:
                    for c_idx, comment in enumerate(post['comments']):
                        c_col1, c_col2 = st.columns([8, 2])
                        with c_col1:
                            st.markdown(f"""
                            <div class="comment-block">
                                <div class="comment-meta">{comment['user']} <span class="comment-time">• {comment['time']}</span></div>
                                <div class="comment-text">{comment['text']}</div>
                            </div>
                            """.replace('\n', ''), unsafe_allow_html=True)
                        with c_col2:
                            st.markdown('<div class="comment-like-btn" style="margin-top: 10px;">', unsafe_allow_html=True)
                            c_heart = "❤️" if comment.get('is_liked', False) else "🤍"
                            c_likes = comment.get('likes', 0)
                            st.button(f"{c_heart} {c_likes if c_likes > 0 else ''}", key=f"clike_{post['id']}_{c_idx}_pg_{page}", on_click=toggle_comment_like, args=(idx, c_idx))
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.caption("No comments yet. Be the first!")
                
                with st.form(key=f"form_comment_{post['id']}_pg_{page}", clear_on_submit=True):
                    new_c_text = st.text_input("Reply to thread", placeholder="Write a comment...", label_visibility="collapsed")
                    if st.form_submit_button("Reply"):
                        add_comment(idx, new_c_text)
                        st.rerun()

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    # A sleek, modern SVG pulse icon
    pulse_logo = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px; margin-bottom: 4px;"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>'''
    
    st.markdown(f"<h2 style='display: flex; align-items: center; justify-content: center;'>🧠 MindPulse</h2><br>", unsafe_allow_html=True)
    page = option_menu(
        menu_title=None,  
        options=["Home", "Profile", "About Us", "Model Info"],
        icons=["house", "person", "people", "gear"],  
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "rgba(128,128,128,0.1)"},
            "nav-link-selected": {"background-color": "#818CF8", "color": "white", "font-weight": "bold"},
        }
    )
    st.markdown("<br><hr><div style='text-align: center; color: grey; font-size: 12px;'>WQF7007 - Group 9</div>", unsafe_allow_html=True)


# ==========================================
# 5. PAGE ROUTING
# ==========================================
if page == "Home":
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Home Feed</h2>", unsafe_allow_html=True)

    with st.container():
        _, form_col, _ = st.columns([1, 8, 1])
        with form_col:
            with st.form(key='post_form', clear_on_submit=True):
                user_text = st.text_input("Describe your thoughts...", placeholder="Type a new post...")
                submit_btn = st.form_submit_button(label="Analyze & Post")

    if submit_btn and user_text.strip() and classifier:
        with st.spinner("Processing NLP sequence..."):
            # 1. Clean the user's text exactly like the training data
            cleaned_input = clean_reddit_text(user_text)
            
            # 2. Feed the cleaned string to the pipeline
            result = classifier(cleaned_input)
            
            # We now extract both the label and the confidence score from the pipeline output
            display_name, css_class, emoji = map_label(result[0]['label'])
            confidence_score = result[0]['score'] 
            
            new_post = {
                "id": f"post_new_{len(st.session_state.feed)}",
                "user": "You", "time": "Just now",
                "text": user_text, 
                "label": display_name, "css": css_class, "emoji": emoji, "confidence": confidence_score,
                "likes": 0, "is_liked": False, 
                "reposts": 0, "is_reposted": False,
                "comments": []
            }
            st.session_state.feed.insert(0, new_post)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render all posts
    for idx, post in enumerate(st.session_state.feed):
        render_post_card(idx, post)


elif page == "Profile":
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>👤 Your Profile</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["My Posts", "My Reposts"])
    
    with tab1:
        st.subheader("Posts created by you")
        my_posts_rendered = False
        for idx, post in enumerate(st.session_state.feed):
            if post['user'] == "You":
                render_post_card(idx, post)
                my_posts_rendered = True
        
        if not my_posts_rendered:
            st.info("You haven't made any posts yet. Head over to the Home feed to create one!")

    with tab2:
        st.subheader("Posts you have reposted")
        reposts_rendered = False
        for idx, post in enumerate(st.session_state.feed):
            if post.get('is_reposted', False):
                render_post_card(idx, post)
                reposts_rendered = True
                
        if not reposts_rendered:
            st.info("You haven't reposted anything yet. Try clicking the repost button on the Home feed!")

elif page == "About Us":
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>👥 About Us</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("Welcome to the MindPulse NLP Classification Project")
        st.write("This application was developed by **Group 9** for the **WQF7007 Natural Language Processing** coursework.")
        
        st.markdown("💻 **Source Code:** [GitHub](https://github.com/24051211-um/mindpulse/blob/main/mindpulse.py)")
        
        st.divider()
        
        st.subheader("Our Mission")
        st.write("Our primary objective is to develop a text classification system that automatically categorizes social media posts to support the early screening of mental health concerns. This initiative directly aligns with the **United Nations Sustainable Development Goal 3 (SDG 3): Good Health and Well-being**, which aims to reduce premature mortality through prevention and early intervention.")
        
        st.divider()

        st.warning("Disclaimer: This system is intended solely as a screening and research tool. The results produced by this model should not be presented or interpreted as a clinical diagnosis.")
        
        st.subheader("Meet the Team")
        st.write("The development of this project was a collaborative effort by our team:")
        
        # Using a Markdown table for a clean, native Streamlit layout
        st.markdown("""
        | Student Name | Core Contributions |
        | :--- | :--- |
        | **JIN QIN** | Documentation Leader |
        | **LEE JER SHEN** | Machine Learning Engineer |
        | **CHEONG MENG BEN** | Deployment Engineer |
        | **HO WEI WEN** | Presenter |
        | **KENNETH WONG WEI KEONG** | Data Engineer |
        """)

elif page == "Model Info":
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>⚙️ Model Information</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("The Dataset & Pre-processing Pipeline")
        st.write("The models are trained on the Reddit Mental Health Dataset (RMHD) sourced from Kaggle, covering posts from January 2019 to August 2022. To preserve the structural integrity and context required for transformer models, traditional methods like stemming or stop-word removal were avoided. Instead, a specialized NLP pipeline was applied:")
        
        st.markdown("""
        * **Noise Removal & Anonymization:** Stripped URLs, HTML tags, and Reddit artifacts (e.g., `[removed]`). Usernames and subreddit mentions were anonymized to `USER` and `SUBREDDIT` to prevent the model from learning spurious associations.
        * **Emotion Normalization Cascade:** Recognizing that emoticons are critical semantic signals in mental health discourse, a 3-layer cascade (using Unicode demojization, a custom 80+ regex lexicon, and the `emot` library) translated symbols like `T-T` or `XD` into explicit English text descriptions.
        * **Deduplication & Balancing:** Removed over 7,800 duplicate documents to prevent data leakage. The final dataset was rigorously balanced to exactly 50,000 posts for each of the 5 target classes, then split 80/10/10 for training, validation, and testing.
        """)

        st.divider()

        st.subheader("Model Architectures")
        
        # Hugging Face Link
        st.markdown("🤗 **Trained Model Weights:** [View MentalBERT on Hugging Face](https://huggingface.co/ben9899/mindpulse-mentalbert/tree/main)")
        
        st.write("This system evaluates two pre-trained transformer models fine-tuned for sequence classification:")
        st.markdown("""
        * **Baseline Model (BERT):** A general-purpose language model featuring 12 transformer encoder layers, 12 attention heads, and approximately 110 million trainable parameters. It was pre-trained on the BooksCorpus and English Wikipedia.
        * **Proposed Model (MentalBERT):** Utilizing the same base architecture as BERT, this domain-adapted model was pre-trained specifically on a large corpus of text from online mental health communities. This allows it to better understand domain-specific terminology, informal expressions, and emotional language.
        """)

        st.divider()

        st.subheader("Fine-Tuning & Training Optimization")
        st.write("To adapt the 110M parameter models to our 200k post dataset, several optimization techniques were applied:")
        st.markdown("""
        * **Mixed Precision Training (FP16):** Used 16-bit floating point arithmetic for forward/backward passes to reduce GPU memory consumption by 50%, while maintaining 32-bit gradients for stability.
        * **Regularization:** Applied L2 Weight Decay (0.01), Dropout (p=0.1), and Gradient Clipping (1.0) to prevent overfitting.
        * **AdamW Optimization:** Utilized a warmup-then-linear-decay schedule (reaching 2e-5 over 5,000 steps) to stabilize early training gradients.
        * **Early Stopping:** Training monitored validation loss with a patience of 2 epochs, restoring the best-performing checkpoint.
        """)

        st.divider()

        st.subheader("Performance Evaluation & Insights")
        st.write("Both the baseline and proposed models were evaluated on the 25,000 sample balanced test set. The side by side performance metrics are as follows:")
        
        st.markdown("""
        | Metric | BERT (Baseline) | MentalBERT (Proposed) |
        | :--- | :--- | :--- |
        | **Macro ROC-AUC** | 0.9140 | 0.9144 |
        | **Accuracy** | 0.7009 | 0.7017 |
        | **Macro Precision** | 0.7009 | 0.7031 |
        | **Macro Recall** | 0.7009 | 0.7017 |
        | **Macro F1** | 0.6987 | 0.7012 |
        | **MCC** | 0.6272 | 0.6277 |
        """)
        
        st.markdown("#### Key Findings")
        st.info("""
        **1. Semantic Overlap vs. Model Failure:**
        While Anxiety and Loneliness were highly distinctive (F1 ~0.82), Depression performed weakest (F1=0.52). The confusion matrix revealed that over 1,250 Depression posts were classified as SuicideWatch. This reflects genuine clinical and semantic overlap between the two states rather than a model failure.
        
        **2. High Crisis Recall:**
        Crucially for a screening tool, the model maintained a high recall (0.756) for SuicideWatch, successfully catching the vast majority of high-risk crisis posts.
        
        **3. Probability Calibration:**
        A high Macro ROC-AUC (0.914) compared to overall accuracy (~0.70) indicates that the model ranks classes very well and outputs well-calibrated probability distributions, even if it struggles at the exact decision boundaries of comorbid conditions.
        """)
