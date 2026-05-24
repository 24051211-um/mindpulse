import streamlit as st
from transformers import pipeline
from datetime import datetime
from streamlit_option_menu import option_menu

# ==========================================
# 1. PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="MindPulse | Dashboard", page_icon="🫀", layout="wide")

st.markdown("""
<style>
    .stApp { font-family: 'Inter', sans-serif; }
    
    .badge {
        padding: 6px 14px; border-radius: 20px; font-size: 15px; font-weight: 700;
        display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px;
    }
    .badge-depression { background-color: #F3E8FF; color: #7E22CE; }
    .badge-anxiety { background-color: #FEE2E2; color: #DC2626; }
    .badge-lonely { background-color: #E0F2FE; color: #2563EB; }
    .badge-mentalhealth { background-color: #DCFCE7; color: #16A34A; }
    .badge-suicidewatch { background-color: #FCE7F3; color: #BE185D; }
    
    .metric-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
    .metric-label { font-size: 13px; font-weight: 600; opacity: 0.8; }
    .progress-bg { background-color: rgba(128, 128, 128, 0.2); height: 6px; border-radius: 3px; width: 100%; overflow: hidden; }
    .progress-fill { background-color: #818CF8; height: 100%; border-radius: 3px; }

    /* Comment Styling */
    .comment-block { 
        padding: 10px 12px; background: rgba(128,128,128,0.05); 
        border-radius: 8px; margin-bottom: 4px;
        border-left: 3px solid #818CF8;
    }
    .comment-meta { font-size: 12px; font-weight: bold; margin-bottom: 4px; }
    .comment-time { font-weight: normal; opacity: 0.6; margin-left: 8px; }
    .comment-text { font-size: 14px; opacity: 0.9; }

    .stButton button { width: 100%; border-radius: 8px; }
    
    /* Make comment like buttons smaller */
    .comment-like-btn button { padding: 2px 5px !important; min-height: 0px !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STATE MANAGEMENT & HELPERS
# ==========================================
@st.cache_resource
def load_model():
    try:
        return pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
    except:
        return None

classifier = load_model()

def map_label(raw_label):
    label = raw_label.lower()
    if "sadness" in label or "depression" in label: return "Depression", "badge-depression", "😔"
    elif "fear" in label or "anxiety" in label: return "Anxiety", "badge-anxiety", "😰"
    elif "anger" in label or "suicide" in label: return "Suicide Watch", "badge-suicidewatch", "🚨"
    elif "lonely" in label: return "Loneliness", "badge-lonely", "😶"
    else: return "Mental Health", "badge-mentalhealth", "🧠"

def current_time_str():
    return datetime.now().strftime("%I:%M %p")

# Expanded session state to include comment likes
if 'feed' not in st.session_state:
    st.session_state.feed = [
        {
            "id": "post_1", "user": "User_837", "time": "10:30 AM", 
            "text": "I've been feeling really overwhelmed lately. Can't focus, my chest is tight. It's making it hard to get through the day. Is this just stress?", 
            "label": "Anxiety", "css": "badge-anxiety", "emoji": "😰", 
            "likes": 14, "is_liked": False,
            "reposts": 2, "is_reposted": False,
            "comments": [
                {"user": "Dr_Smith", "time": "11:15 AM", "text": "Take deep breaths. Try the 4-7-8 method.", "likes": 5, "is_liked": False},
                {"user": "Anon_12", "time": "12:05 PM", "text": "I feel exactly the same way right now.", "likes": 1, "is_liked": False}
            ]
        },
        {
            "id": "post_2", "user": "User_412", "time": "Yesterday", 
            "text": "Nobody really understands what it's like. I feel completely disconnected from everyone around me.", 
            "label": "Loneliness", "css": "badge-lonely", "emoji": "😶", 
            "likes": 8, "is_liked": False,
            "reposts": 0, "is_reposted": False,
            "comments": []
        }
    ]

# Callbacks for Posts
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
            "likes": 0, "is_liked": False # Initialize new comments with 0 likes
        }
        st.session_state.feed[post_idx]["comments"].append(new_comment)

# Callback for Comments
def toggle_comment_like(post_idx, comment_idx):
    if st.session_state.feed[post_idx]["comments"][comment_idx].get("is_liked", False):
        st.session_state.feed[post_idx]["comments"][comment_idx]["likes"] -= 1
        st.session_state.feed[post_idx]["comments"][comment_idx]["is_liked"] = False
    else:
        # Using .get() ensures backward compatibility if older comments lack the key
        current_likes = st.session_state.feed[post_idx]["comments"][comment_idx].get("likes", 0)
        st.session_state.feed[post_idx]["comments"][comment_idx]["likes"] = current_likes + 1
        st.session_state.feed[post_idx]["comments"][comment_idx]["is_liked"] = True

# ==========================================
# 3. REUSABLE UI COMPONENT
# ==========================================
def render_post_card(idx, post):
    """A helper function to draw a post card exactly the same way on any page."""
    left_col, right_col = st.columns([2, 1])

    with left_col:
        with st.container(border=True): 
            # Post Content
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background-color: #818CF8; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px;">
                    {post['user'][0].upper()}
                </div>
                <div style="line-height: 1.2;">
                    <div style="font-weight: bold; font-size: 15px;">{post['user']}</div>
                    <div style="font-size: 12px; opacity: 0.6;">{post['time']}</div>
                </div>
            </div>
            <div style="font-size: 16px; margin-bottom: 20px;">
                {post['text']}
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive Buttons (Like, Repost) on their own row
            act1, act2, _ = st.columns([2, 2, 6])
            
            heart_icon = "❤️" if post['is_liked'] else "🤍"
            act1.button(f"{heart_icon} {post['likes']}", key=f"like_{post['id']}_pg_{page}", on_click=toggle_like, args=(idx,))
            
            repost_icon = "🔁" if post.get('is_reposted', False) else "🔄"
            act2.button(f"{repost_icon} {post.get('reposts', 0)}", key=f"repost_{post['id']}_pg_{page}", on_click=toggle_repost, args=(idx,))
            
            # Move the Expander OUT of the nested columns so it sits nicely below the buttons
            with st.expander(f"💬 View/Add Comments ({len(post['comments'])})", expanded=False):
                if len(post['comments']) > 0:
                    for c_idx, comment in enumerate(post['comments']):
                        # Because the expander is no longer in a nested column, this is allowed!
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

    with right_col:
        with st.container(border=True):
            st.markdown(f"""
            <div style="font-size: 13px; font-weight: 600; opacity: 0.7; margin-bottom: 10px;">Classification:</div>
            <div class="{post['css']} badge">
                <span>{post['emoji']}</span>
                <span>{post['label']}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Emotional Intensity: High</span>
                <div class="progress-bg"><div class="progress-fill" style="width: 85%;"></div></div>
            </div>
            <div class="metric-row">
                <span class="metric-label">Sentiment: Negative</span>
                <div class="progress-bg"><div class="progress-fill" style="width: 70%;"></div></div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🫀 MindPulse</h2><br>", unsafe_allow_html=True)
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
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            with st.form(key='post_form', clear_on_submit=True):
                user_text = st.text_input("Describe your thoughts...", placeholder="Type a new post...")
                submit_btn = st.form_submit_button(label="Analyze & Post")

    if submit_btn and user_text.strip() and classifier:
        with st.spinner("Processing NLP sequence..."):
            result = classifier(user_text)
            display_name, css_class, emoji = map_label(result[0]['label'])
            
            new_post = {
                "id": f"post_new_{len(st.session_state.feed)}",
                "user": "You", "time": "Just now",
                "text": user_text, "label": display_name, "css": css_class, "emoji": emoji,
                "likes": 0, "is_liked": False, 
                "reposts": 0, "is_reposted": False,
                "comments": []
            }
            st.session_state.feed.insert(0, new_post)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render all posts on Home feed
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

# ==========================================
# Placeholder Pages & Documentation
# ==========================================
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
        
        st.divider()
        
        st.subheader("Our Mission")
        st.write("Our primary objective is to develop a text classification system that automatically categorizes social media posts to support the early screening of mental health concerns. This initiative directly aligns with the **United Nations Sustainable Development Goal 3 (SDG 3): Good Health and Well-being**, which aims to reduce premature mortality through prevention and early intervention.")
        
        st.divider()

        st.warning("Disclaimer: This system is intended solely as a screening and research tool. The results produced by this model should not be presented or interpreted as a clinical diagnosis.")
        
        st.subheader("Meet the Team")
        st.write("The development of this project was a collaborative effort by our team:")
        
        # Using a Markdown table for a clean, native Streamlit layout
        st.markdown("""
        | Student Name | Student ID | Core Contributions |
        | :--- | :--- | :--- |
        | **JIN QIN** | U2103281 | Model Training & Evaluation |
        | **LEE JER SHEN** | U2103193 | Model Architecture Design & Training |
        | **CHEONG MENG BEN** | 24051211 | App Deployment |
        | **HO WEI WEN** | 23097016 | Problem Statement, Objectives, Issues & Challenges |
        | **KENNETH WONG WEI KEONG** | U2103199/1 | Data Source Sourcing & Preprocessing Pipeline |
        """)

elif page == "Model Info":
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>⚙️ Model Information</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("The Dataset")
        st.write("The models are trained on the Reddit Mental Health Dataset (RMHD) sourced from Kaggle, covering posts from January 2019 to August 2022. After extensive cleaning using Python's Regular Expressions and emoji libraries, the data was rigorously balanced to contain exactly 50,000 posts for each of the five target subreddits: mentalhealth, anxiety, depression, lonely, and SuicideWatch.")

        st.divider()

        st.subheader("Model Architectures")
        st.write("This system evaluates two pre-trained transformer models fine-tuned for sequence classification:")
        st.markdown("""
        * **Baseline Model (BERT):** A general-purpose language model featuring 12 transformer encoder layers, 12 attention heads, and approximately 110 million trainable parameters. It was pre-trained on the BooksCorpus and English Wikipedia.
        * **Proposed Model (MentalBERT):** Utilizing the same base architecture as BERT, this domain-adapted model was pre-trained specifically on a large corpus of text from online mental health communities. This allows it to better understand domain-specific terminology, informal expressions, and emotional language.
        """)

        st.divider()

        st.subheader("Fine-Tuning & Pipeline Mechanics")
        st.markdown("""
        * **Tokenization:** Text is converted to subword token IDs using the WordPiece algorithm, normalized to a maximum sequence length of 512 tokens.
        * **Classification Head:** The aggregate semantic representation of the post is extracted and fed into a classification head consisting of a Dropout layer (rate = 0.1) and a Linear layer. This outputs 5 logits passed through a softmax function to determine the highest probability class.
        """)