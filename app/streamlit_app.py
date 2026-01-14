"""
Streamlit UI для BioIdeas.

Просмотр идей, фильтрация по скорам, ручная разметка.
"""
import sys
from pathlib import Path

# Add src to path for both local and cloud deployment
_src_path = Path(__file__).parent.parent / "src"
if _src_path.exists() and str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

import streamlit as st
import pandas as pd
from bioideas.config import PROCESSED_DIR, MEMOS_DIR
from bioideas.models import IdeaCard, ScoreCard, EloRating, Nugget, Episode
from bioideas.storage import read_jsonl

st.set_page_config(
    page_title="BioIdeas Explorer",
    page_icon="🧬",
    layout="wide",
)


@st.cache_data
def load_data():
    """Загружает все данные."""
    ideas_file = PROCESSED_DIR / "ideas_deduped.jsonl"
    if not ideas_file.exists():
        ideas_file = PROCESSED_DIR / "ideas.jsonl"
    
    # Debug: show paths
    st.sidebar.text(f"Data dir: {PROCESSED_DIR}")
    st.sidebar.text(f"Exists: {PROCESSED_DIR.exists()}")
    st.sidebar.text(f"Files: {list(PROCESSED_DIR.glob('*.jsonl'))[:3]}")
    
    ideas = read_jsonl(ideas_file, IdeaCard) if ideas_file.exists() else []
    scores = read_jsonl(PROCESSED_DIR / "scores.jsonl", ScoreCard)
    elo_ratings = read_jsonl(PROCESSED_DIR / "elo_ratings.jsonl", EloRating)
    nuggets = read_jsonl(PROCESSED_DIR / "nuggets.jsonl", Nugget)
    episodes = read_jsonl(PROCESSED_DIR / "episodes.jsonl", Episode)
    
    return ideas, scores, elo_ratings, nuggets, episodes


