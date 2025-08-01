import streamlit as st
import plotly.express as px
import pandas as pd

from analysis_service import get_trending_stocks

def render_trending_page():
    st.title("🌟 美股投资推荐")
    st.markdown("### 基于基本面与技术面的Top 50美股分析")
    st.info("评分标准：RSI(30%) + MACD(30%) + 市场情绪(20%) + 价格动量(20%)")
    
    if st.button("🔄 更新推荐列表"):
        with st.spinner("正在分析美股市场，可能需要1-2分钟..."):
            st.session_state['trending'] = get_trending_stocks()
            st.success("更新完成！")
    
    # 首次加载时初始化热门股票
    if 'trending' not in st.session_state:
        with st.spinner("首次加载美股推荐列表，请稍候..."):
            st.session_state['trending'] = get_trending_stocks()
    
    if not st.session_state['trending'].empty:
        # 添加建议图标
        def advice_icon(advice):
            if "强烈买入" in advice:
                return "🚀"
            elif "买入" in advice:
                return "👍"
            elif "观望" in advice:
                return "👀"
            elif "谨慎" in advice:
                return "⚠️"
            else:
                return "👎"
        
        df = st.session_state['trending'].copy()
        df['建议'] = df['买入建议'].apply(advice_icon) + " " + df['买入建议']
        
        st.dataframe(
            df[['股票代码', '公司名称', '当前价格', '涨跌幅', 'RSI', 'MACD', '市场情绪', '情绪分数', '推荐得分', '建议']],
            hide_index=True,
            column_config={
                "涨跌幅": st.column_config.NumberColumn(format="%.2f%%"),
                "当前价格": st.column_config.NumberColumn(format="$%.2f"),
                "情绪分数": st.column_config.ProgressColumn(
                    format="%d", min_value=0, max_value=100
                ),
                "推荐得分": st.column_config.ProgressColumn(
                    format="%d", min_value=0, max_value=100
                )
            },
            height=800
        )
        
        # 情绪分析可视化
        st.markdown("### 市场情绪分布")
        sentiment_df = pd.DataFrame({
            '情绪': df['市场情绪'].value_counts().index,
            '数量': df['市场情绪'].value_counts().values
        })
        fig = px.pie(sentiment_df, names='情绪', values='数量', 
                     title='推荐股票情绪分布', 
                     color='情绪',
                     color_discrete_map={'正面':'#2ECC71', '中性':'#3498DB', '负面':'#E74C3C'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无股票数据")
