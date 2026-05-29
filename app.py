import streamlit as st
import re
import csv
import os
from datetime import datetime # 日時を取得するための機能を追加

# ファイルパスの定義
CSV_FILE = "ng_words.csv"
LOG_FILE = "check_log.csv" # 履歴を保存するファイル名を追加

# ==========================================
# 1. CSV辞書を読み込む関数
# ==========================================
def load_dictionary():
    dictionary = []
    if not os.path.exists(CSV_FILE):
        return dictionary
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dictionary.append(row)
    return dictionary

# ==========================================
# 2. 判定ロジック関数（正規表現対応版）
# ==========================================
def check_text(text, dictionary):
    results = []
    for item in dictionary:
        word_pattern = item["word"]
        reason = item["reason"]
        match_type = item["match_type"]
        
        if match_type == "exact":
            if word_pattern in text:
                count = text.count(word_pattern)
                results.append({
                    "matched_text": word_pattern,
                    "reason": reason,
                    "count": count,
                    "pattern": word_pattern
                })
        elif match_type == "regex":
            matches = re.findall(word_pattern, text)
            if matches:
                unique_matches = set(matches)
                for matched_text in unique_matches:
                    count = text.count(matched_text)
                    results.append({
                        "matched_text": matched_text,
                        "reason": reason,
                        "count": count,
                        "pattern": word_pattern
                    })
    return results

# ==========================================
# 3. ログ（履歴）を保存する関数を追加
# ==========================================
def save_log(input_text, issues):
    """チェックした日時、入力テキスト、検出されたエラー数をCSVに保存する"""
    # ファイルが存在しない場合は、見出し（ヘッダー）行を作成する
    file_exists = os.path.exists(LOG_FILE)
    
    with open(LOG_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # 見出し行
            writer.writerow(["日時", "エラー数", "入力テキスト", "検出されたワード"])
        
        # 保存するデータの作成
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_count = len(issues)
        # 検出されたワードをカンマ区切りの文字列にする
        detected_words = ", ".join([issue["matched_text"] for issue in issues])
        
        # 1行分のデータを書き込む
        writer.writerow([now, error_count, input_text, detected_words])

# ==========================================
# 4. 画面構築（UI）
# ==========================================
def main():
    st.set_page_config(page_title="不動産広告 校閲チェックツール (Ver.3)", layout="wide")
    
    st.title("🏠 不動産広告 校閲チェックツール (Ver.3)")
    st.markdown("チェック結果の履歴を自動保存する機能を追加しました。")

    dictionary = load_dictionary()
    
    with st.sidebar:
        st.header("📋 現在の判定ルール")
        if not dictionary:
            st.error(f"「{CSV_FILE}」が見つからないか、中身が空です。")
        else:
            st.write(f"合計 {len(dictionary)} 個のルールが有効です。")
            st.dataframe(dictionary, use_container_width=True)

    user_input = st.text_area(
        "チェックしたい広告文を入力してください：", 
        height=200
    )
    
    if st.button("校閲チェックを実行"):
        if not dictionary:
            st.error("判定ルールが登録されていないため、チェックを実行できません。")
        elif not user_input.strip():
            st.warning("テキストを入力してください。")
        else:
            st.subheader("🔍 チェック結果")
            
            issues = check_text(user_input, dictionary)
            
            # --- ここでログ保存関数を呼び出す ---
            save_log(user_input, issues)
            
            if not issues:
                st.success("✅ ガイドラインに抵触する表現は見つかりませんでした。")
            else:
                st.error(f"⚠️ {len(issues)} 箇所の指摘事項が見つかりました。修正を検討してください。")
                
                highlighted_text = user_input
                for issue in issues:
                    target = issue["matched_text"]
                    highlighted_text = highlighted_text.replace(
                        target, 
                        f"<span style='color:#d32f2f; background-color:#fce8e6; font-weight:bold; padding:2px 4px; border-radius:3px;'>{target}</span>"
                    )
                
                st.markdown("#### 📝 該当箇所")
                st.markdown(f"<div style='padding:15px; border:1px solid #ecc8c5; border-radius:5px; background-color:#fffbfa; line-height:1.6;'>{highlighted_text}</div>", unsafe_allow_html=True)
                
                st.markdown("#### 💡 指摘内容の詳細")
                for issue in issues:
                    st.warning(f"**「{issue['matched_text']}」**\n\n判定理由: {issue['reason']}")

if __name__ == "__main__":
    main()