def main():
    st.title("🧬 BioIdeas Explorer")
    st.markdown("Анализ идей из биотех-подкастов")
    
    ideas, scores, elo_ratings, nuggets, episodes = load_data()
    
    if not ideas:
        st.warning("Нет данных. Запустите пайплайн сначала.")
        st.code("""
# В терминале:
cd bioideas
pip install -e .
python -m bioideas.pipeline.s01_ingest
python -m bioideas.pipeline.s02_embed_chunks
# ... и т.д.
        """)
        return
    
    scores_map = {s.idea_id: s for s in scores}
    elo_map = {e.idea_id: e for e in elo_ratings}
    nuggets_map = {n.nugget_id: n for n in nuggets}
    
    st.sidebar.header("📊 Статистика")
    st.sidebar.metric("Эпизодов", len(episodes))
    st.sidebar.metric("Идей", len(ideas))
    st.sidebar.metric("Nuggets", len(nuggets))
    st.sidebar.metric("Оценено", len(scores))
    
    st.sidebar.header("🔍 Фильтры")
    
    categories = sorted(set(i.category for i in ideas))
    selected_categories = st.sidebar.multiselect(
        "Категории",
        categories,
        default=categories
    )
    
    horizons = sorted(set(i.horizon for i in ideas))
    selected_horizons = st.sidebar.multiselect(
        "Горизонт",
        horizons,
        default=horizons
    )
    
    min_score = st.sidebar.slider("Мин. общий балл", 0, 50, 20)
    
    sort_by = st.sidebar.selectbox(
        "Сортировка",
        ["Elo рейтинг", "Общий балл", "Solo Start", "Community 6m", "Blue Ocean"]
    )
    
    filtered_ideas = [
        i for i in ideas
        if i.category in selected_categories
        and i.horizon in selected_horizons
        and (scores_map.get(i.idea_id) is None or scores_map[i.idea_id].total_score >= min_score)
    ]
    
    sort_key_map = {
        "Elo рейтинг": lambda i: elo_map.get(i.idea_id, EloRating(idea_id="")).elo,
        "Общий балл": lambda i: scores_map.get(i.idea_id, ScoreCard(idea_id="", score_horizon=0, score_blue_ocean=0, score_solo_start=0, score_community_6m=0, score_exit_2_3y=0, data_access_risk="low", regulatory_risk="low", execution_risk="low", rationale_ru="")).total_score,
        "Solo Start": lambda i: scores_map.get(i.idea_id, ScoreCard(idea_id="", score_horizon=0, score_blue_ocean=0, score_solo_start=0, score_community_6m=0, score_exit_2_3y=0, data_access_risk="low", regulatory_risk="low", execution_risk="low", rationale_ru="")).score_solo_start,
        "Community 6m": lambda i: scores_map.get(i.idea_id, ScoreCard(idea_id="", score_horizon=0, score_blue_ocean=0, score_solo_start=0, score_community_6m=0, score_exit_2_3y=0, data_access_risk="low", regulatory_risk="low", execution_risk="low", rationale_ru="")).score_community_6m,
        "Blue Ocean": lambda i: scores_map.get(i.idea_id, ScoreCard(idea_id="", score_horizon=0, score_blue_ocean=0, score_solo_start=0, score_community_6m=0, score_exit_2_3y=0, data_access_risk="low", regulatory_risk="low", execution_risk="low", rationale_ru="")).score_blue_ocean,
    }
    
    filtered_ideas.sort(key=sort_key_map[sort_by], reverse=True)
    
    st.header(f"💡 Идеи ({len(filtered_ideas)})")
    
    tab1, tab2, tab3 = st.tabs(["📋 Список", "📊 Таблица", "📄 Memos"])
    
    with tab1:
        for i, idea in enumerate(filtered_ideas[:50]):
            score = scores_map.get(idea.idea_id)
            elo = elo_map.get(idea.idea_id)
            
            with st.expander(f"**{i+1}. {idea.title_ru}** | {idea.category} | {idea.horizon}y"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{idea.one_liner_ru}**")
                    st.markdown(f"**Проблема:** {idea.problem_ru}")
                    st.markdown(f"**Решение:** {idea.solution_ru}")
                    st.markdown(f"**Wedge:** {idea.wedge_ru}")
                    st.markdown(f"**MVP (3-6m):** {idea.mvp_3_6m_ru}")
                    st.markdown(f"**Community Hook:** {idea.community_hook_ru}")
                    st.markdown(f"**Монетизация:** {idea.early_monetization_ru}")
                    st.markdown(f"**Покупатели:** {', '.join(idea.acquirer_types_ru)}")
                    st.markdown(f"**Риски:** {', '.join(idea.key_risks_ru)}")
                
                with col2:
                    if score:
                        st.metric("Общий балл", f"{score.total_score}/50")
                        st.progress(score.score_horizon / 10, text=f"Horizon: {score.score_horizon}")
                        st.progress(score.score_blue_ocean / 10, text=f"Blue Ocean: {score.score_blue_ocean}")
                        st.progress(score.score_solo_start / 10, text=f"Solo Start: {score.score_solo_start}")
                        st.progress(score.score_community_6m / 10, text=f"Community: {score.score_community_6m}")
                        st.progress(score.score_exit_2_3y / 10, text=f"Exit: {score.score_exit_2_3y}")
                        
                        risk_colors = {"low": "🟢", "medium": "🟡", "high": "🔴"}
                        st.markdown(f"Data Risk: {risk_colors[score.data_access_risk]}")
                        st.markdown(f"Regulatory Risk: {risk_colors[score.regulatory_risk]}")
                        st.markdown(f"Execution Risk: {risk_colors[score.execution_risk]}")
                    
                    if elo:
                        st.metric("Elo", f"{elo.elo:.0f}", f"{elo.wins}W-{elo.losses}L")
                
                if idea.source_nugget_ids:
                    st.markdown("---")
                    st.markdown("**Source Nuggets:**")
                    for nid in idea.source_nugget_ids[:5]:
                        nugget = nuggets_map.get(nid)
                        if nugget:
                            st.markdown(f"- [{nugget.kind}] {nugget.text_ru}")
    
    with tab2:
        data = []
        for idea in filtered_ideas:
            score = scores_map.get(idea.idea_id)
            elo = elo_map.get(idea.idea_id)
            data.append({
                "Title": idea.title_ru[:50],
                "Category": idea.category,
                "Horizon": idea.horizon,
                "Total": score.total_score if score else 0,
                "Solo": score.score_solo_start if score else 0,
                "Community": score.score_community_6m if score else 0,
                "Blue Ocean": score.score_blue_ocean if score else 0,
                "Elo": int(elo.elo) if elo else 0,
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, height=600)
    
    with tab3:
        st.markdown("### Decision Memos")
        memo_files = sorted(MEMOS_DIR.glob("*.md"))
        
        if not memo_files:
            st.info("Нет memo. Запустите step 08.")
        else:
            for memo_file in memo_files:
                with st.expander(memo_file.stem):
                    st.markdown(memo_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
